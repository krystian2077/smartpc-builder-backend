from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.validation import ValidationRequest, ValidationResponse
from app.services.validation import validate_configuration

router = APIRouter(prefix="/validate", tags=["validation"])


@router.post("", response_model=ValidationResponse)
async def validate_configuration_endpoint(
    request: ValidationRequest,
    db: AsyncSession = Depends(get_db),
):
    """Validate PC configuration compatibility"""
    return await validate_configuration(request.components, db)

