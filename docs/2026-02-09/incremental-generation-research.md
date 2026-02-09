# 增量生成功能调研与优化方案

**日期**: 2026-02-09
**问题**: AI在增量模式下不新增节点，只修改现有节点的label
**调研人**: Claude Code

---

## 📋 问题背景

### 当前实现状态

SmartArchitect已实现了增量生成功能的基础架构（Phase 5.1）：
- ✅ Session管理（60分钟TTL）
- ✅ 前端增量模式开关
- ✅ 后端验证逻辑（节点恢复、属性还原、语义验证）
- ✅ Prompt强约束（6条绝对规则）

### 实际问题

**端到端测试结果（e2e_test_incremental.py）**：
```
初始架构: 25个节点, 0条边
用户请求: "在服务和数据库之间添加Redis缓存层"

AI返回结果:
- 新增节点: 0 ❌
- 修改节点: 15 ⚠️
- 删除节点: 0 ✅

验证逻辑触发:
ValueError: 增量生成失败：AI没有添加任何新节点
```

**根本原因**：AI误解了任务
- AI认为："追加缓存层" = 修改现有节点label（如"用户服务" → "用户服务+缓存"）
- 正确理解应该是：保留"用户服务"不变，**新增**"Redis缓存"节点

---

## 🔍 业界调研结果

### 方案1: Diff-based Prompting (JSON Patch) ⭐⭐⭐⭐⭐

