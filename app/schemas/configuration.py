from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID


class ConfigurationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    device_type: str = Field(..., pattern="^(pc|laptop)$")
    segment: Optional[str] = None
    budget: Optional[float] = None
    component_map: Dict[str, str] = Field(default_factory=dict)  # component_type -> product_id
    total_price: float = Field(..., gt=0)
    performance_score: Optional[float] = None
    is_public: bool = False


class ConfigurationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    component_map: Optional[Dict[str, str]] = None
    total_price: Optional[float] = Field(None, gt=0)
    performance_score: Optional[float] = None
    is_public: Optional[bool] = None


class ConfigurationResponse(BaseModel):
    id: UUID
    user_id: Optional[UUID]
    name: str
    description: Optional[str]
    device_type: str
    segment: Optional[str]
    budget: Optional[float]
    component_map: Dict[str, str]
    total_price: float
    performance_score: Optional[float]
    is_public: bool
    public_link: Optional[str]
    is_valid: bool
    validation_errors: Optional[Dict[str, Any]]
    created_at: str
    updated_at: Optional[str]

    class Config:
        from_attributes = True

