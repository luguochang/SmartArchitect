"""Test JSON repair logic"""
import json
import sys
sys.path.insert(0, 'D:\\file\\openproject\\SmartArchitect\\backend')

from app.services.excalidraw_generator import create_excalidraw_service

# Test case: JSON with missing comma
broken_json = '''{
  "elements": [
    {"id": "1", "type": "rectangle", "x": 100, "y": 100}
    {"id": "2", "type": "ellipse", "x": 200, "y": 200}
  ],
  "appState": {},
  "files": {}
}'''

print("Testing JSON repair logic...")
print("=" * 80)

service = create_excalidraw_service()

# Test _safe_json method
result = service._safe_json(broken_json)

if result and isinstance(result, dict):
    print("[SUCCESS] Repair worked!")
    print(f"  Parsed elements: {len(result.get('elements', []))}")
    print(f"  Result keys: {list(result.keys())}")
else:
    print("[FAILED] Repair failed")
    print(f"  Result: {result}")

# Test with actual markdown fence
broken_json_with_fence = '''```json
{
  "elements": [
    {"id": "1", "type": "rectangle", "x": 100, "y": 100}
    {"id": "2", "type": "ellipse", "x": 200, "y": 200}
  ],
  "appState": {},
  "files": {}
}
```'''

print("\n" + "=" * 80)
print("Testing with markdown fence...")
result2 = service._safe_json(broken_json_with_fence)

if result2 and isinstance(result2, dict):
    print("[SUCCESS] Repair worked!")
    print(f"  Parsed elements: {len(result2.get('elements', []))}")
else:
    print("[FAILED] Repair failed")
    print(f"  Result: {result2}")
