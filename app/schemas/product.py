from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from uuid import UUID
from app.models.product import ProductType, ProductSegment


class ProductCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: ProductType
    segment: Optional[ProductSegment] = None
    price: float = Field(..., gt=0)
    currency: str = Field(default="PLN", max_length=3)
    specifications: Dict[str, Any] = Field(default_factory=dict)
    compatibility: Optional[Dict[str, Any]] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None
    in_stock: bool = True
    performance_score: Optional[float] = None
    gaming_score: Optional[float] = None
    productivity_score: Optional[float] = None


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    segment: Optional[ProductSegment] = None
    price: Optional[float] = Field(None, gt=0)
    specifications: Optional[Dict[str, Any]] = None
    compatibility: Optional[Dict[str, Any]] = None
    in_stock: Optional[bool] = None
    performance_score: Optional[float] = None
    gaming_score: Optional[float] = None
    productivity_score: Optional[float] = None


class ProductResponse(BaseModel):
    id: UUID
    name: str
    type: ProductType
    segment: Optional[ProductSegment]
    price: float
    currency: str
    specifications: Dict[str, Any]
    compatibility: Optional[Dict[str, Any]]
    brand: Optional[str]
    model: Optional[str]
    image_url: Optional[str]
    description: Optional[str]
    in_stock: bool
    performance_score: Optional[float]
    gaming_score: Optional[float]
    productivity_score: Optional[float]

    class Config:
        from_attributes = True

