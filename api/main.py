# api/main.py - SIMPLIFIED VERSION WITH CORE FUNCTIONALITY ONLY
"""
Simplified FastAPI server for name and address validation - Core functionality only
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import pandas as pd
import time
import sys
from pathlib import Path
from datetime import datetime

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
    description="Core validation service with name validation and address CSV processing",
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
    
    logger.info("Starting Name & Address Validation API", "API")
    
    try:
        validation_service = ValidationService()
        dict_status = "with dictionaries" if validation_service.dictionary_status else "AI-only mode"
        logger.info(f"Validation service initialized {dict_status}", "API")
    except Exception as e:
        logger.error(f"Failed to initialize validation service: {e}", "API")

# =============================================================================
# CORE ENDPOINTS - ESSENTIAL FUNCTIONALITY ONLY
# =============================================================================

# Health check
@app.get("/health")
async def health_check():
    """Simple health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": Config.API_VERSION,
        "services": {
            "name_validation": validation_service.is_name_validation_available() if validation_service else False,
            "address_validation": validation_service.is_address_validation_available() if validation_service else False,
            "dictionary_loaded": validation_service.dictionary_status if validation_service else False
        }
    }

# Service status
@app.get("/status", response_model=ServiceStatus)
async def service_status():
    """Get service status"""
    if not validation_service:
        raise HTTPException(status_code=503, detail="Validation service not initialized")
    
    status = validation_service.get_service_status()
    return ServiceStatus(**status)

# =============================================================================
# 1. SINGLE ADDRESS VALIDATION
# =============================================================================

@app.post("/api/validate-address", response_model=AddressValidationResult)
async def validate_single_address(address: AddressRecord):
    """
    Validate a single address using USPS API
    
    Core endpoint for single address validation with USPS standardization
    """
    
    if not validation_service:
        raise HTTPException(status_code=503, detail="Validation service not available")
    
    if not validation_service.is_address_validation_available():
        raise HTTPException(status_code=503, detail="USPS API not configured")
    
    try:
        result = validation_service.validate_single_address(address.dict())
        return AddressValidationResult(**result)
        
    except Exception as e:
        logger.error(f"Address validation error: {e}", "API")
        raise HTTPException(status_code=500, detail=f"Address validation failed: {str(e)}")

# =============================================================================
# 2. MULTIPLE CSV UPLOAD WITH AUTO-STANDARDIZATION
# =============================================================================

