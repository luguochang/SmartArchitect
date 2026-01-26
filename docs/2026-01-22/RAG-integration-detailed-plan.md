# RAG知识库深度集成方案 - SmartArchitect AI

## 项目背景

**目标**: 将RAG知识库深度集成到PPT生成和演讲稿生成功能中，达到生产级别的专业效果。

**当前状态分析**:
- ✅ RAG服务已实现（ChromaDB + all-MiniLM-L6-v2 embedding）
- ✅ PPT/Slidev导出功能已实现（纯数据驱动，无AI增强）
- ✅ 演讲稿生成已实现（基础AI生成，未使用RAG）
- ❌ RAG与导出功能完全隔离，未集成
- ❌ 生成内容缺乏领域知识和最佳实践
- ❌ 前端缺少DocumentUploader组件

**核心痛点**（基于用户反馈）:
1. **演讲稿质量不足**: 仅靠简单输入框+AI生成，内容过于简单，缺乏专业性
2. **缺乏二次编辑能力**: 生成后无法润色和修改，一次性生成难以满足需求
3. **prompt设计欠佳**: 需要定义演讲稿所需要素，约束大模型生成高质量内容
4. **RAG未发挥作用**: 知识库与生成流程隔离，没有为内容提供专业支撑

**问题核心**: 需要系统性的演讲稿生成框架（prompt工程+RAG增强+二次编辑），而不是简单的AI调用。

---

## 技术方案架构

### 核心设计理念

基于2025-2026年前沿研究（Paper2Slides, ChartLlama, RAG-as-Context范式），采用**多阶段生成管道**：

```
Stage 1: 内容规划 (Content Planning)
  ↓ 使用RAG检索相似架构和最佳实践
Stage 2: 智能布局设计 (Layout Design)
  ↓ 根据内容深度自适应调整幻灯片结构
Stage 3: RAG增强叙述 (Narration Enhancement)
  ↓ 为每张幻灯片注入领域知识
Stage 4: 视觉增强 (Visual Enhancement)
  ↓ 生成图表、引用来源
```

---

## 实现方案详解

### 方案1: 增强型RAG服务（简化版）

**文件**: `backend/app/services/rag_enhanced.py` (新建)

**设计原则**（基于用户反馈）:
- ✅ 图相似度使用**简化版本**（节点类型统计+边密度，无需复杂图嵌入）
- ✅ 保持**多provider灵活切换**架构
- ✅ 快速实现，平衡效果与工期

**核心能力**:

1. **混合检索策略** (Hybrid Retrieval - 简化版)
   - 语义搜索（现有能力）
   - **简化的结构相似度**（新增）：基于统计特征，不用图嵌入模型
   - 元数据过滤（新增）：按技术栈、复杂度、领域分类

2. **智能上下文构建**
   ```python
   class EnhancedRAGService:
       async def hybrid_search(
           query: str,
           current_diagram: Optional[Dict],  # 当前画布的nodes+edges
           filters: Optional[Dict],
           top_k: int = 5
       ) -> EnhancedSearchResult:
           # 1. 语义搜索
           text_results = await self.semantic_search(query, top_k * 2)

           # 2. 简化的图结构相似度（如果有当前架构图）
           if current_diagram:
               structure_results = await self.simple_graph_similarity_search(
                   current_diagram, top_k
               )

           # 3. Reranking（使用cross-encoder提升准确度）
           reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
           final = self.rerank(query, text_results, structure_results, reranker)

           return EnhancedSearchResult(
               chunks=final,
               relevance_scores=[...],
               suggested_patterns=["microservices", "event-driven"],  # 自动检测模式
               diagram_matches=[...]  # 匹配到的相似架构
           )
   ```

3. **简化的图特征提取**（节省50%工期，保留80%效果）
   ```python
   def extract_simple_graph_features(diagram: Dict) -> SimpleGraphFeatures:
       """
       使用简单统计特征，无需复杂图嵌入
       """
       nodes = diagram["nodes"]
       edges = diagram["edges"]

       # 节点类型分布（核心特征）
       node_type_counts = Counter([n["type"] for n in nodes])

       # 边密度（连接紧密度）
       max_edges = len(nodes) * (len(nodes) - 1)
       edge_density = len(edges) / max_edges if max_edges > 0 else 0

       # 平均出入度
       in_degree = Counter([e["target"] for e in edges])
       out_degree = Counter([e["source"] for e in edges])
       avg_degree = (sum(in_degree.values()) + sum(out_degree.values())) / (2 * len(nodes))

       # 拓扑分类（简单规则）
       topology = classify_topology_simple(node_type_counts, edge_density)

       return SimpleGraphFeatures(
           node_type_vector=dict(node_type_counts),  # {"api": 3, "database": 2}
           edge_density=edge_density,
           avg_degree=avg_degree,
           topology=topology,  # "layered" | "mesh" | "hub-spoke"
           component_count=len(nodes)
       )

   def calculate_similarity(feat1: SimpleGraphFeatures, feat2: SimpleGraphFeatures) -> float:
       """
       余弦相似度计算（无需深度学习模型）
       """
       # 节点类型向量相似度（权重60%）
       type_similarity = cosine_similarity(
           vectorize_node_types(feat1.node_type_vector),
           vectorize_node_types(feat2.node_type_vector)
       )

       # 边密度相似度（权重20%）
       density_similarity = 1 - abs(feat1.edge_density - feat2.edge_density)

       # 拓扑匹配（权重20%）
       topology_match = 1.0 if feat1.topology == feat2.topology else 0.3

       return 0.6 * type_similarity + 0.2 * density_similarity + 0.2 * topology_match
   ```

**技术依赖**:
- ✅ 无需NetworkX（简化方案）
- ✅ sentence-transformers（仅用于cross-encoder reranking）
- ✅ 现有ChromaDB
- ✅ 标准Python库（Counter, math）

---

### 方案2: RAG驱动的PPT生成

**文件**: `backend/app/services/ppt_exporter_rag.py` (新建)

**生成流程**:

#### Stage 1: 内容规划
```python
async def plan_slide_content(nodes, edges, options):
    # 查询RAG获取相似架构
    rag_context = await rag.hybrid_search(
        query=f"Architecture: {summarize(nodes, edges)}",
        current_diagram={"nodes": nodes, "edges": edges},
        filters={"doc_type": "architecture"},
        top_k=5
    )

    # AI生成幻灯片大纲
    prompt = f"""
    你是技术演示专家，为这个架构生成幻灯片大纲。

    当前架构: {format_architecture(nodes, edges)}

    相关公司文档知识:
    {format_rag_context(rag_context)}

    要求:
    - 时长: {options.duration} ({get_slide_count(options.duration)}张幻灯片)
    - 受众: {options.audience}
    - 技术深度: {options.technical_depth}

    生成JSON格式大纲...
    """

    return ContentPlan.parse_obj(await ai.generate(prompt))
```

