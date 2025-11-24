from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from uuid import UUID
from app.models.inquiry import InquiryType, InquirySource


class InquiryCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=20)
    company: Optional[str] = Field(None, max_length=200)
    inquiry_type: InquiryType
    source: InquirySource
    message: Optional[str] = Field(None, max_length=2000)
    configuration_data: Optional[Dict[str, Any]] = None
    consent_contact: bool = False
    consent_rodo: bool = Field(..., description="RODO consent is required")
    recaptcha_token: Optional[str] = None  # For reCAPTCHA validation


class InquiryResponse(BaseModel):
    id: UUID
    reference_number: str
    first_name: str
    last_name: str
    email: str
    phone: Optional[str]
    company: Optional[str]
    inquiry_type: InquiryType
    source: InquirySource
    message: Optional[str]
    configuration_data: Optional[Dict[str, Any]]
    status: str
    created_at: str

    class Config:
        from_attributes = True

