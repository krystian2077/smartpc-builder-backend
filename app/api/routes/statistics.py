from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.database import get_db
from app.models.inquiry import Inquiry
from app.models.product import Product, ProductType
from app.models.configuration import Configuration

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/inquiries")
async def get_inquiry_statistics(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Get inquiry statistics over time"""
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    
    result = await db.execute(
        select(
            func.date(Inquiry.created_at).label("date"),
            func.count(Inquiry.id).label("count"),
        )
        .where(Inquiry.created_at >= since)
        .group_by(func.date(Inquiry.created_at))
        .order_by(func.date(Inquiry.created_at))
    )
    
    stats = result.all()
    
    return {
        "period_days": days,
        "daily_counts": [
            {"date": str(row.date), "count": row.count} for row in stats
        ],
        "total": sum(row.count for row in stats),
    }


@router.get("/popular-components")
async def get_popular_components(
    db: AsyncSession = Depends(get_db),
):
    """Get most frequently selected components (CPU, GPU)"""
    # This would require tracking component selections in configurations
    # For now, return placeholder structure
    return {
        "most_popular_cpu": [],
        "most_popular_gpu": [],
        "note": "Requires component selection tracking in configurations",
    }


@router.get("/budget-distribution")
async def get_budget_distribution(
    db: AsyncSession = Depends(get_db),
):
    """Get budget distribution from inquiries"""
    result = await db.execute(
        select(Inquiry.configuration_data)
        .where(Inquiry.configuration_data.isnot(None))
    )
    
    budgets = []
    for row in result.scalars().all():
        if isinstance(row, dict) and "budget" in row:
            budgets.append(row["budget"])
    
    if not budgets:
        return {
            "ranges": [],
            "note": "No budget data available",
        }
    
    # Create budget ranges
    ranges = [
        {"min": 0, "max": 3000, "count": 0},
        {"min": 3000, "max": 5000, "count": 0},
        {"min": 5000, "max": 8000, "count": 0},
        {"min": 8000, "max": 12000, "count": 0},
        {"min": 12000, "max": float("inf"), "count": 0},
    ]
    
    for budget in budgets:
        for range_item in ranges:
            if range_item["min"] <= budget < range_item["max"]:
                range_item["count"] += 1
                break
    
    return {"ranges": ranges}


@router.get("/segment-distribution")
async def get_segment_distribution(
    db: AsyncSession = Depends(get_db),
):
    """Get segment distribution from inquiries"""
    result = await db.execute(
        select(Inquiry.configuration_data)
        .where(Inquiry.configuration_data.isnot(None))
    )
    
    segments: Dict[str, int] = {}
    for row in result.scalars().all():
        if isinstance(row, dict) and "segment" in row:
            segment = row["segment"]
            segments[segment] = segments.get(segment, 0) + 1
    
    return {"distribution": segments}

