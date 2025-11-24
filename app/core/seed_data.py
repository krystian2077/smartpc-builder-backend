"""
Seed database with recommended computer sets from TechLipton.
Run this script to populate the database with preset configurations.
"""
import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.product import Product, ProductType, ProductSegment
from app.models.preset import Preset, DeviceType, PresetSegment


# TechLipton recommended sets data
TECHLIPTON_SETS = [
    {
        "name": "Zestaw Komputerowy za 1800 zł - najtańszy PC do gier",
        "description": "Najtańsza jednostka do grania w gry komputerowe bazująca na 6 rdzeniowym i 12 wątkowym procesorze i zintegrowanym układzie graficznym Vega. Polecana dla osób o skromnym budżecie na zakup PC. Komputer jest dedykowany graczom mniej wymagających tytułów, takich jak Fortnite, CS:GO czy World of Tanks.",
        "price": 1854.00,
        "priority": 1,
        "components": [
            {"type": "cpu", "name": "AMD Ryzen 5 5600GT", "price": 450.00, "specs": {"socket": "AM4", "cores": 6, "threads": 12, "base_clock": 3.6, "boost_clock": 4.6, "tdp": 65, "integrated_gpu": "Vega"}},
            {"type": "motherboard", "name": "ASRock B550M-HDV", "price": 350.00, "specs": {"socket": "AM4", "chipset": "B550", "form_factor": "mATX", "ram_slots": 2, "ram_type": "DDR4", "ram_max": 64}},
            {"type": "ram", "name": "ADATA 16GB (2×8) 3200 CL16 Gamix D35", "price": 280.00, "specs": {"type": "DDR4", "speed": 3200, "capacity": 16, "modules": 2, "voltage": 1.35, "latency": "CL16"}},
            {"type": "storage", "name": "MSI 1TB M.2 PCIe Gen4 NVMe Spatium M470 PRO", "price": 350.00, "specs": {"type": "NVMe", "capacity": 1000, "interface": "PCIe Gen4", "form_factor": "M.2"}},
            {"type": "psu", "name": "Deepcool PL550D 550W 80 Plus Bronze", "price": 250.00, "specs": {"wattage": 550, "efficiency": "80 Plus Bronze", "modular": False, "form_factor": "ATX"}},
            {"type": "case", "name": "Silver Monkey X Cassette", "price": 174.00, "specs": {"form_factor": "mATX", "max_gpu_length": 350, "max_cooler_height": 160, "fan_slots": 3}},
        ]
    },
    {
        "name": "Zestaw Komputerowy za 2800 zł - bardzo tani PC do gier",
        "description": "Najtańszy zestaw komputerowy do gier z dedykowaną kartą graficzną w tym zestawieniu. Ze względu na brak dostępności Arc B570 w kwocie poniżej 900 złotych oferuję Wam zestaw z nieco droższą, ale też znacznie wydajniejszą kartą – RX 9060 XT 8GB. Uważam to za lepszy wybór niż zakup GeForce RTX 5060.",
        "price": 2833.00,
        "priority": 2,
        "components": [
            {"type": "cpu", "name": "AMD Ryzen 5 3600", "price": 400.00, "specs": {"socket": "AM4", "cores": 6, "threads": 12, "base_clock": 3.6, "boost_clock": 4.2, "tdp": 65}},
            {"type": "motherboard", "name": "ASRock B550M-HDV", "price": 350.00, "specs": {"socket": "AM4", "chipset": "B550", "form_factor": "mATX", "ram_slots": 2, "ram_type": "DDR4", "ram_max": 64}},
            {"type": "gpu", "name": "ASRock Radeon RX 9060 XT Challenger OC 8GB GDDR6", "price": 1200.00, "specs": {"chipset": "RX 9060 XT", "vram": 8, "memory_type": "GDDR6", "power_consumption": 160}},
            {"type": "ram", "name": "ADATA 16GB (2×8) 3200 CL16 Gamix D35", "price": 280.00, "specs": {"type": "DDR4", "speed": 3200, "capacity": 16, "modules": 2, "voltage": 1.35, "latency": "CL16"}},
            {"type": "storage", "name": "MSI 1TB M.2 PCIe Gen4 NVMe Spatium M470 PRO", "price": 350.00, "specs": {"type": "NVMe", "capacity": 1000, "interface": "PCIe Gen4", "form_factor": "M.2"}},
            {"type": "case", "name": "Silver Monkey X Cassette", "price": 174.00, "specs": {"form_factor": "mATX", "max_gpu_length": 350, "max_cooler_height": 160, "fan_slots": 3}},
            {"type": "psu", "name": "Deepcool PL550D 550W 80 Plus Bronze", "price": 250.00, "specs": {"wattage": 550, "efficiency": "80 Plus Bronze", "modular": False, "form_factor": "ATX"}},
        ]
    },
    {
        "name": "Zestaw Komputerowy za 3500 zł - tani PC do gier",
        "description": "Postawiłem na całkowicie świeżą konfigurację w kwocie 3500 zł. Podstawę zestawu stanowi platforma AM5 na czele z Ryzenem 5 7500F oraz Radeonem RX 9060 XT 8GB. To wysoce polecane zestawienie w tej kwocie pieniędzy.",
        "price": 3500.00,
        "priority": 3,
        "components": [
            {"type": "cpu", "name": "AMD Ryzen 5 7500F TRAY", "price": 750.00, "specs": {"socket": "AM5", "cores": 6, "threads": 12, "base_clock": 3.7, "boost_clock": 5.0, "tdp": 65}},
            {"type": "motherboard", "name": "ASRock B650M-H/M.2 +", "price": 450.00, "specs": {"socket": "AM5", "chipset": "B650", "form_factor": "mATX", "ram_slots": 2, "ram_type": "DDR5", "ram_max": 64}},
            {"type": "gpu", "name": "ASRock Radeon RX 9060 XT Challenger OC 8GB GDDR6", "price": 1200.00, "specs": {"chipset": "RX 9060 XT", "vram": 8, "memory_type": "GDDR6", "power_consumption": 160}},
            {"type": "ram", "name": "Patriot 32GB (2x16GB) 6000 CL30 Viper Elite", "price": 450.00, "specs": {"type": "DDR5", "speed": 6000, "capacity": 32, "modules": 2, "voltage": 1.35, "latency": "CL30"}},
            {"type": "storage", "name": "MSI 1TB M.2 PCIe Gen4 NVMe Spatium M470 PRO", "price": 350.00, "specs": {"type": "NVMe", "capacity": 1000, "interface": "PCIe Gen4", "form_factor": "M.2"}},
            {"type": "psu", "name": "Deepcool PL550D 550W 80 Plus Bronze", "price": 250.00, "specs": {"wattage": 550, "efficiency": "80 Plus Bronze", "modular": False, "form_factor": "ATX"}},
            {"type": "case", "name": "Silver Monkey X Pyxis", "price": 200.00, "specs": {"form_factor": "mATX", "max_gpu_length": 350, "max_cooler_height": 160, "fan_slots": 3}},
        ]
    },
    {
        "name": "Zestaw Komputerowy za 7152 zł - maszyna do grania",
        "description": "Zestaw komputerowy z procesorem AMD Ryzen 5 7500F oraz kartą graficzną GeForce RTX 5070. Idealny do rozgrywki w rozdzielczości 2560×1440 oraz 3840×2160 z wykorzystaniem technologii upscalingu.",
        "price": 7152.00,
        "priority": 4,
        "components": [
            {"type": "cpu", "name": "AMD Ryzen 5 7500F TRAY", "price": 750.00, "specs": {"socket": "AM5", "cores": 6, "threads": 12, "base_clock": 3.7, "boost_clock": 5.0, "tdp": 65}},
            {"type": "motherboard", "name": "ASRock B650M-H/M.2 +", "price": 450.00, "specs": {"socket": "AM5", "chipset": "B650", "form_factor": "mATX", "ram_slots": 2, "ram_type": "DDR5", "ram_max": 64}},
            {"type": "gpu", "name": "ASUS GeForce RTX 5070 Prime OC 16GB GDDR7 DLSS4", "price": 3200.00, "specs": {"chipset": "RTX 5070", "vram": 16, "memory_type": "GDDR7", "power_consumption": 220}},
            {"type": "ram", "name": "Patriot 32GB (2x16GB) 6000 CL30 Viper Elite", "price": 450.00, "specs": {"type": "DDR5", "speed": 6000, "capacity": 32, "modules": 2, "voltage": 1.35, "latency": "CL30"}},
            {"type": "storage", "name": "MSI 1TB M.2 PCIe Gen4 NVMe Spatium M470 PRO", "price": 350.00, "specs": {"type": "NVMe", "capacity": 1000, "interface": "PCIe Gen4", "form_factor": "M.2"}},
            {"type": "cooler", "name": "Thermalright Peerless Assassin 120 SE 120mm", "price": 150.00, "specs": {"type": "Air", "socket": "AM5", "tdp": 200, "noise_level": 25}},
            {"type": "psu", "name": "ENDORFY Supremo FM6 850W 80 Plus Gold EU", "price": 450.00, "specs": {"wattage": 850, "efficiency": "80 Plus Gold", "modular": True, "form_factor": "ATX"}},
            {"type": "case", "name": "Silver Monkey X Pyxis", "price": 200.00, "specs": {"form_factor": "mATX", "max_gpu_length": 350, "max_cooler_height": 160, "fan_slots": 3}},
        ]
    },
    {
        "name": "Zestaw Komputerowy za 8200 zł - maszyna do grania i działania",
        "description": "Zestaw z procesorem Ryzen 7 7800X3D – jednostki o dużym potencjale, szczególnie mocnej w grach komputerowych. W połączeniu z kartą graficzną RTX 5070 Ti tworzy znakomity duet, idealny do rozgrywki w rozdzielczości 2560×1440, a także 3840×2160 z wykorzystaniem technologii upscalingu.",
        "price": 8252.00,
        "priority": 5,
        "components": [
            {"type": "cpu", "name": "AMD Ryzen 7 7800X3D", "price": 1800.00, "specs": {"socket": "AM5", "cores": 8, "threads": 16, "base_clock": 4.2, "boost_clock": 5.0, "tdp": 120}},
            {"type": "motherboard", "name": "ASUS B650E MAX GAMING WIFI", "price": 800.00, "specs": {"socket": "AM5", "chipset": "B650E", "form_factor": "ATX", "ram_slots": 4, "ram_type": "DDR5", "ram_max": 128}},
            {"type": "gpu", "name": "ASUS GeForce RTX 5070 Ti Prime OC 16GB GDDR7 DLSS4", "price": 3800.00, "specs": {"chipset": "RTX 5070 Ti", "vram": 16, "memory_type": "GDDR7", "power_consumption": 250}},
            {"type": "ram", "name": "GOODRAM 32GB (2x16GB) 6000 CL36 IRDM BLACK V SILVER", "price": 500.00, "specs": {"type": "DDR5", "speed": 6000, "capacity": 32, "modules": 2, "voltage": 1.35, "latency": "CL36"}},
            {"type": "storage", "name": "MSI 2TB M.2 PCIe Gen4 NVMe Spatium M470 PRO", "price": 650.00, "specs": {"type": "NVMe", "capacity": 2000, "interface": "PCIe Gen4", "form_factor": "M.2"}},
            {"type": "cooler", "name": "Thermalright Peerless Assassin 120 SE 2x120mm", "price": 150.00, "specs": {"type": "Air", "socket": "AM5", "tdp": 250, "noise_level": 25}},
            {"type": "psu", "name": "ENDORFY Supremo FM6 850W 80 Plus Gold ATX 3.1", "price": 450.00, "specs": {"wattage": 850, "efficiency": "80 Plus Gold", "modular": True, "form_factor": "ATX"}},
            {"type": "case", "name": "Cougar Uniface RGB Black", "price": 302.00, "specs": {"form_factor": "ATX", "max_gpu_length": 400, "max_cooler_height": 180, "fan_slots": 6}},
        ]
    },
    {
        "name": "Zestaw Komputerowy za 9500 zł - maszyna do grania",
        "description": "Pierwsza propozycja komputera z procesorem z pamięcią 3D V-Cache, stworzona z myślą o graniu w rozdzielczości 3840 x 2160 pikseli oraz nieco mniej wszechstronnym użytkowaniu w programach. Sercem tej jednostki jest GeForce RTX 5080, która zapewnia bardzo dobre osiągi.",
        "price": 9552.00,
        "priority": 6,
        "components": [
            {"type": "cpu", "name": "AMD Ryzen 7 7800X3D", "price": 1800.00, "specs": {"socket": "AM5", "cores": 8, "threads": 16, "base_clock": 4.2, "boost_clock": 5.0, "tdp": 120}},
            {"type": "motherboard", "name": "Gigabyte B850 GAMING X WIFI6E", "price": 900.00, "specs": {"socket": "AM5", "chipset": "B850", "form_factor": "ATX", "ram_slots": 4, "ram_type": "DDR5", "ram_max": 128}},
            {"type": "gpu", "name": "Zotac GeForce RTX 5080 Solid Core OC 16GB GDDR7 DLSS4", "price": 4500.00, "specs": {"chipset": "RTX 5080", "vram": 16, "memory_type": "GDDR7", "power_consumption": 320}},
            {"type": "ram", "name": "GOODRAM 32GB (2x16GB) 6400MHz CL32 IRDM BLACK V SILVER", "price": 600.00, "specs": {"type": "DDR5", "speed": 6400, "capacity": 32, "modules": 2, "voltage": 1.35, "latency": "CL32"}},
            {"type": "storage", "name": "Lexar 2TB M.2 PCIe Gen4 NVMe NM790", "price": 700.00, "specs": {"type": "NVMe", "capacity": 2000, "interface": "PCIe Gen4", "form_factor": "M.2"}},
            {"type": "cooler", "name": "SMX Hayate 360", "price": 400.00, "specs": {"type": "AIO", "socket": "AM5", "tdp": 300, "noise_level": 30}},
            {"type": "psu", "name": "MSI MPG A850G PCIe5.0 850W 80 Plus Gold ATX 3.0", "price": 500.00, "specs": {"wattage": 850, "efficiency": "80 Plus Gold", "modular": True, "form_factor": "ATX"}},
            {"type": "case", "name": "Cougar Uniface RGB Black", "price": 302.00, "specs": {"form_factor": "ATX", "max_gpu_length": 400, "max_cooler_height": 180, "fan_slots": 6}},
        ]
    },
    {
        "name": "Zestaw Komputerowy za 10 600 zł - gaming ponad wszystko",
        "description": "Połączenie najszybszego procesora w grach komputerowych z jedną z najmocniejszych desktopowych kart graficznych. Komputer za blisko 12 tysięcy złotych przedstawia się w formie kompleksowej propozycji dla gracza. Platforma korzysta z szybkiej pamięci DDR5 o niskich opóźnieniach.",
        "price": 10600.00,
        "priority": 7,
        "components": [
            {"type": "cpu", "name": "AMD Ryzen 7 9800X3D", "price": 2500.00, "specs": {"socket": "AM5", "cores": 8, "threads": 16, "base_clock": 4.4, "boost_clock": 5.4, "tdp": 120}},
            {"type": "motherboard", "name": "Gigabyte B850 GAMING X WIFI6E", "price": 900.00, "specs": {"socket": "AM5", "chipset": "B850", "form_factor": "ATX", "ram_slots": 4, "ram_type": "DDR5", "ram_max": 128}},
            {"type": "gpu", "name": "Zotac GeForce RTX 5080 Solid Core OC 16GB GDDR7 DLSS4", "price": 4500.00, "specs": {"chipset": "RTX 5080", "vram": 16, "memory_type": "GDDR7", "power_consumption": 320}},
            {"type": "ram", "name": "Lexar 64GB (2x32GB) 6400 CL32 Ares RGB", "price": 1200.00, "specs": {"type": "DDR5", "speed": 6400, "capacity": 64, "modules": 2, "voltage": 1.35, "latency": "CL32"}},
            {"type": "storage", "name": "Lexar 2TB M.2 PCIe Gen4 NVMe NM790", "price": 700.00, "specs": {"type": "NVMe", "capacity": 2000, "interface": "PCIe Gen4", "form_factor": "M.2"}},
            {"type": "cooler", "name": "SMX Hayate 360", "price": 400.00, "specs": {"type": "AIO", "socket": "AM5", "tdp": 300, "noise_level": 30}},
            {"type": "psu", "name": "ENDORFY Supremo FM6 850W 80 Plus Gold ATX 3.1", "price": 450.00, "specs": {"wattage": 850, "efficiency": "80 Plus Gold", "modular": True, "form_factor": "ATX"}},
            {"type": "case", "name": "be quiet! Light Base 500 LX Black", "price": 600.00, "specs": {"form_factor": "ATX", "max_gpu_length": 450, "max_cooler_height": 185, "fan_slots": 7}},
        ]
    },
    {
        "name": "Zestaw Komputerowy za 20 000 zł - dla tych którzy nie liczą się z ceną",
        "description": "Tym razem mówimy już o najszybszym połączeniu CPU + GPU w desktopie. Cena GeForce RTX 5090 delikatnie mówiąc nie zachęca do zakupu, dlatego traktujcie tę propozycję z przymrużeniem oka. Pokazujemy Wam tylko, jaki zestaw można kupić w obecnej chwili nie licząc się z pieniędzmi.",
        "price": 21000.00,
        "priority": 8,
        "components": [
            {"type": "cpu", "name": "AMD Ryzen 9 9950X3D", "price": 4500.00, "specs": {"socket": "AM5", "cores": 16, "threads": 32, "base_clock": 4.2, "boost_clock": 5.7, "tdp": 170}},
            {"type": "motherboard", "name": "Gigabyte X870 AORUS ELITE WIFI7", "price": 1500.00, "specs": {"socket": "AM5", "chipset": "X870", "form_factor": "ATX", "ram_slots": 4, "ram_type": "DDR5", "ram_max": 128}},
            {"type": "gpu", "name": "Gigabyte GeForce RTX 5090 AORUS Master 32GB GDDR7 DLSS4", "price": 10000.00, "specs": {"chipset": "RTX 5090", "vram": 32, "memory_type": "GDDR7", "power_consumption": 450}},
            {"type": "ram", "name": "GOODRAM 64GB (2x32GB) 6000MHz CL30 IRDM BLACK V SILVER", "price": 1200.00, "specs": {"type": "DDR5", "speed": 6000, "capacity": 64, "modules": 2, "voltage": 1.35, "latency": "CL30"}},
            {"type": "storage", "name": "Lexar 2TB M.2 PCIe Gen5 NVMe NM990", "price": 1200.00, "specs": {"type": "NVMe", "capacity": 2000, "interface": "PCIe Gen5", "form_factor": "M.2"}},
            {"type": "cooler", "name": "be quiet! Light Loop 360mm 3x120mm", "price": 600.00, "specs": {"type": "AIO", "socket": "AM5", "tdp": 400, "noise_level": 28}},
            {"type": "psu", "name": "ENDORFY Supremo FM6 1000W 80 Plus Gold ATX 3.1", "price": 700.00, "specs": {"wattage": 1000, "efficiency": "80 Plus Gold", "modular": True, "form_factor": "ATX"}},
            {"type": "case", "name": "Fractal Design Meshify 3 XL Black RGB TG Light Tint", "price": 800.00, "specs": {"form_factor": "E-ATX", "max_gpu_length": 500, "max_cooler_height": 200, "fan_slots": 9}},
        ]
    },
]


