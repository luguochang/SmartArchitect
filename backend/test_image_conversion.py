#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试图片转换功能的独立脚本
使用真实的架构图测试Excalidraw和React Flow生成
"""

import base64
import json
import sys
import io
from pathlib import Path

# 设置标准输出编码为UTF-8（Windows兼容）
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

import requests

# 测试配置
IMAGE_PATH = "tests/8d8c58ed11c145efbd76c954b4fe6233.png"
API_BASE = "http://localhost:8000"

# Custom provider配置（从model_presets.json读取）
try:
    with open("app/model_presets.json", "r", encoding="utf-8") as f:
        presets = json.load(f)
        custom_config = next(
            (p for p in presets["presets"] if p["provider"] == "custom" and p.get("is_default")),
            None
        )
        if not custom_config:
            raise ValueError("No default custom provider found")
except Exception as e:
    print(f"❌ Failed to load config: {e}")
    sys.exit(1)

print("=" * 80)
print("📸 图片转流程图功能测试")
print("=" * 80)
print(f"图片路径: {IMAGE_PATH}")
print(f"Provider: {custom_config['provider']}")
print(f"Model: {custom_config['model_name']}")
print(f"Base URL: {custom_config['base_url']}")
print("=" * 80)

# 读取图片并转换为base64
print("\n📂 读取图片...")
try:
    with open(IMAGE_PATH, "rb") as f:
        image_bytes = f.read()
        image_size = len(image_bytes) / 1024  # KB
        base64_image = base64.b64encode(image_bytes).decode()
        print(f"✅ 图片读取成功: {image_size:.2f} KB")
except Exception as e:
    print(f"❌ 图片读取失败: {e}")
    sys.exit(1)

# 测试1: Excalidraw生成
print("\n" + "=" * 80)
print("🎨 测试1: 生成Excalidraw格式")
print("=" * 80)

request_data_excalidraw = {
    "image_data": f"data:image/png;base64,{base64_image}",
    "prompt": "请分析这张智能体架构图，转换为Excalidraw格式。保留所有模块、组件和连接关系。",
    "provider": custom_config["provider"],
    "api_key": custom_config["api_key"],
    "base_url": custom_config["base_url"],
    "model_name": custom_config["model_name"],
    "width": 1400,
    "height": 900
}

try:
    print("🔄 正在调用API...")
    response = requests.post(
        f"{API_BASE}/api/vision/generate-excalidraw",
        json=request_data_excalidraw,
        timeout=180.0
    )

    print(f"📡 响应状态: {response.status_code}")

    result = response.json()

    if result.get("success"):
        scene = result["scene"]
        elements = scene["elements"]

        print(f"✅ Excalidraw生成成功!")
        print(f"   - 元素总数: {len(elements)}")

        # 统计元素类型
        element_types = {}
        for elem in elements:
            elem_type = elem.get("type", "unknown")
            element_types[elem_type] = element_types.get(elem_type, 0) + 1

        print(f"   - 元素类型分布:")
        for etype, count in sorted(element_types.items()):
            print(f"     • {etype}: {count}")

        # 保存结果
        output_file = "test_excalidraw_output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(scene, f, indent=2, ensure_ascii=False)
        print(f"   - 结果已保存: {output_file}")

        # 显示前3个元素作为示例
        print(f"\n   📄 前3个元素示例:")
        for i, elem in enumerate(elements[:3]):
            print(f"      {i+1}. {elem.get('type', 'unknown')}: {elem.get('text', 'N/A')[:30]}")
    else:
        print(f"❌ 生成失败: {result.get('message', 'Unknown error')}")
        if result.get("raw_response"):
            print(f"   原始响应: {result['raw_response'][:200]}...")

except requests.exceptions.Timeout:
    print("❌ 请求超时（180秒）")
except requests.exceptions.ConnectionError:
    print("❌ 连接失败 - 请确保后端服务正在运行 (python -m app.main)")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

# 测试2: React Flow生成
print("\n" + "=" * 80)
print("🔷 测试2: 生成React Flow格式")
print("=" * 80)

request_data_reactflow = {
    "image_data": f"data:image/png;base64,{base64_image}",
    "prompt": "请分析这张智能体架构图，转换为SmartArchitect React Flow格式。识别各个模块和组件的类型。",
    "provider": custom_config["provider"],
    "api_key": custom_config["api_key"],
    "base_url": custom_config["base_url"],
    "model_name": custom_config["model_name"]
}

try:
    print("🔄 正在调用API...")
    response = requests.post(
        f"{API_BASE}/api/vision/generate-reactflow",
        json=request_data_reactflow,
        timeout=180.0
    )

    print(f"📡 响应状态: {response.status_code}")

    result = response.json()

    if result.get("success"):
        nodes = result["nodes"]
        edges = result["edges"]

        print(f"✅ React Flow生成成功!")
        print(f"   - 节点总数: {len(nodes)}")
        print(f"   - 连接总数: {len(edges)}")

        # 统计节点类型
        node_types = {}
        for node in nodes:
            ntype = node.get("type", "unknown")
            node_types[ntype] = node_types.get(ntype, 0) + 1

        print(f"   - 节点类型分布:")
        for ntype, count in sorted(node_types.items()):
            print(f"     • {ntype}: {count}")

        # 保存结果
        output_file = "test_reactflow_output.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump({"nodes": nodes, "edges": edges}, f, indent=2, ensure_ascii=False)
        print(f"   - 结果已保存: {output_file}")

        # 显示前5个节点
        print(f"\n   📄 前5个节点示例:")
        for i, node in enumerate(nodes[:5]):
            label = node.get("data", {}).get("label", "N/A")
            ntype = node.get("type", "unknown")
            pos = node.get("position", {})
            print(f"      {i+1}. [{ntype}] {label} at ({pos.get('x', 0):.0f}, {pos.get('y', 0):.0f})")

        # 显示连接关系
        if edges:
            print(f"\n   🔗 连接关系示例:")
            for i, edge in enumerate(edges[:3]):
                src = edge.get("source", "?")
                tgt = edge.get("target", "?")
                label = edge.get("label", "")
                print(f"      {i+1}. {src} → {tgt} {f'({label})' if label else ''}")
    else:
        print(f"❌ 生成失败: {result.get('message', 'Unknown error')}")
        if result.get("raw_response"):
            print(f"   原始响应: {result['raw_response'][:200]}...")

except requests.exceptions.Timeout:
    print("❌ 请求超时（180秒）")
except requests.exceptions.ConnectionError:
    print("❌ 连接失败 - 请确保后端服务正在运行 (python -m app.main)")
except Exception as e:
    print(f"❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ 测试完成!")
print("=" * 80)
print("\n📁 生成的文件:")
print("   - test_excalidraw_output.json  (Excalidraw场景)")
print("   - test_reactflow_output.json   (React Flow图表)")
print("\n💡 提示:")
print("   - 将Excalidraw JSON导入到 https://excalidraw.com 查看效果")
print("   - React Flow数据可以在SmartArchitect前端中使用")
print("=" * 80)
