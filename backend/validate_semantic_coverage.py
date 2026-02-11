"""
语义内容验证脚本 - 检测 AI 是否删除或简化了架构内容
不仅比对节点ID和数量，还比对节点的语义内容
"""
import sys
import os
import io

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.schemas import Node, Edge, Position, NodeData
from typing import List, Set, Dict
import re


def extract_semantic_keywords(label: str) -> Set[str]:
    """从节点label提取关键语义词"""
    # 移除常见修饰词
    noise_words = {'service', 'module', 'layer', 'system', 'component',
                   '服务', '模块', '层', '系统', '组件', 'api', 'db', 'database'}

    # 分词（简单实现）
    words = set()

    # 英文分词
    for word in re.findall(r'[A-Za-z]+', label.lower()):
        if word not in noise_words and len(word) > 2:
            words.add(word)

    # 中文分词（提取连续中文字符）
    for word in re.findall(r'[\u4e00-\u9fff]+', label):
        if word not in noise_words and len(word) >= 2:
            words.add(word)

    return words


def analyze_semantic_coverage(
    original_nodes: List[Node],
    final_nodes: List[Node]
) -> Dict:
    """分析语义覆盖率 - 检测是否有内容丢失"""

    # 1. 提取所有原始节点的语义关键词
    original_keywords = {}
    original_keyword_set = set()

    for node in original_nodes:
        keywords = extract_semantic_keywords(node.data.label)
        original_keywords[node.id] = {
            'label': node.data.label,
            'keywords': keywords
        }
        original_keyword_set.update(keywords)

    print(f"\n原始架构语义关键词:")
    print(f"  总关键词数: {len(original_keyword_set)}")
    print(f"  关键词列表: {sorted(original_keyword_set)}")

    # 2. 提取最终节点的语义关键词
    final_keywords = {}
    final_keyword_set = set()

    for node in final_nodes:
        keywords = extract_semantic_keywords(node.data.label)
        final_keywords[node.id] = {
            'label': node.data.label,
            'keywords': keywords
        }
        final_keyword_set.update(keywords)

    print(f"\n最终架构语义关键词:")
    print(f"  总关键词数: {len(final_keyword_set)}")
    print(f"  关键词列表: {sorted(final_keyword_set)}")

    # 3. 计算语义丢失
    lost_keywords = original_keyword_set - final_keyword_set
    new_keywords = final_keyword_set - original_keyword_set

    print(f"\n语义变化分析:")
    print(f"  丢失的关键词 ({len(lost_keywords)}): {sorted(lost_keywords)}")
    print(f"  新增的关键词 ({len(new_keywords)}): {sorted(new_keywords)}")

    # 4. 找出哪些原始节点的语义丢失了
    lost_semantic_nodes = []

    for node_id, info in original_keywords.items():
        node_keywords = info['keywords']
        # 检查这个节点的关键词是否在最终架构中存在
        if node_keywords and not node_keywords.intersection(final_keyword_set):
            lost_semantic_nodes.append({
                'id': node_id,
                'label': info['label'],
                'keywords': node_keywords
            })

    if lost_semantic_nodes:
        print(f"\n⚠️  语义完全丢失的节点 ({len(lost_semantic_nodes)} 个):")
        for node_info in lost_semantic_nodes:
            print(f"  - {node_info['label']} (关键词: {node_info['keywords']})")
            print(f"    → 这些概念在最终架构中完全消失了！")

    # 5. 检测节点被拆分的情况
    print(f"\n检测节点拆分:")
    for orig_id, orig_info in original_keywords.items():
        # 找出最终架构中包含相同关键词的节点
        matching_nodes = []
        for final_id, final_info in final_keywords.items():
            if orig_info['keywords'].intersection(final_info['keywords']):
                matching_nodes.append(final_info['label'])

        if len(matching_nodes) > 1:
            print(f"  '{orig_info['label']}' 可能被拆分为:")
            for match in matching_nodes:
                print(f"    - {match}")

    # 6. 计算语义覆盖率
    coverage = len(final_keyword_set.intersection(original_keyword_set)) / len(original_keyword_set) if original_keyword_set else 0

    print(f"\n语义覆盖率: {coverage * 100:.1f}%")

    if coverage < 0.8:
        print(f"❌ 警告: 语义覆盖率低于80%，可能有大量内容丢失！")
    elif coverage < 0.95:
        print(f"⚠️  注意: 语义覆盖率低于95%，有部分内容丢失")
    else:
        print(f"✓ 语义覆盖良好")

    return {
        'original_keywords': original_keyword_set,
        'final_keywords': final_keyword_set,
        'lost_keywords': lost_keywords,
        'new_keywords': new_keywords,
        'lost_semantic_nodes': lost_semantic_nodes,
        'coverage': coverage
    }


