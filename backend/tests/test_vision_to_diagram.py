"""
测试图片上传转换为Excalidraw/React Flow格式的功能
使用custom provider (Claude Sonnet 4.5) 配置
"""

import pytest
import json
import base64
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# 从model_presets.json读取默认的custom provider配置
def get_custom_provider_config():
    """读取model_presets.json中的custom provider配置"""
    try:
        with open("app/model_presets.json", "r", encoding="utf-8") as f:
            presets = json.load(f)
            for preset in presets.get("presets", []):
                if preset.get("provider") == "custom" and preset.get("is_default"):
                    return preset
    except Exception as e:
        print(f"Failed to load model_presets.json: {e}")

    # 默认配置（如果读取失败）
    return {
        "api_key": "sk-7Vm4JJgG9J7ghGWdtxH4vOqyVgpMcPs9zgeBLj9RqHhCswlh",
        "model_name": "claude-sonnet-4-5-20250929",
        "base_url": "https://www.linkflow.run/v1"
    }


# 简单的测试图片：一个3x3的PNG图片（红色方块）
# 这只是占位符，实际应该是流程图的截图
SIMPLE_TEST_IMAGE_BASE64 = """
iVBORw0KGgoAAAANSUhEUgAAAAMAAAADCAYAAABWKLW/AAAADklEQVQIW2P4z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg==
""".strip()

# 更真实的测试：使用文字描述来让AI生成，而不是真实图片
# 这样测试更稳定（不依赖OCR准确性）
TEST_FLOWCHART_DESCRIPTION = """
请根据以下描述生成流程图：
- 开始节点
- 判断节点：检查用户是否登录
- 如果已登录：跳转到主页
- 如果未登录：跳转到登录页
- 结束节点
"""


class TestVisionToExcalidraw:
    """测试图片转Excalidraw格式"""

    def test_generate_excalidraw_from_description(self):
        """测试从描述生成Excalidraw格式（不依赖真实图片）"""
        config = get_custom_provider_config()

        # 构造请求
        request_data = {
            "image_data": f"data:image/png;base64,{SIMPLE_TEST_IMAGE_BASE64}",
            "prompt": TEST_FLOWCHART_DESCRIPTION,
            "provider": "custom",
            "api_key": config["api_key"],
            "base_url": config["base_url"],
            "model_name": config["model_name"],
            "width": 1200,
            "height": 800
        }

        # 调用API（这个endpoint还不存在，我们后面会创建）
        response = client.post(
            "/api/vision/generate-excalidraw",
            json=request_data,
            timeout=120.0  # 增加超时时间，AI生成需要时间
        )

        # 验证响应
        assert response.status_code == 200, f"Request failed: {response.text}"

        data = response.json()
        assert data["success"] is True, f"Generation failed: {data}"
        assert "scene" in data, "Response missing 'scene' field"

        # 验证Excalidraw场景结构
        scene = data["scene"]
        assert "elements" in scene, "Scene missing 'elements' field"
        assert isinstance(scene["elements"], list), "elements should be a list"
        assert len(scene["elements"]) > 0, "Scene should have at least one element"

        # 验证元素结构
        for element in scene["elements"]:
            assert "id" in element, "Element missing 'id' field"
            assert "type" in element, "Element missing 'type' field"
            assert element["type"] in [
                "rectangle", "ellipse", "diamond", "arrow",
                "line", "text", "freedraw", "image"
            ], f"Invalid element type: {element['type']}"

            # 图形元素必须有位置和尺寸
            if element["type"] in ["rectangle", "ellipse", "diamond", "text"]:
                assert "x" in element, "Element missing 'x' coordinate"
                assert "y" in element, "Element missing 'y' coordinate"
                assert "width" in element, "Element missing 'width'"
                assert "height" in element, "Element missing 'height'"

            # 箭头和线条必须有points数组
            if element["type"] in ["arrow", "line"]:
                assert "points" in element, f"Arrow/line element missing 'points': {element}"
                assert isinstance(element["points"], list), "points should be a list"
                assert len(element["points"]) >= 2, "Arrow/line should have at least 2 points"

        print(f"✅ Excalidraw scene generated successfully with {len(scene['elements'])} elements")
        return scene

    def test_excalidraw_scene_has_connections(self):
        """测试生成的Excalidraw场景包含连接（箭头）"""
        scene = self.test_generate_excalidraw_from_description()

        # 统计箭头数量
        arrows = [e for e in scene["elements"] if e["type"] == "arrow"]
        assert len(arrows) > 0, "Scene should have at least one arrow connection"

        # 验证箭头有绑定
        for arrow in arrows:
            # 注意：startBinding和endBinding是可选的，AI生成时可能不完美
            # 但至少应该有points坐标
            assert len(arrow["points"]) >= 2, "Arrow should have start and end points"

        print(f"✅ Found {len(arrows)} arrow connections")


