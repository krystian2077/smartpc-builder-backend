import asyncio
from app.core.database import AsyncSessionLocal
from app.models.product import Product, ProductType
from app.models.preset import Preset
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def verify_all_presets():
    async with AsyncSessionLocal() as db:
        stmt = select(Preset).options(selectinload(Preset.products))
        result = await db.execute(stmt)
        presets = result.scalars().all()
        
        print(f"Checking {len(presets)} presets...")
        
        for preset in presets:
            has_gpu = False
            gpu_name = "None"
            for p in preset.products:
                if p.type == ProductType.GPU:
                    has_gpu = True
                    gpu_name = p.name
                    break
            
            if has_gpu:
                log_msg = f"[OK] {preset.name} -> {gpu_name}\n"
            else:
                log_msg = f"[FAIL] {preset.name} -> NO GPU FOUND!\n"
            
            print(log_msg.strip())
            with open("verify_output_utf8.txt", "a", encoding="utf-8") as f:
                f.write(log_msg)

if __name__ == "__main__":
    # Clear file
    with open("verify_output_utf8.txt", "w", encoding="utf-8") as f:
        f.write("")
    asyncio.run(verify_all_presets())