#### Stage 2: RAG增强叙述

为每张幻灯片注入领域知识：

```python
async def enhance_with_rag(slides, nodes, edges):
    for slide in slides:
        if slide.type == "component_detail":
            # 为组件获取最佳实践
            for node in slide.featured_nodes:
                rag_results = await rag.hybrid_search(
                    query=f"{node.type} best practices: {node.data.label}",
                    filters={"tech_stack": node.type},
                    top_k=3
                )

                # 生成组件说明（含RAG上下文）
                explanation = await generate_component_explanation(node, rag_results)

                slide.add_speaker_note(explanation.purpose)
                slide.add_best_practices_section(rag_results.suggested_patterns)

        elif slide.type == "flow_analysis":
            # 分析数据流（含RAG上下文）
            flow_path = extract_flow_path(edges, slide.featured_edges)

            rag_results = await rag.hybrid_search(
                query=f"Data flow patterns: {flow_path.description}",
                current_diagram={"nodes": nodes, "edges": edges},
                top_k=5
            )

            flow_analysis = await analyze_flow_with_context(flow_path, rag_results)
            slide.add_analysis_text(flow_analysis)

    return slides
```

#### Stage 3: 视觉增强

```python
async def add_visual_enhancements(slides):
    prs = Presentation()

    for slide_data in slides:
        slide = prs.slides.add_slide(get_layout(slide_data.type))

        # 添加标题和内容
        slide.shapes.title.text = slide_data.title

        # 添加演讲者注释（RAG增强）
        slide.notes_slide.notes_text_frame.text = slide_data.speaker_notes

        # 添加来源引用（页脚）
        add_source_attribution(slide, slide_data.rag_sources)

    return prs.save_to_bytes()
```

**幻灯片结构**:
1. 标题页
2. 架构概览（含统计数据）
3. 核心组件详解（每个组件1页，含RAG最佳实践）
4. 数据流分析（含相似案例参考）
5. 潜在问题与优化建议（基于RAG知识库）
6. 总结与下一步

**API端点**:
```
POST /api/export/ppt-enhanced
Body: {
  nodes, edges, mermaid_code, title,
  rag_options: {
    audience: "executive" | "technical" | "mixed",
    technical_depth: 1-10,
    focus_areas: ["scalability", "security"],
    include_best_practices: true
  }
}
Response: Binary .pptx file
```

---

### 方案3: 专业演讲稿生成系统（核心重点）

**文件**: `backend/app/services/speech_script_rag.py` (新建)

**设计理念**（基于2025-2026最佳实践）:
- 采用 **CO-STAR框架**（Context, Objective, Style, Tone, Audience, Response）
- **Role-based prompting**（告诉AI如何思考）
- **演讲稿要素约束**（定义必需元素，提升专业性）
- **RAG增强**（注入领域知识和案例）
- **二次编辑支持**（保存草稿，支持润色）

**核心创新**:
1. Server-Sent Events (SSE) 实时流式传输
2. 专业Prompt模板系统
3. 二次编辑和版本管理

```python
async def generate_speech_script_stream(nodes, edges, duration, options):
    # Phase 1: RAG上下文检索
    yield StreamEvent(type="CONTEXT_SEARCH", data={"status": "搜索知识库..."})

    rag_context = await rag.hybrid_search(
        query=build_context_query(nodes, edges, duration),
        current_diagram={"nodes": nodes, "edges": edges},
        top_k=10
    )

    yield StreamEvent(
        type="CONTEXT_FOUND",
        data={
            "chunks_found": len(rag_context.chunks),
            "patterns": rag_context.suggested_patterns,
            "sources": [c.metadata.filename for c in rag_context.chunks]
        }
    )

    # Phase 2: 构建增强提示词
    prompt = build_script_prompt(nodes, edges, duration, rag_context, options)

    # Phase 3: 流式生成
    yield StreamEvent(type="GENERATION_START", data={})

    accumulated = ""
    async for token in ai.generate_with_stream(prompt):
        accumulated += token
        yield StreamEvent(type="TOKEN", data={"token": token})

    # Phase 4: 后处理
    final_script = post_process(accumulated, duration)

    yield StreamEvent(
        type="COMPLETE",
        data={
            "script": final_script,
            "word_count": len(final_script.split()),
            "rag_sources": [c.metadata.filename for c in rag_context.chunks]
        }
    )
```

**专业Prompt模板系统**（基于CO-STAR框架和2025最佳实践）:

