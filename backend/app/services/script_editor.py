"""
演讲稿编辑服务 - Script Editor Service
支持保存草稿、版本管理、局部润色、AI改进建议

Author: Claude Code
Date: 2026-01-22
"""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Literal
from difflib import SequenceMatcher

from app.models.schemas import (
    ScriptContent,
    ScriptMetadata,
    ScriptDraft,
    SaveDraftResponse,
    RefinedSectionResponse,
    ImprovementSuggestion,
    ImprovementSuggestions,
)


class ScriptEditorService:
    """
    演讲稿二次编辑服务
    支持保存草稿、版本管理、局部润色
    """

    def __init__(self, storage_dir: str = "./data/scripts"):
        """
        初始化编辑服务

        Args:
            storage_dir: 草稿存储目录
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

        # AI服务将在后续集成
        # TODO: Integrate with AIVisionService
        self.ai_service = None

    async def save_draft(
        self,
        script_id: str,
        content: ScriptContent,
        metadata: ScriptMetadata
    ) -> SaveDraftResponse:
        """
        保存演讲稿草稿（支持增量更新）

        Args:
            script_id: 演讲稿唯一ID
            content: 演讲稿内容（intro, body, conclusion, full_text）
            metadata: 元数据（duration, rag_sources等）

        Returns:
            SaveDraftResponse with script_id, version, saved_at
        """
        draft_file = self.storage_dir / f"{script_id}.json"

        # 如果是已有草稿，读取现有版本号
        current_version = 0
        created_at = None
        if draft_file.exists():
            existing_data = json.loads(draft_file.read_text(encoding='utf-8'))
            current_version = existing_data.get("version", 0)
            created_at = existing_data.get("metadata", {}).get("created_at")

        # 构建草稿数据
        draft_data = {
            "id": script_id,
            "content": {
                "intro": content.intro,
                "body": content.body,
                "conclusion": content.conclusion,
                "full_text": content.full_text
            },
            "metadata": {
                "created_at": created_at or metadata.created_at or datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "duration": metadata.duration,
                "word_count": len(content.full_text.split()),
                "rag_sources": metadata.rag_sources or [],
                "architecture_snapshot": metadata.architecture_snapshot,
                "version": metadata.version
            },
            "version": current_version + 1
        }

        # 写入文件
        draft_file.write_text(
            json.dumps(draft_data, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )

        return SaveDraftResponse(
            script_id=script_id,
            version=draft_data["version"],
            saved_at=draft_data["metadata"]["updated_at"],
            success=True
        )

    async def load_draft(self, script_id: str) -> Optional[ScriptDraft]:
        """
        加载演讲稿草稿

        Args:
            script_id: 演讲稿唯一ID

        Returns:
            ScriptDraft or None if not found
        """
        draft_file = self.storage_dir / f"{script_id}.json"

        if not draft_file.exists():
            return None

        try:
            draft_data = json.loads(draft_file.read_text(encoding='utf-8'))
            return ScriptDraft.parse_obj(draft_data)
        except Exception as e:
            print(f"Error loading draft {script_id}: {e}")
            return None

    async def refine_section(
        self,
        script_id: str,
        section: Literal["intro", "body", "conclusion"],
        user_feedback: str,
        rag_context: Optional[dict] = None
    ) -> RefinedSectionResponse:
        """
        局部润色演讲稿某个章节
        用户可以提供反馈，AI根据反馈重新生成

        Args:
            script_id: 演讲稿ID
            section: 要润色的章节（intro/body/conclusion）
            user_feedback: 用户反馈（如："增加数据支撑"）
            rag_context: 可选的补充RAG上下文

        Returns:
            RefinedSectionResponse with refined_text and changes_summary
        """
        # 加载当前草稿
        draft = await self.load_draft(script_id)
        if not draft:
            raise ValueError(f"Script {script_id} not found")

        current_section_text = getattr(draft.content, section)

        # 构建润色prompt
        refine_prompt = self._build_refine_prompt(
            section, current_section_text, user_feedback, rag_context
        )

        # TODO: 集成AI服务进行实际生成
        # 当前使用模拟数据
        refined_text = self._generate_mock_refined_section(
            current_section_text, user_feedback
        )

        # 更新草稿
        setattr(draft.content, section, refined_text)
        draft.content.full_text = self._rebuild_full_text(draft.content)
        draft.metadata.word_count = len(draft.content.full_text.split())
        draft.metadata.updated_at = datetime.now().isoformat()

        # 保存更新后的草稿
        await self.save_draft(script_id, draft.content, draft.metadata)

        # 生成变更摘要
        changes_summary = self._summarize_changes(current_section_text, refined_text)

        return RefinedSectionResponse(
            script_id=script_id,
            section=section,
            refined_text=refined_text,
            changes_summary=changes_summary,
            success=True
        )

    async def suggest_improvements(
        self,
        script_id: str,
        focus_areas: List[str] = None
    ) -> ImprovementSuggestions:
        """
        AI分析演讲稿，提供改进建议（不直接修改）

        Args:
            script_id: 演讲稿ID
            focus_areas: 关注领域（如：["clarity", "engagement", "flow"]）

        Returns:
            ImprovementSuggestions with score, strengths, weaknesses, suggestions
        """
        if focus_areas is None:
            focus_areas = ["clarity", "engagement", "flow"]

        # 加载草稿
        draft = await self.load_draft(script_id)
        if not draft:
            raise ValueError(f"Script {script_id} not found")

        # 构建分析prompt
        analysis_prompt = self._build_analysis_prompt(draft, focus_areas)

        # TODO: 集成AI服务进行实际分析
        # 当前使用模拟数据
        suggestions = self._generate_mock_suggestions(draft, focus_areas)

        return suggestions

    def _build_refine_prompt(
        self,
        section: str,
        current_text: str,
        user_feedback: str,
        rag_context: Optional[dict] = None
    ) -> str:
        """构建润色prompt"""
        prompt = f"""