@app.post("/api/upload-address-csv")
async def upload_address_csv_files(files: List[UploadFile] = File(...)):
    """
    Upload multiple CSV files with automatic format standardization and USPS validation
    
    Core endpoint for batch address processing:
    1. Accepts multiple CSV files (any address format)
    2. Auto-detects column formats (address, street_address, line1, etc.)
    3. Standardizes to USPS format automatically
    4. Validates all addresses with USPS API
    5. Returns combined results with source tracking
    """
    
    if not validation_service:
        raise HTTPException(status_code=503, detail="Validation service not available")
    
    # Validate inputs
    if len(files) > 10:  # Reasonable limit
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per upload")
    
    for file in files:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} must be CSV format")
    
    try:
        start_time = time.time()
        combined_results = []
        file_summaries = []
        total_records = 0
        total_successful = 0
        
        logger.info(f"Processing {len(files)} CSV files", "API")
        
        for file_index, file in enumerate(files):
            try:
                # Read CSV
                df = pd.read_csv(file.file)
                
                if df.empty:
                    file_summaries.append({
                        "filename": file.filename,
                        "status": "skipped", 
                        "reason": "Empty file",
                        "records": 0
                    })
                    continue
                
                logger.info(f"Processing {file.filename}: {len(df)} rows", "API")
                
                # Process with automatic standardization and USPS validation
                result = validation_service.process_csv_addresses(df)
                
                if result['success']:
                    # Add file tracking to each result
                    for i, address_result in enumerate(result['results']):
                        address_result.update({
                            'source_file': file.filename,
                            'file_row_number': i + 1,
                            'global_row_number': len(combined_results) + 1,
                            'auto_standardized': True
                        })
                    
                    combined_results.extend(result['results'])
                    total_records += result['total_records']
                    total_successful += result['successful_validations']
                    
                    file_summaries.append({
                        "filename": file.filename,
                        "status": "completed",
                        "total_records": result['total_records'],
                        "successful_validations": result['successful_validations'],
                        "success_rate": f"{result['success_rate']:.1%}",
                        "auto_standardized": True
                    })
                    
                else:
                    file_summaries.append({
                        "filename": file.filename,
                        "status": "failed",
                        "reason": result.get('error', 'Processing failed'),
                        "records": len(df)
                    })
                    
            except Exception as file_error:
                logger.error(f"Error processing {file.filename}: {file_error}", "API")
                file_summaries.append({
                    "filename": file.filename,
                    "status": "error",
                    "reason": str(file_error),
                    "records": 0
                })
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Return comprehensive results
        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "processing_summary": {
                "total_files": len(files),
                "total_records": total_records,
                "successful_validations": total_successful,
                "success_rate": total_successful / total_records if total_records > 0 else 0,
                "processing_time_ms": processing_time,
                "auto_standardization": "enabled",
                "usps_validation": validation_service.is_address_validation_available()
            },
            "file_summaries": file_summaries,
            "results": combined_results,
            "usage_info": {
                "auto_standardization": "All CSV formats automatically detected and standardized",
                "supported_formats": [
                    "address, city, state, zip",
                    "street_address, city, state_code, zip_code",
                    "line1, city, stateCd, zipCd",
                    "Plus many other variations"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"CSV processing error: {e}", "API")
        raise HTTPException(status_code=500, detail=f"CSV processing failed: {str(e)}")

# =============================================================================
# 3. NAME VALIDATION (EXISTING FUNCTIONALITY)
# =============================================================================

@app.post("/api/upload-names-csv")
async def upload_names_csv_files(files: List[UploadFile] = File(...)):
    """
    Upload multiple CSV files for name validation with dictionary lookup and AI fallback
    
    Core endpoint for batch name processing:
    1. Accepts multiple CSV files (any name format)
    2. Auto-detects name columns (name, full_name, fullName, etc.)
    3. Validates with dictionary + AI fallback
    4. Returns combined results with validation methods
    """
    
    if not validation_service:
        raise HTTPException(status_code=503, detail="Validation service not available")
    
    # Validate inputs
    if len(files) > 10:  # Reasonable limit
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per upload")
    
    for file in files:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail=f"File {file.filename} must be CSV format")
    
    try:
        start_time = time.time()
        combined_results = []
        file_summaries = []
        total_records = 0
        total_successful = 0
        method_stats = {'deterministic': 0, 'hybrid': 0, 'ai_fallback': 0}
        
        logger.info(f"Processing {len(files)} name CSV files", "API")
        
        for file_index, file in enumerate(files):
            try:
                # Read CSV
                df = pd.read_csv(file.file)
                
                if df.empty:
                    file_summaries.append({
                        "filename": file.filename,
                        "status": "skipped", 
                        "reason": "Empty file",
                        "records": 0
                    })
                    continue
                
                logger.info(f"Processing {file.filename}: {len(df)} rows", "API")
                
                # Process with enhanced name validation
                result = validation_service.process_csv_names(df)
                
                if result['success']:
                    # Add file tracking to each result
                    for i, name_result in enumerate(result['results']):
                        name_result.update({
                            'source_file': file.filename,
                            'file_row_number': i + 1,
                            'global_row_number': len(combined_results) + 1
                        })
                    
                    combined_results.extend(result['results'])
                    total_records += result['total_records']
                    total_successful += result['successful_validations']
                    
                    # Aggregate method stats
                    if 'validation_method_breakdown' in result:
                        breakdown = result['validation_method_breakdown']
                        method_stats['deterministic'] += breakdown.get('deterministic', 0)
                        method_stats['hybrid'] += breakdown.get('hybrid', 0)
                        method_stats['ai_fallback'] += breakdown.get('ai_fallback', 0)
                    
                    file_summaries.append({
                        "filename": file.filename,
                        "status": "completed",
                        "total_records": result['total_records'],
                        "successful_validations": result['successful_validations'],
                        "success_rate": f"{result['success_rate']:.1%}",
                        "dictionary_available": result.get('dictionary_available', False)
                    })
                    
                else:
                    file_summaries.append({
                        "filename": file.filename,
                        "status": "failed",
                        "reason": result.get('error', 'Processing failed'),
                        "records": len(df)
                    })
                    
            except Exception as file_error:
                logger.error(f"Error processing {file.filename}: {file_error}", "API")
                file_summaries.append({
                    "filename": file.filename,
                    "status": "error",
                    "reason": str(file_error),
                    "records": 0
                })
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # Return comprehensive results
        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "processing_summary": {
                "total_files": len(files),
                "total_records": total_records,
                "successful_validations": total_successful,
                "success_rate": total_successful / total_records if total_records > 0 else 0,
                "processing_time_ms": processing_time,
                "validation_methods": method_stats,
                "dictionary_available": validation_service.dictionary_status
            },
            "file_summaries": file_summaries,
            "results": combined_results,
            "validation_info": {
                "dictionary_validation": "Enhanced accuracy with dictionary lookup",
                "ai_fallback": "Pattern matching for names not in dictionaries",
                "supported_formats": [
                    "name, first_name, last_name columns",
                    "full_name, fullName, Name columns",
                    "Plus automatic gender and organization detection"
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Name CSV processing error: {e}", "API")
        raise HTTPException(status_code=500, detail=f"Name CSV processing failed: {str(e)}")


@app.post("/api/validate-names", response_model=NameValidationResponse)
async def validate_names(request: NameValidationRequest):
    """
    Enhanced name validation with dictionary lookup and AI fallback
    """
    
    if not validation_service:
        raise HTTPException(status_code=503, detail="Validation service not available")
    
    try:
        names_data = {"names": [name.dict() for name in request.names]}
        result = validation_service.validate_names(names_data)
        
        if 'processing_stats' in result:
            stats = result['processing_stats']
            methods = stats.get('validation_methods', {})
            det_count = methods.get('deterministic', 0)
            hybrid_count = methods.get('hybrid', 0)
            ai_count = methods.get('ai_fallback', 0)
            
            logger.info(
                f"Name validation processed {len(request.names)} records - "
                f"Dictionary: {det_count}, Hybrid: {hybrid_count}, AI: {ai_count}",
                "API"
            )
        
        response_data = {"names": result['names']}
        return NameValidationResponse(**response_data)
        
    except Exception as e:
        logger.error(f"Name validation error: {e}", "API")
        raise HTTPException(status_code=500, detail=f"Name validation failed: {str(e)}")

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@app.get("/api/example-address")
async def get_example_address():
    """Get example address for testing single address validation"""
    return {
        "example_request": {
            "guid": "test1",
            "line1": "1394 N SAINT LOUIS",
            "line2": None,
            "city": "BATESVILLE",
            "stateCd": "AR",
            "zipCd": "72501",
            "countryCd": "US"
        },
        "usage": "POST /api/validate-address"
    }

@app.get("/api/example-names")
async def get_example_names():
    """Get example names for testing name validation"""
    return {
        "example_request": {
            "names": [
                {
                    "uniqueID": "1",
                    "fullName": "Dr. William Smith Jr.",
                    "genderCd": "",
                    "partyTypeCd": "I",
                    "parseInd": "Y"
                },
                {
                    "uniqueID": "2",
                    "fullName": "TechCorp Solutions LLC",
                    "genderCd": "",
                    "partyTypeCd": "O",
                    "parseInd": "N"
                }
            ]
        },
        "usage": "POST /api/validate-names"
    }

@app.get("/api/sample-csv")
async def get_sample_csv():
    """Get sample CSV data for testing multiple file upload"""
    
    sample_data = [
        {"id": "1", "address": "1394 N SAINT LOUIS", "city": "BATESVILLE", "state": "AR", "zip": "72501"},
        {"id": "2", "street_address": "123 Main Street", "apartment": "Apt 4B", "city": "New York", "state_code": "NY", "zip_code": "10001"},
        {"id": "3", "line1": "456 Oak Avenue", "city": "Los Angeles", "stateCd": "CA", "zipCd": "90210"},
        {"id": "4", "address_line_1": "789 Pine Street", "municipality": "Chicago", "province": "IL", "postal_code": "60601"}
    ]
    
    # Convert to CSV string
    import io
    import csv
    
    output = io.StringIO()
    if sample_data:
        fieldnames = sample_data[0].keys()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sample_data)
        csv_content = output.getvalue()
    else:
        csv_content = ""
    
    return {
        "description": "Sample CSV with mixed address formats for testing",
        "csv_content": csv_content,
        "usage": "Save as .csv file and upload to /api/upload-address-csv"
    }

# =============================================================================
# SERVER STARTUP
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    import socket
    
    def is_port_in_use(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return False
            except socket.error:
                return True
    
    def find_available_port(start_port=8000):
        port = start_port
        while is_port_in_use(port):
            port += 1
            if port > 8100:
                raise Exception("No available ports found")
        return port
    
    try:
        port = 8000
        if is_port_in_use(port):
            port = find_available_port(8001)
            print(f"⚠️  Port 8000 in use, using port {port}")
        
        print(f"🌐 API starting on port {port}")
        print(f"📚 Documentation: http://localhost:{port}/docs")
        print(f"🔍 Health check: http://localhost:{port}/health")
        print(f"📋 Core endpoints:")
        print(f"   • POST /api/validate-address - Single address validation")
        print(f"   • POST /api/upload-address-csv - Multiple CSV upload") 
        print(f"   • POST /api/validate-names - Name validation")
        
        uvicorn.run(app, host="0.0.0.0", port=port)
        
    except Exception as e:
        print(f"❌ Failed to start server: {e}")