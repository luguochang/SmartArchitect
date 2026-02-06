"""
临时测试脚本：验证增量生成功能的核心逻辑
"""
import sys
import os
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.session_manager import get_session_manager
from app.models.schemas import Node, Edge, Position, NodeData
from datetime import datetime, timedelta


def test_session_manager():
    """测试会话管理器基础功能"""
    print("=" * 60)
    print("测试 1: 会话管理器基础功能")
    print("=" * 60)

    manager = get_session_manager()

    # 创建测试节点
    nodes = [
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
            id="db-1",
            type="database",
            position=Position(x=700, y=100),
            data=NodeData(label="MySQL")
        )
    ]

    edges = [
        Edge(id="e1", source="api-1", target="service-1", label="HTTP"),
        Edge(id="e2", source="service-1", target="db-1", label="SQL")
    ]

    # 测试创建会话
    print("\n1. 创建新会话...")
    session_id = manager.create_or_update_session(None, nodes, edges)
    print(f"   ✓ 会话已创建: {session_id}")

    # 测试获取会话
    print("\n2. 获取会话数据...")
    session_data = manager.get_session(session_id)
    if session_data:
        print(f"   ✓ 会话数据获取成功")
        print(f"   - 节点数: {session_data['node_count']}")
        print(f"   - 边数: {session_data['edge_count']}")
        print(f"   - 时间戳: {session_data['timestamp']}")
    else:
        print("   ✗ 会话数据获取失败")
        return False

    # 测试更新会话
    print("\n3. 更新会话（添加一个节点）...")
    new_node = Node(
        id="cache-1",
        type="cache",
        position=Position(x=550, y=250),
        data=NodeData(label="Redis Cache")
    )
    nodes.append(new_node)

    new_edge = Edge(id="e3", source="service-1", target="cache-1", label="Cache")
    edges.append(new_edge)

    session_id_updated = manager.create_or_update_session(session_id, nodes, edges)
    print(f"   ✓ 会话已更新: {session_id_updated}")

    # 验证更新
    session_data_updated = manager.get_session(session_id)
    print(f"   - 更新后节点数: {session_data_updated['node_count']}")
    print(f"   - 更新后边数: {session_data_updated['edge_count']}")

    # 测试删除会话
    print("\n4. 删除会话...")
    manager.delete_session(session_id)
    deleted_session = manager.get_session(session_id)
    if deleted_session is None:
        print("   ✓ 会话已成功删除")
    else:
        print("   ✗ 会话删除失败")
        return False

    print("\n✓ 所有会话管理器测试通过\n")
    return True


