from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from uuid import UUID
from datetime import datetime
import secrets

from app.core.database import get_db
from app.models.inquiry import Inquiry, InquiryType, InquirySource
from app.schemas.inquiry import InquiryCreate, InquiryResponse
from app.services.email import send_inquiry_notification

router = APIRouter(prefix="/inquiries", tags=["inquiries"])


def generate_reference_number() -> str:
    """Generate unique reference number for inquiry"""
    return f"INQ-{datetime.utcnow().strftime('%Y%m%d')}-{secrets.token_hex(4).upper()}"


@router.post("", response_model=InquiryResponse, status_code=201)
async def create_inquiry(
    inquiry: InquiryCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new inquiry/quote request"""
    
    if not inquiry.consent_rodo:
        raise HTTPException(
            status_code=400,
            detail="RODO consent is required",
        )
    
    # Generate reference number
    reference_number = generate_reference_number()
    
    # Create inquiry
    db_inquiry = Inquiry(
        reference_number=reference_number,
        first_name=inquiry.first_name,
        last_name=inquiry.last_name,
        email=inquiry.email,
        phone=inquiry.phone,
        company=inquiry.company,
        inquiry_type=inquiry.inquiry_type,
        source=inquiry.source,
        message=inquiry.message,
        configuration_data=inquiry.configuration_data,
        consent_contact=inquiry.consent_contact,
        consent_rodo=inquiry.consent_rodo,
        status="new",
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )
    
    db.add(db_inquiry)
    await db.commit()
    await db.refresh(db_inquiry)
    
    # Check if this is a preset inquiry and enrich data
    if inquiry.configuration_data and "preset_id" in inquiry.configuration_data:
        try:
            preset_id_str = inquiry.configuration_data["preset_id"]
            # Import here to avoid circular imports if any
            from app.models.preset import Preset
            from sqlalchemy.orm import selectinload
            from uuid import UUID as PyUUID
            
            # Ensure UUID format
            try:
                preset_uuid = PyUUID(str(preset_id_str))
            except ValueError:
                print(f"Invalid UUID: {preset_id_str}")
                raise
            
            result = await db.execute(
                select(Preset)
                .options(selectinload(Preset.products))
                .where(Preset.id == preset_uuid)
            )
            preset = result.scalar_one_or_none()
            
            if preset:
                # Enrich configuration data
                components = {}
                for product in preset.products:
                    components[product.type] = {
                        "name": product.name,
                        "price": product.price,
                        "id": str(product.id)
                    }
                
                # Update configuration data with preset details
                inquiry.configuration_data.update({
                    "device": preset.device_type,
                    "segment": preset.segment,
                    "budget": f"{preset.min_budget}-{preset.max_budget}" if preset.min_budget else str(preset.total_price),
                    "totalPrice": preset.total_price,
                    "components": components,
                    "preset_name": preset.name
                })
                
                # Update the DB object as well so we have the full history
                db_inquiry.configuration_data = inquiry.configuration_data
                
        except Exception as e:
            print(f"Error enriching preset data: {e}")

    # Send email notification
    inquiry_data = inquiry.model_dump()
    # Ensure the enriched data is used
    inquiry_data["configuration_data"] = inquiry.configuration_data
    inquiry_data["reference_number"] = reference_number
    await send_inquiry_notification(reference_number, inquiry_data)
    
    return db_inquiry


@router.get("/{inquiry_id}", response_model=InquiryResponse)
async def get_inquiry(
    inquiry_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single inquiry by ID"""
    result = await db.execute(select(Inquiry).where(Inquiry.id == inquiry_id))
    inquiry = result.scalar_one_or_none()
    
    if not inquiry:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    
    return inquiry


@router.get("", response_model=List[InquiryResponse])
async def list_inquiries(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
):
    """List all inquiries (admin only - should add auth later)"""
    result = await db.execute(
        select(Inquiry)
        .order_by(Inquiry.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    inquiries = result.scalars().all()
    return inquiries

