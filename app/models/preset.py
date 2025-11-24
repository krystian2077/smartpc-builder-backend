from sqlalchemy import Column, String, Integer, Float, JSON, Enum as SQLEnum, ForeignKey, Table, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base


class DeviceType(str, enum.Enum):
    PC = "pc"
    LAPTOP = "laptop"


class PresetSegment(str, enum.Enum):
    HOME = "home"
    GAMING = "gaming"
    PRO = "pro"
    BUSINESS = "business"


# Association table for many-to-many relationship
preset_products = Table(
    "preset_products",
    Base.metadata,
    Column("preset_id", UUID(as_uuid=True), ForeignKey("presets.id"), primary_key=True),
    Column("product_id", UUID(as_uuid=True), ForeignKey("products.id"), primary_key=True),
)


class Preset(Base):
    __tablename__ = "presets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    
    # Preset criteria
    device_type = Column(SQLEnum(DeviceType), nullable=False, index=True)
    segment = Column(SQLEnum(PresetSegment), nullable=False, index=True)
    min_budget = Column(Float, nullable=True)
    max_budget = Column(Float, nullable=True)
    
    # Component mapping (which product IDs for each component type)
    component_map = Column(JSON, nullable=False, default=dict)
    # Example: {cpu: "uuid", motherboard: "uuid", gpu: "uuid", ...}
    
    # Total price and performance
    total_price = Column(Float, nullable=False)
    performance_score = Column(Float, nullable=True)
    
    # Reasoning/justification for recommendation
    reasoning = Column(String(2000), nullable=True)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher = more recommended
    image_url = Column(String(500), nullable=True)  # URL to case image
    
    # Timestamps
    created_at = Column(String, nullable=True)
    updated_at = Column(String, nullable=True)
    
    # Relationships
    products = relationship("Product", back_populates="presets", secondary=preset_products)

