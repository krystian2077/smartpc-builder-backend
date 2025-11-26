from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from app.models.preset import DeviceType, PresetSegment
from app.schemas.product import ProductResponse


class PresetQuery(BaseModel):
    device_type: DeviceType
    segment: PresetSegment
    budget: Optional[float] = Field(None, gt=0)


class PresetCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    device_type: DeviceType
    segment: PresetSegment
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    component_map: Dict[str, str] = Field(default_factory=dict)  # component_type -> product_id
    total_price: float = Field(..., gt=0)
    performance_score: Optional[float] = None
    reasoning: Optional[str] = None
    is_active: bool = True
    priority: int = 0
    image_url: Optional[str] = None  # Add image URL support


class PresetResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    device_type: DeviceType
    segment: PresetSegment
    min_budget: Optional[float]
    max_budget: Optional[float]
    component_map: Dict[str, str]
    total_price: float
    performance_score: Optional[float]
    reasoning: Optional[str]
    is_active: bool
    priority: int
    image_url: Optional[str] = None

    class Config:
        from_attributes = True


class PresetDetailResponse(PresetResponse):
    """Preset response with full product details"""
    products: List[ProductResponse] = Field(default_factory=list)
