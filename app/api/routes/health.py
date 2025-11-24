from fastapi import APIRouter
from app.core.config import settings

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "service": settings.app.name,
        "version": settings.app.version,
        "environment": settings.app.environment,
    }


