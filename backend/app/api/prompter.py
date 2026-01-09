from fastapi import APIRouter, HTTPException, Form
from typing import Optional
import logging

from app.models.schemas import (
    PromptScenarioList,
    PromptExecutionRequest,
    PromptExecutionResponse
)
from app.services.prompter import create_prompter_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/prompter/scenarios", response_model=PromptScenarioList)
async def get_prompt_scenarios():
    """获取所有可用的 Prompter 场景预设

    Returns:
        PromptScenarioList: 包含所有预设场景的列表
    """
    try:
        service = create_prompter_service()
        return service.get_all_scenarios()
    except Exception as e:
        logger.error(f"Failed to get scenarios: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load prompt scenarios: {str(e)}"
        )


@router.post("/prompter/execute", response_model=PromptExecutionResponse)
async def execute_prompt(
    request: PromptExecutionRequest,
    provider: Optional[str] = Form("gemini"),
    api_key: Optional[str] = Form(None),
    base_url: Optional[str] = Form(None),
    model_name: Optional[str] = Form(None)
):
    """执行 Prompter 场景，对当前架构应用 AI 转换

    Args:
        request: 包含场景 ID、节点、边和可选用户输入的请求
        provider: AI 提供商 (gemini, openai, claude, custom)
        api_key: API 密钥（可选，如果已在环境中配置）
        base_url: API 基础 URL（所有 provider 都可传入）
        model_name: 模型名称（所有 provider 都可传入）

    Returns:
        PromptExecutionResponse: 转换后的架构（节点、边、Mermaid 代码）
    """
    try:
        logger.info(f"Executing prompt scenario: {request.scenario_id}")
        logger.info(f"Input: {len(request.nodes)} nodes, {len(request.edges)} edges")

        service = create_prompter_service()
        result = await service.execute_prompt(
            request=request,
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )

        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.message or "Prompt execution failed"
            )

        logger.info(f"Result: {len(result.nodes)} nodes, {len(result.edges)} edges")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prompt execution failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Prompt execution error: {str(e)}"
        )


@router.get("/prompter/health")
async def prompter_health():
    """Prompter 服务健康检查

    Returns:
        dict: 服务状态和可用场景数量
    """
    try:
        service = create_prompter_service()
        scenarios = service.get_all_scenarios()

        return {
            "status": "healthy",
            "scenarios_loaded": len(scenarios.scenarios),
            "available_scenarios": [s.id for s in scenarios.scenarios]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
