from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

from app.models.schemas import (
    FlowTemplateList,
    ChatGenerationRequest,
    ChatGenerationResponse
)
from app.services.chat_generator import create_chat_generator_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/chat-generator/templates", response_model=FlowTemplateList)
async def get_flow_templates():
    """获取所有流程图示例模板

    Returns:
        FlowTemplateList: 包含预设模板（OOM排查、订单流程等）
    """
    try:
        service = create_chat_generator_service()
        return service.get_all_templates()
    except Exception as e:
        logger.error(f"Failed to get templates: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load templates: {str(e)}"
        )


@router.post("/chat-generator/generate", response_model=ChatGenerationResponse)
async def generate_flowchart(request: ChatGenerationRequest):
    """根据用户描述生成流程图

    Args:
        request: 包含用户输入、模板 ID、provider、API key 等配置

    Returns:
        ChatGenerationResponse: 生成的流程图节点、边、Mermaid 代码
    """
    try:
        logger.info(f"Generating flowchart from user input: {request.user_input[:50]}...")

        service = create_chat_generator_service()
        result = await service.generate_flowchart(
            request=request,
            provider=request.provider or "gemini",
            api_key=request.api_key,
            base_url=request.base_url,
            model_name=request.model_name
        )

        if not result.success:
            raise HTTPException(
                status_code=400,
                detail=result.message or "Generation failed"
            )

        logger.info(f"Generated: {len(result.nodes)} nodes, {len(result.edges)} edges")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Flowchart generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Generation error: {str(e)}"
        )
