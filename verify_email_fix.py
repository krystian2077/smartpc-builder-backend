import asyncio

from app.core.database import AsyncSessionLocal
from app.models.preset import Preset
from sqlalchemy import select

async def verify_fix():
    # 1. Get a preset ID
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Preset).limit(1))
        preset = result.scalar_one_or_none()
        if not preset:
            print("No presets found!")
            return
        preset_id = str(preset.id)
        preset_name = preset.name
        print(f"Using preset: {preset_name} ({preset_id})")

    # 2. Send inquiry request
    import urllib.request
    import json

    url = "http://localhost:8000/api/v1/inquiries"
    payload = {
        "first_name": "Test",
        "last_name": "User",
        "email": "test@example.com",
        "phone": "123456789",
        "inquiry_type": "quote_request",
        "source": "contact_page",
        "message": "Testing preset inquiry fix",
        "consent_contact": True,
        "consent_rodo": True,
        "configuration_data": {
            "preset_id": preset_id,
            "preset_name": preset_name
        }
    }

    try:
        req = urllib.request.Request(url)
        req.add_header('Content-Type', 'application/json')
        jsondata = json.dumps(payload).encode('utf-8')
        req.add_header('Content-Length', len(jsondata))
        
        response = urllib.request.urlopen(req, jsondata)
        status_code = response.getcode()
        response_body = response.read().decode('utf-8')
        data = json.loads(response_body)
        
        print(f"Status Code: {status_code}")
        # print(f"Response: {data}")
        
        if status_code == 201:
            # Check if configuration_data in response is enriched
            config_data = data.get("configuration_data", {})
            if "components" in config_data and len(config_data["components"]) > 0:
                print("SUCCESS: Configuration data enriched with components!")
                print(f"Components found: {len(config_data['components'])}")
                print(f"Total Price: {config_data.get('totalPrice')}")
            else:
                print("FAILURE: Configuration data NOT enriched.")
        else:
            print("Request failed.")
            
    except Exception as e:
        print(f"Error sending request: {e}")

if __name__ == "__main__":
    asyncio.run(verify_fix())