async def get_or_create_product(
    db: AsyncSession,
    name: str,
    product_type: ProductType,
    price: float,
    specifications: dict,
    segment: ProductSegment = ProductSegment.GAMING,
) -> Product:
    """Get existing product or create new one"""
    result = await db.execute(
        select(Product).where(Product.name == name, Product.type == product_type)
    )
    product = result.scalar_one_or_none()
    
    if product:
        return product
    
    # Extract brand and model from name
    parts = name.split()
    brand = parts[0] if parts else "Unknown"
    model = " ".join(parts[1:]) if len(parts) > 1 else name
    
    # Calculate performance scores based on component type
    performance_score = None
    gaming_score = None
    
    if product_type == ProductType.CPU:
        cores = specifications.get("cores", 0)
        threads = specifications.get("threads", 0)
        boost_clock = specifications.get("boost_clock", 0)
        performance_score = min(100, (cores * 5 + threads * 2 + boost_clock * 10))
    elif product_type == ProductType.GPU:
        vram = specifications.get("vram", 0)
        power = specifications.get("power_consumption", 0)
        gaming_score = min(100, (vram * 5 + power * 0.5))
        performance_score = gaming_score
    
    product = Product(
        name=name,
        type=product_type,
        segment=segment,
        price=price,
        specifications=specifications,
        brand=brand,
        model=model,
        performance_score=performance_score,
        gaming_score=gaming_score,
        in_stock=True,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )
    db.add(product)
    await db.flush()
    return product