```python
class ProfessionalPromptBuilder:
    """
    专业演讲稿Prompt构建器
    基于CO-STAR框架 + Role-based prompting + 演讲稿要素约束

    参考: https://www.lakera.ai/blog/prompt-engineering-guide
           https://www.ibm.com/think/prompt-engineering
    """

    def build_script_prompt(
        self,
        nodes: List[Node],
        edges: List[Edge],
        duration: str,
        rag_context: EnhancedSearchResult,
        options: ScriptOptions
    ) -> str:
        """
        构建约束式专业演讲稿生成prompt
        """

        # 演讲稿必需要素（约束大模型生成高质量内容）
        duration_specs = {
            "30s": {
                "words": "60-80",
                "structure": "Hook (10s) + Value Proposition (15s) + Call-to-Action (5s)",
                "required_elements": [
                    "开场Hook（用问题或数据吸引注意）",
                    "核心价值陈述（1-2句话）",
                    "关键指标或亮点（1个数字）",
                    "行动号召"
                ],
                "tone": "简洁有力，聚焦价值"
            },
            "2min": {
                "words": "280-320",
                "structure": "开场(30s) + 问题背景(30s) + 解决方案(45s) + 价值证明(30s) + 结尾(15s)",
                "required_elements": [
                    "开场故事或场景（引发共鸣）",
                    "当前痛点/挑战的清晰陈述",
                    "架构设计的3个核心亮点",
                    "RAG案例支撑（至少1个具体例子）",
                    "量化价值（性能/成本/可靠性指标）",
                    "下一步行动或建议"
                ],
                "tone": "专业但易懂，逻辑清晰"
            },
            "5min": {
                "words": "700-800",
                "structure": "开场(1min) + 背景(1min) + 架构设计(2min) + 风险与对策(0.5min) + Q&A引导(0.5min)",
                "required_elements": [
                    "引人入胜的开场（故事/统计/问题）",
                    "业务背景和技术挑战",
                    "架构设计理念和权衡决策",
                    "核心组件深入讲解（3-5个）",
                    "数据流和关键路径分析",
                    "RAG最佳实践引用（至少2个）",
                    "相似案例对比（从RAG获取）",
                    "已知风险和缓解措施",
                    "性能/成本/扩展性分析",
                    "未来演进方向",
                    "开放式问题引导讨论"
                ],
                "tone": "深入浅出，兼顾广度与深度"
            }
        }

        spec = duration_specs[duration]

        # === CO-STAR框架构建 ===

        # C - Context (上下文)
        context_section = f"""
## 📋 CONTEXT (上下文背景)

### 当前架构概览
{self._format_architecture_detailed(nodes, edges)}

### 知识库检索结果（公司最佳实践）
{self._format_rag_context_structured(rag_context)}

### 检测到的架构模式
- 主要模式: {', '.join(rag_context.suggested_patterns[:3])}
- 技术栈: {self._extract_tech_stack(nodes)}
- 复杂度: {self._assess_complexity(nodes, edges)}
"""

        # O - Objective (目标)
        objective_section = f"""
## 🎯 OBJECTIVE (生成目标)

你的任务是为这个技术架构生成一份**专业、有深度、有说服力**的{duration}演讲稿。

目标受众: {options.audience}
- 如果是高管: 强调商业价值、ROI、风险控制
- 如果是技术团队: 深入技术细节、设计权衡、最佳实践
- 如果是混合受众: 分层表达，先讲价值再讲实现

重点关注: {', '.join(options.focus_areas)}
"""

        # S - Style (风格)
        style_section = f"""
## 🎨 STYLE (演讲风格)

写作风格要求:
1. 使用**讲故事**的方式，不要干巴巴的列举
2. 多用**类比和比喻**让复杂概念易懂（如："API网关就像机场安检"）
3. **数据驱动**: 引用具体数字、百分比、对比（从RAG上下文获取）
4. **问题导向**: 先提出问题，再展示解决方案
5. **节奏控制**: {spec['structure']}

参考优秀技术演讲:
- Martin Fowler的架构演讲（清晰的层次结构）
- Simon Sinek的TED演讲（从Why开始）
- Amazon CTO Werner Vogels的技术分享（案例丰富）
"""

        # T - Tone (语气)
        tone_section = f"""
## 🗣️ TONE (语气基调)

语气设定: {options.tone} + {spec['tone']}

具体要求:
- ✅ 自信但不傲慢: "我们的架构..."（不是"我觉得..."）
- ✅ 专业但不晦涩: 避免过度使用行话，必要时解释术语
- ✅ 诚实且透明: 承认trade-offs和已知限制
- ✅ 积极且建设性: 即使讨论问题，也要给出解决路径
- ❌ 避免空洞表述: "非常好"、"很强大"等无实质内容的修饰
"""

        # A - Audience (受众)
        audience_section = f"""
## 👥 AUDIENCE (受众分析)

受众类型: {options.audience}

受众期待:
- 他们想知道: 这个架构能解决什么问题？
- 他们关心的: {self._get_audience_concerns(options.audience)}
- 他们的背景: {self._get_audience_background(options.audience)}

调整策略:
- 技术深度: {self._get_technical_depth(options.audience)}
- 术语使用: {self._get_terminology_guidance(options.audience)}
- 举例方式: {self._get_example_style(options.audience)}
"""

        # R - Response Format (响应格式)
        response_format_section = f"""
## 📝 RESPONSE FORMAT (输出格式)

严格按照以下结构输出:

[INTRO]
{self._generate_intro_template(spec)}

[BODY]
{self._generate_body_template(spec, nodes, edges)}

[CONCLUSION]
{self._generate_conclusion_template(spec)}

## ⚠️ 质量检查清单（生成后自查）
{self._generate_quality_checklist(spec)}
"""

        # === 整合最终Prompt ===
        final_prompt = f"""
{context_section}

{objective_section}

{style_section}

{tone_section}

{audience_section}

{response_format_section}

---

## 🚀 NOW BEGIN GENERATION

时长: {duration} (目标字数: {spec['words']}字)

必须包含的要素:
{chr(10).join(f"- {elem}" for elem in spec['required_elements'])}

记住:
1. 从RAG上下文中至少引用2个具体案例或最佳实践（标注来源）
2. 每个断言都要有数据或案例支撑，避免空洞表述
3. 使用过渡句让段落衔接自然（如："那么，我们是如何实现这一点的呢？"）
4. 在关键点使用**重复和强调**（重要的话说三遍）
5. 结尾要有明确的行动号召或思考问题

开始生成演讲稿:
"""

        return final_prompt

    def _format_architecture_detailed(self, nodes, edges) -> str:
        """详细格式化架构信息"""
        components_by_type = {}
        for node in nodes:
            node_type = node.type or "default"
            if node_type not in components_by_type:
                components_by_type[node_type] = []
            components_by_type[node_type].append(node.data.label)

        arch_summary = f"**组件总数**: {len(nodes)}\n\n**组件分布**:\n"
        for node_type, labels in components_by_type.items():
            arch_summary += f"- {node_type.capitalize()}: {len(labels)}个 ({', '.join(labels[:3])}{'...' if len(labels) > 3 else ''})\n"

        arch_summary += f"\n**连接总数**: {len(edges)}\n"
        if edges:
            key_flows = edges[:5]
            arch_summary += "**关键数据流**:\n"
            for edge in key_flows:
                label_str = f" ({edge.label})" if edge.label else ""
                arch_summary += f"- {edge.source} → {edge.target}{label_str}\n"

        return arch_summary

    def _generate_intro_template(self, spec) -> str:
        """生成开场模板"""
        if spec['words'].startswith('60'):
            return """
（30秒电梯演讲）
- 用1个问题或数据开场（吸引注意）
- 1句话说明这个架构解决什么问题
- 1个核心亮点或指标
- 行动号召
"""
        elif spec['words'].startswith('280'):
            return """
（2分钟开场 - 约60字）
- 讲一个3-5句话的故事或场景（引发共鸣）
- 或者用一个令人惊讶的数据/事实开场
- 快速过渡到当前痛点
- 引出架构设计的必要性

示例: "想象一下，当100万用户同时涌入系统，而你的数据库开始报警。这不是假设，这是我们去年双11遇到的真实场景。今天我要分享的，就是我们如何用这套架构解决这个问题。"
"""
        else:
            return """
（5分钟开场 - 约150字）
- 用故事/统计数据/行业趋势开场（1-2分钟）
- 建立业务背景：为什么需要这个架构？
- 技术挑战：面临哪些具体问题？
- 简要预告：我们的解决方案的核心思路（3个关键词）

示例: "2023年，Gartner报告指出，75%的企业在数字化转型中遇到架构瓶颈。我们公司也不例外。去年，我们的单体应用开始出现性能问题，响应时间从200ms飙升到3秒，用户投诉激增。经过6个月的架构重构，我们不仅解决了性能问题，还将部署频率从每月1次提升到每天10次。今天，我想分享这个架构背后的设计思路和实践经验。"
"""

    def _generate_body_template(self, spec, nodes, edges) -> str:
        """生成主体模板"""
        if spec['words'].startswith('60'):
            return "（30秒主体）直接说核心价值和关键指标，不展开细节"
        elif spec['words'].startswith('280'):
            return """
（2分钟主体 - 约200字）

分3个段落:

**段落1: 架构设计核心思路（60字）**
- 我们采用了什么架构模式？（从RAG上下文引用）
- 为什么选择这个方案？（权衡决策）
- 与传统方案的对比

**段落2: 关键组件和数据流（80字）**
- 3个最重要的组件及其职责
- 核心数据流路径
- 用类比让非技术受众也能理解

**段落3: 价值证明（60字）**
- 性能提升: XX%（具体数字）
- 成本优化: 节省XX（具体金额）
- 或引用RAG中的相似案例: "这种架构在XX公司也取得了类似效果..."
"""
        else:
            return """
（5分钟主体 - 约500字）

分5个段落:

**段落1: 架构设计理念（100字）**
- 设计原则（如：高内聚低耦合、单一职责）
- 为什么选择这些原则？（结合业务场景）
- 从RAG引用业界最佳实践

**段落2-4: 核心组件深入讲解（每个组件80-100字）**
选择3-4个最重要的组件:
- 组件的职责和设计考量
- 技术选型的权衡（为什么用Redis而不是Memcached？）
- 性能数据或压测结果
- 从RAG引用相似案例或反模式

**段落5: 风险与对策（100字）**
- 已知的技术风险（不要回避）
- 缓解措施和备选方案
- 监控和告警策略

**段落6: 价值总结（100字）**
- 量化的业务价值
- 技术债务的改善
- 团队效能提升
"""

    def _generate_conclusion_template(self, spec) -> str:
        """生成结尾模板"""
        if spec['words'].startswith('60'):
            return "（10秒结尾）清晰的行动号召: 'Let's discuss' / '欢迎试用' / '我们可以帮你实现'"
        elif spec['words'].startswith('280'):
            return """
（2分钟结尾 - 约40字）
- 回顾核心价值（1句话）
- 行动号召或下一步建议
- 留一个开放式问题引发思考

示例: "通过这套架构，我们不仅解决了性能问题，更重要的是建立了一个可持续演进的技术体系。如果你也面临类似挑战，不妨思考一下：你的架构是否为未来的增长预留了空间？"
"""
        else:
            return """
（5分钟结尾 - 约100字）
- 总结3个关键要点（呼应开场）
- 未来演进方向
- 抛出2-3个思考问题引导Q&A
- 感谢和联系方式

示例: "今天我们分享了从单体到微服务的架构演进之路。核心要点有三个：第一，渐进式迁移比大爆炸重写更安全；第二，观测性是微服务架构的生命线；第三，团队组织要与架构对齐。未来，我们计划引入服务网格和边缘计算能力。我想留几个问题给大家：1) 你们如何处理微服务的分布式事务？2) 在你们的场景中，服务粒度如何划分？欢迎会后交流。谢谢大家！"
"""

    def _generate_quality_checklist(self, spec) -> str:
        """生成质量检查清单"""
        return f"""
生成后请自查:
- [ ] 字数在目标范围内（{spec['words']}字）
- [ ] 所有必需要素都包含
- [ ] 至少引用了2个RAG上下文中的案例/最佳实践
- [ ] 每个技术断言都有数据或案例支撑
- [ ] 段落之间有自然的过渡
- [ ] 开场有吸引力（不是平铺直叙）
- [ ] 结尾有明确的行动号召或思考问题
- [ ] 避免使用"非常好"、"很强大"等空洞表述
- [ ] 技术术语有必要的解释（尤其对非技术受众）
"""

    def _get_audience_concerns(self, audience: str) -> str:
        """根据受众返回关注点"""
        concerns = {
            "executive": "ROI、业务影响、风险控制、竞争优势",
            "technical": "技术细节、性能指标、可维护性、技术债务",
            "mixed": "业务价值 + 技术亮点的平衡"
        }
        return concerns.get(audience, "业务价值和技术实现的平衡")

    def _get_technical_depth(self, audience: str) -> str:
        """返回技术深度指导"""
        depth = {
            "executive": "高层次，少用技术术语，多讲业务价值",
            "technical": "深入技术细节，可以使用专业术语，但要解释设计决策",
            "mixed": "分层表达：先讲what和why（业务价值），再讲how（技术实现）"
        }
        return depth.get(audience, "中等深度，兼顾业务和技术")
```

