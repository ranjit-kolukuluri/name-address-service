# api/main.py
"""
Updated FastAPI server for name and address validation with dictionary integration
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import pandas as pd
import sys
from pathlib import Path

# Add parent directory to path
current_file = Path(__file__).resolve()
parent_dir = current_file.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from core.services import ValidationService
from core.models import (
    NameValidationRequest, NameValidationResponse, AddressRecord,
    AddressValidationResult, ServiceStatus
)
from utils.logger import logger
from utils.config import Config

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced Name & Address Validation API",
    description="Professional validation service with dictionary integration and AI fallback",
    version=Config.API_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize enhanced validation service
validation_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize enhanced validation service on startup"""
    global validation_service
    
    logger.info("Starting Enhanced Name & Address Validation API v2.0", "API")
    
    try:
        validation_service = ValidationService()
        dict_status = "with dictionaries" if validation_service.dictionary_status else "AI-only mode"
        logger.info(f"Enhanced validation service initialized {dict_status}", "API")
    except Exception as e:
        logger.error(f"Failed to initialize validation service: {e}", "API")

# Enhanced health check endpoint
@app.get("/health")
async def health_check():
    """Enhanced health check endpoint"""
    dict_status = "loaded" if validation_service and validation_service.dictionary_status else "not_available"
    
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00",
        "version": Config.API_VERSION,
        "format": "v2.0 - Enhanced with Dictionary Integration",
        "dictionary_status": dict_status,
        "validation_mode": "Dictionary + AI" if dict_status == "loaded" else "AI Only"
    }

# Enhanced service status endpoint
@app.get("/status", response_model=ServiceStatus)
async def service_status():
    """Get enhanced service status with dictionary information"""
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not initialized"
        )
    
    status = validation_service.get_service_status()
    return ServiceStatus(**status)

# Main enhanced name validation endpoint
@app.post("/api/v2/validate-names", response_model=NameValidationResponse)
async def validate_names_v2_enhanced(request: NameValidationRequest):
    """
    Enhanced name validation with dictionary lookup and AI fallback
    
    Returns additional fields:
    - validationMethod: "deterministic", "hybrid", or "ai_fallback"
    - Dictionary-based confidence scoring
    - Enhanced organization detection
    - Improved gender prediction
    """
    
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not available"
        )
    
    try:
        # Convert Pydantic models to dict format
        names_data = {"names": [name.dict() for name in request.names]}
        
        # Process with enhanced validation
        result = validation_service.validate_names(names_data)
        
        # Log processing statistics
        if 'processing_stats' in result:
            stats = result['processing_stats']
            methods = stats.get('validation_methods', {})
            det_count = methods.get('deterministic', 0)
            hybrid_count = methods.get('hybrid', 0)
            ai_count = methods.get('ai_fallback', 0)
            
            logger.info(
                f"Enhanced API v2 processed {len(request.names)} records - "
                f"Dictionary: {det_count}, Hybrid: {hybrid_count}, AI: {ai_count}",
                "API"
            )
        
        # Convert to response model (exclude processing_stats from response)
        response_data = {"names": result['names']}
        response = NameValidationResponse(**response_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Enhanced API v2 validation error: {e}", "API")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced validation processing failed: {str(e)}"
        )

