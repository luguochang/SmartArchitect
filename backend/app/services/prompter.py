import json
import logging
from pathlib import Path
from typing import List, Optional

from app.models.schemas import (
    PromptScenario,
    PromptScenarioList,
    PromptExecutionRequest,
    PromptExecutionResponse,
    Node,
    Edge,
    ImageAnalysisResponse
)
from app.services.ai_vision import create_vision_service
from app.core.config import settings

logger = logging.getLogger(__name__)


class PrompterService:
    """Prompter 系统服务 - 管理提示词场景和执行"""

    def __init__(self):
        self.presets_path = Path(__file__).parent.parent / "data" / "prompt_presets.json"
        self.scenarios: List[PromptScenario] = []
        self._load_presets()

    def _load_presets(self):
        """从 JSON 文件加载预设场景"""
        try:
            with open(self.presets_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.scenarios = [PromptScenario(**scenario) for scenario in data["scenarios"]]
            logger.info(f"Loaded {len(self.scenarios)} prompt scenarios")
        except Exception as e:
            logger.error(f"Failed to load prompt presets: {e}")
            self.scenarios = []

    def get_all_scenarios(self) -> PromptScenarioList:
        """获取所有可用的场景"""
        return PromptScenarioList(scenarios=self.scenarios)

    def get_scenario(self, scenario_id: str) -> Optional[PromptScenario]:
        """根据 ID 获取场景"""
        for scenario in self.scenarios:
            if scenario.id == scenario_id:
                return scenario
        return None

    async def execute_prompt(
        self,
        request: PromptExecutionRequest,
        provider: str = "gemini",
        api_key: Optional[str] = None
    ) -> PromptExecutionResponse:
        """执行 Prompter 场景"""

        # 1. 获取场景
        scenario = self.get_scenario(request.scenario_id)
        if not scenario:
            return PromptExecutionResponse(
                nodes=request.nodes,
                edges=request.edges,
                mermaid_code=request.mermaid_code or "",
                ai_explanation="",
                success=False,
                message=f"Scenario not found: {request.scenario_id}"
            )

        logger.info(f"Executing prompt scenario: {scenario.name}")

        # 2. 构建提示词
        node_count = len(request.nodes)
        edge_count = len(request.edges)

        # 填充用户提示词模板
        user_prompt = scenario.user_prompt_template.format(
            node_count=node_count,
            edge_count=edge_count
        )

        # 如果用户提供了额外输入,追加到提示词
        if request.user_input:
            user_prompt += f"\n\nAdditional context: {request.user_input}"

        # 3. 构建架构描述
        architecture_desc = self._build_architecture_description(
            request.nodes,
            request.edges
        )

        # 4. 组合完整提示词
        full_prompt = f"""{scenario.system_prompt}

Current Architecture:
{architecture_desc}

Task: {user_prompt}

CRITICAL: You must respond with ONLY valid JSON in this exact format:
{{
  "nodes": [
    {{"id": "string", "type": "api|service|database|default", "position": {{"x": number, "y": number}}, "data": {{"label": "string"}}}}
  ],
  "edges": [
    {{"id": "string", "source": "string", "target": "string", "label": "optional string"}}
  ],
  "mermaid_code": "graph TD\\n  ...",
  "ai_analysis": {{
    "suggestions": ["string"],
    "confidence": 0.0,
    "model_used": "string"
  }}
}}

Do NOT include any explanatory text outside the JSON. The response must be parseable as JSON.
"""

        logger.debug(f"Prompter full prompt:\n{full_prompt}")

        # 5. 调用 AI Vision Service (text-only mode)
        try:
            vision_service = create_vision_service(
                provider=provider,
                api_key=api_key
            )

            # 使用 AI 生成优化后的架构
            result = await self._call_ai_with_text_prompt(
                vision_service,
                full_prompt,
                provider
            )

            return PromptExecutionResponse(
                nodes=result["nodes"],
                edges=result["edges"],
                mermaid_code=result.get("mermaid_code", ""),
                ai_explanation=result.get("ai_explanation", "Architecture transformed successfully"),
                success=True
            )

        except Exception as e:
            logger.error(f"Prompter execution failed: {e}", exc_info=True)
            return PromptExecutionResponse(
                nodes=request.nodes,
                edges=request.edges,
                mermaid_code=request.mermaid_code or "",
                ai_explanation="",
                success=False,
                message=f"Execution failed: {str(e)}"
            )

    def _build_architecture_description(
        self,
        nodes: List[Node],
        edges: List[Edge]
    ) -> str:
        """将当前架构转换为文本描述"""

        desc = f"Architecture with {len(nodes)} components:\n\n"

        # 节点列表
        desc += "Components:\n"
        for node in nodes:
            desc += f"- {node.data.label} (type: {node.type}, id: {node.id})\n"

        # 连接列表
        desc += f"\nConnections ({len(edges)} total):\n"
        for edge in edges:
            source_node = next((n for n in nodes if n.id == edge.source), None)
            target_node = next((n for n in nodes if n.id == edge.target), None)

            source_label = source_node.data.label if source_node else edge.source
            target_label = target_node.data.label if target_node else edge.target
            edge_label = f" ({edge.label})" if edge.label else ""

            desc += f"- {source_label} → {target_label}{edge_label}\n"

        return desc

    async def _call_ai_with_text_prompt(
        self,
        vision_service,
        prompt: str,
        provider: str
    ) -> dict:
        """调用 AI 服务处理文本提示词"""

        if provider == "gemini":
            response = await vision_service._analyze_with_gemini_text(prompt)
        elif provider == "openai":
            response = await vision_service._analyze_with_openai_text(prompt)
        elif provider == "claude":
            response = await vision_service._analyze_with_claude_text(prompt)
        else:
            response = await vision_service._analyze_with_custom_text(prompt)

        return response


# Helper function to create service instance
def create_prompter_service() -> PrompterService:
    """创建 PrompterService 实例"""
    return PrompterService()
