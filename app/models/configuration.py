from sqlalchemy import Column, String, Float, JSON, Boolean, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


# Association table for many-to-many relationship
configuration_products = Table(
    "configuration_products",
    Base.metadata,
    Column("configuration_id", UUID(as_uuid=True), ForeignKey("configurations.id"), primary_key=True),
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
    Column("component_type", String(50), nullable=False),  # cpu, gpu, ram, etc.
)


class Configuration(Base):
    __tablename__ = "configurations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Configuration metadata
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    
    # Configuration data
    device_type = Column(String(20), nullable=False)  # pc or laptop
    segment = Column(String(20), nullable=True)
    budget = Column(Float, nullable=True)
    
    # Component mapping
    component_map = Column(JSON, nullable=False, default=dict)
    # Example: {cpu: "uuid", motherboard: "uuid", gpu: "uuid", ...}
    
    # Totals
    total_price = Column(Float, nullable=False)
    performance_score = Column(Float, nullable=True)
    
    # Sharing
    is_public = Column(Boolean, default=False)
    public_link = Column(String(100), unique=True, nullable=True, index=True)
    
    # Validation status
    is_valid = Column(Boolean, default=True)
    validation_errors = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(String, nullable=False)  # ISO format
    updated_at = Column(String, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="configurations")
    products = relationship("Product", back_populates="configurations", secondary=configuration_products)

