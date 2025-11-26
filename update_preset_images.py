"""
Script to update preset image URLs on Render from local database.
"""

import sqlite3
import requests
import json
from typing import Dict

# Configuration
RENDER_API_URL = "https://smartpc-builder-backend.onrender.com/api/v1"
LOCAL_DB_PATH = "smartpc.db"


def get_local_image_mapping() -> Dict[str, str]:
    """Get mapping of preset names to image URLs from local database."""
    conn = sqlite3.connect(LOCAL_DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT name, image_url FROM presets")
    mapping = {}
    
    for row in cursor.fetchall():
        mapping[row["name"]] = row["image_url"]
    
    conn.close()
    print(f"✓ Found {len(mapping)} presets in local database")
    return mapping


def get_render_presets():
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


def update_preset_image(preset_id: str, image_url: str, preset_name: str) -> bool:
    """Update a preset's image_url on Render."""
    try:
        # Use PATCH to update only the image_url field
        response = requests.patch(
            f"{RENDER_API_URL}/presets/{preset_id}",
            json={"image_url": image_url},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"  ✓ Updated: {preset_name}")
            return True
        else:
            print(f"  ✗ Failed: {preset_name} - Status: {response.status_code}")
            print(f"    Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ✗ Exception for {preset_name}: {e}")
        return False


def main():
    """Main update function."""
    print("=" * 60)
    print("SmartPC Builder - Update Preset Images on Render")
    print("=" * 60)
    
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
    
    # Get local image mapping
    print("\n📚 Reading local database...")
    local_images = get_local_image_mapping()
    
    if not local_images:
        print("⚠ Warning: No presets found in local database")
        return
    
    # Get Render presets
    print("\n🌐 Fetching presets from Render...")
    render_presets = get_render_presets()
    
    if not render_presets:
        print("⚠ Warning: No presets found on Render")
        return
    
    # Update presets
    print(f"\n📤 Updating {len(render_presets)} presets...")
    updated = 0
    skipped = 0
    
    for preset in render_presets:
        preset_name = preset.get("name")
        preset_id = preset.get("id")
        current_image = preset.get("image_url")
        
        if preset_name in local_images:
            new_image = local_images[preset_name]
            
            # Skip if already correct
            if current_image == new_image:
                print(f"  ⊙ Skipped: {preset_name} (already correct)")
                skipped += 1
                continue
            
            # Update
            if update_preset_image(preset_id, new_image, preset_name):
                updated += 1
        else:
            print(f"  ⚠ Warning: '{preset_name}' not found in local database")
    
    print("\n" + "=" * 60)
    print("✅ Update complete!")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   - Updated: {updated}")
    print(f"   - Skipped: {skipped}")
    print(f"   - Total: {len(render_presets)}")
    print(f"\n🌐 Check: https://smartpc-builder-frontend-4tyo.vercel.app")


if __name__ == "__main__":
    main()