**关键改进点**:
1. ✅ **CO-STAR框架**: 提供完整上下文、明确目标、定义风格和语气
2. ✅ **演讲稿要素约束**: 每种时长都有明确的必需要素清单
3. ✅ **模板化指导**: 为intro/body/conclusion提供具体模板和示例
4. ✅ **质量检查清单**: 让AI自查输出质量
5. ✅ **受众自适应**: 根据受众类型调整语气和深度
6. ✅ **RAG强制集成**: 要求至少引用2个RAG案例

**二次编辑和版本管理**:

```python
# backend/app/services/script_editor.py (新建)

class ScriptEditorService:
    """
    演讲稿二次编辑服务
    支持保存草稿、版本管理、局部润色
    """

    def __init__(self):
        # 使用简单的文件存储或数据库
        self.storage_dir = Path("./data/scripts")
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    async def save_draft(
        self,
        script_id: str,
        content: ScriptContent,
        metadata: ScriptMetadata
    ) -> SaveDraftResponse:
        """
        保存演讲稿草稿（支持增量更新）
        """
        draft_file = self.storage_dir / f"{script_id}.json"

        draft_data = {
            "id": script_id,
            "content": {
                "intro": content.intro,
                "body": content.body,
                "conclusion": content.conclusion,
                "full_text": content.full_text
            },
            "metadata": {
                "created_at": metadata.created_at or datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "duration": metadata.duration,
                "word_count": len(content.full_text.split()),
                "rag_sources": metadata.rag_sources,
                "architecture_snapshot": metadata.architecture_snapshot
            },
            "version": metadata.version + 1
        }

        draft_file.write_text(json.dumps(draft_data, ensure_ascii=False, indent=2))

        return SaveDraftResponse(
            script_id=script_id,
            version=draft_data["version"],
            saved_at=draft_data["metadata"]["updated_at"]
        )

    async def load_draft(self, script_id: str) -> Optional[ScriptDraft]:
        """加载演讲稿草稿"""
        draft_file = self.storage_dir / f"{script_id}.json"

        if not draft_file.exists():
            return None

        draft_data = json.loads(draft_file.read_text())
        return ScriptDraft.parse_obj(draft_data)

    async def refine_section(
        self,
        script_id: str,
        section: Literal["intro", "body", "conclusion"],
        user_feedback: str,
        rag_context: Optional[EnhancedSearchResult] = None
    ) -> RefinedSectionResponse:
        """
        局部润色演讲稿某个章节
        用户可以提供反馈，AI根据反馈重新生成
        """

        # 加载当前草稿
        draft = await self.load_draft(script_id)
        if not draft:
            raise ValueError(f"Script {script_id} not found")

        current_section_text = getattr(draft.content, section)

        # 构建润色prompt
        refine_prompt = f"""
你是专业的演讲稿编辑，负责根据用户反馈改进演讲稿的某个章节。

## 当前章节内容（{section}）:
{current_section_text}

## 用户反馈:
{user_feedback}

## 改进要求:
1. 保持原有的核心信息和结构
2. 根据用户反馈进行针对性调整
3. 确保改进后的文字更流畅、更有说服力
4. 保持字数在±20%范围内（当前: {len(current_section_text.split())}字）

{f"## 补充的RAG上下文:\\n{self._format_rag_context(rag_context)}" if rag_context else ""}

请输出改进后的章节内容:
"""

        # 调用AI生成润色版本
        refined_text = await self.ai_service.generate_with_text_prompt(refine_prompt)

        # 更新草稿
        setattr(draft.content, section, refined_text)
        draft.content.full_text = self._rebuild_full_text(draft.content)

        await self.save_draft(script_id, draft.content, draft.metadata)

        return RefinedSectionResponse(
            script_id=script_id,
            section=section,
            refined_text=refined_text,
            changes_summary=self._summarize_changes(current_section_text, refined_text)
        )

    async def suggest_improvements(
        self,
        script_id: str,
        focus_areas: List[str] = ["clarity", "engagement", "flow"]
    ) -> ImprovementSuggestions:
        """
        AI分析演讲稿，提供改进建议（不直接修改）
        """

        draft = await self.load_draft(script_id)

        analysis_prompt = f"""
你是演讲稿专业顾问，分析以下演讲稿并提供改进建议。

{draft.content.full_text}

请从以下维度分析:
{', '.join(focus_areas)}

输出JSON格式:
{{
  "overall_score": 7.5,  // 1-10分
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "suggestions": [
    {{
      "section": "intro" | "body" | "conclusion",
      "issue": "具体问题描述",
      "suggestion": "改进建议",
      "priority": "high" | "medium" | "low"
    }}
  ]
}}
"""

        analysis_json = await self.ai_service.generate_with_text_prompt(analysis_prompt)
        return ImprovementSuggestions.parse_obj(analysis_json)
```

