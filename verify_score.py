import asyncio
from app.core.database import AsyncSessionLocal
from app.models.preset import Preset
from sqlalchemy import select

async def verify_godlike_score():
    async with AsyncSessionLocal() as db:
        stmt = select(Preset).where(Preset.name.like("%GODLIKE%"))
        result = await db.execute(stmt)
        preset = result.scalar_one_or_none()
        
        if preset:
            print(f"Preset: {preset.name}")
            print(f"Performance Score: {preset.performance_score}%")
            if preset.performance_score >= 99:
                print("SUCCESS: Score is ~100%")
            else:
                print("FAILURE: Score is still low.")
        else:
            print("Preset not found.")

if __name__ == "__main__":
    asyncio.run(verify_godlike_score())
