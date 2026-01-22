"""Test improved JSON repair logic"""
import json
import sys
sys.path.insert(0, 'D:\\file\\openproject\\SmartArchitect\\backend')

from app.services.excalidraw_generator import create_excalidraw_service

# Test case 1: JSON with missing comma between array elements
broken_json_1 = '''```json
{
  "elements": [
    {"id": "1", "type": "rectangle", "x": 100, "y": 100, "width": 50, "height": 50, "angle": 0, "strokeColor": "#000", "backgroundColor": "transparent", "fillStyle": "hachure", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 1, "opacity": 100, "groupIds": [], "boundElements": []}
    {"id": "2", "type": "ellipse", "x": 200, "y": 200, "width": 50, "height": 50, "angle": 0, "strokeColor": "#000", "backgroundColor": "transparent", "fillStyle": "hachure", "strokeWidth": 1, "strokeStyle": "solid", "roughness": 1, "opacity": 100, "groupIds": [], "boundElements": []}
  ],
  "appState": {},
  "files": {}
}
```'''

# Test case 2: JSON with missing commas between properties
broken_json_2 = '''{
  "elements": [
    {"id": "1" "type": "rectangle", "x": 100, "y": 100}
  ],
  "appState": {}
}'''

# Test case 3: Incomplete JSON (missing closing braces)
incomplete_json = '''{
  "elements": [
    {"id": "1", "type": "rectangle", "x": 100, "y": 100, "width": 50, "height": 50
  ],
  "appState": {'''

print("=" * 80)
print("TEST: Improved JSON Repair Logic")
print("=" * 80)

service = create_excalidraw_service()

# Test 1
print("\n[Test 1] Missing comma between array elements")
print("-" * 80)
result1 = service._safe_json(broken_json_1)
if result1 and isinstance(result1, dict) and len(result1.get('elements', [])) == 2:
    print("[PASS] Repaired successfully")
    print(f"   Parsed {len(result1['elements'])} elements")
else:
    print("[FAIL] Repair failed")
    print(f"   Result: {result1}")

# Test 2
print("\n[Test 2] Missing commas between properties")
print("-" * 80)
result2 = service._safe_json(broken_json_2)
if result2 and isinstance(result2, dict):
    print("[PASS] Repaired successfully")
    print(f"   Parsed {len(result2.get('elements', []))} elements")
else:
    print("[FAIL] Repair failed")
    print(f"   Result: {result2}")

# Test 3
print("\n[Test 3] Incomplete JSON (bracket tracking)")
print("-" * 80)
result3 = service._safe_json(incomplete_json)
if result3 and isinstance(result3, dict):
    print("[PASS] Repaired successfully")
    print(f"   Keys: {list(result3.keys())}")
else:
    print("[FAIL] Repair failed")
    print(f"   Result: {result3}")

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
passed = sum([
    result1 and len(result1.get('elements', [])) == 2,
    result2 and isinstance(result2, dict),
    result3 and isinstance(result3, dict)
])
print(f"Passed: {passed}/3")
