"""
端到端测试：真实调用 AI 进行增量生成
比较生成前后的节点，验证是否有节点被删除
"""
import sys
import os
import asyncio
import logging
import io
import json

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.session_manager import get_session_manager
from app.services.chat_generator import ChatGeneratorService
from app.models.schemas import ChatGenerationRequest

logger = logging.getLogger(__name__)


def format_node(node):
    """格式化节点信息用于打印"""
    return f"{node.id:15s} | {node.type:15s} | {node.data.label:30s} | ({node.position.x:.0f}, {node.position.y:.0f})"


def format_edge(edge):
    """格式化边信息用于打印"""
    label = edge.label if edge.label else ""
    return f"{edge.id:10s} | {edge.source:15s} -> {edge.target:15s} | {label}"


async def test_real_incremental_generation():
    """端到端真实测试增量生成"""

    print("\n" + "=" * 100)
    print("端到端增量生成测试 - 真实 AI 调用")
    print("=" * 100 + "\n")

    service = ChatGeneratorService()
    session_manager = get_session_manager()

    # ==================== 步骤 1: 第一次生成（初始架构）====================
    print("步骤 1: 第一次生成 - 创建初始架构")
    print("-" * 100)

    request1 = ChatGenerationRequest(
        user_input="设计一个简单的电商系统架构，包含：Web前端、API网关、用户服务、订单服务、用户数据库、订单数据库",
        diagram_type="architecture",
        # 不指定 provider，使用默认配置
        incremental_mode=False,  # 第一次生成不启用增量模式
        session_id=None
    )

    print(f"用户输入: {request1.user_input}")
    print(f"增量模式: {request1.incremental_mode}")
    print("\n正在调用 AI 生成初始架构...")

    try:
        result1 = await service.generate_flowchart(request1)

        if not result1.success:
            print(f"\n✗ 生成失败: {result1.message}")
            return

        initial_nodes = result1.nodes
        initial_edges = result1.edges

        print(f"\n✓ 初始架构生成完成")
        print(f"  - 节点数: {len(initial_nodes)}")
        print(f"  - 边数: {len(initial_edges)}")
        print(f"  - Session ID: {result1.session_id}")

        print(f"\n初始节点列表:")
        print(f"{'ID':<15} | {'Type':<15} | {'Label':<30} | Position")
        print("-" * 100)
        for node in initial_nodes:
            print(format_node(node))

        print(f"\n初始边列表:")
        print(f"{'ID':<10} | {'Source':<15}    {'Target':<15} | Label")
        print("-" * 100)
        for edge in initial_edges:
            print(format_edge(edge))

    except Exception as e:
        print(f"\n✗ 第一次生成出错: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    # ==================== 步骤 2: 保存会话 ====================
    print("\n" + "=" * 100)
    print("步骤 2: 保存初始架构到会话")
    print("-" * 100)

    session_id = session_manager.create_or_update_session(None, initial_nodes, initial_edges)
    print(f"✓ 会话已创建: {session_id}")
    print(f"  - 保存节点数: {len(initial_nodes)}")
    print(f"  - 保存边数: {len(initial_edges)}")

    # 验证会话保存成功
    session_data = session_manager.get_session(session_id)
    if session_data:
        print(f"✓ 会话验证成功，可以加载")
    else:
        print(f"✗ 会话验证失败!")
        return

    # ==================== 步骤 3: 增量生成 ====================
    print("\n" + "=" * 100)
    print("步骤 3: 增量生成 - 追加新功能")
    print("-" * 100)

    request2 = ChatGenerationRequest(
        user_input="在用户服务和用户数据库之间、订单服务和订单数据库之间添加 Redis 缓存层",
        diagram_type="architecture",
        # 不指定 provider，使用默认配置
        incremental_mode=True,  # 启用增量模式
        session_id=session_id   # 传递会话 ID
    )

    print(f"用户输入: {request2.user_input}")
    print(f"增量模式: {request2.incremental_mode}")
    print(f"会话 ID: {request2.session_id}")
    print("\n正在调用 AI 进行增量生成...")

    try:
        result2 = await service.generate_flowchart(request2)

        if not result2.success:
            print(f"\n✗ 增量生成失败: {result2.message}")
            return

        final_nodes = result2.nodes
        final_edges = result2.edges

        print(f"\n✓ 增量生成完成")
        print(f"  - 节点数: {len(final_nodes)}")
        print(f"  - 边数: {len(final_edges)}")
        print(f"  - Session ID: {result2.session_id}")

        print(f"\n最终节点列表:")
        print(f"{'ID':<15} | {'Type':<15} | {'Label':<30} | Position")
        print("-" * 100)
        for node in final_nodes:
            print(format_node(node))

        print(f"\n最终边列表:")
        print(f"{'ID':<10} | {'Source':<15}    {'Target':<15} | Label")
        print("-" * 100)
        for edge in final_edges:
            print(format_edge(edge))

    except Exception as e:
        print(f"\n✗ 增量生成出错: {str(e)}")
        import traceback
        traceback.print_exc()
        session_manager.delete_session(session_id)
        return

    # ==================== 步骤 4: 对比分析 ====================
    print("\n" + "=" * 100)
    print("步骤 4: 对比分析 - 验证节点完整性")
    print("=" * 100)

    # 构建 ID 到节点的映射
    initial_node_map = {n.id: n for n in initial_nodes}
    final_node_map = {n.id: n for n in final_nodes}

    initial_ids = set(initial_node_map.keys())
    final_ids = set(final_node_map.keys())

    # 1. 检查删除的节点
    deleted_ids = initial_ids - final_ids
    if deleted_ids:
        print(f"\n⚠️ 删除的节点 ({len(deleted_ids)} 个):")
        print(f"{'ID':<15} | {'Type':<15} | {'Label':<30}")
        print("-" * 70)
        for node_id in deleted_ids:
            node = initial_node_map[node_id]
            print(f"{node.id:<15} | {node.type:<15} | {node.data.label:<30}")
    else:
        print(f"\n✓ 没有节点被删除")

    # 2. 检查新增的节点
    added_ids = final_ids - initial_ids
    if added_ids:
        print(f"\n✓ 新增的节点 ({len(added_ids)} 个):")
        print(f"{'ID':<15} | {'Type':<15} | {'Label':<30}")
        print("-" * 70)
        for node_id in added_ids:
            node = final_node_map[node_id]
            print(f"{node.id:<15} | {node.type:<15} | {node.data.label:<30}")
    else:
        print(f"\n⚠️ 没有新增节点")

    # 3. 检查修改的节点属性
    common_ids = initial_ids & final_ids
    modified_nodes = []

    for node_id in common_ids:
        initial_node = initial_node_map[node_id]
        final_node = final_node_map[node_id]

        changes = []

        if initial_node.data.label != final_node.data.label:
            changes.append(f"label: {initial_node.data.label} → {final_node.data.label}")

        if initial_node.type != final_node.type:
            changes.append(f"type: {initial_node.type} → {final_node.type}")

        pos_diff = abs(initial_node.position.x - final_node.position.x) + \
                   abs(initial_node.position.y - final_node.position.y)
        if pos_diff > 20:
            changes.append(
                f"position: ({initial_node.position.x}, {initial_node.position.y}) → "
                f"({final_node.position.x}, {final_node.position.y})"
            )

        if changes:
            modified_nodes.append((node_id, changes))

    if modified_nodes:
        print(f"\n⚠️ 修改的节点属性 ({len(modified_nodes)} 个):")
        for node_id, changes in modified_nodes:
            print(f"\n  {node_id}:")
            for change in changes:
                print(f"    - {change}")
    else:
        print(f"\n✓ 没有节点属性被修改")

    # 4. 边的对比
    initial_edge_sigs = {(e.source, e.target) for e in initial_edges}
    final_edge_sigs = {(e.source, e.target) for e in final_edges}

    deleted_edges = initial_edge_sigs - final_edge_sigs
    added_edges = final_edge_sigs - initial_edge_sigs

    if deleted_edges:
        print(f"\n⚠️ 删除的边 ({len(deleted_edges)} 个):")
        for src, tgt in deleted_edges:
            print(f"  {src} -> {tgt}")
    else:
        print(f"\n✓ 没有边被删除")

    if added_edges:
        print(f"\n✓ 新增的边 ({len(added_edges)} 个):")
        for src, tgt in added_edges:
            print(f"  {src} -> {tgt}")
    else:
        print(f"\n⚠️ 没有新增边")

    # ==================== 步骤 5: 总结 ====================
    print("\n" + "=" * 100)
    print("最终总结")
    print("=" * 100)

    print(f"\n初始架构:")
    print(f"  - 节点数: {len(initial_nodes)}")
    print(f"  - 边数: {len(initial_edges)}")

    print(f"\n最终架构:")
    print(f"  - 节点数: {len(final_nodes)}")
    print(f"  - 边数: {len(final_edges)}")

    print(f"\n变化:")
    print(f"  - 删除节点: {len(deleted_ids)}")
    print(f"  - 新增节点: {len(added_ids)}")
    print(f"  - 修改节点: {len(modified_nodes)}")
    print(f"  - 删除边: {len(deleted_edges)}")
    print(f"  - 新增边: {len(added_edges)}")

    # 判断增量生成是否成功
    success = (
        len(deleted_ids) == 0 and          # 没有删除节点
        len(modified_nodes) == 0 and       # 没有修改节点
        len(added_ids) > 0 and             # 有新增节点
        len(deleted_edges) == 0            # 没有删除边
    )

    if success:
        print(f"\n✓ 增量生成成功!")
        print(f"  - 所有原始节点保留完整")
        print(f"  - 成功添加了新节点")
        print(f"  - 没有破坏原有连接")
    else:
        print(f"\n⚠️ 增量生成有问题:")
        if len(deleted_ids) > 0:
            print(f"  - 有 {len(deleted_ids)} 个节点被删除")
        if len(modified_nodes) > 0:
            print(f"  - 有 {len(modified_nodes)} 个节点被修改")
        if len(added_ids) == 0:
            print(f"  - 没有新增节点")
        if len(deleted_edges) > 0:
            print(f"  - 有 {len(deleted_edges)} 条边被删除")

    # 清理会话
    print(f"\n清理会话 {session_id}...")
    session_manager.delete_session(session_id)
    print(f"✓ 会话已删除")

    return success


if __name__ == "__main__":
    try:
        result = asyncio.run(test_real_incremental_generation())
        if result:
            exit(0)
        else:
            exit(1)
    except KeyboardInterrupt:
        print("\n\n用户中断测试")
        exit(130)
    except Exception as e:
        print(f"\n\n测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)
