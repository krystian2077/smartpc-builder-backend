import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from app.core.database import AsyncSessionLocal
from app.models.product import Product
from app.models.preset import Preset

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clear_all_data():
    async with AsyncSessionLocal() as db:
        logger.info("Clearing all products and presets...")
        
        # Delete all presets first (due to foreign key constraints)
        await db.execute(delete(Preset))
        await db.commit()
        logger.info("All presets deleted")
        
        # Delete all products
        await db.execute(delete(Product))
        await db.commit()
        logger.info("All products deleted")
        
        logger.info("Database cleared successfully!")

if __name__ == "__main__":
    asyncio.run(clear_all_data())
