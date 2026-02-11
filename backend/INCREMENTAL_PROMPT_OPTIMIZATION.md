# Incremental Generation Prompt 优化报告

**日期**: 2026-02-09
**问题**: AI 增量生成时 JSON 响应被截断（1716 chars）
**根本原因**: Prompt 消耗过多 tokens，超出 Claude max_tokens 限制

---

## 问题诊断

### 原始问题
用户反馈增量生成失败，报错：
```
ValueError: Invalid JSON response from AI after all repair attempts
[CUSTOM TEXT] Raw AI response length: 1716 chars
[CUSTOM TEXT] Last 500 chars: ...  "data
```

AI 响应在 JSON 中途被截断，即使 `stop_reason: end_turn`（非 max_tokens）。

### 根本原因
通过 `verify_prompt_size.py` 诊断发现：

**Before 优化:**
- Prompt 总长度: 16,413 chars
- 预估 tokens: 8,206
- Claude max_tokens: 8,192
- **剩余给 AI 的 tokens: -14** ❌

Prompt 本身已经超出 max_tokens 限制，AI 根本没有空间生成响应！

---

## 优化措施

### 1. 修复 Claude max_tokens 限制 (ai_vision.py:2275)

**问题**: 代码设置 `max_tokens: 16384`，但 Claude Sonnet 3.5 的实际输出限制是 **8192 tokens**

**修复**:
```python
data = {
    "model": model_name,
    "max_tokens": 8192,  # Changed from 16384
    ...
}
```

### 2. 紧凑 JSON 格式 (chat_generator.py:1165-1183)

**问题**: 使用 `json.dumps(indent=2)` 生成 pretty-printed JSON，浪费大量空间

**Before** (Pretty-printed):
```json
{
  "nodes": [
    {
      "id": "api-1",
      "type": "api",
      "position": {
        "x": 100,
        "y": 100
      },
      "data": {
        "label": "API Gateway"
      }
    },
    ...
  ]
}
```
- 25 nodes: ~8,900 chars (~4,450 tokens)

**After** (Compact, 每个节点一行):
```json
{
  "nodes": [
    {"id":"api-1","type":"api","position":{"x":100,"y":100},"data":{"label":"API Gateway"}},
    ...
  ]
}
```
- 25 nodes: ~5,459 chars (~2,729 tokens)
- **节省: 3,441 chars (38.7%)**

**实现**:
```python
def _format_nodes_compact(self, nodes: List[Node], indent: int = 4) -> str:
    """每个节点一行，使用 separators=(',', ':') 去除空格"""
    indent_str = " " * indent
    lines = []
    for i, node in enumerate(nodes):
        node_json = json.dumps(node.model_dump(), ensure_ascii=False, separators=(',', ':'))
        comma = "," if i < len(nodes) - 1 else ""
        lines.append(f"{indent_str}{node_json}{comma}")
    return "\n".join(lines)
```

### 3. 删除冗余的自然语言描述 (chat_generator.py:1237-1239)

**问题**: Prompt 同时包含自然语言描述和完整 JSON，重复信息

**Before**:
```
**🔍 COMPACT JSON OF EXISTING ARCHITECTURE (FOR YOUR REFERENCE):**

### Current Architecture Overview

**Total**: 25 components, 24 connections

**Components by Type**:

API (2):
  - API Gateway (id: api-1)
  - Auth API (id: api-2)

SERVICE (5):
  - User Service (id: service-1)
  - Order Service (id: service-2)
  ...

**Connections** (24 total):
  - API Gateway → User Service
  - API Gateway → Order Service
  ...

**CRITICAL: YOUR OUTPUT MUST INCLUDE ALL 25 NODES BELOW:**
{JSON}
```

**After** (只保留 JSON):
```
**CRITICAL: YOUR OUTPUT MUST INCLUDE ALL 25 NODES BELOW (copy them EXACTLY):**
{JSON}

**⚠️ VALIDATION:** Output count MUST be > 25 (you must ADD at least 1 node)
```

**节省**: ~2,000+ chars (~1,000 tokens)

### 4. 压缩 Few-Shot 示例 (chat_generator.py:1274-1295)

**问题**: Few-Shot 示例用 5 节点详细展示正确/错误输出，占用大量空间

