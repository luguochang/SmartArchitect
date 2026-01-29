"""
使用真实图片测试Vision to Diagram功能
"""

import pytest
import json
import base64
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 读取custom provider配置
def get_custom_provider_config():
    with open("app/model_presets.json", "r", encoding="utf-8") as f:
        presets = json.load(f)
        for preset in presets.get("presets", []):
            if preset.get("provider") == "custom" and preset.get("is_default"):
                return preset
    raise ValueError("No default custom provider found")

# 读取测试图片
def get_test_image_base64():
    with open("tests/8d8c58ed11c145efbd76c954b4fe6233.png", "rb") as f:
        return base64.b64encode(f.read()).decode()


def test_real_image_to_excalidraw():
    """测试真实图片转Excalidraw"""
    config = get_custom_provider_config()
    image_base64 = get_test_image_base64()

    print(f"\n{'='*80}")
    print(f"测试图片转Excalidraw - 真实图片（131KB）")
    print(f"Provider: {config['provider']}")
    print(f"Model: {config['model_name']}")
    print(f"{'='*80}\n")

    request_data = {
        "image_data": f"data:image/png;base64,{image_base64}",
        "prompt": "请分析这张智能体架构图，转换为Excalidraw格式。保留Planning、Memory、Tools、Action等模块和所有连接关系。",
        "provider": "custom",
        "api_key": config["api_key"],
        "base_url": config["base_url"],
        "model_name": config["model_name"],
        "width": 1400,
        "height": 900
    }

    response = client.post(
        "/api/vision/generate-excalidraw",
        json=request_data,
        timeout=180.0
    )

    assert response.status_code == 200, f"Request failed: {response.text}"

    result = response.json()
    print(f"API响应: success={result.get('success')}")

    if not result.get("success"):
        print(f"❌ 失败原因: {result.get('message')}")
        if result.get("raw_response"):
            print(f"原始响应（前500字符）:\n{result['raw_response'][:500]}")

    assert result["success"] is True, f"Generation failed: {result.get('message')}"

    # 验证Excalidraw场景结构
    scene = result["scene"]
    assert "elements" in scene
    assert isinstance(scene["elements"], list)
    assert len(scene["elements"]) > 0, "Scene should have at least one element"

    # 统计元素
    elements = scene["elements"]
    element_types = {}
    for elem in elements:
        elem_type = elem.get("type", "unknown")
        element_types[elem_type] = element_types.get(elem_type, 0) + 1

    print(f"\n✅ Excalidraw生成成功!")
    print(f"   - 元素总数: {len(elements)}")
    print(f"   - 元素类型分布:")
    for etype, count in sorted(element_types.items()):
        print(f"     • {etype}: {count}")

    # 保存结果
    with open("test_excalidraw_real_output.json", "w", encoding="utf-8") as f:
        json.dump(scene, f, indent=2, ensure_ascii=False)
    print(f"   - 结果已保存: test_excalidraw_real_output.json")

    # 显示示例元素
    print(f"\n   示例元素:")
    for i, elem in enumerate(elements[:5]):
        text = elem.get("text", "")[:30]
        print(f"      {i+1}. {elem.get('type')}: {text if text else '(无文本)'}")


def test_real_image_to_reactflow():
    """测试真实图片转React Flow"""
    config = get_custom_provider_config()
    image_base64 = get_test_image_base64()

    print(f"\n{'='*80}")
    print(f"测试图片转React Flow - 真实图片（131KB）")
    print(f"{'='*80}\n")

    request_data = {
        "image_data": f"data:image/png;base64,{image_base64}",
        "prompt": "请分析这张智能体架构图，转换为SmartArchitect React Flow格式。识别各模块类型（Planning、Memory、Tools、Action）。",
        "provider": "custom",
        "api_key": config["api_key"],
        "base_url": config["base_url"],
        "model_name": config["model_name"]
    }

    response = client.post(
        "/api/vision/generate-reactflow",
        json=request_data,
        timeout=180.0
    )

    assert response.status_code == 200, f"Request failed: {response.text}"

    result = response.json()
    print(f"API响应: success={result.get('success')}")

    if not result.get("success"):
        print(f"❌ 失败原因: {result.get('message')}")
        if result.get("raw_response"):
            print(f"原始响应（前500字符）:\n{result['raw_response'][:500]}")

    assert result["success"] is True, f"Generation failed: {result.get('message')}"

    # 验证React Flow结构
    nodes = result["nodes"]
    edges = result["edges"]

    assert isinstance(nodes, list)
    assert isinstance(edges, list)
    assert len(nodes) > 0, "Should have at least one node"

    # 统计节点类型
    node_types = {}
    for node in nodes:
        ntype = node.get("type", "unknown")
        node_types[ntype] = node_types.get(ntype, 0) + 1

    print(f"\n✅ React Flow生成成功!")
    print(f"   - 节点总数: {len(nodes)}")
    print(f"   - 连接总数: {len(edges)}")
    print(f"   - 节点类型分布:")
    for ntype, count in sorted(node_types.items()):
        print(f"     • {ntype}: {count}")

    # 保存结果
    with open("test_reactflow_real_output.json", "w", encoding="utf-8") as f:
        json.dump({"nodes": nodes, "edges": edges}, f, indent=2, ensure_ascii=False)
    print(f"   - 结果已保存: test_reactflow_real_output.json")

    # 显示示例节点
    print(f"\n   示例节点:")
    for i, node in enumerate(nodes[:5]):
        label = node.get("data", {}).get("label", "N/A")
        ntype = node.get("type", "unknown")
        print(f"      {i+1}. [{ntype}] {label}")


if __name__ == "__main__":
    print("运行测试: pytest tests/test_real_image.py -v -s")
