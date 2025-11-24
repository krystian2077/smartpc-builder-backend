import asyncio
from app.core.database import AsyncSessionLocal
from app.models.product import Product, ProductType
from app.models.preset import Preset
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def check_gpu():
    async with AsyncSessionLocal() as db:
        # 1. Check if GPU exists
        gpu_name = "ASRock Radeon RX 9060 XT Challenger OC 8GB"
        stmt = select(Product).where(Product.name == gpu_name)
        result = await db.execute(stmt)
        gpu = result.scalar_one_or_none()
        
        if gpu:
            print(f"GPU Found: {gpu.name} (ID: {gpu.id}, Type: {gpu.type})")
        else:
            print(f"GPU NOT Found: {gpu_name}")

        # 2. Check Preset
        preset_name = "PRO-KOM GAMER ECO (Ryzen 5 3600 + RX 9060 XT)"
        stmt = select(Preset).where(Preset.name == preset_name).options(selectinload(Preset.products))
        result = await db.execute(stmt)
        preset = result.scalar_one_or_none()
        
        if preset:
            print(f"Preset Found: {preset.name}")
            print("Linked Products:")
            has_gpu = False
            for p in preset.products:
                print(f" - {p.name} ({p.type})")
                if p.type == ProductType.GPU:
                    has_gpu = True
            
            if has_gpu:
                print("SUCCESS: Preset has a GPU.")
            else:
                print("FAILURE: Preset has NO GPU.")
        else:
            print(f"Preset NOT Found: {preset_name}")

if __name__ == "__main__":
    asyncio.run(check_gpu())