**前端二次编辑组件**:

```typescript
// frontend/components/ScriptEditor.tsx (新建)

export function ScriptEditor({ scriptId }: { scriptId: string }) {
  const [draft, setDraft] = useState<ScriptDraft | null>(null);
  const [editingSection, setEditingSection] = useState<string | null>(null);
  const [suggestions, setSuggestions] = useState<ImprovementSuggestion[]>([]);

  // 加载草稿
  useEffect(() => {
    loadDraft(scriptId).then(setDraft);
  }, [scriptId]);

  // 保存草稿（自动保存）
  const autoSave = useDebounce(async (content: ScriptContent) => {
    await fetch(`/api/export/script/${scriptId}/draft`, {
      method: 'PUT',
      body: JSON.stringify({ content })
    });
    toast.success('草稿已自动保存');
  }, 2000);

  // 局部润色
  const refineSection = async (section: string, feedback: string) => {
    setRefining(true);

    try {
      const response = await fetch(`/api/export/script/${scriptId}/refine`, {
        method: 'POST',
        body: JSON.stringify({ section, user_feedback: feedback })
      });

      const { refined_text, changes_summary } = await response.json();

      // 更新UI
      setDraft(prev => ({
        ...prev,
        content: {
          ...prev.content,
          [section]: refined_text
        }
      }));

      // 显示变更摘要
      showChangesModal(changes_summary);
    } finally {
      setRefining(false);
    }
  };

  // 获取改进建议
  const getSuggestions = async () => {
    const response = await fetch(`/api/export/script/${scriptId}/suggestions`);
    const suggestions = await response.json();
    setSuggestions(suggestions.suggestions);
  };

  return (
    <div className="script-editor">
      {/* 左侧：编辑器 */}
      <div className="editor-panel">
        <div className="section-editor" data-section="intro">
          <h3>开场 <button onClick={() => setEditingSection('intro')}>润色</button></h3>
          <textarea
            value={draft?.content.intro}
            onChange={(e) => {
              setDraft(prev => ({
                ...prev,
                content: { ...prev.content, intro: e.target.value }
              }));
              autoSave(draft.content);
            }}
          />
        </div>

        <div className="section-editor" data-section="body">
          <h3>主体 <button onClick={() => setEditingSection('body')}>润色</button></h3>
          <textarea
            value={draft?.content.body}
            onChange={(e) => {
              setDraft(prev => ({
                ...prev,
                content: { ...prev.content, body: e.target.value }
              }));
              autoSave(draft.content);
            }}
          />
        </div>

        <div className="section-editor" data-section="conclusion">
          <h3>结尾 <button onClick={() => setEditingSection('conclusion')}>润色</button></h3>
          <textarea
            value={draft?.content.conclusion}
            onChange={(e) => {
              setDraft(prev => ({
                ...prev,
                content: { ...prev.content, conclusion: e.target.value }
              }));
              autoSave(draft.content);
            }}
          />
        </div>
      </div>

      {/* 右侧：改进建议 */}
      <div className="suggestions-panel">
        <button onClick={getSuggestions}>
          <Sparkles className="w-4 h-4" />
          获取AI改进建议
        </button>

        {suggestions.length > 0 && (
          <div className="suggestions-list">
            {suggestions.map((sug, idx) => (
              <div key={idx} className={`suggestion priority-${sug.priority}`}>
                <h4>{sug.section}</h4>
                <p className="issue">{sug.issue}</p>
                <p className="suggestion">{sug.suggestion}</p>
                <button onClick={() => applySuggestion(sug)}>应用建议</button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 润色对话框 */}
      {editingSection && (
        <RefineDialog
          section={editingSection}
          onRefine={(feedback) => refineSection(editingSection, feedback)}
          onClose={() => setEditingSection(null)}
        />
      )}
    </div>
  );
}

// 润色对话框组件
function RefineDialog({ section, onRefine, onClose }) {
  const [feedback, setFeedback] = useState('');

  return (
    <Modal open onClose={onClose}>
      <div className="refine-dialog">
        <h2>润色 {section} 章节</h2>

        <label>请描述你希望如何改进这个章节:</label>
        <textarea
          placeholder="例如：开场太平淡，希望更有吸引力；或者：主体部分技术细节太多，希望更通俗易懂"
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          rows={4}
        />

        <div className="quick-suggestions">
          <p>快速建议:</p>
          <button onClick={() => setFeedback('增加具体的数据和案例，让内容更有说服力')}>
            增加数据支撑
          </button>
          <button onClick={() => setFeedback('使用更生动的类比和比喻，让技术概念更易懂')}>
            增加类比
          </button>
          <button onClick={() => setFeedback('调整语气，让表达更自信和专业')}>
            调整语气
          </button>
          <button onClick={() => setFeedback('简化表达，去掉冗余内容')}>
            简化表达
          </button>
        </div>

        <div className="actions">
          <button onClick={() => onRefine(feedback)} disabled={!feedback}>
            开始润色
          </button>
          <button onClick={onClose}>取消</button>
        </div>
      </div>
    </Modal>
  );
}
```

