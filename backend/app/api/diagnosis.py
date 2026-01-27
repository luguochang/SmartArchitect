"""诊断端点 - 测试 AI API 连接"""
from fastapi import APIRouter
from pydantic import BaseModel
from app.services.ai_vision import create_vision_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


class DiagnosisRequest(BaseModel):
    provider: str = "custom"
    api_key: str
    base_url: str
    model_name: str


class DiagnosisResponse(BaseModel):
    success: bool
    message: str
    details: dict


@router.post("/diagnosis/test-ai", response_model=DiagnosisResponse)
async def test_ai_connection(request: DiagnosisRequest):
    """测试 AI API 连接是否正常"""
    try:
        logger.info(f"[DIAGNOSIS] Testing {request.provider} with model {request.model_name}")

        vision_service = create_vision_service(
            provider=request.provider,
            api_key=request.api_key,
            base_url=request.base_url,
            model_name=request.model_name
        )

        # 测试简单的流式请求
        tokens = []
        token_count = 0

        logger.info("[DIAGNOSIS] Starting streaming test...")
        async for token in vision_service.generate_with_stream("Say hello in one sentence"):
            tokens.append(token)
            token_count += 1
            if token_count >= 20:  # 只收集前20个token
                break

        accumulated = "".join(tokens)
        logger.info(f"[DIAGNOSIS] Success! Received {token_count} tokens, total {len(accumulated)} chars")

        return DiagnosisResponse(
            success=True,
            message=f"AI API connection successful! Received {token_count} tokens.",
            details={
                "provider": request.provider,
                "model": request.model_name,
                "token_count": token_count,
                "sample_output": accumulated[:200]
            }
        )

    except Exception as e:
        logger.error(f"[DIAGNOSIS] Failed: {e}", exc_info=True)
        return DiagnosisResponse(
            success=False,
            message=f"AI API connection failed: {str(e)}",
            details={
                "provider": request.provider,
                "model": request.model_name,
                "error": str(e),
                "error_type": type(e).__name__
            }
        )
