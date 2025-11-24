import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, engine
from app.models.product import Product, ProductType, ProductSegment
from app.models.preset import Preset, DeviceType, PresetSegment, preset_products
from sqlalchemy import select
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_performance_score(products_list: list, segment: PresetSegment) -> float:
    """Calculate performance score based on components and segment."""
    
    # Component scores mapping
    cpu_scores = {
        "AMD Ryzen 5 3600": 40,
        "AMD Ryzen 5 5600GT": 45,
        "AMD Ryzen 5 8400F": 50,
        "AMD Ryzen 5 8500G": 52,
        "AMD Ryzen 5 7500F": 60,
        "AMD Ryzen 5 7600": 62,
        "AMD Ryzen 5 7600X": 65,
        "AMD Ryzen 5 7500X3D": 68,
        "AMD Ryzen 5 9600X": 70,
        "AMD Ryzen 7 8700F": 72,
        "Intel Core i5-14600KF": 75,
        "AMD Ryzen 7 7700X": 78,
        "AMD Ryzen 7 7800X3D": 90,
        "AMD Ryzen 7 9700X": 85,
        "AMD Ryzen 9 7900X": 88,
        "AMD Ryzen 7 9800X3D": 95,
        "AMD Ryzen 9 9900X": 92,
        "AMD Ryzen 9 9900X3D": 96,
        "AMD Ryzen 9 9950X": 98,
        "AMD Ryzen 9 9950X3D": 100,
    }
    
    gpu_scores = {
        "ASRock Radeon RX 9060 XT Challenger OC 8GB": 45,
        "ASRock Radeon RX 9060 XT Challenger OC 16GB": 50,
        "KFA2 GeForce RTX 5060 Ti 1-Click OC 16GB": 55,
        "Zotac GeForce RTX 5070 Twin Edge 12GB": 70,
        "Sapphire Radeon RX 9070 Pulse 16GB": 75,
        "Gigabyte Radeon RX 9070 XT Gaming OC 16GB": 80,
        "ASRock Radeon RX 9070 XT Steel Legend Dark 16GB": 80,
        "INNO3D GeForce RTX 5070 Ti X3 16GB": 85,
        "ASUS GeForce RTX 5070 Ti Prime OC 16GB": 85,
        "Zotac GeForce RTX 5080 Solid Core OC 16GB": 92,
        "Gigabyte GeForce RTX 5090 AORUS Master 32GB": 100,
    }
    
    # Segment weights
    weights = {
        PresetSegment.GAMING: {"cpu": 0.25, "gpu": 0.50, "ram": 0.15, "storage": 0.10},
        PresetSegment.PRO: {"cpu": 0.40, "gpu": 0.30, "ram": 0.20, "storage": 0.10},
        PresetSegment.BUSINESS: {"cpu": 0.50, "gpu": 0.10, "ram": 0.25, "storage": 0.15},
        PresetSegment.HOME: {"cpu": 0.30, "gpu": 0.35, "ram": 0.20, "storage": 0.15},
    }
    
    scores = {"cpu": 0, "gpu": 0, "ram": 0, "storage": 0}
    
    for product in products_list:
        # CPU scoring
        if product.type == ProductType.CPU:
            scores["cpu"] = cpu_scores.get(product.name, 50)
        
        # GPU scoring
        elif product.type == ProductType.GPU:
            scores["gpu"] = gpu_scores.get(product.name, 50)
        
        # RAM scoring
        elif product.type == ProductType.RAM:
            capacity = product.specifications.get("Pojemność", "16 GB")
            speed = product.specifications.get("Taktowanie", "3200 MHz")
            ram_type = product.specifications.get("Typ", "DDR4")
            
            # Base score from capacity
            if "64 GB" in capacity or "64GB" in capacity:
                ram_score = 100
            elif "32 GB" in capacity or "32GB" in capacity:
                ram_score = 75
            else:
                ram_score = 50
            
            # Adjust for speed and type
            if ram_type == "DDR5":
                if "6400" in speed:
                    ram_score = min(100, ram_score + 10)
                elif "6000" in speed:
                    ram_score = min(100, ram_score + 5)
            
            scores["ram"] = ram_score
        
        # Storage scoring
        elif product.type == ProductType.STORAGE:
            capacity = product.specifications.get("Pojemność", "1 TB")
            interface = product.specifications.get("Interfejs", "PCIe 4.0")
            
            # Base score from capacity
            storage_score = 100 if ("2 TB" in capacity or "2TB" in capacity) else 70
            
            # Adjust for interface
            if "PCIe 5.0" in interface or "Gen5" in interface:
                storage_score = min(100, storage_score + 15)
            
            scores["storage"] = storage_score
    
    # Calculate weighted score
    segment_weights = weights.get(segment, weights[PresetSegment.GAMING])
    
    final_score = (
        scores["cpu"] * segment_weights["cpu"] +
        scores["gpu"] * segment_weights["gpu"] +
        scores["ram"] * segment_weights["ram"] +
        scores["storage"] * segment_weights["storage"]
    )
    
    return round(final_score, 2)

def get_case_image_url(components_list: list) -> str:
    """Get the image URL for the case in the preset."""
    case_image_map = {
        "Silver Monkey X Cassette": "/cases/silver_monkey_cassette.png",
        "Silver Monkey X Coffer": "/cases/silver_monkey_coffer.png",
        "Deepcool CC560 ARGB": "/cases/deepcool_cc560.png",
        "Deepcool CH560": "/cases/deepcool_ch560.png",
        "Silver Monkey X Pyxis": "/cases/silver_monkey_pyxis.png",
        "Cougar Uniface RGB Black": "/cases/cougar_uniface.png",
        "be quiet! Light Base 500 LX Black": "/cases/bequiet_lightbase.png",
        "Fractal Design Meshify 3 XL Black RGB": "/cases/fractal_meshify.png",
    }
    
    # Find the case in components
    for component_name in components_list:
        if component_name in case_image_map:
            return case_image_map[component_name]
    
    # Default fallback image
    return "/cases/default.png"

