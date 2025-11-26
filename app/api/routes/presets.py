from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.core.database import get_db
from app.models.preset import Preset, DeviceType, PresetSegment
from app.models.product import Product
from app.schemas.preset import PresetCreate, PresetResponse, PresetQuery, PresetDetailResponse
from app.schemas.product import ProductResponse

router = APIRouter(prefix="/presets", tags=["presets"])


@router.get("", response_model=List[PresetResponse])
async def get_presets(
    device_type: Optional[DeviceType] = Query(None),
    segment: Optional[PresetSegment] = Query(None),
    budget: Optional[float] = Query(None, gt=0),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get presets with optional filters. Used for recommendations."""
    query = select(Preset).where(Preset.is_active == True)
    
    if device_type:
        query = query.where(Preset.device_type == device_type)
    if segment:
        query = query.where(Preset.segment == segment)
    if budget:
        # Find presets within budget range
        query = query.where(
            and_(
                (Preset.min_budget.is_(None) | (Preset.min_budget <= budget)),
                (Preset.max_budget.is_(None) | (Preset.max_budget >= budget)),
            )
        )
    
    # Order by priority (higher first), then by performance score
    query = query.order_by(Preset.priority.desc(), Preset.performance_score.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    presets = result.scalars().all()
    return presets


@router.get("/recommendations", response_model=List[PresetResponse])
async def get_recommendations(
    query_params: PresetQuery = Depends(),
    limit: int = Query(3, ge=1, le=10),
    db: AsyncSession = Depends(get_db),
):
    """Get top recommendations based on device type, segment, and budget"""
    query = select(Preset).where(
        and_(
            Preset.device_type == query_params.device_type,
            Preset.segment == query_params.segment,
            Preset.is_active == True,
        )
    )
    
    if query_params.budget:
        query = query.where(
            and_(
                (Preset.min_budget.is_(None) | (Preset.min_budget <= query_params.budget)),
                (Preset.max_budget.is_(None) | (Preset.max_budget >= query_params.budget)),
            )
        )
    
    # Order by priority and performance
    query = query.order_by(Preset.priority.desc(), Preset.performance_score.desc())
    query = query.limit(limit)
    
    result = await db.execute(query)
    presets = result.scalars().all()
    return presets


@router.get("/{preset_id}", response_model=PresetResponse)
async def get_preset(
    preset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single preset by ID"""
    result = await db.execute(select(Preset).where(Preset.id == preset_id))
    preset = result.scalar_one_or_none()
    
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    return preset


@router.get("/{preset_id}/details", response_model=PresetDetailResponse)
async def get_preset_details(
    preset_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single preset by ID with full product details"""
    result = await db.execute(
        select(Preset)
        .where(Preset.id == preset_id)
        .options(selectinload(Preset.products))
    )
    preset = result.scalar_one_or_none()
    
    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")
    
    # Convert to response model
    preset_dict = {
        "id": preset.id,
        "name": preset.name,
        "description": preset.description,
        "device_type": preset.device_type,
        "segment": preset.segment,
        "min_budget": preset.min_budget,
        "max_budget": preset.max_budget,
        "component_map": preset.component_map,
        "total_price": preset.total_price,
        "performance_score": preset.performance_score,
        "reasoning": preset.reasoning,
        "is_active": preset.is_active,
        "priority": preset.priority,
        "image_url": preset.image_url,
        "products": [ProductResponse.model_validate(p) for p in preset.products],
    }
    
    return PresetDetailResponse(**preset_dict)


@router.post("", response_model=PresetResponse, status_code=201)
async def create_preset(
    preset: PresetCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new preset"""
    db_preset = Preset(
        **preset.model_dump(),
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )
    db.add(db_preset)
    
    # Populate Many-to-Many relationship from component_map
    if preset.component_map:
        product_ids = list(preset.component_map.values())
        # Fetch all products by UUIDs
        result = await db.execute(
            select(Product).where(Product.id.in_(product_ids))
        )
        products = result.scalars().all()
        # Add products to preset relationship
        db_preset.products = list(products)
    
    await db.commit()
    await db.refresh(db_preset)
    return db_preset