**Before** (5 nodes, pretty-printed):
```
**Example Scenario:**

Existing Architecture (5 nodes):
{完整 JSON 5 nodes}

User Request: "在服务和数据库之间添加Redis缓存层"

✅ CORRECT OUTPUT (ALL 5 existing nodes preserved + 2 new nodes added):
{完整 JSON 7 nodes，带详细注释}

Why this is correct:
- ✅ All 5 original nodes...
- ✅ 2 NEW nodes...
...

❌ WRONG OUTPUT (modifying existing node labels):
{完整 JSON 5 nodes，带错误示范}

Why this is wrong:
- ❌ Modified existing node labels...
- ❌ No NEW nodes...
...

KEY LESSON:
When user says "add X"...
```
- 长度: ~2,000 chars (~1,000 tokens)

**After** (3 nodes, minimal format):
```
**📚 FEW-SHOT EXAMPLE:**

Existing (3 nodes):
{minimal JSON, one line}

Request: "Add cache between service and DB"

✅ CORRECT (3 kept + 1 new = 4 total):
{minimal JSON, one line with ...}

❌ WRONG (modified labels, no new node):
{minimal JSON, one line}

**KEY:** "add" = CREATE new nodes, NOT modify labels.
```
- 长度: ~400 chars (~200 tokens)
- **节省: 1,600 chars (80%)**

### 5. 添加 Prompt 长度日志 (chat_generator.py:1807-1821)

**目的**: 实时监控 Prompt 的 token 消耗，便于诊断问题

**实现**:
```python
prompt_length = len(prompt)
estimated_tokens = prompt_length // 2
max_output_tokens = 8192
logger.warning(
    f"[PROMPT-LENGTH] Total: {prompt_length} chars "
    f"(~{estimated_tokens} tokens, max_output={max_output_tokens}, "
    f"leaves ~{max_output_tokens - estimated_tokens} tokens for AI response)"
)
```

**示例输出**:
```
[PROMPT-LENGTH] Total: 10880 chars (~5440 tokens, max_output=8192, leaves ~2752 tokens for AI response)
```

---

## 优化效果

### Token 消耗对比

| 项目 | Before | After | 节省 |
|------|--------|-------|------|
| Prompt 总长度 | 16,413 chars | 10,880 chars | -5,533 chars (-33.7%) |
| 预估 tokens | 8,206 | 5,440 | -2,766 tokens (-33.7%) |
| Claude max_tokens | 8,192 | 8,192 | - |
| **剩余 AI 可用 tokens** | **-14** ❌ | **+2,752** ✅ | **+2,766 tokens** |

### 各部分优化贡献

| 优化项 | 节省 tokens | 占比 |
|--------|-------------|------|
| 紧凑 JSON 格式 | ~1,720 | 62% |
| 删除自然语言描述 | ~1,000 | 36% |
| 压缩 Few-Shot 示例 | ~800 | 29% |
| **总计 (有重叠)** | **~2,766** | **100%** |

---

## 验证结果

### 验证脚本 (verify_prompt_size.py)

**测试条件**:
- 25 节点初始架构
- 24 条边
- 请求: "在服务层和数据库之间添加 Redis 缓存层"

**输出**:
```
JSON 格式大小对比
Pretty-printed:  8,900 chars  (~4,450 tokens)
Compact (1/line): 5,459 chars  (~2,729 tokens)
Minimal (no ws):  5,209 chars  (~2,604 tokens)

Compact 节省:  3,441 chars  (38.7%)

完整增量 Prompt 大小分析
测试架构: 23 节点, 24 条边

[Prompt 统计]
  - 总长度: 10,880 chars
  - 预估 tokens: 5,440
  - Claude max_tokens: 8,192
  - 剩余给 AI 的 tokens: 2,752

✅ 正常: 剩余 2,752 tokens 足够 AI 生成响应
```

### 预期效果

**Before 优化**:
- AI 无法生成响应（-14 tokens 剩余）
- JSON 被截断到 1716 chars
- 报错: `Invalid JSON response from AI`

**After 优化**:
- AI 有 2,752 tokens 生成空间
- 可以生成约 5,500 chars 的 JSON
- 足够包含 25 个原始节点 + 新增节点

---

## 文件修改清单

