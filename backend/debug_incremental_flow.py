"""
调试脚本：模拟真实的增量生成流程，查看日志输出
"""
import sys
import os
import asyncio
import logging
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置日志输出到控制台，方便查看
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.session_manager import get_session_manager
from app.services.chat_generator import ChatGeneratorService
from app.models.schemas import Node, Edge, Position, NodeData, ChatGenerationRequest

logger = logging.getLogger(__name__)


async def test_incremental_generation_flow():
    """完整模拟真实的增量生成流程"""

    print("\n" + "=" * 80)
    print("模拟真实增量生成流程 - 调试日志")
    print("=" * 80 + "\n")

    # Step 1: 创建初始架构（模拟第一次生成）
    print("步骤 1: 创建初始架构（5 个节点）")
    print("-" * 80)

    initial_nodes = [
        Node(
            id="api-1",
            type="api",
            position=Position(x=100, y=100),
            data=NodeData(label="API Gateway")
        ),
        Node(
            id="service-1",
            type="service",
            position=Position(x=400, y=100),
            data=NodeData(label="User Service")
        ),
        Node(
            id="service-2",
            type="service",
            position=Position(x=400, y=300),
            data=NodeData(label="Order Service")
        ),
        Node(
            id="db-1",
            type="database",
            position=Position(x=700, y=100),
            data=NodeData(label="User DB")
        ),
        Node(
            id="db-2",
            type="database",
            position=Position(x=700, y=300),
            data=NodeData(label="Order DB")
        )
    ]

    initial_edges = [
        Edge(id="e1", source="api-1", target="service-1", label="HTTP"),
        Edge(id="e2", source="api-1", target="service-2", label="HTTP"),
        Edge(id="e3", source="service-1", target="db-1", label="SQL"),
        Edge(id="e4", source="service-2", target="db-2", label="SQL")
    ]

    print(f"初始节点: {[n.data.label for n in initial_nodes]}")
    print(f"初始边数: {len(initial_edges)}")

    # Step 2: 保存到会话
    print("\n步骤 2: 保存画布到会话")
    print("-" * 80)

    session_manager = get_session_manager()
    session_id = session_manager.create_or_update_session(None, initial_nodes, initial_edges)
    print(f"✓ 会话已创建: {session_id}")
    print(f"  - 节点数: {len(initial_nodes)}")
    print(f"  - 边数: {len(initial_edges)}")

    # Step 3: 验证会话已保存
    print("\n步骤 3: 验证会话数据")
    print("-" * 80)

    session_data = session_manager.get_session(session_id)
    if session_data:
        loaded_nodes = [Node(**n) for n in session_data["nodes"]]
        loaded_edges = [Edge(**e) for e in session_data["edges"]]
        print(f"✓ 会话数据加载成功")
        print(f"  - 加载的节点: {[n.data.label for n in loaded_nodes]}")
        print(f"  - 加载的边数: {len(loaded_edges)}")
    else:
        print("✗ 会话数据加载失败!")
        return

    # Step 4: 模拟增量生成请求
    print("\n步骤 4: 构建增量生成 Prompt")
    print("-" * 80)

    service = ChatGeneratorService()
    request = ChatGenerationRequest(
        user_input="在服务和数据库之间添加 Redis 缓存层",
        diagram_type="architecture",
        incremental_mode=True,
        session_id=session_id
    )

    print(f"用户输入: {request.user_input}")
    print(f"增量模式: {request.incremental_mode}")
    print(f"会话 ID: {request.session_id}")

    # 加载现有架构（模拟 generate_flowchart 中的逻辑）
    session_data = session_manager.get_session(request.session_id)
    if session_data:
        existing_nodes = [Node(**n) for n in session_data["nodes"]]
        existing_edges = [Edge(**e) for e in session_data["edges"]]
        print(f"\n✓ 从会话加载的现有架构:")
        print(f"  - 节点数: {len(existing_nodes)}")
        print(f"  - 节点列表: {[n.data.label for n in existing_nodes]}")
        print(f"  - 边数: {len(existing_edges)}")
    else:
        print("\n✗ 无法加载会话数据!")
        return

    # 构建增量 Prompt
    prompt = service._build_incremental_prompt(request, existing_nodes, existing_edges)

    print(f"\n✓ Prompt 已构建 (长度: {len(prompt)} 字符)")

    # 检查 Prompt 中的关键约束
    print("\nPrompt 约束检查:")
    constraints = [
        "DO NOT SIMPLIFY",
        "PRESERVE COMPLEXITY",
        "NO DELETION",
        "NO MODIFICATION",
        "ONLY ADD",
        "Current Architecture Overview"
    ]
    for constraint in constraints:
        if constraint in prompt:
            print(f"  ✓ {constraint}")
        else:
            print(f"  ✗ 缺失: {constraint}")

    # 检查所有节点是否在 Prompt 中
    print("\n原始节点在 Prompt 中的检查:")
    for node in existing_nodes:
        if node.data.label in prompt:
            print(f"  ✓ {node.data.label}")
        else:
            print(f"  ✗ 缺失: {node.data.label}")

    # Step 5: 模拟 AI 返回（故意删除一个节点来测试验证逻辑）
    print("\n步骤 5: 模拟 AI 返回（故意制造错误）")
    print("-" * 80)

    # 模拟 AI 删除了 service-2 和修改了 api-1 的 label
    ai_nodes = [
        Node(
            id="api-1",
            type="api",
            position=Position(x=150, y=120),  # 位置被移动了
            data=NodeData(label="Gateway")  # Label 被简化了
        ),
        Node(
            id="service-1",
            type="service",
            position=Position(x=400, y=100),
            data=NodeData(label="User Service")
        ),
        # service-2 被删除了！
        Node(
            id="db-1",
            type="database",
            position=Position(x=700, y=100),
            data=NodeData(label="User DB")
        ),
        Node(
            id="db-2",
            type="database",
            position=Position(x=700, y=300),
            data=NodeData(label="Order DB")
        ),
        # 新增的缓存节点
        Node(
            id="cache-1",
            type="cache",
            position=Position(x=550, y=100),
            data=NodeData(label="Redis Cache")
        )
    ]

    ai_edges = [
        Edge(id="e1", source="api-1", target="service-1", label="HTTP"),
        # e2 被删除了（到 service-2 的边）
        Edge(id="e3", source="service-1", target="cache-1", label="TCP"),
        Edge(id="e5", source="cache-1", target="db-1", label="Redis Protocol"),
        Edge(id="e6", source="service-2", target="db-2", label="SQL")  # 这条边引用了不存在的 service-2
    ]

    print(f"AI 返回节点数: {len(ai_nodes)}")
    print(f"AI 返回节点: {[n.data.label for n in ai_nodes]}")
    print(f"AI 返回边数: {len(ai_edges)}")

    print(f"\n⚠️ 问题:")
    print(f"  - 删除了节点: service-2 (Order Service)")
    print(f"  - 修改了节点 label: api-1 (API Gateway → Gateway)")
    print(f"  - 移动了节点位置: api-1 (100, 100) → (150, 120)")

    # Step 6: 执行验证逻辑
    print("\n步骤 6: 执行验证和修复逻辑")
    print("-" * 80)

    print("\n开始验证...")
    validated_nodes = service._validate_incremental_result(existing_nodes, ai_nodes)
    merged_edges = service._merge_edges(existing_edges, ai_edges)

    print(f"\n✓ 验证完成")
    print(f"  - 验证后节点数: {len(validated_nodes)}")
    print(f"  - 验证后节点: {[n.data.label for n in validated_nodes]}")
    print(f"  - 合并后边数: {len(merged_edges)}")

    # 检查修复结果
    print("\n修复结果检查:")

    # 检查节点是否恢复
    node_map = {n.id: n for n in validated_nodes}

    if "service-2" in node_map:
        print(f"  ✓ service-2 已恢复: {node_map['service-2'].data.label}")
    else:
        print(f"  ✗ service-2 未恢复!")

    if "api-1" in node_map:
        api_node = node_map["api-1"]
        if api_node.data.label == "API Gateway":
            print(f"  ✓ api-1 label 已恢复: {api_node.data.label}")
        else:
            print(f"  ✗ api-1 label 未恢复: {api_node.data.label}")

        if api_node.position.x == 100 and api_node.position.y == 100:
            print(f"  ✓ api-1 位置已恢复: ({api_node.position.x}, {api_node.position.y})")
        else:
            print(f"  ✗ api-1 位置未恢复: ({api_node.position.x}, {api_node.position.y})")

    # 检查是否有新增节点
    new_nodes = [n for n in validated_nodes if n.id not in {node.id for node in existing_nodes}]
    if new_nodes:
        print(f"\n新增节点:")
        for node in new_nodes:
            print(f"  + {node.id}: {node.data.label}")

    # 最终结果
    print("\n" + "=" * 80)
    print("最终结果对比")
    print("=" * 80)
    print(f"初始节点数: {len(existing_nodes)}")
    print(f"AI 返回节点数: {len(ai_nodes)}")
    print(f"验证后节点数: {len(validated_nodes)}")
    print(f"新增节点数: {len(validated_nodes) - len(existing_nodes)}")

    print(f"\n初始边数: {len(existing_edges)}")
    print(f"AI 返回边数: {len(ai_edges)}")
    print(f"合并后边数: {len(merged_edges)}")
    print(f"新增边数: {len(merged_edges) - len(existing_edges)}")

    if len(validated_nodes) == len(existing_nodes) + 1:  # 5 原始 + 1 新增
        print("\n✓ 增量生成成功: 保留了所有原始节点，并添加了新节点")
    else:
        print("\n✗ 增量生成失败: 节点数量不符合预期")

    # 清理会话
    print("\n清理会话...")
    session_manager.delete_session(session_id)
    print("✓ 会话已删除")


if __name__ == "__main__":
    asyncio.run(test_incremental_generation_flow())
