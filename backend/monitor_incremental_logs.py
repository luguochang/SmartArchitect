"""
实时日志查看脚本 - 帮助诊断增量生成问题
在启动后端后运行这个脚本，它会实时显示增量生成相关的日志
"""
import sys
import time
import re
from pathlib import Path

# 定义关键日志模式
LOG_PATTERNS = {
    "增量模式启用": r"\[INCREMENTAL\] Incremental mode enabled",
    "加载会话": r"\[INCREMENTAL\] Loaded (\d+) nodes, (\d+) edges",
    "构建增量Prompt": r"\[INCREMENTAL\] Building incremental prompt",
    "验证合并": r"\[INCREMENTAL\] Validating and merging",
    "合并结果": r"\[INCREMENTAL\] After merge: (\d+) nodes \(\+(\d+) new\), (\d+) edges \(\+(\d+) new\)",
    "节点删除": r"WARNING.*AI deleted (\d+) nodes: (.*), restoring them",
    "节点修改": r"WARNING.*Node (label|type|position) changed: (.*), reverting",
    "边删除": r"WARNING.*AI deleted (\d+) edges: (.*), restoring them",
}

def parse_log_line(line):
    """解析日志行，提取关键信息"""
    results = {}

    for pattern_name, pattern in LOG_PATTERNS.items():
        match = re.search(pattern, line)
        if match:
            results[pattern_name] = match.groups() if match.groups() else True

    return results

def monitor_logs():
    """监控日志输出"""
    print("=" * 100)
    print("增量生成日志监控")
    print("=" * 100)
    print("\n等待日志输出...\n")
    print("请在前端执行增量生成操作，日志会实时显示在这里\n")

    # 统计信息
    stats = {
        "增量生成次数": 0,
        "节点删除次数": 0,
        "节点修改次数": 0,
        "边删除次数": 0,
    }

    current_generation = None

    try:
        for line in sys.stdin:
            line = line.strip()

            # 解析日志
            parsed = parse_log_line(line)

            if "增量模式启用" in parsed:
                stats["增量生成次数"] += 1
                current_generation = {
                    "initial_nodes": 0,
                    "initial_edges": 0,
                    "final_nodes": 0,
                    "final_edges": 0,
                    "deleted_nodes": [],
                    "modified_nodes": [],
                    "deleted_edges": []
                }
                print("\n" + "=" * 100)
                print(f"🔄 增量生成 #{stats['增量生成次数']} 开始")
                print("=" * 100)

            if "加载会话" in parsed:
                node_count, edge_count = parsed["加载会话"]
                if current_generation:
                    current_generation["initial_nodes"] = int(node_count)
                    current_generation["initial_edges"] = int(edge_count)
                print(f"✓ 加载现有架构: {node_count} 个节点, {edge_count} 条边")

            if "构建增量Prompt" in parsed:
                print(f"✓ 正在构建增量 Prompt（包含 DO NOT SIMPLIFY 约束）")

            if "验证合并" in parsed:
                print(f"✓ 正在验证 AI 返回结果并合并...")

            if "节点删除" in parsed:
                count, nodes = parsed["节点删除"]
                stats["节点删除次数"] += int(count)
                if current_generation:
                    current_generation["deleted_nodes"].append(nodes)
                print(f"⚠️  AI 删除了 {count} 个节点: {nodes}")
                print(f"   🔧 自动恢复中...")

            if "节点修改" in parsed:
                attr_type, detail = parsed["节点修改"]
                stats["节点修改次数"] += 1
                if current_generation:
                    current_generation["modified_nodes"].append(f"{attr_type}: {detail}")
                print(f"⚠️  AI 修改了节点 {attr_type}: {detail[:80]}")
                print(f"   🔧 自动还原中...")

            if "边删除" in parsed:
                count, edges = parsed["边删除"]
                stats["边删除次数"] += int(count)
                if current_generation:
                    current_generation["deleted_edges"].append(edges)
                print(f"⚠️  AI 删除了 {count} 条边: {edges}")
                print(f"   🔧 自动恢复中...")

            if "合并结果" in parsed:
                total_nodes, new_nodes, total_edges, new_edges = parsed["合并结果"]
                if current_generation:
                    current_generation["final_nodes"] = int(total_nodes)
                    current_generation["final_edges"] = int(total_edges)

                print(f"\n✓ 合并完成:")
                print(f"   节点: {current_generation['initial_nodes']} → {total_nodes} (+{new_nodes} 新增)")
                print(f"   边:   {current_generation['initial_edges']} → {total_edges} (+{new_edges} 新增)")

                # 显示问题总结
                if current_generation["deleted_nodes"] or current_generation["modified_nodes"] or current_generation["deleted_edges"]:
                    print(f"\n⚠️  本次生成中 AI 的错误:")
                    if current_generation["deleted_nodes"]:
                        print(f"   - 删除了 {len(current_generation['deleted_nodes'])} 批节点（已恢复）")
                    if current_generation["modified_nodes"]:
                        print(f"   - 修改了 {len(current_generation['modified_nodes'])} 个节点属性（已还原）")
                    if current_generation["deleted_edges"]:
                        print(f"   - 删除了 {len(current_generation['deleted_edges'])} 批边（已恢复）")
                    print(f"\n✅ 验证逻辑已自动修复所有问题")
                else:
                    print(f"\n✅ 本次生成无问题，AI 遵守了所有约束")

                # 检查是否真的新增了节点
                new_node_count = int(new_nodes)
                if new_node_count == 0:
                    print(f"\n❌ 警告: 没有新增节点！AI 可能只是重新生成了现有架构")
                elif new_node_count < 0:
                    print(f"\n❌ 严重警告: 节点数量减少了！验证逻辑可能失效")

    except KeyboardInterrupt:
        print("\n\n" + "=" * 100)
        print("监控结束 - 统计信息")
        print("=" * 100)
        print(f"增量生成次数: {stats['增量生成次数']}")
        print(f"节点删除次数: {stats['节点删除次数']}")
        print(f"节点修改次数: {stats['节点修改次数']}")
        print(f"边删除次数:   {stats['边删除次数']}")
        print("\n按 Ctrl+C 退出")

if __name__ == "__main__":
    print("""
使用方法:
1. 启动后端: cd backend && venv\\Scripts\\python.exe -m app.main 2>&1 | python monitor_incremental_logs.py
2. 在前端执行增量生成操作
3. 观察日志输出，查看验证逻辑是否工作

或者手动复制后台日志，粘贴到这里（Ctrl+D 结束输入）
""")
    monitor_logs()
