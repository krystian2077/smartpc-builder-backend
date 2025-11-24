from sqlalchemy import Column, String, Integer, JSON, Enum as SQLEnum, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base


class InquiryType(str, enum.Enum):
    QUOTE_REQUEST = "quote_request"
    GENERAL_CONTACT = "general_contact"
    CONFIGURATION_CHECK = "configuration_check"
    FIND_FOR_ME = "find_for_me"


class InquirySource(str, enum.Enum):
    LANDING = "landing"
    CONFIGURATOR = "configurator"
    LAPTOP_LIST = "laptop_list"
    CONTACT_PAGE = "contact_page"
    CONFIGURATION_PAGE = "configuration_page"


class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reference_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Contact information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    company = Column(String(200), nullable=True)
    
    # Inquiry details
    inquiry_type = Column(SQLEnum(InquiryType), nullable=False, index=True)
    source = Column(SQLEnum(InquirySource), nullable=False, index=True)
    message = Column(String(2000), nullable=True)
    
    # Configuration data (if applicable)
    configuration_data = Column(JSON, nullable=True)
    # Example: {device_type: "pc", segment: "gaming", budget: 5000, components: [...]}
    
    # Consent
    consent_contact = Column(Boolean, default=False)
    consent_rodo = Column(Boolean, default=False)
    
    # Status
    status = Column(String(50), default="new")  # new, contacted, quoted, closed
    notes = Column(String(1000), nullable=True)
    
    # Timestamps
    created_at = Column(String, nullable=False)  # ISO format
    updated_at = Column(String, nullable=True)
    
    # Relationships
    b2b_details = relationship("InquiryB2BDetails", back_populates="inquiry", uselist=False)


class InquiryB2BDetails(Base):
    __tablename__ = "inquiries_b2b_details"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    inquiry_id = Column(UUID(as_uuid=True), ForeignKey("inquiries.id"), unique=True, nullable=False)
    
    # B2B specific fields
    nip = Column(String(20), nullable=True)
    company_address = Column(String(500), nullable=True)
    delivery_address = Column(String(500), nullable=True)
    payment_terms = Column(String(100), nullable=True)
    expected_quantity = Column(Integer, nullable=True)
    
    # Additional metadata
    additional_data = Column(JSON, nullable=True)
    
    # Relationships
    inquiry = relationship("Inquiry", back_populates="b2b_details")

