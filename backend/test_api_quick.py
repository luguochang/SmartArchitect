"""Quick API test"""
import requests
import json

# Test health endpoint first
try:
    response = requests.get("http://localhost:8000/api/health", timeout=5)
    print(f"Health check: {response.status_code}")
    if response.ok:
        print(f"Response: {response.json()}")
except Exception as e:
    print(f"Backend not running or health endpoint failed: {e}")
    print("\nPlease start backend first:")
    print("  cd backend && python -m app.main")
    exit(1)

# Test Excalidraw generation
print("\n" + "=" * 80)
print("Testing Excalidraw generation endpoint...")
print("=" * 80)

payload = {
    "prompt": "simple login workflow",
    "style": "balanced",
    "width": 1200,
    "height": 800,
    "provider": "siliconflow",
    "api_key": None  # Will use fallback
}

try:
    response = requests.post(
        "http://localhost:8000/api/excalidraw/generate",
        json=payload,
        timeout=30
    )
    print(f"Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Message: {data.get('message', 'N/A')[:100]}")
        print(f"Elements: {len(data.get('scene', {}).get('elements', []))}")
    else:
        print(f"Error response: {response.text[:500]}")
except Exception as e:
    print(f"Request failed: {type(e).__name__}: {e}")