def validate_architectural_complexity(
    original_nodes: List[Node],
    final_nodes: List[Node]
) -> bool:
    """验证架构复杂度是否保持或增加"""

    print("\n" + "=" * 80)
    print("架构复杂度验证")
    print("=" * 80)

    # 1. 节点数量检查
    print(f"\n节点数量:")
    print(f"  原始: {len(original_nodes)}")
    print(f"  最终: {len(final_nodes)}")
    print(f"  变化: {'+' if len(final_nodes) >= len(original_nodes) else ''}{len(final_nodes) - len(original_nodes)}")

    if len(final_nodes) < len(original_nodes):
        print(f"  ❌ 节点数量减少了！")
        return False

    # 2. 节点类型多样性检查
    original_types = {n.type for n in original_nodes if n.type}
    final_types = {n.type for n in final_nodes if n.type}

    print(f"\n节点类型多样性:")
    print(f"  原始类型: {len(original_types)} 种 - {sorted(original_types)}")
    print(f"  最终类型: {len(final_types)} 种 - {sorted(final_types)}")

    lost_types = original_types - final_types
    if lost_types:
        print(f"  ⚠️  丢失的类型: {lost_types}")

    # 3. 语义内容检查（最重要）
    semantic_analysis = analyze_semantic_coverage(original_nodes, final_nodes)

    # 4. 综合判断
    print(f"\n" + "=" * 80)
    print("验证结果")
    print("=" * 80)

    issues = []

    if len(final_nodes) < len(original_nodes):
        issues.append("节点数量减少")

    if semantic_analysis['lost_semantic_nodes']:
        issues.append(f"{len(semantic_analysis['lost_semantic_nodes'])} 个节点的语义完全丢失")

    if semantic_analysis['coverage'] < 0.8:
        issues.append(f"语义覆盖率过低 ({semantic_analysis['coverage'] * 100:.1f}%)")

    if issues:
        print(f"\n❌ 增量生成失败，发现以下问题:")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        print(f"\n这说明 AI 简化了架构，没有真正追加内容！")
        return False
    else:
        print(f"\n✓ 增量生成成功")
        print(f"  - 节点数量增加了 {len(final_nodes) - len(original_nodes)} 个")
        print(f"  - 语义覆盖率: {semantic_analysis['coverage'] * 100:.1f}%")
        print(f"  - 新增关键词: {len(semantic_analysis['new_keywords'])} 个")
        return True


def test_semantic_validation():
    """测试语义验证逻辑"""

    print("\n" + "=" * 80)
    print("测试场景: AI 删除了部分服务，只细化了一个服务")
    print("=" * 80)

    # 原始架构
    original_nodes = [
        Node(id="api-1", type="api", position=Position(x=100, y=100),
             data=NodeData(label="API Gateway")),
        Node(id="service-1", type="service", position=Position(x=300, y=100),
             data=NodeData(label="User Service")),
        Node(id="service-2", type="service", position=Position(x=300, y=200),
             data=NodeData(label="Order Service")),
        Node(id="service-3", type="service", position=Position(x=300, y=300),
             data=NodeData(label="Payment Service")),
        Node(id="db-1", type="database", position=Position(x=500, y=100),
             data=NodeData(label="User Database")),
        Node(id="db-2", type="database", position=Position(x=500, y=200),
             data=NodeData(label="Order Database")),
    ]

    # AI "追加" 后的架构 - 删除了 Order Service 和 Payment Service，细化了 User Service
    final_nodes = [
        Node(id="api-1", type="api", position=Position(x=100, y=100),
             data=NodeData(label="API Gateway")),
        Node(id="service-1", type="service", position=Position(x=300, y=80),
             data=NodeData(label="User Service - Login Module")),
        Node(id="service-1-2", type="service", position=Position(x=300, y=120),
             data=NodeData(label="User Service - Registration Module")),
        Node(id="service-1-3", type="service", position=Position(x=300, y=160),
             data=NodeData(label="User Service - Profile Module")),
        Node(id="cache-1", type="cache", position=Position(x=400, y=100),
             data=NodeData(label="Redis Cache")),
        Node(id="db-1", type="database", position=Position(x=500, y=100),
             data=NodeData(label="User Database")),
        Node(id="db-2", type="database", position=Position(x=500, y=200),
             data=NodeData(label="Order Database")),
    ]

    # 执行验证
    result = validate_architectural_complexity(original_nodes, final_nodes)

    return result


if __name__ == "__main__":
    success = test_semantic_validation()
    exit(0 if success else 1)
