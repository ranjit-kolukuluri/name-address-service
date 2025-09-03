# api/main.py
"""
FastAPI server for name and address validation
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
    description="Professional validation service with USPS integration",
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
        "version": Config.API_VERSION
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

# Name validation endpoint
@app.post("/api/v1/validate-names", response_model=NameValidationResponse)
async def validate_names(request: NameValidationRequest):
    """
    Validate a list of names and return structured results
    
    - **records**: List of name records to validate
    - **uniqueid**: Unique identifier for each record
    - **name**: Full name to validate
    - **gender**: Optional gender hint (M/F)
    - **party_type**: Optional party type hint (I=Individual, O=Organization)  
    - **parseInd**: Parse indicator (Y=parse name, N=use as-is, empty=auto-detect)
    """
    
    if not validation_service:
        raise HTTPException(
            status_code=503,
            detail="Validation service not available"
        )
    
    try:
        # Convert Pydantic models to dict format
        records_dict = [record.dict() for record in request.records]
        
        # Process validation
        result = validation_service.process_api_records(records_dict)
        
        # Convert to response model
        response = NameValidationResponse(**result)
        
        logger.info(f"API call processed: {len(request.records)} records", "API")
        return response
        
    except Exception as e:
        logger.error(f"API validation error: {e}", "API")
        raise HTTPException(
            status_code=500,
            detail=f"Validation processing failed: {str(e)}"
        )

# Single address validation endpoint
@app.post("/api/v1/validate-address", response_model=AddressValidationResult)
async def validate_address(address: AddressRecord):
    """
    Validate a single address using USPS API
    
    - **first_name**: Contact's first name
    - **last_name**: Contact's last name
    - **street_address**: Complete street address
    - **city**: City name
    - **state**: 2-letter state code
    - **zip_code**: ZIP code (5 or 9 digits)
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
@app.post("/api/v1/validate-complete")
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
@app.post("/api/v1/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """
    Upload CSV file for batch name processing
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
        
        # Process names
        result = validation_service.process_csv_names(df)
        
        return result
        
    except Exception as e:
        logger.error(f"CSV processing error: {e}", "API")
        raise HTTPException(
            status_code=500,
            detail=f"CSV processing failed: {str(e)}"
        )

# Example payload endpoint
@app.get("/api/v1/example")
async def get_example_payload():
    """Get example API payload for testing"""
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)