# Legacy endpoint (v1 compatibility)
@app.post("/api/v1/validate-names")
async def validate_names_v1_legacy(request: dict):
    """
    Legacy v1 endpoint for backward compatibility
    Converts old format to new format internally
    """
    
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not available"
        )
    
    try:
        # Convert old format to new format
        old_records = request.get('records', [])
        new_names = []
        
        for record in old_records:
            new_name = {
                'uniqueID': record.get('uniqueid', ''),
                'fullName': record.get('name', ''),
                'genderCd': record.get('gender', ''),
                'partyTypeCd': record.get('party_type', ''),
                'parseInd': record.get('parseInd', 'Y')
            }
            new_names.append(new_name)
        
        # Process with enhanced service
        result = validation_service.validate_names({'names': new_names})
        
        # Convert back to old format for response
        old_format_results = []
        for new_result in result['names']:
            # Determine validation status based on enhanced result
            validation_status = 'valid' if new_result['parseStatus'] in ['Parsed', 'Not Parsed', 'Organization'] else 'invalid'
            
            old_result = {
                'uniqueid': new_result['uniqueID'],
                'name': new_result['fullName'],
                'gender': new_result['outGenderCd'],
                'party_type': new_result['partyTypeCd'],
                'parse_indicator': new_result['parseInd'],
                'validation_status': validation_status,
                'confidence_score': float(new_result['confidenceScore']) / 100,
                'parsed_components': {
                    'first_name': new_result['firstName'] or '',
                    'last_name': new_result['lastName'] or '',
                    'middle_name': new_result['middleName'] or '',
                    'organization_name': new_result['fullName'] if new_result['partyTypeCd'] == 'O' else ''
                },
                'suggestions': {
                    'name_suggestions': [],
                    'gender_prediction': new_result['outGenderCd'],
                    'party_type_prediction': new_result['partyTypeCd']
                },
                'errors': [] if new_result['parseStatus'] != 'Error' else [new_result['errorMessage']],
                'warnings': [] if new_result['parseStatus'] != 'Warning' else [new_result['errorMessage']],
                'validation_method': new_result.get('validationMethod', 'unknown')  # Enhanced info
            }
            old_format_results.append(old_result)
        
        # Calculate success metrics
        successful_count = len([r for r in old_format_results if r['validation_status'] == 'valid'])
        
        return {
            'status': 'success',
            'processed_count': len(old_format_results),
            'successful_count': successful_count,
            'dictionary_enabled': validation_service.dictionary_status,  # Enhanced info
            'results': old_format_results,
            'processing_time_ms': result.get('processing_stats', {}).get('processing_time_ms', 0),
            'timestamp': '2024-01-01T00:00:00'
        }
        
    except Exception as e:
        logger.error(f"API v1 legacy error: {e}", "API")
        raise HTTPException(
            status_code=500,
            detail=f"Legacy validation failed: {str(e)}"
        )

# Single address validation endpoint
@app.post("/api/v2/validate-address", response_model=AddressValidationResult)
async def validate_address(address: AddressRecord):
    """
    Validate a single address using USPS API
    """
    
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not available"
        )
    
    if not validation_service.is_address_validation_available():
        raise HTTPException(
            status_code=503,
            detail="USPS API not configured"
        )
    
    try:
        # Validate the address
        result = validation_service.validate_single_address(address.dict())
        
        return AddressValidationResult(**result)
        
    except Exception as e:
        logger.error(f"Address validation error: {e}", "API")
        raise HTTPException(
            status_code=500,
            detail=f"Address validation failed: {str(e)}"
        )

# Enhanced complete record validation endpoint
@app.post("/api/v2/validate-complete")
async def validate_complete_record(
    first_name: str,
    last_name: str,
    street_address: str,
    city: str,
    state: str,
    zip_code: str
):
    """
    Enhanced complete record validation (name + address)
    """
    
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not available"
        )
    
    try:
        result = validation_service.validate_complete_record(
            first_name, last_name, street_address, city, state, zip_code
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced complete validation error: {e}", "API")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced complete validation failed: {str(e)}"
        )

# Enhanced CSV upload endpoint
@app.post("/api/v2/upload-csv")
async def upload_csv_enhanced(file: UploadFile = File(...)):
    """
    Enhanced CSV upload with validation method tracking
    """
    
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not available"
        )
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=400,
            detail="File must be CSV format"
        )
    
    try:
        # Read CSV
        df = pd.read_csv(file.file)
        logger.info(f"Enhanced CSV uploaded: {file.filename} ({len(df)} rows)", "API")
        
        # Process names with enhanced validation
        result = validation_service.process_csv_names(df)
        
        return result
        
    except Exception as e:
        logger.error(f"Enhanced CSV processing error: {e}", "API")
        raise HTTPException(
            status_code=500,
            detail=f"Enhanced CSV processing failed: {str(e)}"
        )

