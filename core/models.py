# core/models.py
"""
Updated Pydantic models for the name and address validator with new format
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


# API Request Models
class NameRecord(BaseModel):
    uniqueID: str = Field(..., description="Unique identifier for the record")
    fullName: str = Field(..., description="Full name to validate")
    genderCd: Optional[str] = Field("", description="Gender code (M/F/empty)")
    partyTypeCd: Optional[str] = Field("", description="Party type code (I/O/empty)")
    parseInd: Optional[str] = Field("", description="Parse indicator (Y/N/empty)")


class NameValidationRequest(BaseModel):
    names: List[NameRecord] = Field(..., description="List of name records to validate")


class AddressRecord(BaseModel):
    first_name: str
    last_name: str
    street_address: str
    city: str
    state: str
    zip_code: str


# Response Models
class NameValidationResult(BaseModel):
    uniqueID: str
    partyTypeCd: str
    prefix: Optional[str] = None
    firstName: Optional[str] = None
    firstNameStd: Optional[str] = None
    middleName: Optional[str] = None
    lastName: Optional[str] = None
    suffix: Optional[str] = None
    fullName: str
    inGenderCd: str
    outGenderCd: str
    prefixLt: Optional[str] = None
    firstNameLt: Optional[str] = None
    middleNameLt: Optional[str] = None
    lastNameLt: Optional[str] = None
    suffixLt: Optional[str] = None
    parseInd: str
    confidenceScore: str
    parseStatus: str
    errorMessage: str


class NameValidationResponse(BaseModel):
    names: List[NameValidationResult]


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