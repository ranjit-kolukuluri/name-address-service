# core/models.py
"""
Pydantic models for the name and address validator
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# API Request Models
class NameRecord(BaseModel):
    uniqueid: str = Field(..., description="Unique identifier for the record")
    name: str = Field(..., description="Full name to validate")
    gender: Optional[str] = Field("", description="Optional gender hint (M/F)")
    party_type: Optional[str] = Field("", description="Optional party type (I/O)")
    parseInd: Optional[str] = Field("", description="Parse indicator (Y/N)")


class NameValidationRequest(BaseModel):
    records: List[NameRecord] = Field(..., description="List of name records to validate")


class AddressRecord(BaseModel):
    first_name: str
    last_name: str
    street_address: str
    city: str
    state: str
    zip_code: str


# Response Models
class ParsedComponents(BaseModel):
    first_name: Optional[str] = ""
    last_name: Optional[str] = ""
    middle_name: Optional[str] = ""
    organization_name: Optional[str] = ""


class Suggestions(BaseModel):
    name_suggestions: Optional[List[str]] = []
    gender_prediction: Optional[str] = ""
    party_type_prediction: Optional[str] = ""


class ValidationResult(BaseModel):
    uniqueid: str
    name: str
    gender: str
    party_type: str
    parse_indicator: str
    validation_status: str
    confidence_score: float
    parsed_components: ParsedComponents
    suggestions: Suggestions
    errors: List[str]
    warnings: List[str]


class NameValidationResponse(BaseModel):
    status: str
    processed_count: int
    successful_count: int
    results: List[ValidationResult]
    processing_time_ms: int
    timestamp: str


class AddressValidationResult(BaseModel):
    success: bool
    valid: bool
    deliverable: bool
    standardized: Optional[Dict[str, str]] = None
    metadata: Optional[Dict[str, Any]] = None
    confidence: float = 0.0
    error: Optional[str] = None
    details: Optional[str] = None


class ServiceStatus(BaseModel):
    name_validation_available: bool
    address_validation_available: bool
    api_version: str
    timestamp: str