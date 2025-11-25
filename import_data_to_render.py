"""
Script to import data from local SQLite database to Render PostgreSQL via API.
This will copy all products and presets from your local database to production.
"""

import sqlite3
import requests
import json
from typing import List, Dict, Any
import time

# Configuration
RENDER_API_URL = "https://smartpc-builder-backend.onrender.com/api/v1"
LOCAL_DB_PATH = "smartpc.db"

def get_local_products() -> List[Dict[str, Any]]:
    """Extract all products from local SQLite database."""
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM products")
    products = []
    
    for row in cursor.fetchall():
        product = {
            "name": row["name"],
            "type": row["type"].lower(),  # Convert to lowercase (CPU -> cpu)
            "price": row["price"],
            "specifications": json.loads(row["specifications"]) if row["specifications"] else {},
            "image_url": row["image_url"],
            "brand": row["brand"],
            "model": row["model"],
            "in_stock": bool(row["in_stock"]),
        }
        products.append(product)
    
    conn.close()
    print(f"✓ Found {len(products)} products in local database")
    return products


def get_local_presets() -> List[Dict[str, Any]]:
    """Extract all presets from local SQLite database."""
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all presets
    cursor.execute("SELECT * FROM presets")
    presets = []
    
    for row in cursor.fetchall():
        # Get products for this preset
        cursor.execute("""
            SELECT p.id, p.name, p.type, p.price 
            FROM products p
            JOIN preset_products pp ON p.id = pp.product_id
            WHERE pp.preset_id = ?
        """, (row["id"],))
        
        products = []
        for prod_row in cursor.fetchall():
            products.append({
                "id": prod_row["id"],
                "name": prod_row["name"],
                "type": prod_row["type"],
                "price": prod_row["price"],
            })
        
        preset = {
            "name": row["name"],
            "description": row["description"],
            "device_type": row["device_type"].lower(),  # PC -> pc
            "segment": row["segment"].lower(),  # PRO -> pro
            "total_price": row["total_price"],
            "min_budget": row["min_budget"] if row["min_budget"] else None,
            "max_budget": row["max_budget"] if row["max_budget"] else None,
            "image_url": row["image_url"],
            "product_ids": [p["id"] for p in products],
        }
        presets.append(preset)
    
    conn.close()
    print(f"✓ Found {len(presets)} presets in local database")
    return presets


def upload_products(products: List[Dict[str, Any]]) -> Dict[str, str]:
    """Upload products to Render API and return mapping of old IDs to new UUIDs."""
    print(f"\n📤 Uploading {len(products)} products to Render...")
    id_mapping = {}
    
    for i, product in enumerate(products, 1):
        try:
            response = requests.post(
                f"{RENDER_API_URL}/products",
                json=product,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 201:
                new_product = response.json()
                print(f"  ✓ [{i}/{len(products)}] {product['name']}")
                # We'll need to map old product names to new IDs for presets
                id_mapping[product['name']] = new_product['id']
            else:
                print(f"  ✗ [{i}/{len(products)}] {product['name']} - Error: {response.status_code}")
                print(f"    Response: {response.text}")
            
            time.sleep(0.2)  # Rate limiting
            
        except Exception as e:
            print(f"  ✗ [{i}/{len(products)}] {product['name']} - Exception: {e}")
    
    print(f"✓ Uploaded {len(id_mapping)} products successfully")
    return id_mapping


def get_remote_products() -> Dict[str, str]:
    """Get all products from Render API and return name -> ID mapping."""
    try:
        response = requests.get(f"{RENDER_API_URL}/products?limit=1000", timeout=30)
        if response.status_code == 200:
            products = response.json()
            return {p['name']: p['id'] for p in products}
        else:
            print(f"Warning: Could not fetch remote products: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Warning: Exception fetching remote products: {e}")
        return {}


def upload_presets(presets: List[Dict[str, Any]], product_mapping: Dict[str, str]):
    """Upload presets to Render API using product name mapping."""
    print(f"\n📤 Uploading {len(presets)} presets to Render...")
    
    # Get current products from Render to build mapping
    remote_products = get_remote_products()
    
    for i, preset in enumerate(presets, 1):
        try:
            # Map local product IDs to remote UUIDs by name
            # First, get product names from local DB
            conn = sqlite3.connect(LOCAL_DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(preset['product_ids']))
            cursor.execute(f"SELECT name FROM products WHERE id IN ({placeholders})", preset['product_ids'])
            product_names = [row['name'] for row in cursor.fetchall()]
            conn.close()
            
            # Map to remote UUIDs
            remote_product_ids = []
            for name in product_names:
                if name in remote_products:
                    remote_product_ids.append(remote_products[name])
                else:
                    print(f"  ⚠ Warning: Product '{name}' not found in remote database")
            
            # Update preset with remote product IDs
            preset_data = preset.copy()
            preset_data['product_ids'] = remote_product_ids
            
            response = requests.post(
                f"{RENDER_API_URL}/presets",
                json=preset_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 201:
                print(f"  ✓ [{i}/{len(presets)}] {preset['name']}")
            else:
                print(f"  ✗ [{i}/{len(presets)}] {preset['name']} - Error: {response.status_code}")
                print(f"    Response: {response.text}")
            
            time.sleep(0.2)  # Rate limiting
            
        except Exception as e:
            print(f"  ✗ [{i}/{len(presets)}] {preset['name']} - Exception: {e}")
    
    print(f"✓ Preset upload complete")


def main():
    """Main import function."""
    print("=" * 60)
    print("SmartPC Builder - Data Import to Render")
    print("=" * 60)
    
    # Check if local database exists
    try:
        conn = sqlite3.connect(LOCAL_DB_PATH)
        conn.close()
    except Exception as e:
        print(f"❌ Error: Could not connect to local database '{LOCAL_DB_PATH}'")
        print(f"   Make sure the database file exists in the current directory.")
        return
    
    # Check if Render API is accessible
    try:
        response = requests.get(f"{RENDER_API_URL}/health", timeout=10)
        if response.status_code != 200:
            print(f"❌ Error: Render API is not accessible (status: {response.status_code})")
            return
        print("✓ Render API is accessible")
    except Exception as e:
        print(f"❌ Error: Could not connect to Render API: {e}")
        return
    
    # Extract data from local database
    print("\n📚 Reading local database...")
    products = get_local_products()
    presets = get_local_presets()
    
    if not products:
        print("⚠ Warning: No products found in local database")
        return
    
    # Confirm before uploading
    print(f"\n📊 Summary:")
    print(f"   - Products to upload: {len(products)}")
    print(f"   - Presets to upload: {len(presets)}")
    print(f"   - Target: {RENDER_API_URL}")
    
    confirm = input("\n❓ Continue with import? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("❌ Import cancelled")
        return
    
    # Upload products
    product_mapping = upload_products(products)
    
    # Upload presets if we have them
    if presets and product_mapping:
        upload_presets(presets, product_mapping)
    
    print("\n" + "=" * 60)
    print("✅ Import complete!")
    print("=" * 60)
    print(f"\nCheck your frontend: https://smartpc-builder-frontend-4tyo.vercel.app")


if __name__ == "__main__":
    main()
