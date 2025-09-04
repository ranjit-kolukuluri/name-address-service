# api/main.py
"""
Updated FastAPI server for name and address validation with new format
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
    title="Name & Address Validation API",
    description="Professional validation service with USPS integration and AI-based detection",
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

# Initialize validation service
validation_service = None

@app.on_event("startup")
async def startup_event():
    """Initialize validation service on startup"""
    global validation_service
    
    logger.info("Starting Name & Address Validation API v2.0", "API")
    
    try:
        validation_service = ValidationService()
        logger.info("Validation service initialized successfully", "API")
    except Exception as e:
        logger.error(f"Failed to initialize validation service: {e}", "API")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": "2024-01-01T00:00:00",
        "version": Config.API_VERSION,
        "format": "v2.0 - Enhanced with AI detection"
    }

# Service status endpoint
@app.get("/status", response_model=ServiceStatus)
async def service_status():
    """Get detailed service status"""
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not initialized"
        )
    
    status = validation_service.get_service_status()
    return ServiceStatus(**status)

# Main name validation endpoint (new format)
@app.post("/api/v2/validate-names", response_model=NameValidationResponse)
async def validate_names_v2(request: NameValidationRequest):
    """
    Validate names using the new enhanced format with AI detection
    
    Input:
    {
      "names": [
        {
          "uniqueID": "1",
          "fullName": "Bill Smith",
          "genderCd": "M",
          "partyTypeCd": "I", 
          "parseInd": "Y"
        }
      ]
    }
    
    Output:
    {
      "names": [
        {
          "uniqueID": "1",
          "partyTypeCd": "I",
          "prefix": "MR",
          "firstName": "Bill",
          "firstNameStd": "William",
          "middleName": null,
          "lastName": "Smith",
          "suffix": null,
          "fullName": "Bill Smith",
          "inGenderCd": "M",
          "outGenderCd": "M",
          "prefixLt": null,
          "firstNameLt": "BILL",
          "middleNameLt": null,
          "lastNameLt": "SMITH", 
          "suffixLt": null,
          "parseInd": "Y",
          "confidenceScore": "99.9995",
          "parseStatus": "Parsed",
          "errorMessage": "Probably Valid"
        }
      ]
    }
    """
    
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not available"
        )
    
    try:
        # Convert Pydantic models to dict format
        names_data = {"names": [name.dict() for name in request.names]}
        
        # Process validation
        result = validation_service.validate_names(names_data)
        
        # Convert to response model
        response = NameValidationResponse(**result)
        
        logger.info(f"API v2 call processed: {len(request.names)} records", "API")
        return response
        
    except Exception as e:
        logger.error(f"API v2 validation error: {e}", "API")
        raise HTTPException(
            status_code=500,
            detail=f"Validation processing failed: {str(e)}"
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
        
        # Process with new service
        result = validation_service.validate_names({'names': new_names})
        
        # Convert back to old format for response
        old_format_results = []
        for new_result in result['names']:
            old_result = {
                'uniqueid': new_result['uniqueID'],
                'name': new_result['fullName'],
                'gender': new_result['outGenderCd'],
                'party_type': new_result['partyTypeCd'],
                'parse_indicator': new_result['parseInd'],
                'validation_status': 'valid' if new_result['parseStatus'] in ['Parsed', 'Not Parsed'] else 'invalid',
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
                'warnings': []
            }
            old_format_results.append(old_result)
        
        return {
            'status': 'success',
            'processed_count': len(old_format_results),
            'successful_count': len([r for r in old_format_results if r['validation_status'] == 'valid']),
            'results': old_format_results,
            'processing_time_ms': 0,
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

# Complete record validation endpoint
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
    Validate a complete record (name + address)
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
        logger.error(f"Complete validation error: {e}", "API")
        raise HTTPException(
            status_code=500,
            detail=f"Complete validation failed: {str(e)}"
        )

# CSV upload endpoint
@app.post("/api/v2/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload CSV file for batch name processing with new format
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
        logger.info(f"CSV uploaded: {file.filename} ({len(df)} rows)", "API")
        
        # Process names with new format
        result = validation_service.process_csv_names(df)
        
        return result
        
    except Exception as e:
        logger.error(f"CSV processing error: {e}", "API")
        raise HTTPException(
            status_code=500,
            detail=f"CSV processing failed: {str(e)}"
        )

# Example payload endpoint
@app.get("/api/v2/example")
async def get_example_payload_v2():
    """Get example API payload for testing with new format"""
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

# API Documentation endpoint
@app.get("/api/v2/documentation")
async def get_api_documentation():
    """Get API documentation and format information"""
    return {
        "version": "2.0.0",
        "description": "Enhanced Name & Address Validation API with AI-based detection",
        "features": [
            "Intelligent gender prediction using AI when not provided",
            "Smart organization vs individual detection",
            "Enhanced name parsing with prefix/suffix extraction",
            "Name standardization (e.g., Bill -> William)",
            "High-confidence scoring algorithm",
            "USPS address validation integration"
        ],
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
                        "prefixLt": "string - uppercase prefix",
                        "firstNameLt": "string - uppercase first name",
                        "middleNameLt": "string - uppercase middle name",
                        "lastNameLt": "string - uppercase last name",
                        "suffixLt": "string - uppercase suffix",
                        "parseInd": "string - Y/N",
                        "confidenceScore": "string - confidence percentage",
                        "parseStatus": "string - Parsed/Error/Warning",
                        "errorMessage": "string - status message"
                    }
                ]
            }
        },
        "ai_features": {
            "gender_prediction": "Uses pattern analysis and name dictionaries",
            "organization_detection": "Intelligent keyword and pattern matching",
            "name_standardization": "Common nickname to formal name mapping",
            "confidence_scoring": "Multi-factor confidence calculation"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)