# -*- coding: utf-8 -*-
"""简单测试脚本 - 无emoji"""
import json
import base64
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 读取配置
with open("app/model_presets.json", "r", encoding="utf-8") as f:
    presets = json.load(f)
    config = next(p for p in presets["presets"] if p["provider"] == "custom" and p.get("is_default"))

# 读取图片
with open("tests/8d8c58ed11c145efbd76c954b4fe6233.png", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

print("="*80)
print("Testing Excalidraw generation...")
print("="*80)

# 调用API
response = client.post(
    "/api/vision/generate-excalidraw",
    json={
        "image_data": f"data:image/png;base64,{image_base64}",
        "prompt": "Convert this architecture diagram to Excalidraw format",
        "provider": "custom",
        "api_key": config["api_key"],
        "base_url": config["base_url"],
        "model_name": config["model_name"],
        "width": 1400,
        "height": 900
    },
    timeout=180.0
)

result = response.json()

if result.get("success"):
    scene = result["scene"]
    elements = scene["elements"]

    # 统计
    types = {}
    for elem in elements:
        t = elem.get("type", "unknown")
        types[t] = types.get(t, 0) + 1

    print(f"SUCCESS! Generated {len(elements)} elements")
    print("Element types:")
    for t, count in sorted(types.items()):
        print(f"  - {t}: {count}")

    # 保存
    with open("excalidraw_output.json", "w", encoding="utf-8") as f:
        json.dump(scene, f, indent=2, ensure_ascii=False)
    print("\nSaved to: excalidraw_output.json")

    # 显示前5个元素
    print("\nFirst 5 elements:")
    for i, elem in enumerate(elements[:5]):
        text = elem.get("text", "")[:40]
        print(f"  {i+1}. {elem.get('type')}: {text if text else '(no text)'}")
else:
    print(f"FAILED: {result.get('message')}")
