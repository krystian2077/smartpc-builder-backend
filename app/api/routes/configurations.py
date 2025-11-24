from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
from datetime import datetime
import secrets

from app.core.database import get_db
from app.models.configuration import Configuration
from app.schemas.configuration import ConfigurationCreate, ConfigurationUpdate, ConfigurationResponse
from app.services.validation import validate_configuration

router = APIRouter(prefix="/configurations", tags=["configurations"])


def generate_public_link() -> str:
    """Generate unique public link for configuration"""
    return secrets.token_urlsafe(16)


@router.get("", response_model=List[ConfigurationResponse])
async def get_configurations(
    user_id: Optional[UUID] = Query(None),
    public_link: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get configurations"""
    query = select(Configuration)
    
    if public_link:
        query = query.where(Configuration.public_link == public_link)
    elif user_id:
        query = query.where(Configuration.user_id == user_id)
    else:
        query = query.where(Configuration.is_public == True)
    
    query = query.order_by(Configuration.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    configurations = result.scalars().all()
    return configurations


@router.get("/{config_id}", response_model=ConfigurationResponse)
async def get_configuration(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single configuration by ID"""
    result = await db.execute(select(Configuration).where(Configuration.id == config_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return config


@router.post("", response_model=ConfigurationResponse, status_code=201)
async def create_configuration(
    config: ConfigurationCreate,
    user_id: Optional[UUID] = None,  # Should come from auth token
    db: AsyncSession = Depends(get_db),
):
    """Create a new configuration"""
    # Validate configuration
    validation_result = await validate_configuration(config.component_map, db)
    
    public_link = None
    if config.is_public:
        public_link = generate_public_link()
    
    db_config = Configuration(
        user_id=user_id,
        name=config.name,
        description=config.description,
        device_type=config.device_type,
        segment=config.segment,
        budget=config.budget,
        component_map=config.component_map,
        total_price=config.total_price,
        performance_score=config.performance_score,
        is_public=config.is_public,
        public_link=public_link,
        is_valid=validation_result.is_valid,
        validation_errors={
            "issues": [issue.model_dump() for issue in validation_result.issues]
        } if validation_result.issues else None,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )
    
    db.add(db_config)
    await db.commit()
    await db.refresh(db_config)
    return db_config


@router.put("/{config_id}", response_model=ConfigurationResponse)
async def update_configuration(
    config_id: UUID,
    config_update: ConfigurationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a configuration"""
    result = await db.execute(select(Configuration).where(Configuration.id == config_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    update_data = config_update.model_dump(exclude_unset=True)
    
    # Re-validate if components changed
    if "component_map" in update_data:
        validation_result = await validate_configuration(update_data["component_map"], db)
        update_data["is_valid"] = validation_result.is_valid
        update_data["validation_errors"] = {
            "issues": [issue.model_dump() for issue in validation_result.issues]
        } if validation_result.issues else None
    
    # Generate public link if making public
    if update_data.get("is_public") and not config.public_link:
        update_data["public_link"] = generate_public_link()
    
    update_data["updated_at"] = datetime.utcnow().isoformat()
    
    for field, value in update_data.items():
        setattr(config, field, value)
    
    await db.commit()
    await db.refresh(config)
    return config


@router.delete("/{config_id}", status_code=204)
async def delete_configuration(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a configuration"""
    result = await db.execute(select(Configuration).where(Configuration.id == config_id))
    config = result.scalar_one_or_none()
    
    if not config:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    await db.delete(config)
    await db.commit()
    return None