# Dictionary status endpoint
@app.get("/api/v2/dictionary-status")
async def get_dictionary_status():
    """Get detailed dictionary loading status"""
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not available"
        )
    
    validator = validation_service.name_validator
    
    return {
        "dictionaries_loaded": validator.dictionary_loaded,
        "dictionary_path": validator.dictionary_path,
        "available_dictionaries": {
            "first_names": len(validator.first_names_set) > 0,
            "surnames": len(validator.surnames_set) > 0,
            "gender_mappings": len(validator.name_to_gender) > 0,
            "nicknames": len(validator.nickname_to_standard) > 0,
            "business_words": len(validator.business_words_set) > 0,
            "company_suffixes": len(validator.company_suffixes_set) > 0,
            "name_prefixes": len(validator.name_prefixes_set) > 0
        },
        "lookup_counts": {
            "first_names": len(validator.first_names_set),
            "surnames": len(validator.surnames_set),
            "gender_mappings": len(validator.name_to_gender),
            "nickname_mappings": len(validator.nickname_to_standard),
            "business_words": len(validator.business_words_set),
            "company_suffixes": len(validator.company_suffixes_set),
            "name_prefixes": len(validator.name_prefixes_set)
        }
    }

# Enhanced example endpoint
@app.get("/api/v2/example")
async def get_enhanced_example_payload():
    """Get enhanced example API payload for testing"""
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not available"
        )
    
    return validation_service.get_example_payload()

# Legacy example endpoint
@app.get("/api/v1/example")
async def get_example_payload_v1():
    """Get example API payload for testing (legacy format)"""
    return {
        "records": [
            {
                "uniqueid": "001",
                "name": "John Michael Smith",
                "gender": "",
                "party_type": "I",
                "parseInd": "Y"
            },
            {
                "uniqueid": "002",
                "name": "TechCorp Solutions LLC",
                "gender": "",
                "party_type": "O",
                "parseInd": "N"
            },
            {
                "uniqueid": "003",
                "name": "Mary Johnson-Williams",
                "gender": "F",
                "party_type": "",
                "parseInd": "Y"
            }
        ]
    }

# Enhanced API Documentation endpoint
@app.get("/api/v2/documentation")
async def get_enhanced_api_documentation():
    """Get enhanced API documentation with dictionary integration details"""
    dict_status = "loaded" if validation_service and validation_service.dictionary_status else "not_available"
    
    return {
        "version": "2.0.0",
        "description": "Enhanced Name & Address Validation API with dictionary integration and AI fallback",
        "dictionary_status": dict_status,
        "features": [
            "Dictionary-based deterministic validation for maximum accuracy",
            "AI fallback for names not in dictionaries", 
            "Intelligent gender prediction with dictionary support",
            "Smart organization vs individual detection",
            "Enhanced name parsing with comprehensive prefix/suffix extraction",
            "Nickname standardization using dictionary mappings",
            "Multi-factor confidence scoring with method transparency",
            "USPS address validation integration",
            "Validation method tracking (deterministic/hybrid/ai_fallback)"
        ],
        "validation_methods": {
            "deterministic": "Uses dictionary lookup for exact matches - highest accuracy",
            "hybrid": "Combines dictionary lookup with AI prediction",
            "ai_fallback": "AI-based pattern matching when dictionaries can't help"
        },
        "input_format": {
            "endpoint": "/api/v2/validate-names",
            "method": "POST",
            "structure": {
                "names": [
                    {
                        "uniqueID": "string - unique identifier",
                        "fullName": "string - full name to validate",
                        "genderCd": "string - optional gender code (M/F)",
                        "partyTypeCd": "string - optional party type (I/O)",
                        "parseInd": "string - parse indicator (Y/N)"
                    }
                ]
            }
        },
        "output_format": {
            "structure": {
                "names": [
                    {
                        "uniqueID": "string",
                        "partyTypeCd": "string - I or O",
                        "prefix": "string - Mr, Mrs, Dr, etc.",
                        "firstName": "string",
                        "firstNameStd": "string - standardized first name",
                        "middleName": "string",
                        "lastName": "string", 
                        "suffix": "string - Jr, Sr, III, etc.",
                        "fullName": "string - original input",
                        "inGenderCd": "string - input gender",
                        "outGenderCd": "string - predicted/validated gender",
                        "parseInd": "string - Y/N",
                        "confidenceScore": "string - confidence percentage",
                        "parseStatus": "string - Parsed/Error/Warning",
                        "errorMessage": "string - status message",
                        "validationMethod": "string - deterministic/hybrid/ai_fallback"
                    }
                ]
            }
        },
        "confidence_scoring": {
            "deterministic": "90-99% (dictionary-based validation)",
            "hybrid": "70-90% (partial dictionary match + AI)",
            "ai_fallback": "50-80% (AI pattern matching only)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)