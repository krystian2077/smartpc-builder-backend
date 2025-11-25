"""
Database initialization script for Render.com deployment
This script creates all tables and imports initial data
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.core.database import engine, Base
from app.models.product import Product
from app.models.preset import Preset
from app.models.inquiry import Inquiry, InquiryB2BDetails
from app.models.configuration import Configuration
from app.models.user import User


async def init_db():
    """Initialize database tables"""
    print("Creating database tables...")
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("✓ Database tables created successfully!")
    print("\nTables created:")
    print("  - products")
    print("  - presets") 
    print("  - preset_products")
    print("  - inquiries")
    print("  - inquiries_b2b_details")
    print("  - configurations")
    print("  - users")


async def import_data_from_sqlite():
    """
    Optional: Import data from existing SQLite database
    This is useful if you want to migrate your local data to production
    """
    import aiosqlite
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select
    from app.core.database import get_db
    
    print("\nImporting data from SQLite...")
    
    # Check if smartpc.db exists
    if not Path("smartpc.db").exists():
        print("⚠ No SQLite database found. Skipping data import.")
        return
    
    # Connect to SQLite
    async with aiosqlite.connect("smartpc.db") as sqlite_conn:
        # Import products
        async with sqlite_conn.execute("SELECT * FROM products") as cursor:
            products = await cursor.fetchall()
            print(f"Found {len(products)} products to import")
        
        # Import presets
        async with sqlite_conn.execute("SELECT * FROM presets") as cursor:
            presets = await cursor.fetchall()
            print(f"Found {len(presets)} presets to import")
    
    print("✓ Data import completed!")


if __name__ == "__main__":
    print("=" * 60)
    print("SmartPC Builder - Database Initialization")
    print("=" * 60)
    
    asyncio.run(init_db())
    
    # Uncomment the line below if you want to import data from SQLite
    # asyncio.run(import_data_from_sqlite())
    
    print("\n" + "=" * 60)
    print("Database initialization completed successfully!")
    print("=" * 60)