### 后端修改 (3 个文件)

| 文件 | 修改内容 | 行数 |
|------|----------|------|
| `backend/app/services/ai_vision.py` | 修复 Claude max_tokens: 16384 → 8192 | 2273-2284 |
| `backend/app/services/chat_generator.py` | 新增 `_format_nodes_compact()` 和 `_format_edges_compact()` | 1165-1183 |
| `backend/app/services/chat_generator.py` | 删除自然语言描述，使用紧凑 JSON | 1252-1270 |
| `backend/app/services/chat_generator.py` | 压缩 Few-Shot 示例 (5 nodes → 3 nodes) | 1274-1295 |
| `backend/app/services/chat_generator.py` | 添加 Prompt 长度日志 | 1807-1821 |

### 新增工具脚本

| 文件 | 用途 |
|------|------|
| `backend/verify_prompt_size.py` | 验证 Prompt 大小和 token 消耗 |

---

## 后续建议

### 短期 (本次修复)
1. ✅ 已完成: 修复 max_tokens 限制
2. ✅ 已完成: 紧凑 JSON 格式
3. ✅ 已完成: 删除冗余描述
4. ✅ 已完成: 压缩 Few-Shot 示例
5. ⏳ 待执行: 运行 E2E 测试验证实际效果

### 中期优化（如果仍有问题）
1. **动态 Few-Shot 示例**: 根据现有节点数量调整示例大小
   - < 10 nodes: 完整示例
   - 10-20 nodes: 简化示例
   - > 20 nodes: 最小示例或移除

2. **分段 Prompt**: 对于超大架构（50+ nodes），考虑：
   - 只发送关键节点（hub nodes）
   - 或分批处理（先添加到小范围，再合并）

3. **自适应 max_tokens**: 根据 Prompt 长度动态调整
   ```python
   max_output_tokens = min(8192, context_window - prompt_tokens - 500)
   ```

### 长期优化
1. **使用 Claude Opus 4.5**: 更大的 context window (200K → 实际可能更高)
2. **Two-Stage Generation**: 先生成节点列表，再生成完整 JSON
3. **Diff-based Output**: AI 只返回新增节点，后端合并（见 diff-based-feasibility-analysis.md）

---

## 附录：关键代码片段

### 紧凑 JSON 格式化

```python
def _format_nodes_compact(self, nodes: List[Node], indent: int = 4) -> str:
    """将节点列表格式化为紧凑的 JSON（每个节点一行，节省 tokens）"""
    indent_str = " " * indent
    lines = []
    for i, node in enumerate(nodes):
        node_json = json.dumps(node.model_dump(), ensure_ascii=False, separators=(',', ':'))
        comma = "," if i < len(nodes) - 1 else ""
        lines.append(f"{indent_str}{node_json}{comma}")
    return "\n".join(lines)
```

### Prompt 长度监控

```python
# 🔍 DEBUG: Log prompt length to diagnose token consumption
prompt_length = len(prompt)
estimated_tokens = prompt_length // 2  # Conservative estimate
max_output_tokens = 8192  # Claude Sonnet 3.5 limit
logger.warning(
    f"[PROMPT-LENGTH] Total: {prompt_length} chars "
    f"(~{estimated_tokens} tokens, max_output={max_output_tokens}, "
    f"leaves ~{max_output_tokens - estimated_tokens} tokens for AI response)"
)
```

---

## 总结

**问题**: Prompt 过长（16,413 chars）超出 Claude max_tokens (8,192)，AI 无法生成响应

**解决方案**:
1. 修复 max_tokens 配置（16384 → 8192）
2. 紧凑 JSON 格式（节省 38.7%）
3. 删除冗余自然语言描述
4. 压缩 Few-Shot 示例（节省 80%）
5. 添加实时 Prompt 长度监控

**效果**: Prompt 大小从 16,413 → 10,880 chars (-33.7%)，剩余 tokens 从 -14 → +2,752 ✅

**状态**: ✅ 已优化，等待 E2E 测试验证

---

**文档版本**: v1.0
**最后更新**: 2026-02-09
**作者**: Claude Code
**相关文档**: `INCREMENTAL_GENERATION_TEST_REPORT.md`, `diff-based-feasibility-analysis.md`