async def seed_presets():
    """Seed database with TechLipton presets"""
    async with AsyncSessionLocal() as db:
        try:
            # Check if presets already exist
            result = await db.execute(select(Preset))
            existing_presets = result.scalars().all()
            if existing_presets:
                print(f"Found {len(existing_presets)} existing presets. Skipping seed.")
                return
            
            print("Starting to seed TechLipton presets...")
            
            for set_data in TECHLIPTON_SETS:
                component_map = {}
                products_list = []
                
                # Create or get products for each component
                for component in set_data["components"]:
                    product_type = ProductType(component["type"])
                    product = await get_or_create_product(
                        db=db,
                        name=component["name"],
                        product_type=product_type,
                        price=component["price"],
                        specifications=component["specs"],
                        segment=ProductSegment.GAMING,
                    )
                    products_list.append(product)
                    component_map[component["type"]] = str(product.id)
                
                # Calculate performance score
                cpu_product = next((p for p in products_list if p.type == ProductType.CPU), None)
                gpu_product = next((p for p in products_list if p.type == ProductType.GPU), None)
                
                performance_score = None
                if cpu_product and gpu_product:
                    cpu_score = cpu_product.performance_score or 0
                    gpu_score = gpu_product.gaming_score or gpu_product.performance_score or 0
                    performance_score = (cpu_score * 0.4) + (gpu_score * 0.6)
                elif cpu_product:
                    performance_score = cpu_product.performance_score
                
                # Create preset
                preset = Preset(
                    name=set_data["name"],
                    description=set_data["description"],
                    device_type=DeviceType.PC,
                    segment=PresetSegment.GAMING,
                    min_budget=set_data["price"] * 0.9,
                    max_budget=set_data["price"] * 1.1,
                    component_map=component_map,
                    total_price=set_data["price"],
                    performance_score=performance_score,
                    reasoning=f"Zestaw polecany przez TechLipton - {set_data['description'][:100]}",
                    is_active=True,
                    priority=set_data["priority"],
                    created_at=datetime.utcnow().isoformat(),
                    updated_at=datetime.utcnow().isoformat(),
                )
                db.add(preset)
                await db.flush()
                
                # Link products to preset
                preset.products = products_list
                
                print(f"Created preset: {set_data['name']}")
            
            await db.commit()
            print(f"Successfully seeded {len(TECHLIPTON_SETS)} presets!")
            
        except Exception as e:
            await db.rollback()
            print(f"Error seeding presets: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(seed_presets())

