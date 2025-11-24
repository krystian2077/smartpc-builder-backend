from sqlalchemy import Column, String, Integer, Float, JSON, Enum as SQLEnum, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum
from app.core.database import Base


class ProductType(str, enum.Enum):
    CPU = "cpu"
    MOTHERBOARD = "motherboard"
    GPU = "gpu"
    RAM = "ram"
    STORAGE = "storage"
    PSU = "psu"
    CASE = "case"
    COOLER = "cooler"
    PERIPHERAL = "peripheral"
    LAPTOP = "laptop"


class ProductSegment(str, enum.Enum):
    HOME = "home"
    GAMING = "gaming"
    PRO = "pro"
    BUSINESS = "business"


class Product(Base):
    __tablename__ = "products"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(SQLEnum(ProductType), nullable=False, index=True)
    segment = Column(SQLEnum(ProductSegment), nullable=True, index=True)
    
    # Pricing
    price = Column(Float, nullable=False)
    currency = Column(String(3), default="PLN")
    
    # Specifications (stored as JSON for flexibility)
    specifications = Column(JSON, nullable=False, default=dict)
    # Example specs structure:
    # CPU: {socket, cores, threads, base_clock, boost_clock, tdp, integrated_gpu}
    # GPU: {chipset, vram, memory_type, power_consumption, length, width, height}
    # RAM: {type, speed, capacity, modules, voltage, latency}
    # Motherboard: {socket, chipset, form_factor, ram_slots, ram_type, ram_max, pcie_slots}
    # Storage: {type, capacity, interface, read_speed, write_speed, form_factor}
    # PSU: {wattage, efficiency, modular, form_factor, connectors}
    # Case: {form_factor, max_gpu_length, max_cooler_height, fan_slots}
    # Cooler: {type, socket, height, tdp, noise_level}
    # Laptop: {screen_size, cpu, gpu, ram, storage, weight, battery}
    
    # Compatibility info
    compatibility = Column(JSON, nullable=True, default=dict)
    # Example: {socket: "AM5", ram_type: "DDR5", form_factor: "ATX"}
    
    # Metadata
    brand = Column(String(100), nullable=True)
    model = Column(String(200), nullable=True)
    image_url = Column(String(500), nullable=True)
    description = Column(String(2000), nullable=True)
    in_stock = Column(Boolean, default=True)
    
    # Performance scores (optional, for recommendations)
    performance_score = Column(Float, nullable=True)
    gaming_score = Column(Float, nullable=True)
    productivity_score = Column(Float, nullable=True)
    
    # Timestamps
    created_at = Column(String, nullable=True)  # ISO format
    updated_at = Column(String, nullable=True)  # ISO format
    
    # Relationships
    presets = relationship("Preset", back_populates="products", secondary="preset_products")
    configurations = relationship("Configuration", back_populates="products", secondary="configuration_products")