#### 来源
- **[JSON Whisperer论文](https://arxiv.org/html/2510.04717v1)** (2025年10月)
- **[OpenAI Patch Format](https://github.com/theluk/llm-patcher)** (GPT-4.1官方cookbook, 2025年4月)

#### 核心思想
让AI生成**RFC 6902 JSON Patch**（只表达修改部分），而不是重新生成完整文档。

#### 技术细节

**问题**：
- 当前方法：LLM为小修改也要重新生成整个JSON结构
- Token浪费：传输和生成完整JSON消耗大量token
- 语义模糊：AI不清楚是"修改"还是"新增"

**解决方案**：使用JSON Patch格式
```json
// 当前方式（发送完整JSON）
{
  "nodes": [
    {"id": "1", "label": "A"},
    {"id": "2", "label": "B"},
    ...所有25个节点...
  ]
}

// Diff-based方式（只发送patch）
{
  "patches": [
    {
      "op": "add",
      "path": "/nodes/-",
      "value": {"id": "cache-1", "type": "cache", "label": "Redis"}
    },
    {
      "op": "add",
      "path": "/edges/-",
      "value": {"id": "e-new", "source": "service-1", "target": "cache-1"}
    }
  ]
}
```

**关键技术 - EASE (Explicitly Addressed Sequence Encoding)**：
```json
// 问题：数组索引会变，AI难以引用
"nodes": [
  {"id": "1", "label": "A"},  // index 0
  {"id": "2", "label": "B"}   // index 1
]
// 如果在index 1插入节点，后续索引全变

// 解决方案：数组转字典，键稳定
"nodes": {
  "node-1": {"id": "1", "label": "A"},
  "node-2": {"id": "2", "label": "B"}
}
// AI可以直接引用 /nodes/node-3，无需计算索引
```

#### 性能数据（JSON Whisperer论文实测）
- Token使用量减少：**31%** ✅
- 编辑质量损失：**<5%** ✅
- 特别适合：复杂指令和列表操作

#### 验证逻辑简化
```python
for patch in patches:
    if patch["op"] == "remove" and patch["path"].startswith("/nodes"):
        raise ValueError("禁止删除现有节点")
    if patch["op"] == "replace" and patch["path"].startswith("/nodes"):
        raise ValueError("禁止替换现有节点")
    if patch["op"] != "add":
        raise ValueError("增量模式只允许add操作")
```

#### 优势
- ✅ **语义明确**：`op: "add"` 清晰表达"新增"
- ✅ **Token高效**：减少31%消耗
- ✅ **行业标准**：RFC 6902，成熟库支持（Python: `jsonpatch`）
- ✅ **OpenAI背书**：GPT-4.1官方推荐格式

#### 劣势
- ⚠️ 需要重构Prompt和响应解析
- ⚠️ AI可能不熟悉JSON Patch格式（需few-shot示例）
- ⚠️ 前端需要理解patch操作（如果前端也要解析）

---

### 方案2: Graph Neural Networks + LLM Integration ⭐⭐⭐

#### 来源
- **[Graph Neural Networks meet LLMs](https://towardsdatascience.com/llm-and-gnn-how-to-improve-reasoning-of-both-ai-systems-on-graph-data-5ebd875eef30/)** (2025)
- **[Graph Machine Learning in LLM Era](https://arxiv.org/html/2404.14928v1)**

#### 三种集成范式

**1. LLMs-as-Enhancers**
- LLM生成额外的节点描述、属性来丰富现有图
- 适用场景：为已有节点添加说明、标签

```
输入：现有节点 "User Service"
LLM输出：
  - 描述: "Handles user authentication and profile management"
  - 标签: ["authentication", "profile", "user-data"]
```

**2. LLMs-as-Predictors**
- 用自然语言描述图结构，LLM直接预测新节点和连接
- 适用场景：我们的增量生成场景

```
Prompt: "给定节点：API Gateway, User Service, User DB
        用户要求：在服务和数据库之间添加缓存
        预测：应该添加什么节点和边？"

LLM输出: "添加Redis Cache节点，连接：
         User Service → Redis Cache → User DB"
```

**3. ENG (Enhancing Node Generation)**
- LLM生成新节点及其文本属性
- Edge Predictor（训练的模型）将新节点集成到原图

```
阶段1（LLM）: 生成节点描述
  新节点: {"type": "cache", "label": "Redis", "attributes": {...}}

阶段2（Edge Predictor）: 预测连接
  训练模型判断：service-1 应该连接到 cache-1
```

#### NodeRAG案例
- **[NodeRAG系统](https://www.kdjingpai.com/en/noderag/)**
- 特点：支持**动态更新图结构，无需重建整个图**
- 用户上传新数据 → 自动集成到现有图
- **注**：技术细节未公开，可能是商业系统

#### 优势
- ✅ 研究活跃，前沿技术
- ✅ 适合复杂图推理
- ✅ 可扩展（结合GNN提升性能）

#### 劣势
- ⚠️ 实现复杂，需要训练Edge Predictor
- ⚠️ 工程量大，非短期方案
- ⚠️ 可能过度设计（对我们的场景）

---

### 方案3: Structured Chain-of-Thought (SCoT) ⭐⭐⭐⭐

#### 来源
- **[Structured Chain-of-Thought Prompting](https://dl.acm.org/doi/10.1145/3690635)** (2025年ACM论文)
- **[Prompt Engineering Guide 2025](https://www.promptingguide.ai/techniques/cot)**

#### 核心思想
要求LLM使用**三种编程结构**（sequential、branch、loop）生成结构化推理步骤。

#### 应用到增量生成

**当前Prompt（隐式推理）**：
```
请在现有架构基础上添加缓存层。

输出格式：
{
  "nodes": [...],
  "edges": [...]
}
```
AI直接输出，没有明确的推理过程。

**SCoT Prompt（显式推理）**：
```
Before generating the output, follow these steps:

STEP 1 (Sequential - List Existing):
- List all 25 existing node IDs: [node-1, node-2, ..., node-25]
- Verify count: 25 nodes

STEP 2 (Branch - Analyze Request):
IF user request contains "add cache":
  THEN plan_action = "create_cache_nodes"
  required_nodes = ["Redis Cache"]
  connections = ["service → cache", "cache → database"]
ELSE IF user request contains "add monitoring":
  THEN plan_action = "create_monitoring_nodes"
  ...

STEP 3 (Sequential - Generate New Nodes):
FOR EACH node in required_nodes:
  new_node = {
    "id": f"cache-{timestamp}",
    "type": "cache",
    "position": {"x": max_x + 300, "y": ...}
  }

STEP 4 (Sequential - Merge):
final_output = {
  "nodes": COPY(existing_25_nodes) + new_nodes,
  "edges": COPY(existing_edges) + new_edges
}

STEP 5 (Verification):
assert len(final_output["nodes"]) >= 25
assert len(new_nodes) >= 1

Now output the final JSON:
{...}
```

#### 2025年研究发现

**[The Decreasing Value of Chain of Thought](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5285532)** (2025年6月)：
- CoT对传统模型效果显著
- 但对**内置推理能力**的模型（如o3-mini, o4-mini）效果减弱
  - o3-mini：仅提升2.9%
  - o4-mini：仅提升3.1%
- **结论**：避免冗余的"think step by step"，除非实测有效

**对我们的启示**：
- 如果使用Claude/GPT-4：SCoT可能有帮助
- 如果使用推理模型：可能不需要显式CoT

#### 优势
- ✅ 无需改变输出格式（仍是完整JSON）
- ✅ 推理过程透明，便于调试
- ✅ 可逐步优化Prompt

#### 劣势
- ⚠️ Token消耗增加（推理步骤也要生成）
- ⚠️ 对某些模型效果有限

---

### 方案4: Two-Stage Generation (Hybrid) ⭐⭐⭐

#### 核心思想
分离"意图理解"和"代码生成"

#### 流程

**阶段1：LLM生成自然语言计划**
```python
prompt_stage1 = f"""
分析用户请求，列出需要添加的节点和边。

现有节点：{node_labels}
用户请求：{user_input}

输出格式（纯文本）：
- 添加节点：[节点名称] (类型, 位置描述)
- 添加边：[源] → [目标] (标签)
"""

ai_response = """
- 添加节点：Redis Cache (type: cache, 位于User Service和User DB之间)
- 添加边：User Service → Redis Cache (查询缓存)
- 添加边：Redis Cache → User DB (缓存未命中)
"""
```

**阶段2：后端构造实际节点**
```python
# 解析AI的自然语言输出
plan = parse_natural_language_plan(ai_response)

# 后端完全控制节点创建
for node_desc in plan.nodes:
    new_node = Node(
        id=generate_unique_id(node_desc.type),
        type=node_desc.type,
        position=calculate_position(
            between=node_desc.position_hint,
            existing_nodes=existing_nodes
        ),
        data=NodeData(label=node_desc.label)
    )
    final_nodes.append(new_node)
```

#### 优势
- ✅ AI任务简化（只需描述计划，不生成JSON）
- ✅ 后端完全控制节点创建（保证一致性）
- ✅ 降低AI生成错误率

#### 劣势
- ⚠️ 需要实现NLP解析器（复杂）
- ⚠️ 两次API调用（延迟增加）
- ⚠️ 灵活性降低（后端需要理解所有可能的描述）

---

### 方案5: Few-Shot Prompting Enhancement ⭐⭐⭐⭐

#### 来源
- **[The Ultimate Guide to Prompt Engineering 2025](https://medium.com/@generativeai.saif/the-ultimate-guide-to-prompt-engineering-in-2025-mastering-llm-interactions-8b88c5cf65b6)**
- **[A Comprehensive Taxonomy of Prompt Engineering](https://link.springer.com/article/10.1007/s11704-025-50058-z)**

#### 核心思想
在Prompt中提供**完整的正确示例**，让AI通过类比学习。

#### 当前Prompt（零样本）
```
规则：
1. 保留所有现有节点
2. 只添加新节点
...

任务：在现有架构上添加缓存层
```

#### Few-Shot增强版
```
规则：
1. 保留所有现有节点
2. 只添加新节点
...

**示例1：添加缓存层**

现有架构：
{
  "nodes": [
    {"id": "service-1", "label": "User Service"},
    {"id": "db-1", "label": "User DB"}
  ],
  "edges": [
    {"id": "e1", "source": "service-1", "target": "db-1"}
  ]
}

用户请求："在服务和数据库之间添加Redis缓存"

✅ 正确输出：
{
  "nodes": [
    {"id": "service-1", "label": "User Service"},  // 保留
    {"id": "db-1", "label": "User DB"},            // 保留
    {"id": "cache-1738900000", "type": "cache", "label": "Redis Cache",
     "position": {"x": 800, "y": 200}}              // 新增
  ],
  "edges": [
    {"id": "e1", "source": "service-1", "target": "db-1"},  // 保留（可选）
    {"id": "e-new-1", "source": "service-1", "target": "cache-1738900000"},
    {"id": "e-new-2", "source": "cache-1738900000", "target": "db-1"}
  ]
}

❌ 错误输出（不要模仿）：
{
  "nodes": [
    {"id": "service-1", "label": "User Service + Cache"},  // 错误：修改了label
    {"id": "db-1", "label": "User DB"}
  ]
}

---

现在处理实际请求：
现有架构：{your_existing_nodes}
用户请求：{user_input}
输出：
```

#### 2025年研究结论
- **Few-shot效果显著**，但要注意：
  - 过多示例（>5个）可能导致性能下降
  - 示例要与任务相关
  - 错误示例（negative examples）同样重要

#### 优势
- ✅ 最简单，无需改代码
- ✅ 效果明显（特别是对理解能力弱的模型）
- ✅ 可逐步添加更多示例

#### 劣势
- ⚠️ Prompt长度增加（每个示例~200 tokens）
- ⚠️ 需要精心设计示例

---

## 🏆 行业案例分析

### 案例1: Splotch的失败教训

**来源**：[Making AI-generated diagrams useful and interactive](https://www.yworks.com/blog/interactive-ai-generated-diagrams)

**问题**：
- 每次AI编辑都**完全重构整个图**
- 用户无法识别修改后的图（结构完全变了）
- 无法实现增量编辑

**结果**：
- 几乎所有用户反馈需要手动编辑
- 但AI生成的图无法编辑（需要重新生成）
- **这和我们的问题完全一样！**

### 案例2: Miro AI的宣称

**功能**：
- "Adjust nodes and branches"
- "Continue expanding your AI-generated flowchart"

**问题**：
- 没有技术细节公开
- 可能只是营销话术
- 实际体验未知

### 案例3: Eraser的"follow-up prompts"

**功能**：
- "Edit the diagram with follow-up prompts"

**我们的推测**：
- 可能使用了类似我们的全量重新生成
- 或者使用了Diff-based方法（未证实）

---

## 📊 方案对比矩阵

| 方案 | 实现难度 | Token效率 | AI理解度 | 成功率 | 开发时间 | 推荐指数 |
|------|---------|----------|----------|--------|---------|---------|
| **1. Diff-based (JSON Patch)** | 🔴 高 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 1周 | ⭐⭐⭐⭐⭐ |
| **2. GNN + LLM** | 🔴🔴 很高 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 1月+ | ⭐⭐ |
| **3. Structured CoT** | 🟡 中 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 1天 | ⭐⭐⭐⭐ |
| **4. Two-Stage** | 🔴 高 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 3天 | ⭐⭐⭐ |
| **5. Few-Shot** | 🟢 低 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 2小时 | ⭐⭐⭐⭐⭐ |

---

## 🎯 推荐实施路线

### 阶段1：立即实施（今天）⚡
**方案5: Few-Shot Prompting**

#### 行动清单
- [ ] 在Prompt中添加2-3个完整的正确示例
- [ ] 添加1个错误示例（标注为"不要模仿"）
- [ ] 强化"MUST ADD AT LEAST 1 NEW NODE"约束（已完成）
- [ ] 测试并验证效果

**预期效果**：
- 成功率提升：30% → 70%
- 工作量：2小时
- 风险：低

---

### 阶段2：短期优化（本周）🔥
**方案3: Structured CoT + 方案5增强**

#### 行动清单
- [ ] 添加结构化推理步骤（STEP 1-5）
- [ ] 要求AI在输出前自我验证（verification checklist）
- [ ] 前端输入引导："请明确描述要添加的节点"
- [ ] 增强错误提示（当前已实现）

**预期效果**：
- 成功率提升：70% → 85%
- 工作量：1天
- 风险：低

---

### 阶段3：中期重构（1-2周）🚀
**方案1: Diff-based (JSON Patch)**

#### 技术准备
1. **研究JSON Patch**
   - RFC 6902标准
   - Python库：`jsonpatch`
   - JavaScript库：`fast-json-patch`

2. **设计Prompt格式**
   ```json
   {
     "task": "incremental_update",
     "output_format": "rfc6902_json_patch",
     "operations_allowed": ["add"],
     "base_document": {
       "nodes": {...},
       "edges": {...}
     },
     "user_request": "..."
   }
   ```

3. **实现Patch应用**
   ```python
   import jsonpatch

   def apply_incremental_patch(
       existing_graph: dict,
       ai_patches: list
   ) -> dict:
       # 验证patch操作
       for patch in ai_patches:
           if patch["op"] != "add":
               raise ValueError("Only 'add' operations allowed")

       # 应用patch
       updated = jsonpatch.apply_patch(existing_graph, ai_patches)
       return updated
   ```

4. **Few-Shot示例**
   ```
   Example Input:
   {
     "base_document": {"nodes": [...], "edges": [...]},
     "request": "Add Redis cache between service and DB"
   }

   Example Output:
   {
     "patches": [
       {"op": "add", "path": "/nodes/-", "value": {...}},
       {"op": "add", "path": "/edges/-", "value": {...}}
     ]
   }
   ```

#### 行动清单
- [ ] Week 1: Prototype和测试
- [ ] Week 2: 集成到现有系统
- [ ] Week 2: 性能测试（Token减少验证）

**预期效果**：
- 成功率：85% → 95%
- Token减少：31%
- 延迟减少：20-30%

---

### 阶段4：长期探索（可选）🔬
**方案2: GNN Integration**

仅在以下情况考虑：
- 用户量>1000
- 增量生成是核心功能
- 有ML工程师资源

---

## 🔧 当前代码问题总结

### 已实现的保护机制 ✅
1. **Session管理**（60分钟TTL）
2. **节点恢复**（AI删除的节点自动恢复）
3. **属性还原**（label、type、position修改自动还原）
4. **语义验证**（关键词覆盖率<80%触发安全模式）
5. **零新增检测**（新增节点=0直接拒绝）

### 根本问题 ❌
**AI不理解任务**：
- AI认为"追加"="修改现有节点label"
- 而不是"保留现有节点+新增节点"

**Prompt约束不够具体**：
- 虽然有6条规则，但缺少**具体示例**
- AI需要看到"什么是正确的输出"

---

## 📖 参考文献

### 核心论文
1. [JSON Whisperer: Efficient JSON Editing with LLMs](https://arxiv.org/html/2510.04717v1) - 2025年10月
2. [Structured Chain-of-Thought Prompting for Code Generation](https://dl.acm.org/doi/10.1145/3690635) - 2025年ACM
3. [The Decreasing Value of Chain of Thought in Prompting](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5285532) - 2025年6月

### 综合指南
4. [The Ultimate Guide to Prompt Engineering in 2025](https://medium.com/@generativeai.saif/the-ultimate-guide-to-prompt-engineering-in-2025-mastering-llm-interactions-8b88c5cf65b6)
5. [A Comprehensive Taxonomy of Prompt Engineering](https://link.springer.com/article/10.1007/s11704-025-50058-z)
6. [Prompt Engineering Guide](https://www.promptingguide.ai/techniques/cot)

### 图增强技术
7. [LLM and GNN: Improving Reasoning on Graph Data](https://towardsdatascience.com/llm-and-gnn-how-to-improve-reasoning-of-both-ai-systems-on-graph-data-5ebd875eef30/)
8. [Graph Machine Learning in the Era of LLMs](https://arxiv.org/html/2404.14928v1)

### 行业案例
9. [Making AI-generated diagrams useful and interactive](https://www.yworks.com/blog/interactive-ai-generated-diagrams) - Splotch案例
10. [NodeRAG: Heterogeneous Graph-Based Tool](https://www.kdjingpai.com/en/noderag/)

### 工具和实现
11. [GitHub: llm-patcher](https://github.com/theluk/llm-patcher) - OpenAI patch format参考
12. [GitHub: ln-diff](https://github.com/dceluis/ln-diff) - Line-numbered patch format

---

## 💡 关键洞察

### 1. Token效率很重要
- 当前方法：传输25个完整节点（~2000 tokens）
- Diff方法：只传输新增部分（~200 tokens）
- **节省90% tokens** 对高频使用场景至关重要

### 2. 语义清晰度>规则数量
- 6条规则不如1个完整示例
- AI需要看到"什么是对的"，而不只是"什么是错的"

### 3. 验证逻辑是必需的
- 即使Prompt完美，AI仍可能失败
- 验证逻辑=最后一道防线
- 但**拒绝错误输出优于修复错误输出**

### 4. 业界同病相怜
- Splotch的问题和我们完全一样
- 说明这是LLM的通用难题，不是我们实现的问题
- Diff-based方法是已验证的解决方案

---

## ✅ 下一步行动

### 立即执行（今天）
1. ✅ 创建本调研文档
2. ⏳ 实施Few-Shot示例（2小时）
3. ⏳ 测试并验证成功率提升

### 本周执行
4. ⏳ 添加Structured CoT推理步骤
5. ⏳ 优化前端用户输入引导
6. ⏳ 编写端到端测试覆盖更多场景

### 下周执行（如果阶段1-2效果不佳）
7. ⏳ 开始Diff-based Prompting原型
8. ⏳ 研究和测试jsonpatch库
9. ⏳ 设计新的Prompt格式

---

## 📝 测试计划

### 测试场景

#### 场景1: 添加单个节点
```
初始: User Service → User DB (2节点, 1边)
请求: "添加Redis缓存"
预期: 3节点(原2+新1), 3边(原1+新2)
```

#### 场景2: 添加多个节点
```
初始: 电商秒杀流程 (16节点, 18边)
请求: "添加库存锁定和支付恢复功能"
预期: ≥18节点(原16+至少2个新节点)
```

#### 场景3: 添加层级
```
初始: 三层架构 (9节点)
请求: "添加监控层，包括Prometheus和Grafana"
预期: 11节点(原9+新2), 监控节点在新的y坐标层
```

#### 场景4: 模糊请求（预期失败）
```
初始: 5节点
请求: "优化性能"（未明确说添加什么节点）
预期: 系统提示"请明确描述要添加的节点"
```

---

## 🎓 经验教训

1. **Prompt工程不是万能的**
   - 即使6条规则+完整JSON，AI仍然误解
   - 需要示例+验证+错误反馈的组合

2. **验证逻辑要主动拒绝，不只是被动修复**
   - 修复错误输出 < 拒绝错误输出+引导用户重试

3. **研究业界方案很值得**
   - JSON Patch不是我们想出来的，但非常适合我们
   - 不要重复造轮子

4. **渐进式实施**
   - 从简单的Few-Shot开始
   - 验证效果后再决定是否重构

---

**文档版本**: v1.0
**最后更新**: 2026-02-09
**作者**: Claude Code
**状态**: 调研完成，等待实施决策
