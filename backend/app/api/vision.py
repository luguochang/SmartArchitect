from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from typing import Optional
import logging

from app.models.schemas import ImageAnalysisResponse
from app.services.ai_vision import create_vision_service

router = APIRouter()
logger = logging.getLogger(__name__)

# 支持的图片格式
ALLOWED_CONTENT_TYPES = [
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/webp"
]

# 最大文件大小（10MB）
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.post("/vision/analyze", response_model=ImageAnalysisResponse)
async def analyze_architecture_image(
    file: UploadFile = File(..., description="Architecture diagram image"),
    provider_form: Optional[str] = Form(None, description="AI provider (gemini, openai, claude, siliconflow, custom)"),
    provider_query: Optional[str] = Query(None, alias="provider", description="AI provider (gemini, openai, claude, siliconflow, custom)"),
    analyze_bottlenecks: bool = Form(True, description="Analyze architecture bottlenecks"),
    api_key: Optional[str] = Form(None, description="API key for custom provider"),
    base_url: Optional[str] = Form(None, description="Base URL for custom provider"),
    model_name: Optional[str] = Form(None, description="Model name for custom provider")
):
    """
    Analyze architecture diagram image using AI vision models.

    - **file**: Image file (PNG, JPG, JPEG, WEBP, max 10MB)
    - **provider**: AI provider (gemini, openai, claude, siliconflow, custom)
    - **analyze_bottlenecks**: Whether to analyze architecture bottlenecks
    - **api_key**: API key (required for custom provider)
    - **base_url**: Base URL (required for custom provider)
    - **model_name**: Model name (required for custom provider)

    Returns:
    - nodes: List of React Flow nodes
    - edges: List of React Flow edges
    - mermaid_code: Generated Mermaid.js code
    - ai_analysis: Architecture analysis results (if requested)
    """

    # 验证文件类型
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Allowed types: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )

    # 读取文件内容
    try:
        image_data = await file.read()
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read file: {str(e)}"
        )

    # 验证文件大小
    file_size = len(image_data)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size / 1024 / 1024:.2f}MB. "
                   f"Maximum size: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
        )

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="Empty file uploaded"
        )

    # 决定 provider（优先表单，其次 query，默认 gemini）
    provider = provider_form or provider_query or "gemini"

    # 验证 provider
    if provider not in ["gemini", "openai", "claude", "siliconflow", "custom"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}. "
                   f"Allowed: gemini, openai, claude, siliconflow, custom"
        )

    if provider == "siliconflow":
        raise HTTPException(
            status_code=400,
            detail="SiliconFlow is currently supported for text-only. Choose gemini/openai/claude/custom for image analysis."
        )

    # 验证自定义 provider 的必需参数
    if provider == "custom":
        if not base_url:
            raise HTTPException(
                status_code=400,
                detail="base_url is required for custom provider"
            )
        if not model_name:
            raise HTTPException(
                status_code=400,
                detail="model_name is required for custom provider"
            )

    # 创建 Vision Service（所有 provider 都传递 api_key）
    try:
        vision_service = create_vision_service(
            provider,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )
    except Exception as e:
        logger.error(f"Failed to initialize {provider} service: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize AI service: {str(e)}. "
                   f"Please check API key configuration."
        )

    # 分析图片
    try:
        logger.info(f"Analyzing image with {provider}, size: {file_size} bytes")
        result = await vision_service.analyze_architecture(
            image_data=image_data,
            analyze_bottlenecks=analyze_bottlenecks
        )
        logger.info(f"Analysis successful: {len(result.nodes)} nodes, {len(result.edges)} edges")
        return result

    except ValueError as e:
        # AI 响应解析错误
        logger.error(f"AI response parsing error: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse AI response: {str(e)}"
        )

    except Exception as e:
        # 其他错误
        logger.error(f"Image analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Image analysis failed: {str(e)}"
        )


@router.get("/vision/health")
async def vision_health_check():
    """Check if vision service is available"""
    return {
        "status": "healthy",
        "service": "vision",
        "supported_providers": ["gemini", "openai", "claude", "custom", "siliconflow"],
        "notes": {"siliconflow": "text-only in current release"},
        "max_file_size_mb": MAX_FILE_SIZE / 1024 / 1024,
        "allowed_formats": ALLOWED_CONTENT_TYPES
    }