**API端点（二次编辑）**:
```
PUT /api/export/script/{script_id}/draft
Body: { content: { intro, body, conclusion } }
Response: { script_id, version, saved_at }

POST /api/export/script/{script_id}/refine
Body: { section: "intro"|"body"|"conclusion", user_feedback: "..." }
Response: { script_id, section, refined_text, changes_summary }

GET /api/export/script/{script_id}/suggestions
Query: ?focus_areas=clarity,engagement
Response: { overall_score, strengths, weaknesses, suggestions[] }

GET /api/export/script/{script_id}/draft
Response: ScriptDraft (完整草稿内容)
```

**关键改进点（二次编辑）**:
1. ✅ **草稿自动保存**: 用户编辑时自动保存（debounce 2秒）
2. ✅ **分章节编辑**: intro/body/conclusion独立编辑和润色
3. ✅ **AI改进建议**: 不直接修改，而是提供建议列表供用户选择
4. ✅ **快速润色模板**: 预设常见的润色需求（增加数据、增加类比等）
5. ✅ **变更追踪**: 润色后显示修改摘要，用户可对比查看
6. ✅ **版本管理**: 每次保存增加版本号，可回溯历史版本

---

**API端点（流式生成）**:
```
POST /api/export/script-stream
Body: {
  nodes, edges, duration,
  options: {
    tone: "professional" | "casual",
    audience: "executive" | "technical",
    focus_areas: ["scalability"]
  }
}
Response: text/event-stream (SSE)

Event stream:
data: {"type": "CONTEXT_FOUND", "data": {...}}

data: {"type": "TOKEN", "data": {"token": "..."}}

data: {"type": "COMPLETE", "data": {"script": "...", "sources": [...]}}
```

---

### 方案4: 前端集成

**文件**: `frontend/components/EnhancedExportMenu.tsx` (新建)

**用户体验流程**:

1. **RAG上下文预览**（在导出前）
   ```tsx
   const previewRAGContext = async () => {
     const response = await fetch('/api/rag/preview', {
       method: 'POST',
       body: JSON.stringify({
         nodes, edges,
         query: `Architecture export: ${summarizeArchitecture(nodes, edges)}`
       })
     });

     const context = await response.json();
     setContextPreview(context);
   };

   // UI显示
   {contextPreview && (
     <div className="context-preview-panel">
       <h3>找到 {contextPreview.chunks_found} 个相关文档</h3>
       <ul>
         {contextPreview.patterns.map(pattern => (
           <li key={pattern}>{pattern}</li>
         ))}
       </ul>
       <div className="source-badges">
         {contextPreview.sources.map(source => (
           <span className="badge">{source}</span>
         ))}
       </div>
     </div>
   )}
   ```

2. **配置导出选项**
   ```tsx
   <div className="export-options">
     <label>受众级别</label>
     <select value={ragOptions.audienceLevel}>
       <option value="executive">高管（高层概览）</option>
       <option value="technical">技术人员（详细）</option>
       <option value="mixed">混合受众</option>
     </select>

     <label>重点领域</label>
     <MultiSelect
       options={['可扩展性', '安全性', '成本', '性能']}
       value={ragOptions.focusAreas}
     />
   </div>
   ```

3. **流式演讲稿生成（打字机效果）**
   ```tsx
   const generateScriptStream = async (duration: string) => {
     const response = await fetch('/api/export/script-stream', {
       method: 'POST',
       headers: { 'Accept': 'text/event-stream' },
       body: JSON.stringify({ nodes, edges, duration, options: ragOptions })
     });

     const reader = response.body!.getReader();
     const decoder = new TextDecoder();

     while (true) {
       const { done, value } = await reader.read();
       if (done) break;

       const chunk = decoder.decode(value);
       const lines = chunk.split('\n\n');

       for (const line of lines) {
         if (!line.startsWith('data: ')) continue;

         const event = JSON.parse(line.slice(6));

         if (event.type === 'TOKEN') {
           // 打字机效果
           setScript(prev => prev + event.data.token);
         } else if (event.type === 'COMPLETE') {
           setFinalScript(event.data.script);
           showSourcesModal(event.data.rag_sources);
         }
       }
     }
   };
   ```

---

### 方案5: 高级功能 - 多模态图表生成

**文件**: `backend/app/services/chart_generator.py` (新建)

基于ChartLlama研究，使用AI生成性能对比图表：

