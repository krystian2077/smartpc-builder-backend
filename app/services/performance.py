from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.product import Product


# FPS mapping for popular games (simplified)
FPS_MAPPINGS = {
    "gta_v": {
        "1080p_ultra": {
            "rtx_4090": 180,
            "rtx_4080": 150,
            "rtx_4070": 120,
            "rtx_4060": 90,
            "rx_7900": 160,
            "rx_7800": 130,
            "rx_7700": 100,
        },
        "1440p_ultra": {
            "rtx_4090": 140,
            "rtx_4080": 110,
            "rtx_4070": 85,
            "rtx_4060": 65,
            "rx_7900": 120,
            "rx_7800": 95,
            "rx_7700": 75,
        },
        "4k_ultra": {
            "rtx_4090": 90,
            "rtx_4080": 70,
            "rtx_4070": 50,
            "rtx_4060": 35,
            "rx_7900": 80,
            "rx_7800": 60,
            "rx_7700": 45,
        },
    },
    "cyberpunk_2077": {
        "1080p_ultra": {
            "rtx_4090": 120,
            "rtx_4080": 95,
            "rtx_4070": 70,
            "rtx_4060": 50,
            "rx_7900": 100,
            "rx_7800": 75,
            "rx_7700": 55,
        },
        "1440p_ultra": {
            "rtx_4090": 85,
            "rtx_4080": 65,
            "rtx_4070": 45,
            "rtx_4060": 30,
            "rx_7900": 70,
            "rx_7800": 50,
            "rx_7700": 35,
        },
        "4k_ultra": {
            "rtx_4090": 50,
            "rtx_4080": 38,
            "rtx_4070": 25,
            "rtx_4060": 18,
            "rx_7900": 42,
            "rx_7800": 30,
            "rx_7700": 20,
        },
    },
}


def estimate_fps(
    gpu_model: str,
    game: str,
    resolution: str,
    settings: str = "ultra",
) -> Optional[int]:
    """
    Estimate FPS for a game based on GPU model.
    Returns approximate FPS or None if not found.
    """
    game_key = game.lower().replace(" ", "_")
    resolution_key = f"{resolution}_{settings}"
    
    if game_key not in FPS_MAPPINGS:
        return None
    
    game_data = FPS_MAPPINGS[game_key]
    if resolution_key not in game_data:
        return None
    
    # Normalize GPU model name
    gpu_normalized = gpu_model.lower().replace(" ", "_")
    
    # Try to find matching GPU
    for gpu_key, fps in game_data[resolution_key].items():
        if gpu_key in gpu_normalized:
            return fps
    
    return None


async def calculate_performance_score(
    components: Dict[str, str],
    db: AsyncSession,
) -> Optional[float]:
    """
    Calculate overall performance score for a configuration.
    Based on CPU and GPU performance scores.
    """
    cpu_id = components.get("cpu")
    gpu_id = components.get("gpu")
    
    if not cpu_id or not gpu_id:
        return None
    
    # Fetch products
    result = await db.execute(
        select(Product).where(Product.id.in_([cpu_id, gpu_id]))
    )
    products = {str(p.id): p for p in result.scalars().all()}
    
    cpu = products.get(cpu_id)
    gpu = products.get(gpu_id)
    
    if not cpu or not gpu:
        return None
    
    # Calculate weighted score
    cpu_score = cpu.performance_score or 0
    gpu_score = gpu.gaming_score or gpu.performance_score or 0
    
    # Weight: CPU 40%, GPU 60%
    total_score = (cpu_score * 0.4) + (gpu_score * 0.6)
    
    return total_score


def analyze_configuration_strengths_weaknesses(
    components: Dict[str, str],
    products: Dict[str, Product],
) -> Dict[str, Any]:
    """
    Analyze configuration and return strengths and weaknesses.
    """
    strengths = []
    weaknesses = []
    
    cpu = products.get(components.get("cpu", ""))
    gpu = products.get(components.get("gpu", ""))
    ram = products.get(components.get("ram", ""))
    storage = products.get(components.get("storage", ""))
    
    if cpu:
        if cpu.performance_score and cpu.performance_score > 80:
            strengths.append("Wydajny procesor")
        elif cpu.performance_score and cpu.performance_score < 50:
            weaknesses.append("Słabszy procesor może być wąskim gardłem")
    
    if gpu:
        if gpu.gaming_score and gpu.gaming_score > 80:
            strengths.append("Mocna karta graficzna")
        elif gpu.gaming_score and gpu.gaming_score < 50:
            weaknesses.append("Karta graficzna może ograniczać wydajność w grach")
    
    if ram:
        ram_capacity = ram.specifications.get("capacity", 0)
        if isinstance(ram_capacity, (int, float)) and ram_capacity >= 32:
            strengths.append("Duża ilość pamięci RAM")
        elif isinstance(ram_capacity, (int, float)) and ram_capacity < 16:
            weaknesses.append("Mała ilość RAM może ograniczać wydajność")
    
    if storage:
        storage_type = ram.specifications.get("type", "").lower()
        if "nvme" in storage_type or "ssd" in storage_type:
            strengths.append("Szybki dysk SSD")
        else:
            weaknesses.append("Wolniejszy dysk HDD")
    
    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
    }

