import asyncio
from app.core.database import AsyncSessionLocal
from app.models.preset import Preset
from sqlalchemy import delete

async def delete_presets():
    async with AsyncSessionLocal() as db:
        print("Deleting all presets...")
        await db.execute(delete(Preset))
        await db.commit()
        print("All presets deleted.")

if __name__ == "__main__":
    asyncio.run(delete_presets())