```python
class MultimodalChartGenerator:
    async def generate_performance_chart(component: Node, rag_context):
        # 从RAG提取性能指标
        metrics = extract_metrics_from_rag(rag_context)

        # AI生成图表配置
        prompt = f"""
为{component.data.label}生成性能对比图表。

基准数据（来自RAG）:
{format_metrics(metrics)}

生成JSON:
{{
  "chart_type": "bar" | "line",
  "data": {{"labels": [...], "datasets": [...]}},
  "options": {{"title": "...", "scales": {{...}}}}
}}
"""

        chart_json = await ai.generate(prompt)

        # 用matplotlib生成图表图片
        fig, ax = plt.subplots(figsize=(8, 6))
        # ... 绘制图表 ...

        # 嵌入PPT幻灯片
        slide.shapes.add_picture(img_stream, ...)
```

---

## 实施路线图（基于用户反馈调整）

### Phase 1: 专业演讲稿生成系统 (Week 1-2)
**优先级**: 🔴 最高（用户核心痛点）

**任务**:
1. 创建 `backend/app/services/speech_script_rag.py`
   - 实现 `ProfessionalPromptBuilder` 类（CO-STAR框架）
   - 实现流式生成pipeline
   - 构建三种时长的专业prompt模板
   - 添加RAG上下文集成

2. 创建 `backend/app/services/script_editor.py`
   - 实现草稿保存和加载
   - 实现分章节润色功能
   - 实现AI改进建议生成

3. 更新 `backend/app/api/export.py`
   - 添加 `POST /api/export/script-stream` (流式生成)
   - 添加 `PUT /api/export/script/{id}/draft` (保存草稿)
   - 添加 `POST /api/export/script/{id}/refine` (润色)
   - 添加 `GET /api/export/script/{id}/suggestions` (改进建议)

4. 前端组件开发
   - 创建 `frontend/components/ScriptGenerator.tsx` (生成界面)
   - 创建 `frontend/components/ScriptEditor.tsx` (编辑器)
   - 创建 `frontend/components/RefineDialog.tsx` (润色对话框)

**验证标准**:
- [ ] 使用CO-STAR框架的prompt模板生成的演讲稿专业度评分 > 8/10
- [ ] 生成的演讲稿包含至少2个RAG来源的案例引用
- [ ] 二次编辑功能可用，润色后质量明显提升
- [ ] 流式传输流畅，首token延迟 < 3s

**交付物**:
- 功能完整的演讲稿生成和编辑系统
- 支持3种时长（30s/2min/5min）
- 支持分章节润色和AI改进建议

---

### Phase 2: RAG服务增强（简化版） (Week 2-3)
**优先级**: 🟡 中（为Phase 1提供更好支持）

**任务**:
1. 创建 `backend/app/services/rag_enhanced.py`
   - 实现简化的图特征提取（节点类型统计+边密度）
   - 实现余弦相似度计算（无需深度学习模型）
   - 添加元数据提取和过滤

2. 增强 `backend/app/services/rag.py`
   - 添加文档上传时的自动元数据提取
   - 添加技术栈识别（从文档内容）
   - 添加复杂度评估

3. 更新 `backend/app/models/schemas.py`
   - 添加 `SimpleGraphFeatures` 模型
   - 添加 `DocumentMetadata` 模型

**验证标准**:
- [ ] 简化的结构相似度搜索准确率 > 70%
- [ ] 元数据过滤准确率 > 85%
- [ ] RAG查询延迟 < 2s（首次）, < 500ms（缓存）

---

### Phase 3: RAG驱动PPT生成 (Week 4-5)
**优先级**: 🟡 中（在演讲稿基础上扩展）

**任务**:
1. 创建 `backend/app/services/ppt_exporter_rag.py`
   - 实现内容规划阶段（RAG查询）
   - 实现幻灯片叙述增强
   - 添加来源引用和最佳实践注释

2. 更新 `backend/app/api/export.py`
   - 添加 `POST /api/export/ppt-enhanced` 端点
   - 添加 `POST /api/rag/preview` 端点（上下文预览）

3. 前端组件
   - 更新 `ExportMenu` 添加RAG增强选项
   - 创建 `RAGContextPreview` 组件

**验证标准**:
- [ ] 生成的PPT包含RAG来源的最佳实践
- [ ] 演讲者注释含领域知识
- [ ] 页脚显示来源引用

---

### Phase 4: 前端全面集成 (Week 6)
**优先级**: 🔴 高（完整用户体验）

**任务**:
1. 集成所有后端功能到统一的UI
2. 优化流式体验（打字机效果）
3. 添加来源引用展示
4. 添加演讲稿历史版本管理

**验证标准**:
- [ ] 完整的生成→编辑→导出工作流
- [ ] 打字机效果流畅（无卡顿）
- [ ] 用户体验评分 > 4/5

---

### Phase 5: 高级功能（可选） (Week 7+)
**优先级**: 🟢 低（Nice-to-have）

**任务**:
- Slidev RAG增强
- 多模态图表生成
- A/B测试不同prompt模板
- 导出分析仪表板

---

## 调整说明（基于用户反馈）

**相比原计划的主要调整**:

1. **优先级重排**:
   - ✅ 演讲稿生成从Week 5提前到Week 1（最高优先级）
   - ✅ 图相似度简化，从复杂的图嵌入改为简单统计特征
   - ✅ PPT生成延后到Week 4（在演讲稿验证成功后）

2. **功能增强**:
   - ✅ 新增专业Prompt模板系统（CO-STAR框架）
   - ✅ 新增二次编辑和润色功能（用户明确需求）
   - ✅ 新增AI改进建议（而非直接修改）

3. **技术简化**:
   - ✅ 图相似度不用NetworkX和图嵌入，用简单统计特征
   - ✅ 保持多provider架构（不固定某个provider）
   - ✅ 分阶段交付，快速验证效果

**预期工期**: 5-6周核心功能，7+周完整功能

---

## 技术可行性评估

### ✅ 高可行性
- **RAG混合检索**: ChromaDB支持元数据过滤，NetworkX成熟
- **文本叙述增强**: 提示词工程，无技术门槛
- **流式API**: FastAPI原生支持SSE
- **前端集成**: React + Zustand已有类似模式

### ⚠️ 中等可行性
- **图相似度搜索**: 需要图嵌入模型（可用graph2vec或简化为特征向量）
- **多模态图表生成**: 需要AI+matplotlib协调（可降级为纯matplotlib）
- **Reranking**: Cross-encoder推理较慢（可缓存结果）

