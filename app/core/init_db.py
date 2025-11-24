"""
Initialize database - create all tables.
Run this script to set up the database schema.
"""
import asyncio
from app.core.database import engine, Base
from app.models import (
    Product,
    Preset,
    Inquiry,
    InquiryB2BDetails,
    User,
    Configuration,
)


async def init_db():
    """Create all database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("Database tables created successfully!")


if __name__ == "__main__":
    asyncio.run(init_db())