你是专业的演讲稿编辑，负责根据用户反馈改进演讲稿的某个章节。

## 当前章节内容（{section}）:
{current_text}

## 用户反馈:
{user_feedback}

## 改进要求:
1. 保持原有的核心信息和结构
2. 根据用户反馈进行针对性调整
3. 确保改进后的文字更流畅、更有说服力
4. 保持字数在±20%范围内（当前: {len(current_text.split())}字）

"""

        if rag_context:
            prompt += f"\n## 补充的RAG上下文:\n{self._format_rag_context(rag_context)}\n"

        prompt += "\n请输出改进后的章节内容:\n"

        return prompt

    def _build_analysis_prompt(
        self,
        draft: ScriptDraft,
        focus_areas: List[str]
    ) -> str:
        """构建分析prompt"""
        return f"""
你是演讲稿专业顾问，分析以下演讲稿并提供改进建议。

## 演讲稿内容:
{draft.content.full_text}

## 分析维度:
{', '.join(focus_areas)}

## 元数据:
- 时长: {draft.metadata.duration}
- 字数: {draft.metadata.word_count}
- RAG来源: {len(draft.metadata.rag_sources)}个

请输出JSON格式分析结果:
{{
  "overall_score": 7.5,  // 1-10分
  "strengths": ["具体优点1", "具体优点2"],
  "weaknesses": ["具体问题1", "具体问题2"],
  "suggestions": [
    {{
      "section": "intro" | "body" | "conclusion" | "overall",
      "issue": "具体问题描述",
      "suggestion": "改进建议",
      "priority": "high" | "medium" | "low"
    }}
  ]
}}
"""

    def _rebuild_full_text(self, content: ScriptContent) -> str:
        """
        重新构建完整演讲稿文本

        Args:
            content: ScriptContent对象

        Returns:
            完整的演讲稿文本
        """
        sections = []

        if content.intro:
            sections.append("[INTRO]\n" + content.intro)

        if content.body:
            sections.append("\n[BODY]\n" + content.body)

        if content.conclusion:
            sections.append("\n[CONCLUSION]\n" + content.conclusion)

        return "\n".join(sections)

    def _summarize_changes(self, old_text: str, new_text: str) -> str:
        """
        生成文本变更摘要

        Args:
            old_text: 原文本
            new_text: 新文本

        Returns:
            变更摘要描述
        """
        # 使用SequenceMatcher计算相似度
        similarity = SequenceMatcher(None, old_text, new_text).ratio()

        old_words = len(old_text.split())
        new_words = len(new_text.split())
        word_change = new_words - old_words
        word_change_percent = (word_change / old_words * 100) if old_words > 0 else 0

        # 生成摘要
        summary_parts = []

        if similarity > 0.9:
            summary_parts.append("微调优化")
        elif similarity > 0.7:
            summary_parts.append("适度修改")
        elif similarity > 0.5:
            summary_parts.append("大幅改写")
        else:
            summary_parts.append("完全重写")

        if abs(word_change_percent) > 5:
            if word_change > 0:
                summary_parts.append(f"扩充内容（+{word_change}字，+{word_change_percent:.1f}%）")
            else:
                summary_parts.append(f"精简内容（{word_change}字，{word_change_percent:.1f}%）")

        # 简单的内容分析
        if "数据" in new_text and "数据" not in old_text:
            summary_parts.append("增加数据支撑")

        if "例如" in new_text and "例如" not in old_text:
            summary_parts.append("增加案例说明")

        if len(new_text.split("。")) > len(old_text.split("。")):
            summary_parts.append("增加句子数量")

        return "；".join(summary_parts) if summary_parts else "保持原样"

    def _format_rag_context(self, rag_context: dict) -> str:
        """
        格式化RAG上下文为可读文本

        Args:
            rag_context: RAG检索结果

        Returns:
            格式化的上下文文本
        """
        if not rag_context:
            return "无补充上下文"

        formatted = []

        if "chunks" in rag_context:
            for idx, chunk in enumerate(rag_context["chunks"][:3], 1):
                content = chunk.get("content", "")
                source = chunk.get("metadata", {}).get("filename", "Unknown")
                formatted.append(f"### 来源 {idx}: {source}\n{content[:200]}...")

        return "\n\n".join(formatted) if formatted else "无相关上下文"

    # ========== 模拟数据生成方法（用于测试）==========

    def _generate_mock_refined_section(
        self,
        original_text: str,
        user_feedback: str
    ) -> str:
        """
        生成模拟的润色文本（用于测试）
        TODO: 替换为实际AI生成
        """
        # 根据反馈关键词进行简单修改
        refined = original_text

        if "数据" in user_feedback or "案例" in user_feedback:
            # 在文本中插入数据示例
            refined = refined.replace(
                "。",
                "。根据我们的统计数据，这一方案使系统响应时间降低了40%，吞吐量提升了3倍。",
                1
            )

        if "类比" in user_feedback or "生动" in user_feedback:
            # 增加类比
            refined = refined.replace(
                "架构",
                "架构（就像城市的交通网络）",
                1
            )

        if "简化" in user_feedback or "精简" in user_feedback:
            # 简化表达
            sentences = refined.split("。")
            refined = "。".join(sentences[:max(1, len(sentences) - 1)]) + "。"

        if "专业" in user_feedback or "语气" in user_feedback:
            # 调整语气
            refined = refined.replace("我们觉得", "我们的分析表明")
            refined = refined.replace("可能", "明确")

        return refined

    def _generate_mock_suggestions(
        self,
        draft: ScriptDraft,
        focus_areas: List[str]
    ) -> ImprovementSuggestions:
        """
        生成模拟的改进建议（用于测试）
        TODO: 替换为实际AI分析
        """
        # 根据字数和时长评估基础分数
        target_words = {
            "30s": 70,
            "2min": 300,
            "5min": 750
        }

        target = target_words.get(draft.metadata.duration, 300)
        word_diff = abs(draft.metadata.word_count - target)
        word_score = max(5.0, 10.0 - (word_diff / target * 5))

        # 基于RAG来源数量评分
        rag_score = min(10.0, 5.0 + len(draft.metadata.rag_sources) * 1.5)

        overall_score = (word_score + rag_score) / 2

        # 生成优点
        strengths = []
        if draft.metadata.word_count > target * 0.9:
            strengths.append("字数控制恰当，符合目标时长要求")
        if draft.metadata.rag_sources:
            strengths.append(f"引用了{len(draft.metadata.rag_sources)}个RAG来源，内容有据可依")
        if "例如" in draft.content.full_text:
            strengths.append("包含具体案例说明，增强说服力")

        # 生成弱点
        weaknesses = []
        if draft.metadata.word_count < target * 0.8:
            weaknesses.append("内容偏少，可以扩充更多细节和案例")
        if "数据" not in draft.content.full_text and "%" not in draft.content.full_text:
            weaknesses.append("缺少量化数据支撑，建议增加具体指标")
        if draft.content.intro.count("。") < 2:
            weaknesses.append("开场部分过于简短，缺乏吸引力")

        # 生成具体建议
        suggestions = []

        if "clarity" in focus_areas:
            suggestions.append(ImprovementSuggestion(
                section="body",
                issue="主体部分技术术语较多，可能影响理解",
                suggestion="为关键技术术语增加通俗易懂的类比或解释",
                priority="medium"
            ))

        if "engagement" in focus_areas:
            suggestions.append(ImprovementSuggestion(
                section="intro",
                issue="开场缺少引人入胜的Hook",
                suggestion="可以用一个令人惊讶的数据或故事开场，例如：'想象一下，当100万用户同时涌入系统时...'",
                priority="high"
            ))

        if "flow" in focus_areas:
            suggestions.append(ImprovementSuggestion(
                section="overall",
                issue="段落之间过渡不够自然",
                suggestion="在段落间增加过渡句，如：'那么，我们是如何实现这一点的呢？'",
                priority="low"
            ))

        # 根据字数差异添加建议
        if word_diff > target * 0.2:
            suggestions.append(ImprovementSuggestion(
                section="overall",
                issue=f"当前字数{draft.metadata.word_count}，与目标{target}字相差{word_diff}字",
                suggestion="调整内容密度，确保在目标时长内完整表达核心观点",
                priority="high"
            ))

        return ImprovementSuggestions(
            overall_score=round(overall_score, 1),
            strengths=strengths or ["演讲稿结构完整"],
            weaknesses=weaknesses or ["暂无明显问题"],
            suggestions=suggestions,
            success=True
        )


# 全局服务实例（懒加载）
_script_editor_service: Optional[ScriptEditorService] = None


def get_script_editor_service() -> ScriptEditorService:
    """
    获取ScriptEditorService单例

    Returns:
        ScriptEditorService实例
    """
    global _script_editor_service
    if _script_editor_service is None:
        _script_editor_service = ScriptEditorService()
    return _script_editor_service