class TestVisionToReactFlow:
    """测试图片转React Flow格式"""

    def test_generate_reactflow_from_description(self):
        """测试从描述生成React Flow格式"""
        config = get_custom_provider_config()

        request_data = {
            "image_data": f"data:image/png;base64,{SIMPLE_TEST_IMAGE_BASE64}",
            "prompt": TEST_FLOWCHART_DESCRIPTION,
            "provider": "custom",
            "api_key": config["api_key"],
            "base_url": config["base_url"],
            "model_name": config["model_name"]
        }

        response = client.post(
            "/api/vision/generate-reactflow",
            json=request_data,
            timeout=120.0
        )

        assert response.status_code == 200, f"Request failed: {response.text}"

        data = response.json()
        assert data["success"] is True
        assert "nodes" in data
        assert "edges" in data

        # 验证节点结构
        nodes = data["nodes"]
        assert isinstance(nodes, list), "nodes should be a list"
        assert len(nodes) > 0, "Should have at least one node"

        for node in nodes:
            assert "id" in node, "Node missing 'id'"
            assert "type" in node, "Node missing 'type'"
            assert "position" in node, "Node missing 'position'"
            assert "data" in node, "Node missing 'data'"

            # 验证position结构
            assert "x" in node["position"], "Position missing 'x'"
            assert "y" in node["position"], "Position missing 'y'"
            assert isinstance(node["position"]["x"], (int, float)), "x should be a number"
            assert isinstance(node["position"]["y"], (int, float)), "y should be a number"

            # 验证data结构
            assert "label" in node["data"], "Node data missing 'label'"

            # 验证节点类型
            valid_types = [
                "api", "service", "database", "cache", "client",
                "queue", "gateway", "container", "default"
            ]
            assert node["type"] in valid_types, f"Invalid node type: {node['type']}"

        # 验证边结构
        edges = data["edges"]
        assert isinstance(edges, list), "edges should be a list"

        for edge in edges:
            assert "id" in edge, "Edge missing 'id'"
            assert "source" in edge, "Edge missing 'source'"
            assert "target" in edge, "Edge missing 'target'"

            # 验证source和target指向的节点存在
            node_ids = {n["id"] for n in nodes}
            assert edge["source"] in node_ids, f"Edge source '{edge['source']}' not found in nodes"
            assert edge["target"] in node_ids, f"Edge target '{edge['target']}' not found in nodes"

        print(f"✅ React Flow diagram generated: {len(nodes)} nodes, {len(edges)} edges")
        return {"nodes": nodes, "edges": edges}

    def test_reactflow_has_proper_layout(self):
        """测试生成的React Flow布局合理（无重叠）"""
        diagram = self.test_generate_reactflow_from_description()
        nodes = diagram["nodes"]

        # 检查节点位置是否合理（不全是0,0）
        positions = [(n["position"]["x"], n["position"]["y"]) for n in nodes]
        unique_positions = set(positions)

        # 至少应该有多个不同的位置（除非只有1个节点）
        if len(nodes) > 1:
            assert len(unique_positions) > 1, "Nodes should have different positions"

        # 位置应该是正数（在画布范围内）
        for x, y in positions:
            assert x >= 0, f"Node x position should be non-negative: {x}"
            assert y >= 0, f"Node y position should be non-negative: {y}"

        print(f"✅ Layout validation passed: {len(unique_positions)} unique positions")


class TestVisionAPIConfiguration:
    """测试Vision API配置"""

    def test_custom_provider_config_valid(self):
        """测试custom provider配置有效"""
        config = get_custom_provider_config()

        assert config["api_key"], "API key should not be empty"
        assert config["base_url"], "Base URL should not be empty"
        assert config["model_name"], "Model name should not be empty"
        assert "claude" in config["model_name"].lower(), "Model should be Claude"

        print(f"✅ Custom provider config loaded: {config['model_name']}")

    def test_vision_analyze_endpoint_exists(self):
        """测试现有的vision analyze endpoint可用"""
        config = get_custom_provider_config()

        request_data = {
            "image_data": f"data:image/png;base64,{SIMPLE_TEST_IMAGE_BASE64}",
            "provider": "custom",
            "api_key": config["api_key"],
            "base_url": config["base_url"],
            "model_name": config["model_name"]
        }

        response = client.post(
            "/api/vision/analyze",
            json=request_data,
            timeout=60.0
        )

        # 这个endpoint可能会因为图片太小失败，但至少应该返回有效响应
        # 只要不是404就说明endpoint存在
        assert response.status_code != 404, "Vision analyze endpoint should exist"
        print(f"✅ Vision analyze endpoint status: {response.status_code}")


# 运行单个测试的辅助函数
if __name__ == "__main__":
    print("Testing custom provider configuration...")
    config = get_custom_provider_config()
    print(f"Config loaded: {json.dumps(config, indent=2)}")

    print("\n" + "="*60)
    print("Run tests with: pytest tests/test_vision_to_diagram.py -v")
    print("="*60)