async def seed_techlipton_data():
    async with AsyncSessionLocal() as db:
        logger.info("Starting TechLipton data seeding...")

        # --- 1. Define Products (Components & Laptops) ---
        products_data = [
            # --- AMD Processors ---
            {"name": "AMD Ryzen 5 5600GT", "type": ProductType.CPU, "price": 549.00, "specifications": {"Rdzenie": 6, "Wątki": 12, "Gniazdo": "AM4", "Taktowanie bazowe": "3.6 GHz", "Taktowanie boost": "4.6 GHz", "Benchmark": "19 800 pkt"}, "description": "Zintegrowana grafika Vega"},
            {"name": "AMD Ryzen 5 3600", "type": ProductType.CPU, "price": 399.00, "specifications": {"Rdzenie": 6, "Wątki": 12, "Gniazdo": "AM4", "Taktowanie bazowe": "3.6 GHz", "Taktowanie boost": "4.2 GHz", "Benchmark": "17 800 pkt"}, "description": "Klasyk wydajności"},
            {"name": "AMD Ryzen 5 7500F", "type": ProductType.CPU, "price": 749.00, "specifications": {"Rdzenie": 6, "Wątki": 12, "Gniazdo": "AM5", "Taktowanie bazowe": "3.7 GHz", "Taktowanie boost": "5.0 GHz", "Benchmark": "26 500 pkt"}, "description": "Budżetowy król AM5"},
            {"name": "AMD Ryzen 5 8400F", "type": ProductType.CPU, "price": 569.00, "specifications": {"Rdzenie": 6, "Wątki": 12, "Gniazdo": "AM5", "Taktowanie bazowe": "4.2 GHz", "Taktowanie boost": "4.7 GHz", "Benchmark": "24 002 pkt"}, "description": "Budżetowy procesor AM5"},
            {"name": "AMD Ryzen 5 8500G", "type": ProductType.CPU, "price": 659.00, "specifications": {"Rdzenie": 6, "Wątki": 12, "Gniazdo": "AM5", "Taktowanie bazowe": "3.5 GHz", "Taktowanie boost": "5.0 GHz", "Benchmark": "21 862 pkt"}, "description": "Zintegrowana grafika RDNA 3"},
            {"name": "AMD Ryzen 5 7600", "type": ProductType.CPU, "price": 739.00, "specifications": {"Rdzenie": 6, "Wątki": 12, "Gniazdo": "AM5", "Taktowanie bazowe": "3.8 GHz", "Taktowanie boost": "5.1 GHz", "Benchmark": "27 012 pkt"}, "description": "Świetny do gier"},
            {"name": "AMD Ryzen 5 7600X", "type": ProductType.CPU, "price": 769.00, "specifications": {"Rdzenie": 6, "Wątki": 12, "Gniazdo": "AM5", "Taktowanie bazowe": "4.7 GHz", "Taktowanie boost": "5.3 GHz", "Benchmark": "28 953 pkt"}, "description": "Wyższe taktowanie"},
            {"name": "AMD Ryzen 5 9600X", "type": ProductType.CPU, "price": 879.00, "specifications": {"Rdzenie": 6, "Wątki": 12, "Gniazdo": "AM5", "Taktowanie bazowe": "3.9 GHz", "Taktowanie boost": "5.4 GHz", "Benchmark": "29 821 pkt"}, "description": "Najnowsza architektura Zen 5"},
            {"name": "AMD Ryzen 7 8700F", "type": ProductType.CPU, "price": 899.00, "specifications": {"Rdzenie": 8, "Wątki": 16, "Gniazdo": "AM5", "Taktowanie bazowe": "4.1 GHz", "Taktowanie boost": "5.0 GHz", "Benchmark": "32 036 pkt"}, "description": "8 rdzeni w dobrej cenie"},
            {"name": "AMD Ryzen 7 7700X", "type": ProductType.CPU, "price": 1149.00, "specifications": {"Rdzenie": 8, "Wątki": 16, "Gniazdo": "AM5", "Taktowanie bazowe": "4.5 GHz", "Taktowanie boost": "5.4 GHz", "Benchmark": "36 536 pkt"}, "description": "Wydajność wielowątkowa"},
            {"name": "AMD Ryzen 5 7500X3D", "type": ProductType.CPU, "price": 1219.00, "specifications": {"Rdzenie": 6, "Wątki": 12, "Gniazdo": "AM5", "Taktowanie bazowe": "4.0 GHz", "Taktowanie boost": "4.5 GHz", "Benchmark": "25 287 pkt"}, "description": "Technologia 3D V-Cache"},
            {"name": "AMD Ryzen 7 9700X", "type": ProductType.CPU, "price": 1299.00, "specifications": {"Rdzenie": 8, "Wątki": 16, "Gniazdo": "AM5", "Taktowanie bazowe": "3.8 GHz", "Taktowanie boost": "5.5 GHz", "Benchmark": "37 576 pkt"}, "description": "Nowa generacja 8 rdzeni"},
            {"name": "AMD Ryzen 9 7900X", "type": ProductType.CPU, "price": 1399.00, "specifications": {"Rdzenie": 12, "Wątki": 24, "Gniazdo": "AM5", "Taktowanie bazowe": "4.7 GHz", "Taktowanie boost": "5.6 GHz", "Benchmark": "52 422 pkt"}, "description": "Do pracy i gier"},
            {"name": "AMD Ryzen 7 7800X3D", "type": ProductType.CPU, "price": 1649.00, "specifications": {"Rdzenie": 8, "Wątki": 16, "Gniazdo": "AM5", "Taktowanie bazowe": "4.2 GHz", "Taktowanie boost": "5.0 GHz", "Benchmark": "35 059 pkt"}, "description": "Najlepszy procesor do gier"},
            {"name": "AMD Ryzen 9 9900X", "type": ProductType.CPU, "price": 1719.00, "specifications": {"Rdzenie": 12, "Wątki": 24, "Gniazdo": "AM5", "Taktowanie bazowe": "4.4 GHz", "Taktowanie boost": "5.6 GHz", "Benchmark": "54 763 pkt"}, "description": "Zen 5 z 12 rdzeniami"},
            {"name": "AMD Ryzen 7 9800X3D", "type": ProductType.CPU, "price": 1999.00, "specifications": {"Rdzenie": 8, "Wątki": 16, "Gniazdo": "AM5", "Taktowanie bazowe": "4.7 GHz", "Taktowanie boost": "5.2 GHz", "Benchmark": "40 162 pkt"}, "description": "Absolutny top wydajności"},
            {"name": "AMD Ryzen 9 9950X", "type": ProductType.CPU, "price": 2349.00, "specifications": {"Rdzenie": 16, "Wątki": 32, "Gniazdo": "AM5", "Taktowanie bazowe": "4.3 GHz", "Taktowanie boost": "5.7 GHz", "Benchmark": "66 972 pkt"}, "description": "Flagowiec Zen 5"},
            {"name": "AMD Ryzen 9 9900X3D", "type": ProductType.CPU, "price": 2549.00, "specifications": {"Rdzenie": 12, "Wątki": 24, "Gniazdo": "AM5", "Taktowanie bazowe": "4.4 GHz", "Taktowanie boost": "5.5 GHz", "Benchmark": "56 398 pkt"}, "description": "12 rdzeni z 3D V-Cache"},
            {"name": "AMD Ryzen 9 9950X3D", "type": ProductType.CPU, "price": 2949.00, "specifications": {"Rdzenie": 16, "Wątki": 32, "Gniazdo": "AM5", "Taktowanie bazowe": "4.3 GHz", "Taktowanie boost": "5.7 GHz", "Benchmark": "70 420 pkt"}, "description": "Potwór wielowątkowy"},
            
            # --- Intel Processors ---
            {"name": "Intel Core i5-14400F", "type": ProductType.CPU, "price": 699.00, "specifications": {"Rdzenie": 10, "Wątki": 16, "Gniazdo": "LGA1700", "Taktowanie bazowe": "2.5 GHz", "Taktowanie boost": "4.7 GHz", "Benchmark": "25 692 pkt"}, "description": "Budżetowy Intel 14. generacji"},
            {"name": "Intel Core i5-14600K", "type": ProductType.CPU, "price": 779.00, "specifications": {"Rdzenie": 14, "Wątki": 20, "Gniazdo": "LGA1700", "Taktowanie bazowe": "3.5 GHz", "Taktowanie boost": "5.3 GHz", "Benchmark": "38 619 pkt"}, "description": "Odblokowany mnożnik"},
            {"name": "Intel Core i5-14600KF", "type": ProductType.CPU, "price": 699.00, "specifications": {"Rdzenie": 14, "Wątki": 20, "Gniazdo": "LGA1700", "Taktowanie bazowe": "3.5 GHz", "Taktowanie boost": "5.3 GHz", "Benchmark": "38 671 pkt"}, "description": "Bez zintegrowanej grafiki"},
            {"name": "Intel Core i7-12700KF", "type": ProductType.CPU, "price": 779.00, "specifications": {"Rdzenie": 12, "Wątki": 20, "Gniazdo": "LGA1700", "Taktowanie bazowe": "3.6 GHz", "Taktowanie boost": "5.0 GHz", "Benchmark": "34 069 pkt"}, "description": "12. generacja Alder Lake"},
            {"name": "Intel Core Ultra 5 225", "type": ProductType.CPU, "price": 799.00, "specifications": {"Rdzenie": 10, "Wątki": 12, "Gniazdo": "LGA1851", "Taktowanie bazowe": "3.3 GHz", "Taktowanie boost": "4.9 GHz", "Benchmark": "31 097 pkt"}, "description": "Nowa architektura Arrow Lake"},
            {"name": "Intel Core Ultra 5 245KF", "type": ProductType.CPU, "price": 829.00, "specifications": {"Rdzenie": 14, "Wątki": 20, "Gniazdo": "LGA1851", "Taktowanie bazowe": "3.6 GHz", "Taktowanie boost": "5.2 GHz", "Benchmark": "43 413 pkt"}, "description": "Bez zintegrowanej grafiki"},
            {"name": "Intel Core Ultra 5 245K", "type": ProductType.CPU, "price": 899.00, "specifications": {"Rdzenie": 14, "Wątki": 20, "Gniazdo": "LGA1851", "Taktowanie bazowe": "3.6 GHz", "Taktowanie boost": "5.2 GHz", "Benchmark": "43 424 pkt"}, "description": "Odblokowany mnożnik"},
            {"name": "Intel Core Ultra 7 265KF", "type": ProductType.CPU, "price": 1249.00, "specifications": {"Rdzenie": 20, "Wątki": 28, "Gniazdo": "LGA1851", "Taktowanie bazowe": "3.9 GHz", "Taktowanie boost": "5.5 GHz", "Benchmark": "58 704 pkt"}, "description": "Wysoka wydajność wielowątkowa"},
            {"name": "Intel Core i7-14700F", "type": ProductType.CPU, "price": 1279.00, "specifications": {"Rdzenie": 20, "Wątki": 28, "Gniazdo": "LGA1700", "Taktowanie bazowe": "2.1 GHz", "Taktowanie boost": "5.4 GHz", "Benchmark": "41 473 pkt"}, "description": "20 rdzeni dla profesjonalistów"},
            {"name": "Intel Core Ultra 7 265K", "type": ProductType.CPU, "price": 1349.00, "specifications": {"Rdzenie": 20, "Wątki": 28, "Gniazdo": "LGA1851", "Taktowanie bazowe": "3.9 GHz", "Taktowanie boost": "5.5 GHz", "Benchmark": "58 789 pkt"}, "description": "Topowy Core Ultra 7"},
            {"name": "Intel Core i7-14700KF", "type": ProductType.CPU, "price": 1399.00, "specifications": {"Rdzenie": 20, "Wątki": 28, "Gniazdo": "LGA1700", "Taktowanie bazowe": "3.4 GHz", "Taktowanie boost": "5.6 GHz", "Benchmark": "52 247 pkt"}, "description": "Średnia wydajność"},
            {"name": "Intel Core i7-14700K", "type": ProductType.CPU, "price": 1449.00, "specifications": {"Rdzenie": 20, "Wątki": 28, "Gniazdo": "LGA1700", "Taktowanie bazowe": "3.4 GHz", "Taktowanie boost": "5.6 GHz", "Benchmark": "52 241 pkt"}, "description": "Odblokowany i7"},
            {"name": "Intel Core Ultra 7 265", "type": ProductType.CPU, "price": 1479.00, "specifications": {"Rdzenie": 20, "Wątki": 28, "Gniazdo": "LGA1851", "Taktowanie bazowe": "2.4 GHz", "Taktowanie boost": "5.3 GHz", "Benchmark": "49 635 pkt"}, "description": "Zablokowany mnożnik"},
            {"name": "Intel Core i9-14900KF", "type": ProductType.CPU, "price": 1799.00, "specifications": {"Rdzenie": 24, "Wątki": 32, "Gniazdo": "LGA1700", "Taktowanie bazowe": "3.2 GHz", "Taktowanie boost": "6.0 GHz", "Benchmark": "58 338 pkt"}, "description": "Bez grafiki zintegrowanej"},
            {"name": "Intel Core i9-14900K", "type": ProductType.CPU, "price": 1949.00, "specifications": {"Rdzenie": 24, "Wątki": 32, "Gniazdo": "LGA1700", "Taktowanie bazowe": "3.2 GHz", "Taktowanie boost": "6.0 GHz", "Benchmark": "58 552 pkt"}, "description": "Flagowiec 14. generacji"},
            {"name": "Intel Core Ultra 9 285K", "type": ProductType.CPU, "price": 2149.00, "specifications": {"Rdzenie": 24, "Wątki": 32, "Gniazdo": "LGA1851", "Taktowanie bazowe": "3.7 GHz", "Taktowanie boost": "5.7 GHz", "Benchmark": "67 516 pkt"}, "description": "Najnowsza architektura"},
            {"name": "Intel Core Ultra 9 285", "type": ProductType.CPU, "price": 2399.00, "specifications": {"Rdzenie": 24, "Wątki": 32, "Gniazdo": "LGA1851", "Taktowanie bazowe": "2.5 GHz", "Taktowanie boost": "5.6 GHz", "Benchmark": "57 579 pkt"}, "description": "Topowy Core Ultra 9"},
            
            # --- NVIDIA Graphics Cards ---
            # RTX 5060 8GB
            {"name": "MSI GeForce RTX 5060 Ventus 2X OC 8GB", "type": ProductType.GPU, "price": 1339.00, "specifications": {"VRAM": "8 GB", "Długość": "197 mm", "Taktowanie boost": "2535 MHz", "Wentylatory": "2"}, "description": "Kompaktowa karta z DLSS 4"},
            {"name": "Gigabyte GeForce RTX 5060 Windforce Max OC 8GB", "type": ProductType.GPU, "price": 1339.00, "specifications": {"VRAM": "8 GB", "Długość": "199 mm", "Taktowanie boost": "2512 MHz", "Wentylatory": "2"}, "description": "Wydajne chłodzenie"},
            {"name": "ASUS GeForce RTX 5060 Dual OC 8GB", "type": ProductType.GPU, "price": 1350.00, "specifications": {"VRAM": "8 GB", "Długość": "228 mm", "Taktowanie boost": "2535 MHz", "Wentylatory": "2"}, "description": "Dual OC od ASUS"},
            {"name": "Gigabyte GeForce RTX 5060 Eagle Max OC 8GB", "type": ProductType.GPU, "price": 1399.00, "specifications": {"VRAM": "8 GB", "Długość": "281 mm", "Taktowanie boost": "2550 MHz", "Wentylatory": "3"}, "description": "Trójwentylatorowa Eagle"},
            {"name": "Gigabyte GeForce RTX 5060 Gaming OC 8GB", "type": ProductType.GPU, "price": 1469.00, "specifications": {"VRAM": "8 GB", "Długość": "281 mm", "Taktowanie boost": "2810 MHz", "Wentylatory": "3"}, "description": "Gaming z RGB"},
            {"name": "MSI GeForce RTX 5060 Gaming OC 8GB", "type": ProductType.GPU, "price": 1479.00, "specifications": {"VRAM": "8 GB", "Długość": "248 mm", "Taktowanie boost": "2640 MHz", "Wentylatory": "2"}, "description": "MSI Gaming OC"},
            {"name": "ASUS GeForce RTX 5060 Prime OC 8GB", "type": ProductType.GPU, "price": 1512.00, "specifications": {"VRAM": "8 GB", "Długość": "268 mm", "Taktowanie boost": "2527 MHz", "Wentylatory": "3"}, "description": "Biało-czarna Prime"},
            {"name": "Gigabyte GeForce RTX 5060 AORUS Elite 8GB", "type": ProductType.GPU, "price": 1549.00, "specifications": {"VRAM": "8 GB", "Długość": "329 mm", "Taktowanie boost": "2722 MHz", "Wentylatory": "3"}, "description": "AORUS z RGB"},
            {"name": "Gigabyte GeForce RTX 5060 Aero OC 8GB", "type": ProductType.GPU, "price": 1559.00, "specifications": {"VRAM": "8 GB", "Długość": "281 mm", "Taktowanie boost": "2595 MHz", "Wentylatory": "3"}, "description": "Biała Aero OC"},
            
            # RTX 5060 Ti 8GB
            {"name": "Gigabyte GeForce RTX 5060 Ti Windforce OC 8GB", "type": ProductType.GPU, "price": 1699.00, "specifications": {"VRAM": "8 GB", "Długość": "272 mm", "Taktowanie boost": "2587 MHz", "Wentylatory": "3"}, "description": "Ti Windforce"},
            {"name": "Gigabyte GeForce RTX 5060 Ti Eagle OC 8GB", "type": ProductType.GPU, "price": 1779.00, "specifications": {"VRAM": "8 GB", "Długość": "215 mm", "Taktowanie boost": "2617 MHz", "Wentylatory": "2"}, "description": "Kompaktowa Eagle"},
            {"name": "MSI GeForce RTX 5060 Ti Ventus 2X OC Plus 8GB", "type": ProductType.GPU, "price": 1819.00, "specifications": {"VRAM": "8 GB", "Długość": "250 mm", "Taktowanie boost": "2575 MHz", "Wentylatory": "2"}, "description": "Ventus Plus"},
            {"name": "Gigabyte GeForce RTX 5060 Ti Gaming OC 8GB", "type": ProductType.GPU, "price": 1879.00, "specifications": {"VRAM": "8 GB", "Długość": "281 mm", "Taktowanie boost": "2600 MHz", "Wentylatory": "3"}, "description": "Gaming OC"},
            
            # RTX 5060 Ti 16GB
            {"name": "Gigabyte GeForce RTX 5060 Ti Windforce OC 16GB", "type": ProductType.GPU, "price": 1999.00, "specifications": {"VRAM": "16 GB", "Długość": "272 mm", "Taktowanie boost": "2587 MHz", "Wentylatory": "3"}, "description": "16GB Windforce"},
            {"name": "Gigabyte GeForce RTX 5060 Ti Eagle OC 16GB", "type": ProductType.GPU, "price": 2079.00, "specifications": {"VRAM": "16 GB", "Długość": "215 mm", "Taktowanie boost": "2617 MHz", "Wentylatory": "2"}, "description": "16GB Eagle"},
            {"name": "Gigabyte GeForce RTX 5060 Ti Eagle Max OC 16GB", "type": ProductType.GPU, "price": 2149.00, "specifications": {"VRAM": "16 GB", "Długość": "281 mm", "Taktowanie boost": "2600 MHz", "Wentylatory": "3"}, "description": "Eagle Max 16GB"},
            {"name": "MSI GeForce RTX 5060 Ti Gaming OC 16GB", "type": ProductType.GPU, "price": 2249.00, "specifications": {"VRAM": "16 GB", "Długość": "281 mm", "Taktowanie boost": "2610 MHz", "Wentylatory": "3"}, "description": "MSI Gaming 16GB"},
            {"name": "ASUS GeForce RTX 5060 Ti Prime OC 16GB", "type": ProductType.GPU, "price": 2299.00, "specifications": {"VRAM": "16 GB", "Długość": "300 mm", "Taktowanie boost": "2535 MHz", "Wentylatory": "3"}, "description": "Prime 16GB"},
            {"name": "Gigabyte GeForce RTX 5060 Ti Aero OC 16GB", "type": ProductType.GPU, "price": 2299.00, "specifications": {"VRAM": "16 GB", "Długość": "300 mm", "Taktowanie boost": "2600 MHz", "Wentylatory": "3"}, "description": "Biała Aero 16GB"},
            {"name": "Gigabyte GeForce RTX 5060 Ti AORUS Elite 16GB", "type": ProductType.GPU, "price": 2359.00, "specifications": {"VRAM": "16 GB", "Długość": "332 mm", "Taktowanie boost": "2700 MHz", "Wentylatory": "3"}, "description": "AORUS Elite 16GB"},
            
            # RTX 5070 12GB
            {"name": "ASUS GeForce RTX 5070 Dual OC 12GB", "type": ProductType.GPU, "price": 2445.00, "specifications": {"VRAM": "12 GB", "Długość": "230 mm", "Taktowanie boost": "2550 MHz", "Wentylatory": "2"}, "description": "Dual OC 5070"},
            {"name": "Gigabyte GeForce RTX 5070 Windforce OC 12GB", "type": ProductType.GPU, "price": 2469.00, "specifications": {"VRAM": "12 GB", "Długość": "300 mm", "Taktowanie boost": "2542 MHz", "Wentylatory": "3"}, "description": "Windforce 5070"},
            {"name": "MSI GeForce RTX 5070 Ventus 2X OC 12GB", "type": ProductType.GPU, "price": 2499.00, "specifications": {"VRAM": "12 GB", "Długość": "236 mm", "Taktowanie boost": "2557 MHz", "Wentylatory": "2"}, "description": "Kompaktowa Ventus"},
            {"name": "MSI GeForce RTX 5070 Ventus 2X OC White 12GB", "type": ProductType.GPU, "price": 2649.00, "specifications": {"VRAM": "12 GB", "Długość": "236 mm", "Taktowanie boost": "2557 MHz", "Wentylatory": "2"}, "description": "Biała Ventus"},
            {"name": "Gigabyte GeForce RTX 5070 Eagle OC Ice 12GB", "type": ProductType.GPU, "price": 2669.00, "specifications": {"VRAM": "12 GB", "Długość": "300 mm", "Taktowanie boost": "2580 MHz", "Wentylatory": "3"}, "description": "Biała Eagle Ice"},
            {"name": "Gigabyte GeForce RTX 5070 Eagle OC 12GB", "type": ProductType.GPU, "price": 2699.00, "specifications": {"VRAM": "12 GB", "Długość": "300 mm", "Taktowanie boost": "2570 MHz", "Wentylatory": "3"}, "description": "Eagle OC"},
            {"name": "Gigabyte GeForce RTX 5070 Gaming OC 12GB", "type": ProductType.GPU, "price": 2729.00, "specifications": {"VRAM": "12 GB", "Długość": "300 mm", "Taktowanie boost": "2625 MHz", "Wentylatory": "3"}, "description": "Gaming OC"},
            {"name": "ASUS GeForce RTX 5070 Prime OC White 12GB", "type": ProductType.GPU, "price": 2899.00, "specifications": {"VRAM": "12 GB", "Długość": "300 mm", "Taktowanie boost": "2560 MHz", "Wentylatory": "3"}, "description": "Biała Prime"},
            {"name": "Gigabyte GeForce RTX 5070 Aero OC 12GB", "type": ProductType.GPU, "price": 2899.00, "specifications": {"VRAM": "12 GB", "Długość": "300 mm", "Taktowanie boost": "2600 MHz", "Wentylatory": "3"}, "description": "Aero OC"},
            {"name": "MSI GeForce RTX 5070 Gaming Trio OC 12GB", "type": ProductType.GPU, "price": 2939.00, "specifications": {"VRAM": "12 GB", "Długość": "338 mm", "Taktowanie boost": "2675 MHz", "Wentylatory": "3"}, "description": "Gaming Trio"},
            {"name": "MSI GeForce RTX 5070 Gaming Trio OC White 12GB", "type": ProductType.GPU, "price": 3099.00, "specifications": {"VRAM": "12 GB", "Długość": "338 mm", "Taktowanie boost": "2675 MHz", "Wentylatory": "3"}, "description": "Biała Trio"},
            {"name": "Gigabyte GeForce RTX 5070 AORUS Master 12GB", "type": ProductType.GPU, "price": 3189.00, "specifications": {"VRAM": "12 GB", "Długość": "338 mm", "Taktowanie boost": "2715 MHz", "Wentylatory": "3"}, "description": "AORUS Master"},
            {"name": "ASUS GeForce RTX 5070 ROG Strix OC 12GB", "type": ProductType.GPU, "price": 3599.00, "specifications": {"VRAM": "12 GB", "Długość": "336 mm", "Taktowanie boost": "2700 MHz", "Wentylatory": "3"}, "description": "ROG Strix OC"},
            
            # RTX 5070 Ti 16GB
            {"name": "MSI GeForce RTX 5070 Ti Ventus 3X OC 16GB", "type": ProductType.GPU, "price": 3599.00, "specifications": {"VRAM": "16 GB", "Długość": "303 mm", "Taktowanie boost": "2482 MHz", "Wentylatory": "3"}, "description": "Ventus 3X Ti"},
            {"name": "Gigabyte GeForce RTX 5070 Ti Windforce OC 16GB", "type": ProductType.GPU, "price": 3619.00, "specifications": {"VRAM": "16 GB", "Długość": "304 mm", "Taktowanie boost": "2540 MHz", "Wentylatory": "3"}, "description": "Windforce Ti"},
            {"name": "Gigabyte GeForce RTX 5070 Ti Eagle OC 16GB", "type": ProductType.GPU, "price": 3729.00, "specifications": {"VRAM": "16 GB", "Długość": "304 mm", "Taktowanie boost": "2542 MHz", "Wentylatory": "3"}, "description": "Eagle Ti"},
            {"name": "Gigabyte GeForce RTX 5070 Ti Eagle OC Ice 16GB", "type": ProductType.GPU, "price": 3999.00, "specifications": {"VRAM": "16 GB", "Długość": "304 mm", "Taktowanie boost": "2542 MHz", "Wentylatory": "3"}, "description": "Biała Eagle Ti"},
            {"name": "Gigabyte GeForce RTX 5070 Ti Gaming OC 16GB", "type": ProductType.GPU, "price": 3999.00, "specifications": {"VRAM": "16 GB", "Długość": "342 mm", "Taktowanie boost": "2588 MHz", "Wentylatory": "3"}, "description": "Gaming Ti"},
            {"name": "Gigabyte GeForce RTX 5070 Ti Aero OC 16GB", "type": ProductType.GPU, "price": 4119.00, "specifications": {"VRAM": "16 GB", "Długość": "300 mm", "Taktowanie boost": "2588 MHz", "Wentylatory": "3"}, "description": "Aero Ti"},
            {"name": "MSI GeForce RTX 5070 Ti Gaming Trio OC 16GB", "type": ProductType.GPU, "price": 4179.00, "specifications": {"VRAM": "16 GB", "Długość": "338 mm", "Taktowanie boost": "2625 MHz", "Wentylatory": "3"}, "description": "Trio Ti"},
            {"name": "MSI GeForce RTX 5070 Ti Gaming Trio OC White 16GB", "type": ProductType.GPU, "price": 4299.00, "specifications": {"VRAM": "16 GB", "Długość": "338 mm", "Taktowanie boost": "2625 MHz", "Wentylatory": "3"}, "description": "Biała Trio Ti"},
            {"name": "ASUS GeForce RTX 5070 Ti ROG Strix OC 16GB", "type": ProductType.GPU, "price": 4849.00, "specifications": {"VRAM": "16 GB", "Długość": "336 mm", "Taktowanie boost": "2650 MHz", "Wentylatory": "3"}, "description": "ROG Strix Ti"},
            
            # RTX 5080 16GB
            {"name": "Gigabyte GeForce RTX 5080 Windforce OC 16GB", "type": ProductType.GPU, "price": 4649.00, "specifications": {"VRAM": "16 GB", "Długość": "304 mm", "Taktowanie boost": "2675 MHz", "Wentylatory": "3"}, "description": "Windforce 5080"},
            {"name": "MSI GeForce RTX 5080 Ventus 3X OC White 16GB", "type": ProductType.GPU, "price": 5499.00, "specifications": {"VRAM": "16 GB", "Długość": "320 mm", "Taktowanie boost": "2700 MHz", "Wentylatory": "3"}, "description": "Biała Ventus 5080"},
            {"name": "Gigabyte GeForce RTX 5080 Gaming OC 16GB", "type": ProductType.GPU, "price": 5589.00, "specifications": {"VRAM": "16 GB", "Długość": "342 mm", "Taktowanie boost": "2730 MHz", "Wentylatory": "3"}, "description": "Gaming 5080"},
            {"name": "Gigabyte GeForce RTX 5080 Aero OC 16GB", "type": ProductType.GPU, "price": 5599.00, "specifications": {"VRAM": "16 GB", "Długość": "342 mm", "Taktowanie boost": "2730 MHz", "Wentylatory": "3"}, "description": "Biała Aero 5080"},
            {"name": "Gigabyte GeForce RTX 5080 AORUS Master 16GB", "type": ProductType.GPU, "price": 6199.00, "specifications": {"VRAM": "16 GB", "Długość": "342 mm", "Taktowanie boost": "2805 MHz", "Wentylatory": "3"}, "description": "AORUS Master 5080"},
            {"name": "Gigabyte GeForce RTX 5080 AORUS Master Ice 16GB", "type": ProductType.GPU, "price": 6299.00, "specifications": {"VRAM": "16 GB", "Długość": "342 mm", "Taktowanie boost": "2805 MHz", "Wentylatory": "3"}, "description": "Biała AORUS 5080"},
            {"name": "ASUS GeForce RTX 5080 TUF Gaming OC 16GB", "type": ProductType.GPU, "price": 6499.00, "specifications": {"VRAM": "16 GB", "Długość": "326 mm", "Taktowanie boost": "2675 MHz", "Wentylatory": "3"}, "description": "TUF Gaming 5080"},
            {"name": "Zotac GeForce RTX 5080 Solid Core OC 16GB", "type": ProductType.GPU, "price": 5899.00, "specifications": {"VRAM": "16 GB", "Długość": "330 mm", "Taktowanie boost": "2750 MHz", "Wentylatory": "3"}, "description": "Solid Core 5080"},

            # RTX 5090 32GB
            {"name": "Gigabyte GeForce RTX 5090 AORUS Master 32GB", "type": ProductType.GPU, "price": 9999.00, "specifications": {"VRAM": "32 GB", "Długość": "360 mm", "Taktowanie boost": "2900 MHz", "Wentylatory": "3"}, "description": "Topowy potwór 5090"},

            # Missing RTX 5060 Ti / 5070 / 5070 Ti
            {"name": "KFA2 GeForce RTX 5060 Ti 1-Click OC 16GB", "type": ProductType.GPU, "price": 1999.00, "specifications": {"VRAM": "16 GB", "Długość": "250 mm", "Taktowanie boost": "2565 MHz", "Wentylatory": "2"}, "description": "KFA2 1-Click OC"},
            {"name": "Zotac GeForce RTX 5070 Twin Edge 12GB", "type": ProductType.GPU, "price": 2599.00, "specifications": {"VRAM": "12 GB", "Długość": "230 mm", "Taktowanie boost": "2550 MHz", "Wentylatory": "2"}, "description": "Twin Edge 5070"},
            {"name": "INNO3D GeForce RTX 5070 Ti X3 16GB", "type": ProductType.GPU, "price": 3899.00, "specifications": {"VRAM": "16 GB", "Długość": "300 mm", "Taktowanie boost": "2600 MHz", "Wentylatory": "3"}, "description": "INNO3D X3"},
            {"name": "ASUS GeForce RTX 5070 Ti Prime OC 16GB", "type": ProductType.GPU, "price": 3999.00, "specifications": {"VRAM": "16 GB", "Długość": "310 mm", "Taktowanie boost": "2610 MHz", "Wentylatory": "3"}, "description": "Prime OC Ti"},
            
            # --- AMD Radeon Graphics Cards ---
            # RX 7700 XT
            {"name": "ASRock Radeon RX 7700 XT Challenger OC 12GB", "type": ProductType.GPU, "price": 1499.00, "specifications": {"VRAM": "12 GB", "Długość": "266 mm", "Taktowanie boost": "2584 MHz", "Wentylatory": "2"}, "description": "Challenger OC 12GB"},
            
            # RX 9060 XT 8GB
            {"name": "ASRock Radeon RX 9060 XT Challenger OC 8GB", "type": ProductType.GPU, "price": 1350.00, "specifications": {"VRAM": "8 GB", "Długość": "260 mm", "Taktowanie boost": "3100 MHz", "Wentylatory": "2"}, "description": "Challenger OC 8GB"},
            
            # RX 9060 XT 8GB
            {"name": "Gigabyte Radeon RX 9060 XT Gaming 8GB", "type": ProductType.GPU, "price": 1399.00, "specifications": {"VRAM": "8 GB", "Długość": "281 mm", "Taktowanie boost": "3130 MHz", "Wentylatory": "3"}, "description": "Gaming 8GB"},
            {"name": "Gigabyte Radeon RX 9060 XT Gaming OC 8GB", "type": ProductType.GPU, "price": 1449.00, "specifications": {"VRAM": "8 GB", "Długość": "281 mm", "Taktowanie boost": "3130 MHz", "Wentylatory": "3"}, "description": "Gaming OC 8GB"},
            
            # RX 9060 XT 16GB
            {"name": "ASRock Radeon RX 9060 XT Challenger OC 16GB", "type": ProductType.GPU, "price": 1599.00, "specifications": {"VRAM": "16 GB", "Długość": "249 mm", "Taktowanie boost": "3130 MHz", "Wentylatory": "2"}, "description": "Challenger OC 16GB"},
            {"name": "Sapphire Radeon RX 9060 XT Pulse OC 16GB", "type": ProductType.GPU, "price": 1599.00, "specifications": {"VRAM": "16 GB", "Długość": "240 mm", "Taktowanie boost": "3290 MHz", "Wentylatory": "2"}, "description": "Pulse OC 16GB"},
            {"name": "Sapphire Radeon RX 9060 XT Pure OC 16GB", "type": ProductType.GPU, "price": 1649.00, "specifications": {"VRAM": "16 GB", "Długość": "290 mm", "Taktowanie boost": "3290 MHz", "Wentylatory": "3"}, "description": "Biała Pure OC"},
            {"name": "Gigabyte Radeon RX 9060 XT Gaming OC 16GB", "type": ProductType.GPU, "price": 1679.00, "specifications": {"VRAM": "16 GB", "Długość": "281 mm", "Taktowanie boost": "3320 MHz", "Wentylatory": "3"}, "description": "Gaming OC 16GB"},
            {"name": "ASUS Radeon RX 9060 XT Dual 16GB", "type": ProductType.GPU, "price": 1729.00, "specifications": {"VRAM": "16 GB", "Długość": "275 mm", "Taktowanie boost": "3130 MHz", "Wentylatory": "2"}, "description": "Dual 16GB"},
            {"name": "Sapphire Radeon RX 9060 XT Nitro+ OC 16GB", "type": ProductType.GPU, "price": 1778.00, "specifications": {"VRAM": "16 GB", "Długość": "300 mm", "Taktowanie boost": "3290 MHz", "Wentylatory": "3"}, "description": "Nitro+ OC 16GB"},
            {"name": "ASUS Radeon RX 9060 XT Prime OC 16GB", "type": ProductType.GPU, "price": 1859.00, "specifications": {"VRAM": "16 GB", "Długość": "300 mm", "Taktowanie boost": "3310 MHz", "Wentylatory": "3"}, "description": "Prime OC 16GB"},
            {"name": "ASUS Radeon RX 9060 XT TUF Gaming OC 16GB", "type": ProductType.GPU, "price": 1999.00, "specifications": {"VRAM": "16 GB", "Długość": "304 mm", "Taktowanie boost": "3130 MHz", "Wentylatory": "3"}, "description": "TUF Gaming OC"},
            
            # RX 9070 16GB
            {"name": "Gigabyte Radeon RX 9070 Gaming OC 16GB", "type": ProductType.GPU, "price": 2599.00, "specifications": {"VRAM": "16 GB", "Długość": "300 mm", "Taktowanie boost": "2700 MHz", "Wentylatory": "3"}, "description": "Gaming OC 9070"},
            {"name": "Sapphire Radeon RX 9070 Pulse 16GB", "type": ProductType.GPU, "price": 2599.00, "specifications": {"VRAM": "16 GB", "Długość": "300 mm", "Taktowanie boost": "2970 MHz", "Wentylatory": "3"}, "description": "Pulse 9070"},
            {"name": "Sapphire Radeon RX 9070 Pure OC 16GB", "type": ProductType.GPU, "price": 2699.00, "specifications": {"VRAM": "16 GB", "Długość": "320 mm", "Taktowanie boost": "2700 MHz", "Wentylatory": "3"}, "description": "Biała Pure 9070"},
            
            # RX 9070 XT 16GB
            {"name": "Gigabyte Radeon RX 9070 XT Gaming OC 16GB", "type": ProductType.GPU, "price": 2869.00, "specifications": {"VRAM": "16 GB", "Długość": "335 mm", "Taktowanie boost": "3010 MHz", "Wentylatory": "3"}, "description": "Gaming OC XT"},
            {"name": "Sapphire Radeon RX 9070 XT Pulse 16GB", "type": ProductType.GPU, "price": 2949.00, "specifications": {"VRAM": "16 GB", "Długość": "320 mm", "Taktowanie boost": "2970 MHz", "Wentylatory": "3"}, "description": "Pulse XT"},
            {"name": "ASRock Radeon RX 9070 XT Steel Legend Dark 16GB", "type": ProductType.GPU, "price": 2949.00, "specifications": {"VRAM": "16 GB", "Długość": "330 mm", "Taktowanie boost": "3010 MHz", "Wentylatory": "3"}, "description": "Steel Legend XT"},
            {"name": "ASRock Radeon RX 9070 XT Taichi OC 16GB", "type": ProductType.GPU, "price": 3119.00, "specifications": {"VRAM": "16 GB", "Długość": "338 mm", "Taktowanie boost": "3010 MHz", "Wentylatory": "3"}, "description": "Taichi OC XT"},
            {"name": "Sapphire Radeon RX 9070 XT Pure OC 16GB", "type": ProductType.GPU, "price": 3149.00, "specifications": {"VRAM": "16 GB", "Długość": "320 mm", "Taktowanie boost": "3010 MHz", "Wentylatory": "3"}, "description": "Biała Pure XT"},
            {"name": "ASRock B550M-HDV", "type": ProductType.MOTHERBOARD, "price": 329.00, "specifications": {"Gniazdo": "AM4", "Sloty RAM": "2× DDR4", "Wi-Fi": "Nie", "Bluetooth": "Nie", "Chipset": "B550", "Format": "mATX"}, "description": "Budżetowa płyta AM4"},
            {"name": "ASRock B650M-H/M.2+", "type": ProductType.MOTHERBOARD, "price": 449.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "2× DDR5", "Wi-Fi": "Nie", "Bluetooth": "Nie", "Chipset": "B650", "Format": "mATX"}, "description": "Tania płyta AM5"},
            {"name": "ASRock B650M-HDV/M.2", "type": ProductType.MOTHERBOARD, "price": 529.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "2× DDR5", "Wi-Fi": "Nie", "Bluetooth": "Nie", "Chipset": "B650", "Format": "mATX"}, "description": "Solidna sekcja zasilania"},
            {"name": "Gigabyte B650 EAGLE", "type": ProductType.MOTHERBOARD, "price": 649.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Nie", "Bluetooth": "Nie", "Chipset": "B650", "Format": "ATX"}, "description": "Dobry stosunek ceny do jakości"},
            {"name": "ASRock Z790 Pro RS", "type": ProductType.MOTHERBOARD, "price": 899.00, "specifications": {"Gniazdo": "LGA1700", "Sloty RAM": "4× DDR5", "Wi-Fi": "Nie", "Bluetooth": "Nie", "Chipset": "Z790", "Format": "ATX"}, "description": "Solidna płyta pod Intela"},
            {"name": "ASUS B650E MAX GAMING WIFI", "type": ProductType.MOTHERBOARD, "price": 999.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B650E", "Format": "ATX"}, "description": "Dla graczy z WiFi"},
            {"name": "Gigabyte X870 AORUS ELITE WIFI7", "type": ProductType.MOTHERBOARD, "price": 1349.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Wi-Fi 7", "Bluetooth": "Tak", "Chipset": "X870", "Format": "ATX"}, "description": "Topowa płyta AORUS"},
            {"name": "Gigabyte B850 GAMING WF6", "type": ProductType.MOTHERBOARD, "price": 719.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B850", "Format": "ATX"}, "description": "B850 Gaming WF6"},
            {"name": "Gigabyte B850 EAGLE WIFI6E", "type": ProductType.MOTHERBOARD, "price": 739.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B850", "Format": "ATX"}, "description": "B850 Eagle"},
            {"name": "ASUS TUF GAMING B650-PLUS WIFI", "type": ProductType.MOTHERBOARD, "price": 809.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B650", "Format": "ATX"}, "description": "TUF Gaming Plus"},
            {"name": "Gigabyte B850 GAMING X WIFI6E", "type": ProductType.MOTHERBOARD, "price": 829.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B850", "Format": "ATX"}, "description": "B850 Gaming X"},
            {"name": "ASUS ROG STRIX B650-A GAMING WIFI", "type": ProductType.MOTHERBOARD, "price": 849.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B650", "Format": "ATX"}, "description": "ROG Strix B650-A"},
            {"name": "Gigabyte B650E AORUS ELITE X AX ICE", "type": ProductType.MOTHERBOARD, "price": 859.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B650E", "Format": "ATX"}, "description": "AORUS Elite ICE"},
            {"name": "MSI B850 GAMING PLUS WIFI", "type": ProductType.MOTHERBOARD, "price": 879.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B850", "Format": "ATX"}, "description": "B850 Gaming Plus"},
            {"name": "Gigabyte X870 GAMING WF6", "type": ProductType.MOTHERBOARD, "price": 959.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "X870", "Format": "ATX"}, "description": "X870 Gaming"},
            {"name": "MSI B850 GAMING PLUS WIFI PZ", "type": ProductType.MOTHERBOARD, "price": 979.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B850", "Format": "ATX"}, "description": "B850 Gaming PZ"},
            {"name": "Gigabyte B850 A ELITE WF7", "type": ProductType.MOTHERBOARD, "price": 979.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B850", "Format": "ATX"}, "description": "B850 Elite WF7"},
            {"name": "MSI MAG B850 TOMAHAWK MAX WIFI", "type": ProductType.MOTHERBOARD, "price": 1039.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B850", "Format": "ATX"}, "description": "Tomahawk Max"},
            {"name": "Gigabyte X870 GAMING X WIFI7", "type": ProductType.MOTHERBOARD, "price": 1069.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Wi-Fi 7", "Bluetooth": "Tak", "Bluetooth": "Tak", "Chipset": "X870", "Format": "ATX"}, "description": "X870 Gaming X"},
            {"name": "Gigabyte B650 AORUS ELITE AX ICE", "type": ProductType.MOTHERBOARD, "price": 1070.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B650", "Format": "ATX"}, "description": "AORUS Elite ICE"},
            {"name": "Gigabyte X870 AORUS ELITE WIFI7 ICE", "type": ProductType.MOTHERBOARD, "price": 1179.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Wi-Fi 7", "Bluetooth": "Tak", "Chipset": "X870", "Format": "ATX"}, "description": "X870 AORUS ICE"},
            {"name": "Gigabyte X870E A ELITE WIFI7", "type": ProductType.MOTHERBOARD, "price": 1239.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Wi-Fi 7", "Bluetooth": "Tak", "Chipset": "X870E", "Format": "ATX"}, "description": "X870E Elite"},
            {"name": "ASUS ROG STRIX B650E-F GAMING WIFI", "type": ProductType.MOTHERBOARD, "price": 1279.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B650E", "Format": "ATX"}, "description": "ROG Strix B650E-F"},
            {"name": "MSI MAG X870E TOMAHAWK WIFI", "type": ProductType.MOTHERBOARD, "price": 1389.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Wi-Fi 7", "Bluetooth": "Tak", "Chipset": "X870E", "Format": "ATX"}, "description": "X870E Tomahawk"},
            {"name": "ASUS ROG STRIX B650E-E GAMING WIFI", "type": ProductType.MOTHERBOARD, "price": 1399.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "B650E", "Format": "ATX"}, "description": "ROG Strix B650E-E"},
            {"name": "Gigabyte X870E AORUS ELITE X3D", "type": ProductType.MOTHERBOARD, "price": 1499.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Tak", "Bluetooth": "Tak", "Chipset": "X870E", "Format": "ATX"}, "description": "X870E X3D"},
            {"name": "MSI MPG X870E CARBON WIFI", "type": ProductType.MOTHERBOARD, "price": 2169.00, "specifications": {"Gniazdo": "AM5", "Sloty RAM": "4× DDR5", "Wi-Fi": "Wi-Fi 7", "Bluetooth": "Tak", "Chipset": "X870E", "Format": "ATX"}, "description": "X870E Carbon"},
            # --- RAM ---
            {"name": "ADATA 16GB (2x8) 3200 CL16 Gamix D35", "type": ProductType.RAM, "price": 169.00, "specifications": {"Pojemność": "16 GB", "Taktowanie": "3200 MHz", "Opóźnienie": "CL16", "Typ": "DDR4"}, "description": "Dobre DDR4"},
            {"name": "Patriot 32GB (2x16GB) 6000 CL30 Viper Elite 5 RGB", "type": ProductType.RAM, "price": 529.00, "specifications": {"Pojemność": "32 GB", "Taktowanie": "6000 MHz", "Opóźnienie": "CL30", "Typ": "DDR5"}, "description": "Szybkie DDR5 z RGB"},
            {"name": "Patriot 32GB (2x16GB) 6000MT/s CL30 Venom", "type": ProductType.RAM, "price": 519.00, "specifications": {"Pojemność": "32 GB", "Taktowanie": "6000 MHz", "Opóźnienie": "CL30", "Typ": "DDR5"}, "description": "Wydajne pamięci Venom"},
            {"name": "GOODRAM 32GB (2x16GB) 6000 CL36 IRDM BLACK V SILVER", "type": ProductType.RAM, "price": 489.00, "specifications": {"Pojemność": "32 GB", "Taktowanie": "6000 MHz", "Opóźnienie": "CL36", "Typ": "DDR5"}, "description": "Polskie dobre pamięci"},
            {"name": "GOODRAM 32GB (2x16GB) 6400MHz CL32 IRDM BLACK V SILVER", "type": ProductType.RAM, "price": 549.00, "specifications": {"Pojemność": "32 GB", "Taktowanie": "6400 MHz", "Opóźnienie": "CL32", "Typ": "DDR5"}, "description": "Szybsze IRDM"},
            {"name": "Lexar 64GB (2x32GB) 6400 CL32 Ares RGB", "type": ProductType.RAM, "price": 999.00, "specifications": {"Pojemność": "64 GB", "Taktowanie": "6400 MHz", "Opóźnienie": "CL32", "Typ": "DDR5"}, "description": "64GB do pracy"},
            {"name": "GOODRAM 64GB (2x32GB) 6000MHz CL30 IRDM BLACK V SILVER", "type": ProductType.RAM, "price": 949.00, "specifications": {"Pojemność": "64 GB", "Taktowanie": "6000 MHz", "Opóźnienie": "CL30", "Typ": "DDR5"}, "description": "Duża pojemność"},

            # --- Storage ---
            {"name": "MSI 1TB M.2 PCIe Gen4 NVMe Spatium M470 PRO", "type": ProductType.STORAGE, "price": 329.00, "specifications": {"Pojemność": "1 TB", "Interfejs": "PCIe 4.0", "Odczyt": "5000 MB/s", "Zapis": "4400 MB/s"}, "description": "Szybki dysk Gen4"},
            {"name": "ADATA 1TB M.2 PCIe Gen4 NVMe LEGEND 900", "type": ProductType.STORAGE, "price": 299.00, "specifications": {"Pojemność": "1 TB", "Interfejs": "PCIe 4.0", "Odczyt": "7000 MB/s", "Zapis": "5400 MB/s"}, "description": "Bardzo szybki i tani"},
            {"name": "MSI 2TB M.2 PCIe Gen4 NVMe Spatium M470 PRO", "type": ProductType.STORAGE, "price": 599.00, "specifications": {"Pojemność": "2 TB", "Interfejs": "PCIe 4.0", "Odczyt": "5000 MB/s", "Zapis": "4400 MB/s"}, "description": "2TB przestrzeni"},
            {"name": "Lexar 2TB M.2 PCIe Gen4 NVMe NM790", "type": ProductType.STORAGE, "price": 649.00, "specifications": {"Pojemność": "2 TB", "Interfejs": "PCIe 4.0", "Odczyt": "7400 MB/s", "Zapis": "6500 MB/s"}, "description": "Topowa wydajność Gen4"},
            {"name": "Lexar 2TB M.2 PCIe Gen5 NVMe NM990", "type": ProductType.STORAGE, "price": 1299.00, "specifications": {"Pojemność": "2 TB", "Interfejs": "PCIe 5.0", "Odczyt": "10000 MB/s", "Zapis": "9000 MB/s"}, "description": "Ultra szybki Gen5"},

            # --- PSU ---
            {"name": "Deepcool PL550D 550W 80 Plus Bronze", "type": ProductType.PSU, "price": 229.00, "specifications": {"Moc": "550 W", "Certyfikat": "80 Plus Bronze", "Modularny": "Nie"}, "description": "Solidny zasilacz"},
            {"name": "Deepcool PL650D 650W 80 Plus Bronze", "type": ProductType.PSU, "price": 269.00, "specifications": {"Moc": "650 W", "Certyfikat": "80 Plus Bronze", "Modularny": "Nie"}, "description": "Większa moc"},
            {"name": "Deepcool PL800D 800W 80 Plus Bronze", "type": ProductType.PSU, "price": 329.00, "specifications": {"Moc": "800 W", "Certyfikat": "80 Plus Bronze", "Modularny": "Nie"}, "description": "Mocny Bronze"},
            {"name": "Silver Monkey X Okame M2 850W 80 Plus Gold EU", "type": ProductType.PSU, "price": 449.00, "specifications": {"Moc": "850 W", "Certyfikat": "80 Plus Gold", "Modularny": "Tak"}, "description": "Złoty standard"},
            {"name": "ENDORFY Supremo FM6 850W 80 Plus Gold ATX 3.1", "type": ProductType.PSU, "price": 529.00, "specifications": {"Moc": "850 W", "Certyfikat": "80 Plus Gold", "Modularny": "Tak", "Standard": "ATX 3.1"}, "description": "Nowy standard ATX 3.1"},
            {"name": "MSI MPG A850G PCIe5.0 850W 80 Plus Gold", "type": ProductType.PSU, "price": 599.00, "specifications": {"Moc": "850 W", "Certyfikat": "80 Plus Gold", "Modularny": "Tak", "Standard": "ATX 3.0"}, "description": "Gotowy na PCIe 5.0"},
            {"name": "ENDORFY Supremo FM6 1000W 80 Plus Gold ATX 3.1", "type": ProductType.PSU, "price": 699.00, "specifications": {"Moc": "1000 W", "Certyfikat": "80 Plus Gold", "Modularny": "Tak", "Standard": "ATX 3.1"}, "description": "1000W mocy"},

            # --- Cases ---
            {"name": "Silver Monkey X Cassette", "type": ProductType.CASE, "price": 199.00, "specifications": {"Typ": "Midi Tower", "Okno": "Tak", "Wentylatory": "4"}, "description": "Tania i przewiewna"},
            {"name": "Silver Monkey X Coffer", "type": ProductType.CASE, "price": 249.00, "specifications": {"Typ": "Midi Tower", "Okno": "Tak", "Wentylatory": "4"}, "description": "Dobra wentylacja"},
            {"name": "Deepcool CC560 ARGB", "type": ProductType.CASE, "price": 279.00, "specifications": {"Typ": "Midi Tower", "Okno": "Tak", "Wentylatory": "4 ARGB"}, "description": "Podświetlenie ARGB"},
            {"name": "Deepcool CH560", "type": ProductType.CASE, "price": 399.00, "specifications": {"Typ": "Midi Tower", "Okno": "Tak", "Wentylatory": "4"}, "description": "Duża przewiewność"},
            {"name": "Silver Monkey X Pyxis", "type": ProductType.CASE, "price": 349.00, "specifications": {"Typ": "Midi Tower", "Okno": "Tak", "Wentylatory": "4"}, "description": "Nowoczesny design"},
            {"name": "Cougar Uniface RGB Black", "type": ProductType.CASE, "price": 399.00, "specifications": {"Typ": "Midi Tower", "Okno": "Tak", "Wentylatory": "3 RGB"}, "description": "Stylowa obudowa"},
            {"name": "be quiet! Light Base 500 LX Black", "type": ProductType.CASE, "price": 649.00, "specifications": {"Typ": "Midi Tower", "Okno": "Tak", "Wentylatory": "4"}, "description": "Cisza i światło"},
            {"name": "Fractal Design Meshify 3 XL Black RGB", "type": ProductType.CASE, "price": 999.00, "specifications": {"Typ": "Full Tower", "Okno": "Tak", "Wentylatory": "4"}, "description": "Ogromna przestrzeń"},

            # --- Coolers ---
            {"name": "Deepcool AG400 120mm", "type": ProductType.COOLER, "price": 119.00, "specifications": {"Typ": "Powietrzne", "Wentylator": "120mm", "TDP": "200W"}, "description": "Dobre tanie chłodzenie"},
            {"name": "Thermalright Burst Assassin 120 SE Argb", "type": ProductType.COOLER, "price": 139.00, "specifications": {"Typ": "Powietrzne", "Wentylator": "120mm", "TDP": "220W"}, "description": "Wydajne z ARGB"},
            {"name": "SMX Hayate 360", "type": ProductType.COOLER, "price": 399.00, "specifications": {"Typ": "AiO", "Rozmiar": "360mm", "Wentylatory": "3x120mm"}, "description": "Tanie AiO 360"},
            {"name": "Thermalright Peerless Assassin 120 SE", "type": ProductType.COOLER, "price": 189.00, "specifications": {"Typ": "Powietrzne", "Wentylator": "2x120mm", "TDP": "250W"}, "description": "Król opłacalności"},
            {"name": "be quiet! Light Loop 360mm", "type": ProductType.COOLER, "price": 699.00, "specifications": {"Typ": "AiO", "Rozmiar": "360mm", "Wentylatory": "3x120mm"}, "description": "Ciche i wydajne AiO"},
        ]

        # Insert Products
        created_products = {}
        for p_data in products_data:
            # Check if exists
            stmt = select(Product).where(Product.name == p_data["name"])
            result = await db.execute(stmt)
            existing_product = result.scalar_one_or_none()

            if not existing_product:
                product = Product(**p_data)
                db.add(product)
                await db.commit()
                await db.refresh(product)
                created_products[p_data["name"]] = product
            else:
                created_products[p_data["name"]] = existing_product
        
        logger.info(f"Products seeded/verified: {len(created_products)}")

        # --- 2. Define Presets ---
        presets_data = [
            {
                "name": "PRO-KOM START (Ryzen 5 5600GT)",
                "price": 1899.00,
                "components": ["AMD Ryzen 5 5600GT", "ASRock B550M-HDV", "ADATA 16GB (2x8) 3200 CL16 Gamix D35", "MSI 1TB M.2 PCIe Gen4 NVMe Spatium M470 PRO", "Deepcool PL550D 550W 80 Plus Bronze", "Silver Monkey X Cassette"],
                "description": "Idealny wybór na start przygody z gamingiem, oferujący solidną wydajność w przystępnej cenie. Zintegrowany układ graficzny w procesorze Ryzen 5 5600GT pozwala na płynną rozgrywkę w popularne tytuły e-sportowe jak CS:GO czy League of Legends. To doskonała baza do przyszłej rozbudowy o dedykowaną kartę graficzną, gdy Twoje wymagania wzrosną. Jego mocną stroną jest świetny stosunek ceny do możliwości oraz energooszczędność. Jeśli szukasz taniego, ale rozwojowego komputera do nauki i lżejszych gier, ten zestaw jest dla Ciebie.",
                "segment": PresetSegment.GAMING,
                "min_budget": 1500,
                "max_budget": 2200
            },
            {
                "name": "PRO-KOM GAMER ECO (Ryzen 5 3600 + RX 9060 XT)",
                "price": 2899.00,
                "components": ["AMD Ryzen 5 3600", "ASRock B550M-HDV", "ASRock Radeon RX 9060 XT Challenger OC 8GB", "ADATA 16GB (2x8) 3200 CL16 Gamix D35", "MSI 1TB M.2 PCIe Gen4 NVMe Spatium M470 PRO", "Silver Monkey X Cassette", "Deepcool PL550D 550W 80 Plus Bronze"],
                "description": "Ekonomiczna propozycja dla graczy, którzy chcą cieszyć się nowszymi grami bez wydawania fortuny. Połączenie sprawdzonego procesora Ryzen 5 3600 z nowoczesną kartą RX 9060 XT zapewnia płynność w rozdzielczości 1080p. Zestaw ten świetnie sprawdzi się w grach typu Fortnite, GTA V czy Wiedźmin 3 na średnich i wysokich ustawieniach. Minusem może być starsza platforma AM4, jednak nadrabia to bardzo atrakcyjną ceną. Wybierz go, jeśli liczysz każdą złotówkę, ale nie chcesz rezygnować z dedykowanej grafiki.",
                "segment": PresetSegment.GAMING,
                "min_budget": 2500,
                "max_budget": 3200
            },
            {
                "name": "PRO-KOM GAMER (Ryzen 5 7500F + RX 9060 XT)",
                "price": 4199.00,
                "components": ["AMD Ryzen 5 7500F", "ASRock B650M-H/M.2+", "ASRock Radeon RX 9060 XT Challenger OC 8GB", "Patriot 32GB (2x16GB) 6000 CL30 Viper Elite 5 RGB", "ADATA 1TB M.2 PCIe Gen4 NVMe LEGEND 900", "Deepcool PL550D 550W 80 Plus Bronze", "Silver Monkey X Coffer", "Deepcool AG400 120mm"],
                "description": "Nowoczesny zestaw oparty na przyszłościowej platformie AM5, gwarantujący łatwą modernizację w przyszłości. Procesor Ryzen 5 7500F w parze z RX 9060 XT to duet stworzony do komfortowego grania w Full HD. Dzięki szybkiej pamięci DDR5 komputer działa błyskawicznie, zapewniając krótki czas ładowania gier i aplikacji. To idealny balans między wydajnością a ceną dla świadomego gracza. Jeśli szukasz komputera, który posłuży Ci przez lata i pozwoli na łatwy upgrade, to strzał w dziesiątkę.",
                "segment": PresetSegment.GAMING,
                "min_budget": 3500,
                "max_budget": 4200
            },
            {
                "name": "PRO-KOM GAMER PLUS (Ryzen 5 7500F + RX 9060 XT 16GB)",
                "price": 4499.00,
                "components": ["AMD Ryzen 5 7500F", "ASRock B650M-HDV/M.2", "Patriot 32GB (2x16GB) 6000 CL30 Viper Elite 5 RGB", "ASRock Radeon RX 9060 XT Challenger OC 16GB", "Deepcool PL550D 550W 80 Plus Bronze", "ADATA 1TB M.2 PCIe Gen4 NVMe LEGEND 900", "Silver Monkey X Coffer", "Deepcool AG400 120mm"],
                "description": "Ulepszona wersja naszego bestsellera, wyposażona w kartę graficzną z aż 16GB pamięci VRAM. Taka ilość pamięci wideo to klucz do płynnej rozgrywki w nowsze tytuły wymagające dużej ilości tekstur. Zestaw ten poradzi sobie nie tylko z grami, ale także z podstawową obróbką wideo czy grafiką. Jego atutem jest ogromny zapas pamięci karty graficznej, co czyni go bardziej odpornym na upływ czasu. Wybierz ten model, jeśli chcesz grać na wyższych ustawieniach tekstur bez obaw o spadki wydajności.",
                "segment": PresetSegment.GAMING,
                "min_budget": 4200,
                "max_budget": 4600
            },
            {
                "name": "PRO-KOM GAMER RTX (Ryzen 5 7500F + RTX 5060 Ti)",
                "price": 4899.00,
                "components": ["AMD Ryzen 5 7500F", "ASRock B650M-HDV/M.2", "Patriot 32GB (2x16GB) 6000 CL30 Viper Elite 5 RGB", "KFA2 GeForce RTX 5060 Ti 1-Click OC 16GB", "Deepcool PL550D 550W 80 Plus Bronze", "Deepcool CC560 ARGB", "ADATA 1TB M.2 PCIe Gen4 NVMe LEGEND 900", "Deepcool AG400 120mm"],
                "description": "Wejście w świat Ray Tracingu i technologii DLSS dzięki karcie GeForce RTX 5060 Ti. Ten zestaw to idealna propozycja dla osób ceniących piękną grafikę i realistyczne oświetlenie w grach. Procesor Ryzen 5 7500F zapewnia, że karta graficzna będzie pracować na pełnych obrotach w każdej grze. To doskonały wybór do monitorów 1080p o wysokim odświeżaniu, gwarantujący przewagę w grach sieciowych. Jeśli zależy Ci na technologiach NVIDIA i streamowaniu rozgrywki, ten PC Cię nie zawiedzie.",
                "segment": PresetSegment.GAMING,
                "min_budget": 4600,
                "max_budget": 5000
            },
            {
                "name": "PRO-KOM ELITE (Ryzen 5 7500F + RTX 5070)",
                "price": 5299.00,
                "components": ["AMD Ryzen 5 7500F", "ASRock B650M-HDV/M.2", "Patriot 32GB (2x16GB) 6000 CL30 Viper Elite 5 RGB", "Zotac GeForce RTX 5070 Twin Edge 12GB", "Deepcool PL650D 650W 80 Plus Bronze", "Deepcool CC560 ARGB", "ADATA 1TB M.2 PCIe Gen4 NVMe LEGEND 900", "Deepcool AG400 120mm"],
                "description": "Przepustka do gamingu w rozdzielczości 1440p dzięki potężnej karcie RTX 5070. Zestaw ten oferuje bezkompromisową wydajność w najnowszych grach AAA, zapewniając stabilne klatki na sekundę. Dzięki nowoczesnej architekturze i szybkim podzespołom, praca i zabawa na tym komputerze to czysta przyjemność. Jego siłą jest uniwersalność – świetnie sprawdzi się zarówno w grach, jak i w pracy twórczej. Jeśli oczekujesz wysokiej jakości obrazu i płynności bez kompromisów, to wybór dla Ciebie.",
                "segment": PresetSegment.GAMING,
                "min_budget": 5000,
                "max_budget": 5500
            },
            {
                "name": "PRO-KOM ELITE RED (Ryzen 5 7500F + RX 9070 XT)",
                "price": 5799.00,
                "components": ["AMD Ryzen 5 7500F", "Gigabyte B650 EAGLE", "Patriot 32GB (2x16GB) 6000MT/s CL30 Venom", "Gigabyte Radeon RX 9070 XT Gaming OC 16GB", "Deepcool PL800D 800W 80 Plus Bronze", "ADATA 1TB M.2 PCIe Gen4 NVMe LEGEND 900", "Deepcool CC560 ARGB", "Thermalright Burst Assassin 120 SE Argb"],
                "description": "Alternatywa dla fanów \"Czerwonych\", oferująca potężną moc obliczeniową w grach rasteryzowanych. Karta RX 9070 XT to bestia wydajności, która w wielu tytułach wyprzedza konkurencję w swoim przedziale cenowym. Zestaw ten jest idealny dla graczy, którzy stawiają na czystą moc i wysoki framerate w rozdzielczości 1440p. Dzięki dużej ilości pamięci VRAM, komputer jest gotowy na nadchodzące, wymagające gry. Wybierz go, jeśli szukasz maksymalnej wydajności w klasycznym renderingu.",
                "segment": PresetSegment.GAMING,
                "min_budget": 5500,
                "max_budget": 6000
            },
            {
                "name": "PRO-KOM MASTER (i5-14600K + RX 9070 XT)",
                "price": 6899.00,
                "components": ["Intel Core i5-14600KF", "ASRock Z790 Pro RS", "GOODRAM 32GB (2x16GB) 6000 CL36 IRDM BLACK V SILVER", "ASRock Radeon RX 9070 XT Steel Legend Dark 16GB", "Silver Monkey X Okame M2 850W 80 Plus Gold EU", "MSI 1TB M.2 PCIe Gen4 NVMe Spatium M470 PRO", "SMX Hayate 360", "Deepcool CH560"],
                "description": "Profesjonalna maszyna łącząca wydajność procesora Intel Core i5-14600K z mocą karty RX 9070 XT. To zestaw stworzony nie tylko do gier, ale także do zaawansowanej pracy, takiej jak montaż wideo czy rendering 3D. Hybrydowa architektura procesora Intel zapewnia świetną wielozadaniowość i responsywność systemu. Jest to idealne rozwiązanie dla twórców treści, którzy po godzinach chcą zrelaksować się przy ulubionych grach w wysokich detalach. Jeśli potrzebujesz komputera do pracy i rozrywki na najwyższym poziomie, ten model spełni Twoje oczekiwania.",
                "segment": PresetSegment.PRO,
                "min_budget": 6500,
                "max_budget": 7000
            },
            {
                "name": "PRO-KOM MASTER NEXT (Ryzen 5 9600X + RTX 5070 Ti)",
                "price": 7199.00,
                "components": ["AMD Ryzen 5 9600X", "ASUS B650E MAX GAMING WIFI", "GOODRAM 32GB (2x16GB) 6000 CL36 IRDM BLACK V SILVER", "INNO3D GeForce RTX 5070 Ti X3 16GB", "Silver Monkey X Okame M2 850W 80 Plus Gold EU", "MSI 1TB M.2 PCIe Gen4 NVMe Spatium M470 PRO", "Thermalright Peerless Assassin 120 SE", "Silver Monkey X Pyxis"],
                "description": "Zestaw nowej generacji z procesorem Ryzen 5 9600X, oferujący najnowocześniejsze technologie na rynku. Karta RTX 5070 Ti zapewnia niesamowitą wydajność w Ray Tracingu, czyniąc gry niemal fotorealistycznymi. To komputer dla entuzjastów, którzy chcą być na bieżąco z nowinkami technologicznymi i oczekują najwyższej kultury pracy. Jego zaletą jest niezwykle nowoczesna platforma, gotowa na przyszłe wyzwania. Wybierz go, jeśli chcesz mieć pewność, że Twój PC poradzi sobie z każdą grą przez długi czas.",
                "segment": PresetSegment.GAMING,
                "min_budget": 7000,
                "max_budget": 7500
            },
            {
                "name": "PRO-KOM X3D LEGEND (Ryzen 7 7800X3D + RTX 5070 Ti)",
                "price": 8299.00,
                "components": ["AMD Ryzen 7 7800X3D", "ASUS B650E MAX GAMING WIFI", "GOODRAM 32GB (2x16GB) 6000 CL36 IRDM BLACK V SILVER", "ASUS GeForce RTX 5070 Ti Prime OC 16GB", "Cougar Uniface RGB Black", "ENDORFY Supremo FM6 850W 80 Plus Gold ATX 3.1", "MSI 2TB M.2 PCIe Gen4 NVMe Spatium M470 PRO", "Thermalright Peerless Assassin 120 SE"],
                "description": "Marzenie każdego gracza – zestaw z najlepszym procesorem gamingowym na świecie, Ryzen 7 7800X3D. Technologia 3D V-Cache zapewnia niespotykaną płynność i minimalne opóźnienia w grach symulacyjnych i strategiach. W połączeniu z RTX 5070 Ti otrzymujesz maszynę, która nie klęka przed żadnym tytułem. To absolutny top dla wymagających graczy, dla których liczy się każda klatka na sekundę. Jeśli gaming to Twoja pasja i nie uznajesz półśrodków, ten zestaw jest stworzony dla Ciebie.",
                "segment": PresetSegment.GAMING,
                "min_budget": 8000,
                "max_budget": 8800
            },
            {
                "name": "PRO-KOM ULTRA (Ryzen 7 9800X3D + RTX 5080)",
                "price": 9599.00,
                "components": ["AMD Ryzen 7 9800X3D", "Gigabyte B850 GAMING X WIFI6E", "GOODRAM 32GB (2x16GB) 6400MHz CL32 IRDM BLACK V SILVER", "Zotac GeForce RTX 5080 Solid Core OC 16GB", "Cougar Uniface RGB Black", "MSI MPG A850G PCIe5.0 850W 80 Plus Gold", "Lexar 2TB M.2 PCIe Gen4 NVMe NM790", "SMX Hayate 360"],
                "description": "Potężna bestia z procesorem Ryzen 7 9800X3D i kartą RTX 5080, stworzona do grania w 4K. Ten komputer to definicja wydajności, oferująca zapas mocy na lata do przodu. Dzięki topowym podzespołom, każda gra wygląda i działa obłędnie, a praca z wymagającymi aplikacjami jest błyskawiczna. To wybór dla osób, które chcą doświadczyć gamingu w najlepszej możliwej jakości bez żadnych przycięć. Jeśli Twój budżet pozwala na to, co najlepsze, PRO-KOM ULTRA jest odpowiedzią na Twoje potrzeby.",
                "segment": PresetSegment.GAMING,
                "min_budget": 9000,
                "max_budget": 10000
            },
            {
                "name": "PRO-KOM ULTRA MAX (Ryzen 7 9800X3D + RTX 5080 + 64GB)",
                "price": 10699.00,
                "components": ["AMD Ryzen 7 9800X3D", "Gigabyte B850 GAMING X WIFI6E", "Lexar 64GB (2x32GB) 6400 CL32 Ares RGB", "Zotac GeForce RTX 5080 Solid Core OC 16GB", "SMX Hayate 360", "ENDORFY Supremo FM6 850W 80 Plus Gold ATX 3.1", "Lexar 2TB M.2 PCIe Gen4 NVMe NM790", "be quiet! Light Base 500 LX Black"],
                "description": "Ulepszona wersja modelu ULTRA, wzbogacona o 64GB pamięci RAM i jeszcze lepszą obudowę. To stacja robocza i gamingowa w jednym, która poradzi sobie z najbardziej wymagających zadaniami profesjonalnymi. Ogromna ilość pamięci operacyjnej pozwala na swobodną pracę z wieloma aplikacjami jednocześnie i edycję materiałów w wysokiej rozdzielczości. Jest to komputer bez słabych punktów, zaprojektowany dla najbardziej wymagających użytkowników. Wybierz go, jeśli potrzebujesz bezkompromisowej maszyny do wszystkiego.",
                "segment": PresetSegment.GAMING,
                "min_budget": 10000,
                "max_budget": 11000
            },
            {
                "name": "PRO-KOM GODLIKE (Ryzen 9 9950X3D + RTX 5090)",
                "price": 21099.00,
                "components": ["AMD Ryzen 9 9950X3D", "Gigabyte X870 AORUS ELITE WIFI7", "GOODRAM 64GB (2x32GB) 6000MHz CL30 IRDM BLACK V SILVER", "Gigabyte GeForce RTX 5090 AORUS Master 32GB", "Fractal Design Meshify 3 XL Black RGB", "ENDORFY Supremo FM6 1000W 80 Plus Gold ATX 3.1", "Lexar 2TB M.2 PCIe Gen5 NVMe NM990", "be quiet! Light Loop 360mm"],
                "description": "Absolutny szczyt techniki, wyposażony w najmocniejsze podzespoły dostępne na rynku konsumenckim. Ryzen 9 9950X3D i RTX 5090 to duet, który wyznacza nowe standardy wydajności, miażdżąc każdy benchmark. Ten komputer to demonstracja siły, przeznaczona dla entuzjastów, którzy muszą mieć to, co absolutnie najlepsze. Zapewnia niewyobrażalną płynność w 4K, a nawet 8K, oraz błyskawiczną pracę w profesjonalnych zastosowaniach. Jeśli cena nie gra roli, a liczy się tylko perfekcja, PRO-KOM GODLIKE jest jedynym słusznym wyborem.",
                "segment": PresetSegment.PRO,
                "min_budget": 18000,
                "max_budget": 25000
            }
        ]

        # Insert Presets
        for p_data in presets_data:
            # Check if exists
            stmt = select(Preset).where(Preset.name == p_data["name"])
            result = await db.execute(stmt)
            existing_preset = result.scalar_one_or_none()

            if not existing_preset:
                # Map components to products
                component_map = {}
                products_list = []
                
                for comp_name in p_data["components"]:
                    product = created_products.get(comp_name)
                    if product:
                        products_list.append(product)
                        # Simple mapping logic
                        if product.type == ProductType.CPU:
                            component_map["cpu"] = str(product.id)
                        elif product.type == ProductType.GPU:
                            component_map["gpu"] = str(product.id)
                        elif product.type == ProductType.MOTHERBOARD:
                            component_map["motherboard"] = str(product.id)
                        elif product.type == ProductType.RAM:
                            component_map["ram"] = str(product.id)
                        elif product.type == ProductType.STORAGE:
                            component_map["storage"] = str(product.id)
                        elif product.type == ProductType.PSU:
                            component_map["psu"] = str(product.id)
                        elif product.type == ProductType.CASE:
                            component_map["case"] = str(product.id)
                        elif product.type == ProductType.COOLER:
                            component_map["cooler"] = str(product.id)
                        elif product.type == ProductType.LAPTOP:
                            component_map["laptop"] = str(product.id)

                # Calculate performance score based on components
                performance_score = calculate_performance_score(products_list, p_data["segment"])
                
                # Get case image URL
                image_url = get_case_image_url(p_data["components"])
                
                preset = Preset(
                    name=p_data["name"],
                    description=p_data["description"],
                    device_type=p_data.get("device_type", DeviceType.PC),
                    segment=p_data["segment"],
                    min_budget=p_data["min_budget"],
                    max_budget=p_data["max_budget"],
                    total_price=p_data["price"],
                    component_map=component_map,
                    performance_score=performance_score,
                    image_url=image_url
                )
                db.add(preset)
                await db.commit()
                await db.refresh(preset, attribute_names=["products"])
                
                # Add relationships
                for product in products_list:
                    preset.products.append(product)
                
                await db.commit()
                logger.info(f"Created preset: {preset.name}")
            else:
                logger.info(f"Preset already exists: {p_data['name']}")

if __name__ == "__main__":
    asyncio.run(seed_techlipton_data())