### ⚡ 风险点
- **RAG查询延迟**: 首次查询26s（缓解：预热+缓存）
- **流式传输中断**: 网络问题（缓解：断点续传）
- **AI幻觉**: RAG上下文不相关（缓解：相关性阈值过滤）

---

## 性能优化策略

### RAG查询优化
```python
# 查询缓存（Redis）
@cached(ttl=3600, key_prefix="rag:search")
async def cached_hybrid_search(query: str):
    return await rag.hybrid_search(query)

# 并行查询
async def parallel_rag_queries(queries: List[str]):
    tasks = [rag.hybrid_search(q) for q in queries]
    return await asyncio.gather(*tasks)
```

### 流式传输优化
```python
# Token缓冲（避免网络抖动）
BUFFER_SIZE = 10
token_buffer = []

async for token in ai_stream:
    token_buffer.append(token)
    if len(token_buffer) >= BUFFER_SIZE:
        yield "".join(token_buffer)
        token_buffer.clear()
```

---

## 质量保证标准

### 专业性指标
- ✅ PPT包含至少3个RAG来源的最佳实践
- ✅ 演讲稿引用至少2个具体案例（来自RAG）
- ✅ 所有断言都有来源引用

### 准确性指标
- ✅ RAG检索相关性 > 0.7（基于人工评估）
- ✅ 生成内容与架构图一致性 > 95%
- ✅ 无明显AI幻觉（由RAG上下文约束）

### 可用性指标
- ✅ PPT导出时间 < 30s
- ✅ 演讲稿生成首token延迟 < 3s
- ✅ 流式传输无明显卡顿（帧率 > 10 token/s）

---

## 关键文件路径

### 后端核心文件
- `D:\file\openproject\SmartArchitect\backend\app\services\rag.py` - 现有RAG服务（需增强）
- `D:\file\openproject\SmartArchitect\backend\app\services\rag_enhanced.py` - 增强RAG服务（新建）
- `D:\file\openproject\SmartArchitect\backend\app\services\ppt_exporter_rag.py` - RAG驱动PPT（新建）
- `D:\file\openproject\SmartArchitect\backend\app\services\speech_script_rag.py` - 流式演讲稿（新建）
- `D:\file\openproject\SmartArchitect\backend\app\services\ai_vision.py` - AI服务（需增强）
- `D:\file\openproject\SmartArchitect\backend\app\api\export.py` - 导出API（需扩展）
- `D:\file\openproject\SmartArchitect\backend\app\models\schemas.py` - 数据模型（需扩展）

### 前端核心文件
- `D:\file\openproject\SmartArchitect\frontend\components\ExportMenu.tsx` - 现有导出菜单（需替换）
- `D:\file\openproject\SmartArchitect\frontend\components\EnhancedExportMenu.tsx` - 增强导出菜单（新建）
- `D:\file\openproject\SmartArchitect\frontend\components\RAGContextPreview.tsx` - 上下文预览（新建）
- `D:\file\openproject\SmartArchitect\frontend\components\ScriptGeneratorStream.tsx` - 流式脚本（新建）
- `D:\file\openproject\SmartArchitect\frontend\lib\store\useArchitectStore.ts` - 全局状态（需扩展）

---

## 参考资料

技术方案基于以下2025-2026前沿研究和最佳实践：

### RAG与演示文稿生成
- [Mastering PowerPoint Creation with RAG-Powered Automation](https://abxda.medium.com/mastering-powerpoint-creation-with-rag-powered-automation-in-google-colab-e3499015d6d6) - RAG-powered presentation automation实践
- [AI Presentation Makers 2026](https://www.slidesai.io/blog/best-ai-presentation-makers) - Tome/Gamma等AI工具的设计模式
- [Architecture Project Presentation Guide](https://slidemodel.com/architecture-project-presentation/) - 架构演示最佳实践

### Prompt Engineering最佳实践（2025-2026）
- [IBM's 2026 Guide to Prompt Engineering](https://www.ibm.com/think/prompt-engineering) - 企业级prompt工程指南，强调context engineering
- [Lakera's Ultimate Prompt Engineering Guide 2025](https://www.lakera.ai/blog/prompt-engineering-guide) - CO-STAR框架和role-based prompting
- [7 Prompt Engineering Templates That Work](https://dextralabs.com/blog/prompt-engineering-templates/) - 生产级prompt模板
- [Prompt Engineering Best Practices 2025](https://garrettlanders.com/prompt-engineering-guide-2025/) - 企业实施67%生产力提升案例

### 多模态AI与图表生成
- [ChartLlama: Multimodal LLM for Chart Generation](https://tingxueronghua.github.io/ChartLlama/) - 图表理解与生成
- [Multimodal AI Models 2026](https://www.bentoml.com/blog/multimodal-ai-a-guide-to-open-source-vision-language-models) - Claude 4/GPT-4V能力分析
- [LLM Visualization 2025](https://ai2.work/technology/ai-tech-llm-visualization-2025/) - 可视化最佳实践和未来方向

### 技术演讲与表达
- [Architecture Presentation to Clients](https://wonderslide.com/blog/presenting-an-architectural-project-to-clients/) - 客户演示的5个关键要素
- [Successful Architecture Project Presentation Tips](https://www.re-thinkingthefuture.com/rtf-fresh-perspectives/a1265-10-tips-to-make-successful-architecture-project-presentation/) - 10个成功演示技巧

---

## 验收标准

### 最终交付物
1. 增强型RAG服务（支持混合检索）
2. RAG驱动PPT生成器（6-8张专业幻灯片）
3. 流式演讲稿生成器（打字机效果）
4. 前端完整集成（上下文预览+配置UI）
5. 完整的API文档和使用示例

### 效果验证
- [ ] 生成的PPT包含领域知识（非空洞模板）
- [ ] 演讲稿引用具体案例（来自RAG）
- [ ] 所有来源可追溯（引用标注）
- [ ] 用户反馈专业性评分 > 8/10
- [ ] 技术团队评估可用性 > 85%

---

## 总结

这是一个**生产级**的RAG深度集成方案，不是玩具级别的demo。核心创新：

1. **混合检索** - 不仅语义匹配，还匹配架构结构
2. **多阶段生成** - 从规划到叙述到视觉的完整管道
3. **来源可追溯** - 所有断言都有RAG来源引用
4. **流式体验** - 实时反馈，无需长时间等待
5. **自适应深度** - 根据受众调整技术深度

基于Paper2Slides、ChartLlama等2025-2026前沿研究，结合SmartArchitect现有的ReactFlow和Excalidraw能力，可实现超越市面上通用工具的专业效果。
