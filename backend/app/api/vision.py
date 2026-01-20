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


@router.post("/vision/analyze-flowchart", response_model=ImageAnalysisResponse)
async def analyze_flowchart_screenshot(
    file: UploadFile = File(..., description="Flowchart screenshot (PNG/JPG/WEBP)"),
    provider: str = Form("gemini", description="AI provider: gemini, openai, claude, siliconflow, custom"),
    preserve_layout: bool = Form(True, description="Preserve original node positions"),
    fast_mode: bool = Form(True, description="Use fast mode (simplified prompt for image recognition)"),
    api_key: Optional[str] = Form(None, description="Optional API key"),
    base_url: Optional[str] = Form(None, description="Custom provider base URL"),
    model_name: Optional[str] = Form(None, description="Custom model name"),
):
    """
    识别流程图截图，转换为可编辑的 ReactFlow 格式

    **功能特点：**
    - 支持多种流程图工具截图（Visio、ProcessOn、Draw.io等）
    - 识别 BPMN 标准节点（开始/结束/任务/判断）
    - 支持手绘流程图照片
    - 可选保留原始布局或自动重排

    **与 /vision/analyze 的区别：**
    - /vision/analyze: 针对架构图（API、Service、Database等）
    - /vision/analyze-flowchart: 针对流程图（开始/结束/判断等）

    **参数：**
    - file: 流程图截图文件（支持 PNG/JPG/WEBP，最大10MB）
    - provider: AI模型提供商
      - gemini: Google Gemini 2.5 Flash（推荐，速度快）
      - openai: GPT-4 Vision
      - claude: Claude 3.5 Sonnet（准确率高）
      - siliconflow: SiliconFlow Qwen3-VL-32B-Thinking（视觉模型）
      - custom: 自定义API（需提供 base_url 和 model_name）
    - preserve_layout: 是否保留原图布局
      - true: 尽量保持节点位置关系
      - false: AI自动优化布局
    - fast_mode: 是否使用快速模式（默认 true，推荐用于图片识别）
      - true: 简化 prompt，60-120秒完成，适合图片识别
      - false: 详细 prompt，200+秒，高质量，适合文本生成
    - api_key: 可选的API密钥（优先使用，否则使用环境变量）

    **返回：**
    - nodes: ReactFlow 节点数组（匹配现有17种形状）
    - edges: 连线数组
    - mermaid_code: Mermaid 代码
    - warnings: 识别警告（如：未支持的形状映射）
    - flowchart_analysis: 流程分析（复杂度、分支数等）
    """

    # 验证文件类型
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )

    # 读取文件
    try:
        image_data = await file.read()
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read file: {str(e)}"
        )

    # 验证文件大小
    file_size = len(image_data)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size / 1024 / 1024:.2f}MB. Max: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # 验证 provider
    if provider not in ["gemini", "openai", "claude", "siliconflow", "custom"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}. Allowed: gemini, openai, claude, siliconflow, custom"
        )

    # 验证自定义 provider
    if provider == "custom":
        if not base_url:
            raise HTTPException(status_code=400, detail="base_url required for custom provider")
        if not model_name:
            raise HTTPException(status_code=400, detail="model_name required for custom provider")

    # 创建 Vision Service
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
            detail=f"Failed to initialize AI service: {str(e)}"
        )

    # 分析流程图
    try:
        logger.info(f"[FLOWCHART API] Analyzing with {provider}, size: {file_size} bytes, preserve_layout: {preserve_layout}, fast_mode: {fast_mode}")

        result = await vision_service.analyze_flowchart(
            image_data=image_data,
            preserve_layout=preserve_layout,
            fast_mode=fast_mode
        )

        logger.info(f"[FLOWCHART API] Success: {len(result.nodes)} nodes, {len(result.edges)} edges")

        # 记录警告（如果有）
        if result.warnings:
            logger.warning(f"[FLOWCHART API] Warnings: {result.warnings}")

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
        logger.error(f"Flowchart analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Flowchart analysis failed: {str(e)}"
        )


@router.get("/vision/health")
async def vision_health_check():
    """Check if vision service is available"""
    return {
        "status": "healthy",
        "service": "vision",
        "supported_providers": ["gemini", "openai", "claude", "custom", "siliconflow"],
        "notes": {
            "siliconflow": "Supports vision models (e.g., Qwen3-VL-32B-Thinking)",
            "processing_time": "Vision analysis may take 60-180 seconds depending on model"
        },
        "max_file_size_mb": MAX_FILE_SIZE / 1024 / 1024,
        "allowed_formats": ALLOWED_CONTENT_TYPES
    }
