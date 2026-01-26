"""
专业演讲稿生成服务
基于CO-STAR框架和RAG增强

Author: SmartArchitect Team
Date: 2026-01-22
"""

from typing import List, Optional, Dict, AsyncGenerator
from collections import Counter
import json
import logging
import asyncio
from pathlib import Path

from app.models.schemas import (
    Node, Edge, ScriptOptions, ScriptContent, ScriptMetadata,
    StreamEvent, EnhancedSpeechScriptRequest
)

logger = logging.getLogger(__name__)


class ProfessionalPromptBuilder:
    """
    专业演讲稿Prompt构建器
    基于CO-STAR框架 + Role-based prompting + 演讲稿要素约束

    参考:
    - https://www.lakera.ai/blog/prompt-engineering-guide
    - https://www.ibm.com/think/prompt-engineering
    """

    def __init__(self):
        # 演讲稿必需要素（约束大模型生成高质量内容）
        self.duration_specs = {
            "30s": {
                "words": "120-160",
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
                "words": "560-640",
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
                "words": "1400-1600",
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

    def build_script_prompt(
        self,
        nodes: List[Node],
        edges: List[Edge],
        duration: str,
        rag_context: Optional[Dict] = None,
        options: Optional[ScriptOptions] = None
    ) -> str:
        """
        构建约束式专业演讲稿生成prompt
        """
        if options is None:
            options = ScriptOptions()

        spec = self.duration_specs[duration]

        # === CO-STAR框架构建 ===

        # C - Context (上下文)
        context_section = f"""
## 📋 CONTEXT (上下文背景)

### 当前架构概览
{self._format_architecture_detailed(nodes, edges)}

### 知识库检索结果（公司最佳实践）
{self._format_rag_context_structured(rag_context) if rag_context else "（暂无RAG上下文）"}

### 检测到的架构模式
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

    def _format_architecture_detailed(self, nodes: List[Node], edges: List[Edge]) -> str:
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

    def _format_rag_context_structured(self, rag_context: Optional[Dict]) -> str:
        """格式化RAG上下文"""
        if not rag_context:
            return "（暂无相关文档）"

        chunks = rag_context.get("chunks", [])
        if not chunks:
            return "（暂无相关文档）"

        formatted = f"找到 {len(chunks)} 个相关文档片段:\n\n"
        for i, chunk in enumerate(chunks[:3], 1):
            formatted += f"{i}. {chunk.get('content', '')[:200]}...\n"
            formatted += f"   来源: {chunk.get('metadata', {}).get('filename', 'Unknown')}\n\n"

        return formatted

    def _extract_tech_stack(self, nodes: List[Node]) -> str:
        """提取技术栈"""
        # 从节点类型推断技术栈
        node_types = [n.type for n in nodes if n.type]
        type_counts = Counter(node_types)

        tech_stack = []
        if type_counts.get("database") or type_counts.get("storage"):
            tech_stack.append("数据存储")
        if type_counts.get("api") or type_counts.get("gateway"):
            tech_stack.append("API网关")
        if type_counts.get("service"):
            tech_stack.append("微服务")
        if type_counts.get("cache"):
            tech_stack.append("缓存")

        return ", ".join(tech_stack) if tech_stack else "通用架构"

    def _assess_complexity(self, nodes: List[Node], edges: List[Edge]) -> str:
        """评估架构复杂度"""
        node_count = len(nodes)
        edge_count = len(edges)

        if node_count <= 5 and edge_count <= 5:
            return "简单（5个以下组件）"
        elif node_count <= 15 and edge_count <= 20:
            return "中等（5-15个组件）"
        else:
            return f"复杂（{node_count}个组件，{edge_count}个连接）"

    def _generate_intro_template(self, spec: Dict) -> str:
        """生成开场模板"""
        if spec['words'].startswith('120'):
            return """
（30秒电梯演讲）
- 用1个问题或数据开场（吸引注意）
- 1句话说明这个架构解决什么问题
- 1个核心亮点或指标
- 行动号召
"""
        elif spec['words'].startswith('560'):
            return """
（2分钟开场 - 约120字）
- 讲一个3-5句话的故事或场景（引发共鸣）
- 或者用一个令人惊讶的数据/事实开场
- 快速过渡到当前痛点
- 引出架构设计的必要性

示例: "想象一下，当100万用户同时涌入系统，而你的数据库开始报警。这不是假设，这是我们去年双11遇到的真实场景。今天我要分享的，就是我们如何用这套架构解决这个问题。"
"""
        else:
            return """
（5分钟开场 - 约300字）
- 用故事/统计数据/行业趋势开场（1-2分钟）
- 建立业务背景：为什么需要这个架构？
- 技术挑战：面临哪些具体问题？
- 简要预告：我们的解决方案的核心思路（3个关键词）

示例: "2023年，Gartner报告指出，75%的企业在数字化转型中遇到架构瓶颈。我们公司也不例外。去年，我们的单体应用开始出现性能问题，响应时间从200ms飙升到3秒，用户投诉激增。经过6个月的架构重构，我们不仅解决了性能问题，还将部署频率从每月1次提升到每天10次。今天，我想分享这个架构背后的设计思路和实践经验。"
"""

    def _generate_body_template(self, spec: Dict, nodes: List[Node], edges: List[Edge]) -> str:
        """生成主体模板"""
        if spec['words'].startswith('120'):
            return "（30秒主体）直接说核心价值和关键指标，不展开细节"
        elif spec['words'].startswith('560'):
            return """
（2分钟主体 - 约400字）

分3个段落:

**段落1: 架构设计核心思路（120字）**
- 我们采用了什么架构模式？（从RAG上下文引用）
- 为什么选择这个方案？（权衡决策）
- 与传统方案的对比

**段落2: 关键组件和数据流（160字）**
- 3个最重要的组件及其职责
- 核心数据流路径
- 用类比让非技术受众也能理解

**段落3: 价值证明（120字）**
- 性能提升: XX%（具体数字）
- 成本优化: 节省XX（具体金额）
- 或引用RAG中的相似案例: "这种架构在XX公司也取得了类似效果..."
"""
        else:
            return """
（5分钟主体 - 约1000字）

分5个段落:

**段落1: 架构设计理念（200字）**
- 设计原则（如：高内聚低耦合、单一职责）
- 为什么选择这些原则？（结合业务场景）
- 从RAG引用业界最佳实践

**段落2-4: 核心组件深入讲解（每个组件160-200字）**
选择3-4个最重要的组件:
- 组件的职责和设计考量
- 技术选型的权衡（为什么用Redis而不是Memcached？）
- 性能数据或压测结果
- 从RAG引用相似案例或反模式

**段落5: 风险与对策（200字）**
- 已知的技术风险（不要回避）
- 缓解措施和备选方案
- 监控和告警策略

**段落6: 价值总结（200字）**
- 量化的业务价值
- 技术债务的改善
- 团队效能提升
"""

    def _generate_conclusion_template(self, spec: Dict) -> str:
        """生成结尾模板"""
        if spec['words'].startswith('120'):
            return "（10秒结尾）清晰的行动号召: 'Let's discuss' / '欢迎试用' / '我们可以帮你实现'"
        elif spec['words'].startswith('560'):
            return """
（2分钟结尾 - 约80字）
- 回顾核心价值（1句话）
- 行动号召或下一步建议
- 留一个开放式问题引发思考

示例: "通过这套架构，我们不仅解决了性能问题，更重要的是建立了一个可持续演进的技术体系。如果你也面临类似挑战，不妨思考一下：你的架构是否为未来的增长预留了空间？"
"""
        else:
            return """
（5分钟结尾 - 约200字）
- 总结3个关键要点（呼应开场）
- 未来演进方向
- 抛出2-3个思考问题引导Q&A
- 感谢和联系方式

示例: "今天我们分享了从单体到微服务的架构演进之路。核心要点有三个：第一，渐进式迁移比大爆炸重写更安全；第二，观测性是微服务架构的生命线；第三，团队组织要与架构对齐。未来，我们计划引入服务网格和边缘计算能力。我想留几个问题给大家：1) 你们如何处理微服务的分布式事务？2) 在你们的场景中，服务粒度如何划分？欢迎会后交流。谢谢大家！"
"""

    def _generate_quality_checklist(self, spec: Dict) -> str:
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

    def _get_audience_background(self, audience: str) -> str:
        """根据受众返回背景"""
        backgrounds = {
            "executive": "高管背景，关注战略和ROI，不熟悉技术细节",
            "technical": "技术背景，熟悉专业术语，关注实现细节",
            "mixed": "混合背景，包含技术和非技术人员"
        }
        return backgrounds.get(audience, "混合背景")

    def _get_technical_depth(self, audience: str) -> str:
        """返回技术深度指导"""
        depth = {
            "executive": "高层次，少用技术术语，多讲业务价值",
            "technical": "深入技术细节，可以使用专业术语，但要解释设计决策",
            "mixed": "分层表达：先讲what和why（业务价值），再讲how（技术实现）"
        }
        return depth.get(audience, "中等深度，兼顾业务和技术")

    def _get_terminology_guidance(self, audience: str) -> str:
        """返回术语使用指导"""
        guidance = {
            "executive": "避免技术术语，必要时用类比解释",
            "technical": "可以使用专业术语，但要解释关键概念",
            "mixed": "技术术语后加简单解释（如：'微服务，即将系统拆分为独立的小服务'）"
        }
        return guidance.get(audience, "适度使用，加以解释")

    def _get_example_style(self, audience: str) -> str:
        """返回举例方式"""
        styles = {
            "executive": "用商业案例，引用知名公司（如：Amazon、Netflix）",
            "technical": "用技术案例，引用具体技术栈和数据",
            "mixed": "先讲商业价值，再讲技术细节"
        }
        return styles.get(audience, "兼顾商业和技术案例")


class RAGSpeechScriptGenerator:
    """
    演讲稿生成器（带RAG增强和流式传输）
    """

    def __init__(self, rag_service=None, ai_service=None):
        self.prompt_builder = ProfessionalPromptBuilder()
        self.rag_service = rag_service
        self.ai_service = ai_service
        logger.info(f"RAGSpeechScriptGenerator initialized with AI service: {ai_service is not None}")

    async def generate_speech_script_stream(
        self,
        nodes: List[Node],
        edges: List[Edge],
        duration: str,
        options: Optional[ScriptOptions] = None
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        流式生成演讲稿

        Yields:
            StreamEvent: 流式事件（CONTEXT_SEARCH, CONTEXT_FOUND, TOKEN, COMPLETE等）
        """
        if options is None:
            options = ScriptOptions()

        try:
            # Phase 1: RAG上下文检索
            yield StreamEvent(
                type="CONTEXT_SEARCH",
                data={"status": "搜索知识库..."}
            )

            rag_context = None
            if self.rag_service:
                try:
                    # 构建查询
                    query = self.build_context_query(nodes, edges, duration)

                    # 调用RAG服务（这里需要实现RAG服务的集成）
                    # rag_context = await self.rag_service.search(query, top_k=10)

                    # 临时mock数据（实际应调用RAG服务）
                    rag_context = {
                        "chunks": [],
                        "query": query
                    }

                    yield StreamEvent(
                        type="CONTEXT_FOUND",
                        data={
                            "chunks_found": len(rag_context.get("chunks", [])),
                            "patterns": [],
                            "sources": []
                        }
                    )
                except Exception as e:
                    # RAG失败不影响生成，只是警告
                    yield StreamEvent(
                        type="CONTEXT_FOUND",
                        data={
                            "chunks_found": 0,
                            "warning": f"RAG查询失败: {str(e)}"
                        }
                    )
            else:
                # 没有RAG服务，也要发出CONTEXT_FOUND事件
                rag_context = {"chunks": [], "suggested_patterns": []}
                yield StreamEvent(
                    type="CONTEXT_FOUND",
                    data={
                        "chunks_found": 0,
                        "patterns": [],
                        "sources": [],
                        "note": "RAG服务未启用"
                    }
                )

            # Phase 2: 构建增强提示词
            prompt = self.prompt_builder.build_script_prompt(
                nodes, edges, duration, rag_context, options
            )

            # Phase 3: 流式生成
            yield StreamEvent(
                type="GENERATION_START",
                data={"message": "AI正在创作演讲稿，请稍候..."}
            )

            accumulated = ""
            current_section = "intro"

            # 使用AI服务生成演讲稿
            if self.ai_service:
                logger.info("Using AI service to generate speech script with streaming")
                try:
                    # 使用真正的流式生成
                    async for chunk in self.ai_service.generate_speech_script_stream(
                        nodes=nodes,
                        edges=edges,
                        duration=duration
                    ):
                        accumulated += chunk

                        # 发送chunks
                        yield StreamEvent(
                            type="TOKEN",
                            data={"token": chunk, "section": current_section}
                        )

                        # 检测章节切换（基于常见的段落模式）
                        if "\n\n" in accumulated[-30:] and len(accumulated) > 100:
                            # 简单启发式判断章节
                            word_count = self._count_words(accumulated)
                            target = self._get_target_words(duration)

                            if current_section == "intro" and word_count > target * 0.2:
                                current_section = "body"
                                yield StreamEvent(
                                    type="SECTION_COMPLETE",
                                    data={
                                        "section": "intro",
                                        "content": ""
                                    }
                                )
                            elif current_section == "body" and word_count > target * 0.8:
                                current_section = "conclusion"
                                yield StreamEvent(
                                    type="SECTION_COMPLETE",
                                    data={
                                        "section": "body",
                                        "content": ""
                                    }
                                )

                    logger.info(f"Streaming generation completed, total length: {len(accumulated)}")

                except Exception as ai_error:
                    logger.error(f"AI service generation failed: {ai_error}", exc_info=True)
                    logger.warning("Falling back to mock data")
                    # 降级到Mock数据
                    accumulated = self._generate_mock_script(nodes, edges, duration)
            else:
                logger.warning("No AI service configured, using mock data")
                # 没有AI服务，使用Mock数据
                mock_script = self._generate_mock_script(nodes, edges, duration)

                # 模拟流式输出
                for char in mock_script:
                    accumulated += char
                    yield StreamEvent(
                        type="TOKEN",
                        data={"token": char, "section": current_section}
                    )
                    await asyncio.sleep(0.001)

                    # 检测章节切换
                    if "[BODY]" in accumulated and current_section == "intro":
                        current_section = "body"
                        yield StreamEvent(
                            type="SECTION_COMPLETE",
                            data={
                                "section": "intro",
                                "content": self.extract_section(accumulated, "intro")
                            }
                        )
                    elif "[CONCLUSION]" in accumulated and current_section == "body":
                        current_section = "conclusion"
                        yield StreamEvent(
                            type="SECTION_COMPLETE",
                            data={
                                "section": "body",
                                "content": self.extract_section(accumulated, "body")
                            }
                        )

            # Phase 4: 后处理
            final_script = self.post_process_script(accumulated, duration)
            sections = self._split_into_sections(final_script)

            yield StreamEvent(
                type="COMPLETE",
                data={
                    "script": {
                        "intro": sections.get("intro", ""),
                        "body": sections.get("body", ""),
                        "conclusion": sections.get("conclusion", ""),
                        "full_text": final_script
                    },
                    "word_count": self._count_words(final_script),
                    "estimated_seconds": self.estimate_duration(final_script),
                    "rag_sources": []
                }
            )

        except Exception as e:
            yield StreamEvent(
                type="ERROR",
                data={"error": str(e)}
            )

    def build_context_query(
        self,
        nodes: List[Node],
        edges: List[Edge],
        duration: str
    ) -> str:
        """构建RAG查询字符串"""
        # 提取关键组件
        node_labels = [n.data.label for n in nodes[:5]]

        # 提取节点类型
        node_types = list(set([n.type for n in nodes if n.type]))

        query = f"Architecture with {len(nodes)} components: "
        query += ", ".join(node_labels)
        query += f". Types: {', '.join(node_types)}"

        return query

    def post_process_script(self, script: str, duration: str) -> str:
        """
        后处理演讲稿

        Args:
            script: 原始脚本（包含 [INTRO]、[BODY]、[CONCLUSION] 标记）
            duration: 时长

        Returns:
            str: 处理后的演讲稿（保留完整内容）
        """
        # 移除markdown标记
        script = script.replace("[INTRO]\n", "").replace("[BODY]\n", "").replace("[CONCLUSION]\n", "")
        script = script.replace("[INTRO]", "").replace("[BODY]", "").replace("[CONCLUSION]", "")

        # 清理多个连续空行（替换为最多2个换行）
        import re
        script = re.sub(r'\n{3,}', '\n\n', script)

        return script.strip()

    def estimate_duration(self, script: str) -> int:
        """
        估算演讲时长（秒数）

        Args:
            script: 演讲稿文本

        Returns:
            int: 预估时长（秒）
        """
        word_count = self._count_words(script)

        # 平均每分钟150字
        minutes = word_count / 150
        seconds = int(minutes * 60)

        return seconds

    def _count_words(self, text: str) -> int:
        """
        智能计算中英文混合文本的字数

        中文字符计为1个字，英文单词计为1个词

        Args:
            text: 文本内容

        Returns:
            int: 字数
        """
        import re

        # 移除所有空白字符
        text_no_space = re.sub(r'\s+', '', text)

        # 分离中文字符和英文单词
        # 中文字符范围：\u4e00-\u9fff
        chinese_chars = re.findall(r'[\u4e00-\u9fff]', text_no_space)
        chinese_count = len(chinese_chars)

        # 英文单词（连续的英文字母）
        english_words = re.findall(r'[a-zA-Z]+', text)
        english_count = len(english_words)

        # 数字和符号不计入字数
        total = chinese_count + english_count

        return total

    def _get_target_words(self, duration: str) -> int:
        """获取目标字数"""
        targets = {
            "30s": 140,
            "2min": 600,
            "5min": 1500
        }
        return targets.get(duration, 600)

    def extract_section(self, accumulated: str, section: str) -> str:
        """提取特定章节"""
        if section == "intro":
            if "[BODY]" in accumulated:
                return accumulated.split("[BODY]")[0].replace("[INTRO]", "").strip()
        elif section == "body":
            if "[BODY]" in accumulated and "[CONCLUSION]" in accumulated:
                body_part = accumulated.split("[BODY]")[1]
                return body_part.split("[CONCLUSION]")[0].strip()
        elif section == "conclusion":
            if "[CONCLUSION]" in accumulated:
                return accumulated.split("[CONCLUSION]")[1].strip()

        return ""

    def _split_into_sections(self, script: str) -> dict:
        """将演讲稿分割为三个章节"""
        # 简单策略：按段落数量分割
        paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]

        if len(paragraphs) <= 3:
            return {
                "intro": paragraphs[0] if len(paragraphs) > 0 else "",
                "body": paragraphs[1] if len(paragraphs) > 1 else "",
                "conclusion": paragraphs[2] if len(paragraphs) > 2 else ""
            }

        # 按比例分割：开场20%，主体60%，结尾20%
        total = len(paragraphs)
        intro_end = max(1, int(total * 0.2))
        body_end = max(intro_end + 1, int(total * 0.8))

        return {
            "intro": "\n\n".join(paragraphs[:intro_end]),
            "body": "\n\n".join(paragraphs[intro_end:body_end]),
            "conclusion": "\n\n".join(paragraphs[body_end:])
        }

    def _generate_mock_script(
        self,
        nodes: List[Node],
        edges: List[Edge],
        duration: str
    ) -> str:
        """生成mock演讲稿（用于测试）"""
        node_count = len(nodes)
        edge_count = len(edges)

        if duration == "30s":
            return f"""[INTRO]
想象一下，当系统面临{node_count}个关键组件的协同挑战时，如何确保高可用性？今天我想分享我们的架构设计方案。

[BODY]
我们的架构包含{node_count}个核心组件，通过{edge_count}个关键连接实现数据流转。核心设计理念是模块化和解耦，每个组件职责清晰，便于扩展和维护。

[CONCLUSION]
这套架构不仅解决了当前问题，更为未来增长预留了空间。欢迎交流讨论！"""

        elif duration == "2min":
            components = ", ".join([n.data.label for n in nodes[:3]])
            return f"""[INTRO]
在当今快速发展的技术环境中，系统架构面临着前所未有的挑战。我们的系统包含{node_count}个组件，如何确保它们高效协作？今天，我想分享我们在架构设计上的实践和思考。

[BODY]
首先，让我介绍一下架构的核心组件。我们有{components}等{node_count}个关键模块，它们通过{edge_count}个精心设计的连接点进行数据交换。

在设计过程中，我们遵循了几个核心原则：第一，高内聚低耦合，确保每个组件职责单一；第二，可扩展性优先，为未来增长预留空间；第三，容错设计，任何单点故障都不会影响整体服务。

具体来说，我们采用了异步消息传递机制，将各组件解耦；使用缓存层提升性能，减少数据库压力；部署了监控告警系统，实时追踪系统健康状态。

通过这套架构，我们实现了99.9%的可用性，响应时间从原来的500ms降低到100ms以内，成本节省了30%。

[CONCLUSION]
总结一下，好的架构不是一蹴而就的，而是在实践中不断演进的。我们的经验是：从简单开始，持续优化，始终关注业务价值。如果你也面临类似挑战，欢迎会后交流。谢谢大家！"""

        else:  # 5min
            return f"""[INTRO]
各位同事，大家好！今天我想和大家分享一个我们团队在过去六个月中完成的架构升级项目。这个项目不仅解决了性能瓶颈，更重要的是，它为我们未来的业务增长奠定了坚实的技术基础。

让我先从一个场景说起。去年双11期间，当用户流量突增到平时的10倍时，我们的系统开始出现响应缓慢，甚至部分服务不可用。这次事故让我们意识到，原有的架构已经无法支撑业务的快速发展，必须进行彻底的重构。

[BODY]
在深入分析后，我们发现了几个核心问题：第一，单体应用架构导致任何小改动都需要整体重启；第二，数据库成为性能瓶颈，查询响应时间随着数据量增长急剧上升；第三，缺乏有效的缓存机制，大量重复计算浪费资源。

基于这些问题，我们设计了全新的架构。这个架构包含{node_count}个核心组件，通过{edge_count}个清晰定义的接口进行交互。核心设计理念有三点：第一，微服务化，将单体应用拆分为独立的服务单元；第二，多级缓存，从边缘到数据库建立完整的缓存体系；第三，异步化，非关键路径全部异步处理，提升响应速度。

让我详细介绍几个关键组件。{nodes[0].data.label if nodes else '核心组件'}负责业务逻辑处理，采用无状态设计，可以水平扩展。我们选择这个方案而不是传统的有状态服务，是因为无状态设计在云环境下更容易实现自动伸缩，运维成本更低。

{nodes[1].data.label if len(nodes) > 1 else '数据层'}使用了读写分离和分库分表策略。通过这种方式，我们将单库的压力分散到多个实例，查询性能提升了5倍。同时，我们引入了Redis作为缓存层，命中率达到95%，大幅减轻了数据库负担。

在数据流方面，我们建立了一套完整的异步消息系统。所有非实时的操作，如日志记录、数据统计、通知发送等，都通过消息队列异步处理。这不仅提升了用户体验，也让系统更加健壮。即使下游服务暂时不可用，消息也会被持久化保存，待恢复后继续处理。

当然，任何架构都不是完美的，我们也面临一些挑战。比如，微服务带来的分布式事务问题，我们采用了最终一致性方案，通过补偿机制确保数据正确性。再比如，服务间调用链路变长，可能导致延迟累积，我们通过熔断降级机制来保护系统稳定性。

从实施效果来看，新架构带来的改进非常明显。系统可用性从95%提升到99.9%，响应时间中位数从500ms降低到80ms，在双11期间轻松支撑了3倍于去年的流量。更重要的是，开发效率提升了50%，团队可以独立并行开发不同的服务模块，部署频率从每周一次提升到每天多次。

[CONCLUSION]
总结一下今天分享的核心要点。第一，架构设计要从业务痛点出发，不要为了技术而技术。第二，没有银弹，每种方案都有trade-off，要根据实际情况选择。第三，架构是演进的，从简单开始，持续优化，不要追求一步到位。

展望未来，我们计划引入服务网格技术，进一步简化服务间通信；同时探索边缘计算，将计算能力下沉到离用户更近的地方。

最后，我想留几个问题给大家思考：第一，在你们的场景中，如何平衡系统复杂度和可维护性？第二，微服务拆分的粒度如何把握？第三，如何建立有效的监控体系来保障分布式系统的稳定性？

如果大家对这些话题感兴趣，欢迎会后交流。我的联系方式在最后一页，期待和大家深入探讨。谢谢大家的聆听！"""


# ============================================================
# Service Factory (Singleton Pattern)
# ============================================================

# 不再使用单例模式，每次调用都创建新实例以支持不同的provider和api_key


def get_rag_speech_script_generator(
    provider: str = "gemini",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None
) -> RAGSpeechScriptGenerator:
    """
    Get RAGSpeechScriptGenerator instance with AI service

    Args:
        provider: AI provider (gemini, openai, claude, siliconflow, custom)
        api_key: API key for the provider
        base_url: Base URL for custom provider
        model_name: Model name for the provider

    Returns:
        RAGSpeechScriptGenerator instance with AI service configured
    """
    from app.services.ai_vision import create_vision_service

    # 创建AI视觉服务，传递所有配置参数
    ai_service = create_vision_service(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model_name=model_name
    )

    # 创建RAG演讲稿生成器（暂时不集成RAG服务）
    generator = RAGSpeechScriptGenerator(rag_service=None, ai_service=ai_service)

    logger.info(f"Created RAGSpeechScriptGenerator with provider: {provider}, model: {model_name or 'default'}")
    return generator