def test_incremental_prompt_building():
    """测试增量生成 Prompt 构建逻辑"""
    print("=" * 60)
    print("测试 2: 增量生成 Prompt 构建")
    print("=" * 60)

    from app.services.chat_generator import ChatGeneratorService
    from app.models.schemas import ChatGenerationRequest

    service = ChatGeneratorService()

    # 准备现有架构
    existing_nodes = [
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
            id="db-1",
            type="database",
            position=Position(x=700, y=100),
            data=NodeData(label="MySQL")
        )
    ]

    existing_edges = [
        Edge(id="e1", source="api-1", target="service-1"),
        Edge(id="e2", source="service-1", target="db-1")
    ]

    request = ChatGenerationRequest(
        user_input="在服务和数据库之间添加 Redis 缓存层",
        diagram_type="architecture",
        incremental_mode=True
    )

    print("\n1. 构建增量生成 Prompt...")
    try:
        prompt = service._build_incremental_prompt(request, existing_nodes, existing_edges)
        print("   ✓ Prompt 构建成功")

        # 验证 Prompt 包含关键信息
        checks = [
            ("PRESERVE ALL EXISTING NODES" in prompt, "包含节点保护指令"),
            ("api-1" in prompt, "包含现有节点 ID"),
            ("3 nodes" in prompt or "3个节点" in prompt, "包含节点计数"),
            ("x=1000" in prompt or "x >= " in prompt, "包含位置约束"),
        ]

        print("\n   Prompt 内容验证:")
        for check, description in checks:
            status = "✓" if check else "✗"
            print(f"   {status} {description}")

        all_passed = all(check for check, _ in checks)
        if all_passed:
            print("\n✓ Prompt 构建测试通过\n")
        else:
            print("\n✗ 部分 Prompt 验证失败\n")

        return all_passed

    except Exception as e:
        print(f"   ✗ Prompt 构建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_validation_logic():
    """测试验证和冲突解决逻辑"""
    print("=" * 60)
    print("测试 3: 验证和冲突解决逻辑")
    print("=" * 60)

    from app.services.chat_generator import ChatGeneratorService

    service = ChatGeneratorService()

    # 场景 1: AI 误删节点
    print("\n场景 1: AI 误删节点自动恢复")
    original_nodes = [
        Node(id="api-1", type="api", position=Position(x=100, y=100),
             data=NodeData(label="API")),
        Node(id="service-1", type="service", position=Position(x=400, y=100),
             data=NodeData(label="Service")),
        Node(id="db-1", type="database", position=Position(x=700, y=100),
             data=NodeData(label="DB"))
    ]

    # AI 返回结果缺少一个节点
    ai_nodes = [
        Node(id="api-1", type="api", position=Position(x=100, y=100),
             data=NodeData(label="API")),
        Node(id="db-1", type="database", position=Position(x=700, y=100),
             data=NodeData(label="DB")),
        # service-1 被 AI 误删
        Node(id="cache-1", type="cache", position=Position(x=550, y=250),
             data=NodeData(label="Cache"))
    ]

    print(f"   - 原始节点数: {len(original_nodes)}")
    print(f"   - AI 返回节点数: {len(ai_nodes)}")

    validated_nodes = service._validate_incremental_result(original_nodes, ai_nodes)

    print(f"   - 验证后节点数: {len(validated_nodes)}")

    # 验证所有原始节点都存在
    original_ids = {n.id for n in original_nodes}
    validated_ids = {n.id for n in validated_nodes}

    if original_ids.issubset(validated_ids):
        print("   ✓ 所有原始节点已恢复")
    else:
        missing = original_ids - validated_ids
        print(f"   ✗ 缺失节点: {missing}")
        return False

    # 场景 2: 重复 ID
    print("\n场景 2: 重复 ID 自动重命名")
    ai_nodes_duplicate = [
        Node(id="api-1", type="api", position=Position(x=100, y=100),
             data=NodeData(label="API")),
        Node(id="service-1", type="service", position=Position(x=400, y=100),
             data=NodeData(label="Service")),
        Node(id="api-1", type="api", position=Position(x=200, y=200),
             data=NodeData(label="API 2")),  # 重复 ID
    ]

    validated_nodes_dup = service._validate_incremental_result([], ai_nodes_duplicate)
    validated_ids_dup = [n.id for n in validated_nodes_dup]

    print(f"   - 原始 ID 列表: {[n.id for n in ai_nodes_duplicate]}")
    print(f"   - 验证后 ID 列表: {validated_ids_dup}")

    # 检查是否有重命名
    unique_ids = len(set(validated_ids_dup))
    if unique_ids == len(validated_nodes_dup):
        print(f"   ✓ 所有 ID 已去重 ({unique_ids} 个唯一 ID)")
    else:
        print(f"   ✗ 仍存在重复 ID")
        return False

    # 场景 3: 位置重叠
    print("\n场景 3: 位置重叠自动调整")
    overlapping_nodes = [
        Node(id="node-1", type="default", position=Position(x=100, y=100),
             data=NodeData(label="Node 1")),
        Node(id="node-2", type="default", position=Position(x=110, y=105),
             data=NodeData(label="Node 2")),  # 重叠位置
    ]

    resolved_nodes = service._resolve_position_overlaps(overlapping_nodes)

    node1_pos = resolved_nodes[0].position
    node2_pos = resolved_nodes[1].position

    distance = ((node1_pos.x - node2_pos.x) ** 2 + (node1_pos.y - node2_pos.y) ** 2) ** 0.5

    print(f"   - Node 1 位置: ({node1_pos.x}, {node1_pos.y})")
    print(f"   - Node 2 位置: ({node2_pos.x}, {node2_pos.y})")
    print(f"   - 节点间距: {distance:.1f}px")

    if distance >= 100:
        print(f"   ✓ 位置重叠已解决 (距离 >= 100px)")
    else:
        print(f"   ✗ 位置仍然重叠 (距离 < 100px)")
        return False

    print("\n✓ 所有验证逻辑测试通过\n")
    return True


def test_edge_merging():
    """测试边合并逻辑"""
    print("=" * 60)
    print("测试 4: 边合并和去重")
    print("=" * 60)

    from app.services.chat_generator import ChatGeneratorService

    service = ChatGeneratorService()

    original_edges = [
        Edge(id="e1", source="api-1", target="service-1", label="HTTP"),
        Edge(id="e2", source="service-1", target="db-1", label="SQL"),
    ]

    ai_edges = [
        Edge(id="e1", source="api-1", target="service-1", label="HTTP"),  # 重复
        Edge(id="e3", source="service-1", target="cache-1", label="Cache"),  # 新边
    ]

    print(f"\n原始边数: {len(original_edges)}")
    print(f"AI 返回边数: {len(ai_edges)}")

    merged_edges = service._merge_edges(original_edges, ai_edges)

    print(f"合并后边数: {len(merged_edges)}")

    # 验证去重和合并
    edge_signatures = {f"{e.source}->{e.target}" for e in merged_edges}
    print(f"唯一边签名: {edge_signatures}")

    if len(merged_edges) == 3 and len(edge_signatures) == 3:
        print("✓ 边合并测试通过\n")
        return True
    else:
        print("✗ 边合并失败\n")
        return False


def test_prompt_preserves_complexity():
    """测试 Prompt 是否包含保持复杂度的约束"""
    print("=" * 60)
    print("测试 5: Prompt 复杂度保持约束")
    print("=" * 60)

    from app.services.chat_generator import ChatGeneratorService
    from app.models.schemas import ChatGenerationRequest

    service = ChatGeneratorService()

    # 创建现有架构（4 节点）
    existing_nodes = [
        Node(id="api-1", type="api", position=Position(x=100, y=100),
             data=NodeData(label="API Gateway")),
        Node(id="service-1", type="service", position=Position(x=400, y=100),
             data=NodeData(label="User Service")),
        Node(id="service-2", type="service", position=Position(x=400, y=300),
             data=NodeData(label="Order Service")),
        Node(id="db-1", type="database", position=Position(x=700, y=200),
             data=NodeData(label="PostgreSQL"))
    ]

    existing_edges = [
        Edge(id="e1", source="api-1", target="service-1", label="HTTP"),
        Edge(id="e2", source="api-1", target="service-2", label="HTTP"),
        Edge(id="e3", source="service-1", target="db-1", label="SQL")
    ]

    request = ChatGenerationRequest(
        user_input="添加 Redis 缓存层",
        diagram_type="architecture",
        incremental_mode=True
    )

    print("\n1. 构建增量 Prompt...")
    prompt = service._build_incremental_prompt(request, existing_nodes, existing_edges)

    # 验证 Prompt 包含关键约束
    checks = [
        ("DO NOT SIMPLIFY", "DO NOT SIMPLIFY" in prompt),
        ("PRESERVE COMPLEXITY", "PRESERVE COMPLEXITY" in prompt),
        ("NO DELETION", "NO DELETION" in prompt),
        ("NO MODIFICATION", "NO MODIFICATION" in prompt),
        ("NO MERGE", "NO MERGE" in prompt),
        ("ONLY ADD", "ONLY ADD" in prompt),
        ("自然语言描述", "Current Architecture Overview" in prompt or "NATURAL LANGUAGE" in prompt),
        ("包含所有节点", all(node.data.label in prompt for node in existing_nodes))
    ]

    print("\n2. 检查约束条件:")
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✓ Prompt 约束测试通过\n")
        return True
    else:
        print("\n✗ Prompt 约束测试失败\n")
        return False


def test_validate_preserves_node_attributes():
    """测试验证逻辑是否保护节点属性"""
    print("=" * 60)
    print("测试 6: 节点属性保护验证")
    print("=" * 60)

    from app.services.chat_generator import ChatGeneratorService

    service = ChatGeneratorService()

    # 原始节点
    original_nodes = [
        Node(id="api-1", type="api", position=Position(x=100, y=100),
             data=NodeData(label="API Gateway")),
        Node(id="service-1", type="service", position=Position(x=400, y=100),
             data=NodeData(label="User Service"))
    ]

    # AI 修改了节点属性
    ai_nodes = [
        Node(id="api-1", type="service",  # 类型被改了
             position=Position(x=200, y=150),  # 位置被移动了
             data=NodeData(label="Gateway API")),  # Label 被改了
        Node(id="service-1", type="api",  # 类型被改了
             position=Position(x=400, y=100),  # 位置未变
             data=NodeData(label="UserService"))  # Label 被改了
    ]

    print("\n1. 原始节点:")
    for node in original_nodes:
        print(f"   - {node.id}: type={node.type}, label={node.data.label}, pos=({node.position.x}, {node.position.y})")

    print("\n2. AI 修改后的节点:")
    for node in ai_nodes:
        print(f"   - {node.id}: type={node.type}, label={node.data.label}, pos=({node.position.x}, {node.position.y})")

    print("\n3. 执行验证逻辑...")
    validated = service._validate_incremental_result(original_nodes, ai_nodes)

    print("\n4. 验证后的节点:")
    for node in validated:
        print(f"   - {node.id}: type={node.type}, label={node.data.label}, pos=({node.position.x}, {node.position.y})")

    # 验证属性已恢复
    checks = [
        ("api-1 类型恢复", validated[0].type == "api"),
        ("api-1 标签恢复", validated[0].data.label == "API Gateway"),
        ("api-1 位置恢复", validated[0].position.x == 100 and validated[0].position.y == 100),
        ("service-1 类型恢复", validated[1].type == "service"),
        ("service-1 标签恢复", validated[1].data.label == "User Service")
    ]

    print("\n5. 属性恢复检查:")
    all_passed = True
    for check_name, passed in checks:
        status = "✓" if passed else "✗"
        print(f"   {status} {check_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print("\n✓ 节点属性保护测试通过\n")
        return True
    else:
        print("\n✗ 节点属性保护测试失败\n")
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("增量生成功能 - 单元测试套件")
    print("=" * 60 + "\n")

    results = []

    try:
        results.append(("会话管理器", test_session_manager()))
    except Exception as e:
        print(f"✗ 会话管理器测试异常: {str(e)}\n")
        import traceback
        traceback.print_exc()
        results.append(("会话管理器", False))

    try:
        results.append(("Prompt 构建", test_incremental_prompt_building()))
    except Exception as e:
        print(f"✗ Prompt 构建测试异常: {str(e)}\n")
        import traceback
        traceback.print_exc()
        results.append(("Prompt 构建", False))

    try:
        results.append(("验证逻辑", test_validation_logic()))
    except Exception as e:
        print(f"✗ 验证逻辑测试异常: {str(e)}\n")
        import traceback
        traceback.print_exc()
        results.append(("验证逻辑", False))

    try:
        results.append(("边合并", test_edge_merging()))
    except Exception as e:
        print(f"✗ 边合并测试异常: {str(e)}\n")
        import traceback
        traceback.print_exc()
        results.append(("边合并", False))

    try:
        results.append(("Prompt 复杂度约束", test_prompt_preserves_complexity()))
    except Exception as e:
        print(f"✗ Prompt 复杂度约束测试异常: {str(e)}\n")
        import traceback
        traceback.print_exc()
        results.append(("Prompt 复杂度约束", False))

    try:
        results.append(("节点属性保护", test_validate_preserves_node_attributes()))
    except Exception as e:
        print(f"✗ 节点属性保护测试异常: {str(e)}\n")
        import traceback
        traceback.print_exc()
        results.append(("节点属性保护", False))

    # 总结
    print("=" * 60)
    print("测试总结")
    print("=" * 60)

    for name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{status}: {name}")

    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)

    print(f"\n总计: {passed_count}/{total_count} 测试通过")

    if passed_count == total_count:
        print("\n✓ 所有测试通过!")
        return 0
    else:
        print("\n✗ 部分测试失败")
        return 1


if __name__ == "__main__":
    exit(main())
