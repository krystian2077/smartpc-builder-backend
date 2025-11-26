"""
Script to delete all presets from Render.
Use this before re-importing presets with correct data.
"""

import requests
import time

# Configuration
RENDER_API_URL = "https://smartpc-builder-backend.onrender.com/api/v1"


def get_all_presets():
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
        response = requests.delete(
            f"{RENDER_API_URL}/presets/{preset_id}",
            timeout=30
        )
        
        if response.status_code in [200, 204]:
            print(f"  ✓ Deleted: {preset_name}")
            return True
        else:
            print(f"  ✗ Failed: {preset_name} - Status: {response.status_code}")
            print(f"    Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"  ✗ Exception for {preset_name}: {e}")
        return False


def main():
    """Main deletion function."""
    print("=" * 60)
    print("SmartPC Builder - Delete All Presets from Render")
    print("=" * 60)
    print("\n⚠️  WARNING: This will DELETE ALL presets from production!")
    
    # Confirm
    confirm = input("\n❓ Are you sure you want to continue? (yes/no): ")
    if confirm.lower() not in ['yes', 'y']:
        print("❌ Deletion cancelled")
        return
    
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
    
    # Get all presets
    print("\n🌐 Fetching presets from Render...")
    presets = get_all_presets()
    
    if not presets:
        print("⚠ No presets found - nothing to delete")
        return
    
    # Delete all presets
    print(f"\n🗑️  Deleting {len(presets)} presets...")
    deleted = 0
    
    for preset in presets:
        preset_name = preset.get("name", "Unknown")
        preset_id = preset.get("id")
        
        if delete_preset(preset_id, preset_name):
            deleted += 1
            time.sleep(0.2)  # Rate limiting
    
    print("\n" + "=" * 60)
    print("✅ Deletion complete!")
    print("=" * 60)
    print(f"\n📊 Summary:")
    print(f"   - Deleted: {deleted}/{len(presets)}")
    print(f"\n▶️  Next step: Run 'python import_data_to_render.py' to re-import with correct data")


if __name__ == "__main__":
    main()
