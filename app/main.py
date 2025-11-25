from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.middleware.rate_limit import RateLimitMiddleware
from app.api.routes.health import router as health_router
from app.api.routes.products import router as products_router
from app.api.routes.presets import router as presets_router
from app.api.routes.validation import router as validation_router
from app.api.routes.inquiries import router as inquiries_router
from app.api.routes.configurations import router as configurations_router
from app.api.routes.auth import router as auth_router
from app.api.routes.import_export import router as import_export_router
from app.api.routes.statistics import router as statistics_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="SmartPC Builder API",
        version=settings.app.version,
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add rate limiting for inquiries endpoint
    application.add_middleware(RateLimitMiddleware, requests_per_minute=10)

    application.include_router(health_router, prefix="/api/v1")
    application.include_router(products_router, prefix="/api/v1")
    application.include_router(presets_router, prefix="/api/v1")
    application.include_router(validation_router, prefix="/api/v1")
    application.include_router(inquiries_router, prefix="/api/v1")
    application.include_router(configurations_router, prefix="/api/v1")
    application.include_router(auth_router, prefix="/api/v1")
    application.include_router(import_export_router, prefix="/api/v1")
    application.include_router(statistics_router, prefix="/api/v1")
    
    # Startup event: Initialize database tables
    @application.on_event("startup")
    async def startup_event():
        """Create database tables on startup if they don't exist"""
        from app.core.database import engine, Base
        
        try:
            async with engine.begin() as conn:
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
            print("✓ Database tables initialized successfully")
        except Exception as e:
            print(f"⚠ Database initialization error: {e}")
            # Don't fail startup - tables might already exist

    return application


app = create_app()


