"""
Quick script to delete and re-import only presets (products remain unchanged).
Much faster than full import.
"""

import sqlite3
import requests
import json
from typing import List, Dict, Any
import time

# Configuration
RENDER_API_URL = "https://smartpc-builder-backend.onrender.com/api/v1"
LOCAL_DB_PATH = "smartpc.db"


def get_local_presets() -> List[Dict[str, Any]]:
    """Extract all presets from local SQLite database."""
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
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
            "device_type": row["device_type"].lower(),
            "segment": row["segment"].lower(),
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


def get_all_presets_from_render():
    """Fetch all presets from Render API."""
    try:
        response = requests.get(f"{RENDER_API_URL}/presets?limit=100", timeout=30)
        if response.status_code == 200:
            presets = response.json()
            print(f"✓ Found {len(presets)} presets on Render")
            return presets
        else:
            print(f"✗ Error fetching presets: {response.status_code}")
            return []
    except Exception as e:
        print(f"✗ Exception: {e}")
        return []


def delete_preset(preset_id: str, preset_name: str) -> bool:
    """Delete a preset from Render."""
    try:
        response = requests.delete(f"{RENDER_API_URL}/presets/{preset_id}", timeout=30)
        
        if response.status_code in [200, 204]:
            return True
        else:
            print(f"  ✗ Failed to delete {preset_name}: {response.status_code}")
            return False
    except Exception as e:
        print(f"  ✗ Exception for {preset_name}: {e}")
        return False


def get_remote_products() -> Dict[str, str]:
    """Get all products from Render API and return name -> ID mapping."""
    try:
        response = requests.get(f"{RENDER_API_URL}/products?limit=1000", timeout=30)
        if response.status_code == 200:
            products = response.json()
            print(f"✓ Found {len(products)} products on Render for mapping")
            return {p['name']: p['id'] for p in products}
        else:
            print(f"Warning: Could not fetch remote products: {response.status_code}")
            return {}
    except Exception as e:
        print(f"Warning: Exception fetching remote products: {e}")
        return {}


def upload_presets(presets: List[Dict[str, Any]]):
    """Upload presets to Render API using product name mapping."""
    print(f"\n📤 Uploading {len(presets)} presets to Render...")
    
    # Get current products from Render to build mapping
    remote_products = get_remote_products()
    
    if not remote_products:
        print("❌ Error: Could not fetch products from Render. Cannot proceed.")
        return
    
    success_count = 0
    
    for i, preset in enumerate(presets, 1):
        try:
            # Map local product IDs to remote UUIDs by name and type
            conn = sqlite3.connect(LOCAL_DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(preset['product_ids']))
            cursor.execute(f"SELECT name, type FROM products WHERE id IN ({placeholders})", preset['product_ids'])
            products_data = [(row['name'], row['type']) for row in cursor.fetchall()]
            conn.close()
            
            # Build component_map: {type: product_uuid}
            component_map = {}
            for name, product_type in products_data:
                if name in remote_products:
                    component_map[product_type.upper()] = remote_products[name]
                else:
                    print(f"  ⚠ Warning: Product '{name}' not found in remote database")
            
            # Update preset with component_map and remove product_ids
            preset_data = preset.copy()
            del preset_data['product_ids']
            preset_data['component_map'] = component_map
            
            response = requests.post(
                f"{RENDER_API_URL}/presets",
                json=preset_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 201:
                print(f"  ✓ [{i}/{len(presets)}] {preset['name']}")
                success_count += 1
            else:
                print(f"  ✗ [{i}/{len(presets)}] {preset['name']} - Error: {response.status_code}")
                print(f"    Response: {response.text}")
            
            time.sleep(0.2)
            
        except Exception as e:
            print(f"  ✗ [{i}/{len(presets)}] {preset['name']} - Exception: {e}")
    
    print(f"✓ Uploaded {success_count}/{len(presets)} presets successfully")


def main():
    """Main function."""
    print("=" * 60)
    print("SmartPC Builder - Reimport Presets Only")
    print("=" * 60)
    print("\nThis will delete all presets and re-import them from local DB.")
    print("Products will NOT be touched.\n")
    
    # Check Render API
    try:
        response = requests.get(f"{RENDER_API_URL}/health", timeout=10)
        if response.status_code != 200:
            print(f"❌ Error: Render API is not accessible")
            return
        print("✓ Render API is accessible")
    except Exception as e:
        print(f"❌ Error: Could not connect to Render API: {e}")
        return
    
    # Confirm
    confirm = input("\n❓ Continue? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("❌ Cancelled")
        return
    
    # Step 1: Delete all presets
    print("\n🗑️  Step 1: Deleting all presets from Render...")
    presets_to_delete = get_all_presets_from_render()
    deleted = 0
    
    for preset in presets_to_delete:
        if delete_preset(preset['id'], preset['name']):
            deleted += 1
            print(f"  ✓ Deleted: {preset['name']}")
        time.sleep(0.2)
    
    print(f"✓ Deleted {deleted} presets")
    
    # Step 2: Read local presets
    print("\n📚 Step 2: Reading local database...")
    local_presets = get_local_presets()
    
    if not local_presets:
        print("⚠ Warning: No presets found in local database")
        return
    
    # Step 3: Upload presets
    print("\n📤 Step 3: Uploading presets...")
    upload_presets(local_presets)
    
    print("\n" + "=" * 60)
    print("✅ Reimport complete!")
    print("=" * 60)
    print(f"\n🌐 Check: https://smartpc-builder-frontend-4tyo.vercel.app")


if __name__ == "__main__":
    main()
