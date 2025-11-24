from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.preset import Preset, DeviceType, PresetSegment
from app.models.product import Product, ProductType, ProductSegment


async def get_recommendations(
    device_type: DeviceType,
    segment: PresetSegment,
    budget: float,
    db: AsyncSession,
    limit: int = 3,
) -> List[Preset]:
    """
    Rule-based recommendation engine.
    Returns top presets matching criteria, ordered by priority and performance.
    """
    query = select(Preset).where(
        and_(
            Preset.device_type == device_type,
            Preset.segment == segment,
            Preset.is_active == True,
            (Preset.min_budget.is_(None) | (Preset.min_budget <= budget)),
            (Preset.max_budget.is_(None) | (Preset.max_budget >= budget)),
        )
    )
    
    # Order by priority (higher first), then performance score
    query = query.order_by(
        Preset.priority.desc(),
        Preset.performance_score.desc(),
    )
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    presets = result.scalars().all()
    
    return presets


def generate_recommendation_reasoning(
    preset: Preset,
    device_type: DeviceType,
    segment: PresetSegment,
    budget: float,
) -> str:
    """Generate human-readable reasoning for why this preset is recommended"""
    reasons = []
    
    if preset.performance_score:
        reasons.append(f"Wysoki wynik wydajności: {preset.performance_score:.0f} punktów")
    
    if segment == PresetSegment.GAMING:
        reasons.append("Optymalizacja pod kątem gier")
    elif segment == PresetSegment.PRO:
        reasons.append("Zoptymalizowany do pracy profesjonalnej")
    elif segment == PresetSegment.BUSINESS:
        reasons.append("Idealny do zastosowań biznesowych")
    else:
        reasons.append("Uniwersalny zestaw do codziennego użytku")
    
    if preset.total_price <= budget * 0.9:
        reasons.append("Mieści się w budżecie z zapasem")
    elif preset.total_price <= budget:
        reasons.append("Dopasowany do budżetu")
    
    if preset.reasoning:
        reasons.append(preset.reasoning)
    
    return ". ".join(reasons) if reasons else "Rekomendowany zestaw"


async def get_alternative_components(
    component_type: ProductType,
    current_product_id: str,
    segment: Optional[ProductSegment],
    db: AsyncSession,
    limit: int = 5,
) -> List[Product]:
    """
    Get alternative products for a component type, filtered by compatibility.
    Used in "Replace component" feature.
    """
    # Get current product to understand compatibility requirements
    result = await db.execute(
        select(Product).where(Product.id == current_product_id)
    )
    current_product = result.scalar_one_or_none()
    
    if not current_product:
        return []
    
    # Build query for alternatives
    query = select(Product).where(
        and_(
            Product.type == component_type,
            Product.id != current_product_id,
            Product.in_stock == True,
        )
    )
    
    if segment:
        query = query.where(Product.segment == segment)
    
    # Order by performance score or price
    query = query.order_by(
        Product.performance_score.desc().nulls_last(),
        Product.price.asc(),
    )
    
    query = query.limit(limit)
    
    result = await db.execute(query)
    products = result.scalars().all()
    
    return products

