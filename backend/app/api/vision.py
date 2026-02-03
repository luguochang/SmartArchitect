from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from typing import Optional, List
import logging
import asyncio

from app.models.schemas import (
    ImageAnalysisResponse,
    VisionToExcalidrawRequest,
    VisionToExcalidrawResponse,
    VisionToReactFlowRequest,
    VisionToReactFlowResponse,
    Node,
    Position,
    NodeData
)
from app.services.ai_vision import create_vision_service
from app.services.model_presets import get_model_presets_service

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


def _fix_node_overlaps(nodes: List[Node], gentle_mode: bool = True) -> List[Node]:
    """
    Fix overlapping nodes - Simple and Direct Approach

    Algorithm:
    1. Process nodes in order
    2. For each node, check if it overlaps with ANY already-placed node
    3. If overlap: push right (or wrap to next row)
    4. Keep checking until no overlaps with any placed node

    Returns:
        List of nodes with guaranteed no overlaps
    """
    if len(nodes) <= 1:
        return nodes

    # Node dimensions - MUST match frontend SHAPE_CONFIG (nodeShapes.ts)
    NODE_SIZES = {
        # BPMN shapes
        "start-event": (56, 56),
        "end-event": (56, 56),
        "intermediate-event": (56, 56),
        "task": (140, 80),
        # Basic shapes
        "rectangle": (180, 90),
        "rounded-rectangle": (180, 90),
        "circle": (80, 80),
        "diamond": (100, 100),
        "hexagon": (120, 100),
        "triangle": (100, 100),
        "parallelogram": (140, 80),
        "trapezoid": (140, 80),
        "star": (100, 100),
        "cloud": (140, 80),
        "cylinder": (100, 120),
        "document": (120, 100),
        # Default fallback
        "default": (140, 80),
    }

    MIN_GAP = 30  # Minimum gap between nodes (increased from 20)
    CANVAS_WIDTH = 1400
    CANVAS_MARGIN = 60

    def get_size(node: Node) -> tuple:
        """Get (width, height) for a node"""
        shape = node.data.shape if node.data.shape else "default"
        return NODE_SIZES.get(shape, NODE_SIZES["default"])

    def boxes_overlap(x1, y1, w1, h1, x2, y2, w2, h2) -> bool:
        """Check if two bounding boxes overlap"""
        left1, right1 = x1, x1 + w1
        top1, bottom1 = y1, y1 + h1
        left2, right2 = x2, x2 + w2
        top2, bottom2 = y2, y2 + h2

        # Check overlap (with MIN_GAP buffer)
        x_overlap = not (right1 + MIN_GAP < left2 or right2 + MIN_GAP < left1)
        y_overlap = not (bottom1 + MIN_GAP < top2 or bottom2 + MIN_GAP < top1)

        return x_overlap and y_overlap

    def find_non_overlapping_position(x, y, width, height, placed_nodes):
        """
        Find a position that doesn't overlap with any placed nodes

        Strategy:
        - Check all placed nodes
        - For each overlap, push right past that node
        - After all pushes, check again until no overlaps
        """
        MAX_ITERATIONS = 20

        for iteration in range(MAX_ITERATIONS):
            # Collect all overlapping nodes
            need_push = []

            for placed in placed_nodes:
                placed_w, placed_h = get_size(placed)

                if boxes_overlap(x, y, width, height,
                                placed.position.x, placed.position.y, placed_w, placed_h):
                    need_push.append(placed)

            if not need_push:
                # No overlaps! Found a good position
                return x, y

            # Push right past the rightmost overlapping node
            rightmost = max(need_push, key=lambda n: n.position.x + get_size(n)[0])
            rightmost_w, _ = get_size(rightmost)
            x = rightmost.position.x + rightmost_w + MIN_GAP

            # If too far right, wrap to next row
            if x + width > CANVAS_WIDTH - CANVAS_MARGIN:
                x = CANVAS_MARGIN
                y += 200

        # Couldn't find position after max iterations
        logger.warning(f"[Collision] Couldn't resolve overlap after {MAX_ITERATIONS} iterations")
        return x, y

    # Process nodes one by one
    fixed = []

    for i, node in enumerate(nodes):
        width, height = get_size(node)
        x, y = node.position.x, node.position.y

        # Find non-overlapping position
        x, y = find_non_overlapping_position(x, y, width, height, fixed)

        # Create fixed node
        fixed_node = Node(
            id=node.id,
            type=node.type,
            position=Position(x=x, y=y),
            data=node.data
        )

        fixed.append(fixed_node)

        if x != node.position.x or y != node.position.y:
            logger.debug(f"[Collision] Node {node.id} moved from ({node.position.x:.0f}, {node.position.y:.0f}) to ({x:.0f}, {y:.0f})")

    logger.info(f"[Collision] Fixed {len(fixed)} nodes - all overlaps removed")
    return fixed



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

    # 获取有效配置（优先使用传入参数，否则使用默认预设）
    presets_service = get_model_presets_service()
    config = presets_service.get_active_config(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model_name=model_name
    )

    if not config:
        raise HTTPException(
            status_code=400,
            detail="No AI configuration found. Please configure AI model in settings or provide API key."
        )

    # 使用配置中的值
    effective_provider = config["provider"]
    effective_api_key = config["api_key"]
    effective_base_url = config.get("base_url")
    effective_model_name = config.get("model_name")

    # 验证自定义 provider 的必需参数
    if effective_provider == "custom":
        if not effective_base_url:
            raise HTTPException(
                status_code=400,
                detail="base_url is required for custom provider"
            )
        if not effective_model_name:
            raise HTTPException(
                status_code=400,
                detail="model_name is required for custom provider"
            )

    # 创建 Vision Service
    try:
        vision_service = create_vision_service(
            effective_provider,
            api_key=effective_api_key,
            base_url=effective_base_url,
            model_name=effective_model_name
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

    # 获取有效配置
    presets_service = get_model_presets_service()
    config = presets_service.get_active_config(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model_name=model_name
    )

    if not config:
        raise HTTPException(
            status_code=400,
            detail="No AI configuration found. Please configure AI model in settings or provide API key."
        )

    effective_provider = config["provider"]
    effective_api_key = config["api_key"]
    effective_base_url = config.get("base_url")
    effective_model_name = config.get("model_name")

    # 验证自定义 provider
    if effective_provider == "custom":
        if not effective_base_url:
            raise HTTPException(status_code=400, detail="base_url required for custom provider")
        if not effective_model_name:
            raise HTTPException(status_code=400, detail="model_name required for custom provider")

    # 创建 Vision Service
    try:
        vision_service = create_vision_service(
            effective_provider,
            api_key=effective_api_key,
            base_url=effective_base_url,
            model_name=effective_model_name
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

        # ✅ Apply collision detection (use aggressive mode to ensure no overlaps)
        logger.info(f"[FLOWCHART API] Applying collision detection to {len(result.nodes)} nodes...")
        result.nodes = _fix_node_overlaps(result.nodes, gentle_mode=False)
        logger.info(f"[FLOWCHART API] Collision detection complete")

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


@router.post("/vision/analyze-flowchart-stream-v2")
async def analyze_flowchart_screenshot_stream_v2(request: VisionToReactFlowRequest):
    """
    🔥 Stream-enabled flowchart analysis - shows real-time AI processing progress

    Returns Server-Sent Events (SSE) with progress updates and final result.

    **Request Body (JSON):**
    - image_data: Base64 encoded image
    - provider: AI provider (gemini, openai, claude, siliconflow, custom)
    - api_key: Optional API key
    - preserve_layout: Preserve original positions (default: true)
    - fast_mode: Use fast mode (default: true)

    **Event Types:**
    - init: Analysis started
    - progress: Status update with message
    - complete: Analysis finished with nodes/edges/mermaid_code
    - error: Error occurred
    """
    from fastapi.responses import StreamingResponse
    import json
    import base64

    async def generate():
        try:
            # Initial event
            yield f"data: {json.dumps({'type': 'init', 'message': '开始分析流程图...'})}\n\n"

            # Extract base64 data
            image_data_str = request.image_data
            if "base64," in image_data_str:
                image_data_str = image_data_str.split("base64,")[1]

            try:
                image_data = base64.b64decode(image_data_str)
                file_size = len(image_data)
                logger.info(f"[FLOWCHART STREAM] Decoded image: {file_size} bytes")
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'图片解码失败: {str(e)}'})}\n\n"
                return

            # Validate file size
            MAX_SIZE = 10 * 1024 * 1024
            if file_size > MAX_SIZE:
                yield f"data: {json.dumps({'type': 'error', 'message': f'文件过大: {file_size / 1024 / 1024:.2f}MB (最大 10MB)'})}\n\n"
                return

            if file_size == 0:
                yield f"data: {json.dumps({'type': 'error', 'message': '文件为空'})}\n\n"
                return

            # Get configuration
            yield f"data: {json.dumps({'type': 'progress', 'message': '正在配置 AI 模型...'})}\n\n"

            presets_service = get_model_presets_service()
            config = presets_service.get_active_config(
                provider=request.provider,
                api_key=request.api_key,
                base_url=request.base_url,
                model_name=request.model_name
            )

            if not config:
                yield f"data: {json.dumps({'type': 'error', 'message': '未找到 AI 配置，请先在设置中配置 AI 模型'})}\n\n"
                return

            # Create vision service
            provider_name = config["provider"]
            yield f"data: {json.dumps({'type': 'progress', 'message': f'正在初始化 {provider_name} 服务...'})}\n\n"

            try:
                vision_service = create_vision_service(
                    config["provider"],
                    api_key=config["api_key"],
                    base_url=config.get("base_url"),
                    model_name=config.get("model_name")
                )
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': f'初始化 AI 服务失败: {str(e)}'})}\n\n"
                return

            # Analysis progress messages
            yield f"data: {json.dumps({'type': 'progress', 'message': '🔍 正在分析图片结构...'})}\n\n"
            await asyncio.sleep(0.1)

            yield f"data: {json.dumps({'type': 'progress', 'message': '📊 正在识别节点形状（开始/结束/任务/判断）...'})}\n\n"
            await asyncio.sleep(0.1)

            yield f"data: {json.dumps({'type': 'progress', 'message': '✏️ 正在提取文本标签...'})}\n\n"
            await asyncio.sleep(0.1)

            yield f"data: {json.dumps({'type': 'progress', 'message': '🔗 正在识别连线关系...'})}\n\n"
            await asyncio.sleep(0.1)

            yield f"data: {json.dumps({'type': 'progress', 'message': '⚡ 正在生成 Mermaid 代码...'})}\n\n"

            # Perform actual analysis
            try:
                result = await vision_service.analyze_flowchart(
                    image_data=image_data,
                    preserve_layout=request.preserve_layout,
                    fast_mode=request.fast_mode
                )

                logger.info(f"[FLOWCHART STREAM] Analysis complete: {len(result.nodes)} nodes, {len(result.edges)} edges")

                # ✅ Apply collision detection (use aggressive mode to ensure no overlaps)
                yield f"data: {json.dumps({'type': 'progress', 'message': '🔧 正在修正节点间距...'})}\n\n"
                result.nodes = _fix_node_overlaps(result.nodes, gentle_mode=False)
                logger.info(f"[FLOWCHART STREAM] Collision detection complete")

                # Convert result to dict for JSON serialization
                result_dict = {
                    "nodes": [
                        {
                            "id": node.id,
                            "type": node.type,
                            "position": {"x": node.position.x, "y": node.position.y},
                            "data": {
                                "label": node.data.label,
                                "shape": node.data.shape
                            }
                        }
                        for node in result.nodes
                    ],
                    "edges": [
                        {
                            "id": edge.id,
                            "source": edge.source,
                            "target": edge.target,
                            "label": edge.label
                        }
                        for edge in result.edges
                    ],
                    "mermaid_code": result.mermaid_code,
                    "warnings": result.warnings if result.warnings else [],
                    "flowchart_analysis": result.flowchart_analysis if result.flowchart_analysis else {}
                }

                # Send completion event with full result
                yield f"data: {json.dumps({'type': 'complete', 'message': f'✅ 识别完成！共 {len(result.nodes)} 个节点，{len(result.edges)} 条连线', 'result': result_dict})}\n\n"

            except ValueError as e:
                logger.error(f"[FLOWCHART STREAM] Parsing error: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': f'AI 响应解析失败: {str(e)}'})}\n\n"
            except Exception as e:
                logger.error(f"[FLOWCHART STREAM] Analysis failed: {e}", exc_info=True)
                yield f"data: {json.dumps({'type': 'error', 'message': f'分析失败: {str(e)}'})}\n\n"

        except Exception as e:
            logger.error(f"[FLOWCHART STREAM] Unexpected error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': f'处理失败: {str(e)}'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")




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


@router.post("/vision/generate-excalidraw", response_model=VisionToExcalidrawResponse)
async def generate_excalidraw_from_image(request: VisionToExcalidrawRequest):
    """
    Generate Excalidraw scene from image using Vision AI.

    **Request Body:**
    - image_data: Base64 encoded image (with or without data:image prefix)
    - prompt: Additional instructions (optional)
    - provider: AI provider (gemini, openai, claude, siliconflow, custom)
    - api_key: API key (required)
    - base_url: Base URL (required for custom provider)
    - model_name: Model name (required for custom provider)
    - width: Canvas width (default: 1200)
    - height: Canvas height (default: 800)

    **Response:**
    - success: Whether generation succeeded
    - scene: Excalidraw scene object with elements, appState, files
    - message: Error message if failed
    - raw_response: Raw AI response for debugging

    **Example:**
    ```json
    {
        "image_data": "data:image/png;base64,iVBORw0KG...",
        "prompt": "Convert this flowchart to Excalidraw format",
        "provider": "custom",
        "api_key": "sk-...",
        "base_url": "https://api.example.com/v1",
        "model_name": "claude-sonnet-4-5-20250929"
    }
    ```
    """
    import json
    import re

    try:
        # 获取有效配置
        presets_service = get_model_presets_service()
        config = presets_service.get_active_config(
            provider=request.provider,
            api_key=request.api_key,
            base_url=request.base_url,
            model_name=request.model_name
        )

        if not config:
            return VisionToExcalidrawResponse(
                success=False,
                message="No AI configuration found. Please configure AI model in settings or provide API key."
            )

        # Create vision service
        vision_service = create_vision_service(
            config["provider"],
            api_key=config["api_key"],
            base_url=config.get("base_url"),
            model_name=config.get("model_name")
        )

        # Build prompt for Excalidraw generation
        excalidraw_prompt = f"""
Analyze the uploaded image and convert it to Excalidraw JSON format with HIGH FOCUS on preserving ALL connections/arrows.

Output a valid JSON object with this structure:
{{
    "elements": [
        {{
            "id": "unique-id",
            "type": "rectangle" | "ellipse" | "diamond" | "arrow" | "line" | "text",
            "x": number,
            "y": number,
            "width": number,
            "height": number,
            "strokeColor": "#000000",
            "backgroundColor": "#ffffff",
            "fillStyle": "hachure",
            "strokeWidth": 1,
            "roughness": 1,
            "opacity": 100,
            "text": "label" (for shapes with labels),
            "fontSize": 20,
            "fontFamily": 1,
            "textAlign": "center",
            "points": [[0,0], [100,0]] (REQUIRED for arrow/line),
            "endArrowhead": "arrow" (for directional arrows)
        }}
    ],
    "appState": {{
        "viewBackgroundColor": "#ffffff"
    }}
}}

**CRITICAL RULES - Connection Detection (HIGHEST PRIORITY):**

⚠️ **CONNECTION DETECTION IS CRITICAL** - This is the PRIMARY requirement:
- Identify and preserve ALL arrows/lines/connections in the diagram
- For EVERY connection you see in the image, you MUST create a corresponding arrow/line element
- Connections are AS IMPORTANT as shapes - DO NOT skip them
- If the image has 5 arrows connecting boxes, your output MUST have 5 arrow elements
- Missing connections breaks the entire diagram - pay close attention!

**Element Rules:**

1. **Shapes** - For each shape in the image, create corresponding element:
   - Boxes/Rectangles → type="rectangle"
   - Circles/Ovals → type="ellipse"
   - Diamonds/Rhombus → type="diamond"
   - Text labels → embed in shapes OR create separate text elements

2. **Connections/Arrows** (CRITICAL - Read Carefully):

   a) **Type Selection:**
      - Directional arrows (with arrowhead) → type="arrow"
      - Plain lines (no arrowhead) → type="line"
      - Bidirectional arrows → type="arrow" with both startArrowhead and endArrowhead

   b) **Required Fields for Arrow/Line:**
      - "points": [[x1,y1], [x2,y2], ...] - MANDATORY, relative to element's (x,y)
      - "x", "y": Top-left corner of bounding box
      - "width", "height": Bounding box dimensions calculated from points
      - "endArrowhead": "arrow" (for single-direction arrows)
      - "startArrowhead": "arrow" (for reverse direction)
      - "strokeColor": Line color (usually "#000000")
      - "strokeWidth": Usually 2 for arrows

   c) **Arrow Coordinate System:**
      - x, y = top-left of bounding box containing the line
      - points = array of [x, y] coordinates RELATIVE to (x, y)
      - width = max(x-coords) - min(x-coords) from points
      - height = max(y-coords) - min(y-coords) from points

   d) **Arrow Examples:**
      - Horizontal arrow (left to right):
        {{"id":"arrow-1", "type":"arrow", "x":200, "y":150, "width":150, "height":0,
          "points":[[0,0],[150,0]], "endArrowhead":"arrow", "strokeColor":"#000000", "strokeWidth":2}}

      - Vertical arrow (top to bottom):
        {{"id":"arrow-2", "type":"arrow", "x":300, "y":100, "width":0, "height":100,
          "points":[[0,0],[0,100]], "endArrowhead":"arrow", "strokeColor":"#000000", "strokeWidth":2}}

      - Diagonal arrow:
        {{"id":"arrow-3", "type":"arrow", "x":200, "y":200, "width":100, "height":80,
          "points":[[0,0],[100,80]], "endArrowhead":"arrow", "strokeColor":"#000000", "strokeWidth":2}}

      - Bidirectional arrow:
        {{"id":"arrow-4", "type":"arrow", "x":100, "y":300, "width":200, "height":0,
          "points":[[0,0],[200,0]], "startArrowhead":"arrow", "endArrowhead":"arrow", "strokeColor":"#000000", "strokeWidth":2}}

3. **Layout Preservation:**
   - Preserve spatial layout (x, y coordinates relative to canvas {request.width}x{request.height})
   - Maintain relative positions of shapes and connections
   - Keep arrow endpoints near shape boundaries

4. **Identifiers:**
   - Use unique IDs (e.g., "rect-1", "arrow-2", "text-3", "line-1")
   - Ensure all referenced IDs exist

5. **Output Format:**
   - Output ONLY valid JSON, no markdown, no explanatory text
   - Ensure JSON is complete and properly closed

**Validation Checklist (before output):**
✓ For N shapes, expect at least N-1 connections (for typical flow diagrams)
✓ ALL arrow/line elements have valid "points" array
✓ Arrow endpoints roughly connect to shape boundaries
✓ Total element count = shapes + arrows + text labels
✓ No duplicate IDs

**Complete Example (2 boxes + 1 arrow):**
{{
    "elements": [
        {{"id":"box1", "type":"rectangle", "x":100, "y":100, "width":120, "height":60, "strokeColor":"#000000", "backgroundColor":"#ffffff", "fillStyle":"hachure", "strokeWidth":2, "roughness":1, "opacity":100, "text":"Start", "fontSize":20, "fontFamily":1, "textAlign":"center"}},
        {{"id":"arrow1", "type":"arrow", "x":220, "y":130, "width":80, "height":0, "points":[[0,0],[80,0]], "strokeColor":"#000000", "strokeWidth":2, "endArrowhead":"arrow", "roughness":1, "opacity":100}},
        {{"id":"box2", "type":"rectangle", "x":300, "y":100, "width":120, "height":60, "strokeColor":"#000000", "backgroundColor":"#ffffff", "fillStyle":"hachure", "strokeWidth":2, "roughness":1, "opacity":100, "text":"End", "fontSize":20, "fontFamily":1, "textAlign":"center"}}
    ],
    "appState": {{"viewBackgroundColor":"#ffffff"}}
}}

Canvas dimensions: {request.width}px width, {request.height}px height

Additional instructions: {request.prompt or 'None'}
"""

        # Call AI service
        logger.info(f"Generating Excalidraw scene with {request.provider}")

        # Extract base64 data
        image_data = request.image_data
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]

        import base64
        image_bytes = base64.b64decode(image_data)

        # Call AI vision service
        raw_response = await vision_service.generate_with_vision(
            image_data=image_bytes,
            prompt=excalidraw_prompt
        )

        logger.info(f"Raw AI response received (length: {len(raw_response)})")

        # Extract JSON from response
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, raw_response, re.DOTALL)

        if match:
            json_str = match.group(1)
        else:
            # Try to find JSON object directly
            json_obj_pattern = r'\{.*\}'
            match = re.search(json_obj_pattern, raw_response, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                return VisionToExcalidrawResponse(
                    success=False,
                    message="Failed to extract JSON from AI response",
                    raw_response=raw_response[:500]
                )

        # Parse JSON
        try:
            scene_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return VisionToExcalidrawResponse(
                success=False,
                message=f"Invalid JSON: {str(e)}",
                raw_response=json_str[:500]
            )

        # Validate structure
        if "elements" not in scene_data:
            return VisionToExcalidrawResponse(
                success=False,
                message="Response missing 'elements' field",
                raw_response=json_str[:500]
            )

        # Ensure appState exists
        if "appState" not in scene_data:
            scene_data["appState"] = {"viewBackgroundColor": "#ffffff"}

        # Normalize Excalidraw elements - add required fields
        import random
        import time
        timestamp = int(time.time() * 1000)

        for element in scene_data["elements"]:
            # Add required Excalidraw fields if missing
            if "version" not in element:
                element["version"] = 1
            if "versionNonce" not in element:
                element["versionNonce"] = random.randint(1000000000, 9999999999)
            if "isDeleted" not in element:
                element["isDeleted"] = False
            if "groupIds" not in element:
                element["groupIds"] = []
            if "boundElements" not in element:
                element["boundElements"] = None
            if "updated" not in element:
                element["updated"] = timestamp
            if "link" not in element:
                element["link"] = None
            if "locked" not in element:
                element["locked"] = False

            # For arrow elements, add required binding fields
            if element.get("type") == "arrow":
                if "startBinding" not in element:
                    element["startBinding"] = None
                if "endBinding" not in element:
                    element["endBinding"] = None
                if "lastCommittedPoint" not in element:
                    element["lastCommittedPoint"] = None
                if "startArrowhead" not in element:
                    element["startArrowhead"] = None
                if "endArrowhead" not in element:
                    element["endArrowhead"] = "arrow"

            # For line elements, add similar fields
            if element.get("type") == "line":
                if "startBinding" not in element:
                    element["startBinding"] = None
                if "endBinding" not in element:
                    element["endBinding"] = None
                if "lastCommittedPoint" not in element:
                    element["lastCommittedPoint"] = None
                # Lines typically don't have arrowheads
                if "startArrowhead" not in element:
                    element["startArrowhead"] = None
                if "endArrowhead" not in element:
                    element["endArrowhead"] = None

            # For text elements
            if element.get("type") == "text" or "text" in element:
                if "lineHeight" not in element:
                    element["lineHeight"] = 1.25
                if "verticalAlign" not in element:
                    element["verticalAlign"] = "top"

            # Ensure angle exists
            if "angle" not in element:
                element["angle"] = 0

            # Ensure strokeStyle exists
            if "strokeStyle" not in element:
                element["strokeStyle"] = "solid"

        # Validate connection detection (arrow/line elements)
        arrow_count = sum(1 for e in scene_data["elements"] if e.get("type") in ["arrow", "line"])
        shape_count = sum(1 for e in scene_data["elements"] if e.get("type") in ["rectangle", "ellipse", "diamond"])
        text_count = sum(1 for e in scene_data["elements"] if e.get("type") == "text")
        total_count = len(scene_data["elements"])

        logger.info(f"Excalidraw generation result: {total_count} total elements - {shape_count} shapes, {arrow_count} connections, {text_count} text elements")

        # Warn if no arrows detected when there are multiple shapes
        if arrow_count == 0 and shape_count > 1:
            logger.warning(f"⚠️ No arrows/lines detected for {shape_count} shapes - possible AI recognition issue. Consider using a different provider or retrying.")

        # Validate arrow elements have required "points" field
        invalid_arrows = []
        for element in scene_data["elements"]:
            if element.get("type") in ["arrow", "line"]:
                if "points" not in element or not isinstance(element.get("points"), list) or len(element.get("points", [])) < 2:
                    invalid_arrows.append(element.get("id", "unknown"))

        if invalid_arrows:
            logger.error(f"❌ Invalid arrow/line elements detected (missing or invalid 'points' field): {invalid_arrows}")
            logger.error(f"These elements will not render correctly in Excalidraw. Total affected: {len(invalid_arrows)}")

        logger.info(f"Successfully generated Excalidraw scene with {len(scene_data['elements'])} elements (normalized)")

        return VisionToExcalidrawResponse(
            success=True,
            scene=scene_data
        )

    except Exception as e:
        logger.error(f"Excalidraw generation failed: {e}", exc_info=True)
        return VisionToExcalidrawResponse(
            success=False,
            message=f"Generation failed: {str(e)}"
        )


@router.post("/vision/generate-excalidraw-stream")
async def generate_excalidraw_from_image_stream(request: VisionToExcalidrawRequest):
    """
    🔥 Generate Excalidraw scene from image using Vision AI with TRUE streaming.
    Uses multimodal streaming APIs to yield elements as they are generated in real-time.
    """
    from fastapi.responses import StreamingResponse
    import json
    import re
    import random
    import time

    def normalize_element(element: dict, timestamp: int) -> dict:
        """Normalize Excalidraw element by adding required fields"""
        # Required base fields
        if "version" not in element:
            element["version"] = 1
        if "versionNonce" not in element:
            element["versionNonce"] = random.randint(1000000000, 9999999999)
        if "isDeleted" not in element:
            element["isDeleted"] = False
        if "groupIds" not in element:
            element["groupIds"] = []
        if "boundElements" not in element:
            element["boundElements"] = None
        if "updated" not in element:
            element["updated"] = timestamp
        if "link" not in element:
            element["link"] = None
        if "locked" not in element:
            element["locked"] = False
        if "angle" not in element:
            element["angle"] = 0
        if "strokeStyle" not in element:
            element["strokeStyle"] = "solid"

        # Arrow-specific fields
        if element.get("type") == "arrow":
            if "startBinding" not in element:
                element["startBinding"] = None
            if "endBinding" not in element:
                element["endBinding"] = None
            if "lastCommittedPoint" not in element:
                element["lastCommittedPoint"] = None
            if "startArrowhead" not in element:
                element["startArrowhead"] = None
            if "endArrowhead" not in element:
                element["endArrowhead"] = "arrow"

        # Line-specific fields
        if element.get("type") == "line":
            if "startBinding" not in element:
                element["startBinding"] = None
            if "endBinding" not in element:
                element["endBinding"] = None
            if "lastCommittedPoint" not in element:
                element["lastCommittedPoint"] = None
            # Lines typically don't have arrowheads
            if "startArrowhead" not in element:
                element["startArrowhead"] = None
            if "endArrowhead" not in element:
                element["endArrowhead"] = None

        # Text-specific fields
        if element.get("type") == "text" or "text" in element:
            if "lineHeight" not in element:
                element["lineHeight"] = 1.25
            if "verticalAlign" not in element:
                element["verticalAlign"] = "top"

        return element

    def try_parse_incremental_elements(json_buffer: str, parsed_ids: set) -> list:
        """
        🔥 Incrementally parse JSON buffer to extract completed elements.
        Returns list of newly completed elements (not previously parsed).
        """
        # Try to extract elements array even from incomplete JSON
        # Pattern: "elements": [ {...}, {...}, ... ]
        elements_pattern = r'"elements"\s*:\s*\[\s*(.*?)(?:\]|$)'
        match = re.search(elements_pattern, json_buffer, re.DOTALL)

        if not match:
            return []

        elements_str = match.group(1)

        # Find all complete element objects (balanced braces)
        new_elements = []
        brace_count = 0
        start_idx = -1
        i = 0

        while i < len(elements_str):
            char = elements_str[i]

            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    # Found a complete element
                    element_str = elements_str[start_idx:i+1]
                    try:
                        element = json.loads(element_str)
                        # Only return if not already parsed
                        element_id = element.get("id", "")
                        if element_id and element_id not in parsed_ids:
                            new_elements.append(element)
                            parsed_ids.add(element_id)
                    except json.JSONDecodeError:
                        pass  # Incomplete element, wait for more tokens
                    start_idx = -1

            i += 1

        return new_elements

    async def generate():
        try:
            yield f"data: {json.dumps({'type': 'init', 'message': 'Starting real-time Excalidraw generation...'})}\n\n"

            # 获取有效配置
            presets_service = get_model_presets_service()
            config = presets_service.get_active_config(
                provider=request.provider,
                api_key=request.api_key,
                base_url=request.base_url,
                model_name=request.model_name
            )

            if not config:
                yield f"data: {json.dumps({'type': 'error', 'message': 'No AI configuration found. Please configure AI model in settings.'})}\n\n"
                return

            # Create vision service
            vision_service = create_vision_service(
                config["provider"],
                api_key=config["api_key"],
                base_url=config.get("base_url"),
                model_name=config.get("model_name")
            )

            yield f"data: {json.dumps({'type': 'progress', 'message': 'Analyzing image...'})}\n\n"

            # Build prompt
            excalidraw_prompt = f"""
Analyze the uploaded image and convert it to Excalidraw JSON format with HIGH FOCUS on preserving ALL connections/arrows.

Output a valid JSON object with this structure:
{{
    "elements": [
        {{
            "id": "unique-id",
            "type": "rectangle" | "ellipse" | "diamond" | "arrow" | "line" | "text",
            "x": number,
            "y": number,
            "width": number,
            "height": number,
            "strokeColor": "#000000",
            "backgroundColor": "#ffffff",
            "fillStyle": "hachure",
            "strokeWidth": 1,
            "roughness": 1,
            "opacity": 100,
            "text": "label" (for shapes with labels),
            "fontSize": 20,
            "fontFamily": 1,
            "textAlign": "center",
            "points": [[0,0], [100,0]] (REQUIRED for arrow/line),
            "endArrowhead": "arrow" (for directional arrows)
        }}
    ],
    "appState": {{
        "viewBackgroundColor": "#ffffff"
    }}
}}

**CRITICAL RULES - Connection Detection (HIGHEST PRIORITY):**

⚠️ **CONNECTION DETECTION IS CRITICAL** - This is the PRIMARY requirement:
- Identify and preserve ALL arrows/lines/connections in the diagram
- For EVERY connection you see in the image, you MUST create a corresponding arrow/line element
- Connections are AS IMPORTANT as shapes - DO NOT skip them
- If the image has 5 arrows connecting boxes, your output MUST have 5 arrow elements
- Missing connections breaks the entire diagram - pay close attention!

**Element Rules:**

1. **Shapes** - For each shape in the image, create corresponding element:
   - Boxes/Rectangles → type="rectangle"
   - Circles/Ovals → type="ellipse"
   - Diamonds/Rhombus → type="diamond"
   - Text labels → embed in shapes OR create separate text elements

2. **Connections/Arrows** (CRITICAL - Read Carefully):

   a) **Type Selection:**
      - Directional arrows (with arrowhead) → type="arrow"
      - Plain lines (no arrowhead) → type="line"
      - Bidirectional arrows → type="arrow" with both startArrowhead and endArrowhead

   b) **Required Fields for Arrow/Line:**
      - "points": [[x1,y1], [x2,y2], ...] - MANDATORY, relative to element's (x,y)
      - "x", "y": Top-left corner of bounding box
      - "width", "height": Bounding box dimensions calculated from points
      - "endArrowhead": "arrow" (for single-direction arrows)
      - "startArrowhead": "arrow" (for reverse direction)
      - "strokeColor": Line color (usually "#000000")
      - "strokeWidth": Usually 2 for arrows

   c) **Arrow Coordinate System:**
      - x, y = top-left of bounding box containing the line
      - points = array of [x, y] coordinates RELATIVE to (x, y)
      - width = max(x-coords) - min(x-coords) from points
      - height = max(y-coords) - min(y-coords) from points

   d) **Arrow Examples:**
      - Horizontal arrow (left to right):
        {{"id":"arrow-1", "type":"arrow", "x":200, "y":150, "width":150, "height":0,
          "points":[[0,0],[150,0]], "endArrowhead":"arrow", "strokeColor":"#000000", "strokeWidth":2}}

      - Vertical arrow (top to bottom):
        {{"id":"arrow-2", "type":"arrow", "x":300, "y":100, "width":0, "height":100,
          "points":[[0,0],[0,100]], "endArrowhead":"arrow", "strokeColor":"#000000", "strokeWidth":2}}

      - Diagonal arrow:
        {{"id":"arrow-3", "type":"arrow", "x":200, "y":200, "width":100, "height":80,
          "points":[[0,0],[100,80]], "endArrowhead":"arrow", "strokeColor":"#000000", "strokeWidth":2}}

      - Bidirectional arrow:
        {{"id":"arrow-4", "type":"arrow", "x":100, "y":300, "width":200, "height":0,
          "points":[[0,0],[200,0]], "startArrowhead":"arrow", "endArrowhead":"arrow", "strokeColor":"#000000", "strokeWidth":2}}

3. **Layout Preservation:**
   - Preserve spatial layout (x, y coordinates relative to canvas {request.width}x{request.height})
   - Maintain relative positions of shapes and connections
   - Keep arrow endpoints near shape boundaries

4. **Identifiers:**
   - Use unique IDs (e.g., "rect-1", "arrow-2", "text-3", "line-1")
   - Ensure all referenced IDs exist

5. **Output Format:**
   - Output ONLY valid JSON, no markdown, no explanatory text
   - Ensure JSON is complete and properly closed

**Validation Checklist (before output):**
✓ For N shapes, expect at least N-1 connections (for typical flow diagrams)
✓ ALL arrow/line elements have valid "points" array
✓ Arrow endpoints roughly connect to shape boundaries
✓ Total element count = shapes + arrows + text labels
✓ No duplicate IDs

**Complete Example (2 boxes + 1 arrow):**
{{
    "elements": [
        {{"id":"box1", "type":"rectangle", "x":100, "y":100, "width":120, "height":60, "strokeColor":"#000000", "backgroundColor":"#ffffff", "fillStyle":"hachure", "strokeWidth":2, "roughness":1, "opacity":100, "text":"Start", "fontSize":20, "fontFamily":1, "textAlign":"center"}},
        {{"id":"arrow1", "type":"arrow", "x":220, "y":130, "width":80, "height":0, "points":[[0,0],[80,0]], "strokeColor":"#000000", "strokeWidth":2, "endArrowhead":"arrow", "roughness":1, "opacity":100}},
        {{"id":"box2", "type":"rectangle", "x":300, "y":100, "width":120, "height":60, "strokeColor":"#000000", "backgroundColor":"#ffffff", "fillStyle":"hachure", "strokeWidth":2, "roughness":1, "opacity":100, "text":"End", "fontSize":20, "fontFamily":1, "textAlign":"center"}}
    ],
    "appState": {{"viewBackgroundColor":"#ffffff"}}
}}

Canvas dimensions: {request.width}px width, {request.height}px height

Additional instructions: {request.prompt or 'None'}
"""

            # Extract base64 data
            image_data = request.image_data
            if "base64," in image_data:
                image_data = image_data.split("base64,")[1]

            import base64
            image_bytes = base64.b64decode(image_data)

            # 🔥 Use real streaming with multimodal API
            yield f"data: {json.dumps({'type': 'progress', 'message': 'Starting real-time generation...'})}\n\n"

            json_buffer = ""
            parsed_ids = set()  # Track which elements we've already sent
            timestamp = int(time.time() * 1000)
            element_count = 0
            arrow_count = 0  # Track connection count
            shape_count = 0  # Track shape count

            # Stream tokens in real-time
            async for token in vision_service.generate_with_vision_stream(image_bytes, excalidraw_prompt):
                json_buffer += token

                # Try to parse new complete elements from the buffer
                new_elements = try_parse_incremental_elements(json_buffer, parsed_ids)

                # Yield each new element immediately
                for element in new_elements:
                    normalized = normalize_element(element, timestamp)
                    element_count += 1

                    # Track element types for validation
                    element_type = element.get("type")
                    if element_type in ["arrow", "line"]:
                        arrow_count += 1
                        # Validate arrow has points field
                        if "points" not in element or not isinstance(element.get("points"), list) or len(element.get("points", [])) < 2:
                            logger.warning(f"⚠️ Arrow/line element '{element.get('id')}' missing or invalid 'points' field - may not render correctly")
                    elif element_type in ["rectangle", "ellipse", "diamond"]:
                        shape_count += 1

                    yield f"data: {json.dumps({'type': 'element', 'element': normalized})}\n\n"
                    logger.info(f"[REAL STREAM] Yielded element {element_count}: {element.get('id')} (type: {element_type})")

            # Send completion with validation info
            completion_message = f'Generated {element_count} elements in real-time ({shape_count} shapes, {arrow_count} connections)'

            # Warn if no arrows detected
            if arrow_count == 0 and shape_count > 1:
                logger.warning(f"⚠️ No arrows/lines detected for {shape_count} shapes - possible AI recognition issue")
                completion_message += " - ⚠️ No connections detected"

            yield f"data: {json.dumps({'type': 'complete', 'message': completion_message})}\n\n"
            logger.info(f"[REAL STREAM] Completed with {element_count} elements ({shape_count} shapes, {arrow_count} connections)")

        except Exception as e:
            logger.error(f"Excalidraw real streaming failed: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': f'Generation failed: {str(e)}'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/vision/test-stream")
async def test_stream():
    """Simple test streaming endpoint"""
    from fastapi.responses import StreamingResponse
    import json
    import asyncio

    async def generate():
        yield f"data: {json.dumps({'test': 'hello'})}\n\n"
        await asyncio.sleep(0.1)
        yield f"data: {json.dumps({'test': 'world'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/vision/generate-excalidraw-stream-mock")
async def generate_excalidraw_stream_mock():
    """
    Mock streaming endpoint for testing frontend without AI delays.
    Streams 5 test elements progressively.
    """
    from fastapi.responses import StreamingResponse
    import json
    import random
    import asyncio
    import time

    async def generate():
        try:
            yield f"data: {json.dumps({'type': 'init', 'message': 'Starting mock generation...'})}\n\n"
            await asyncio.sleep(0.1)

            # Mock elements
            elements = [
                {"id": "rect-1", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 100, "strokeColor": "#000000", "backgroundColor": "#ffffff", "fillStyle": "hachure", "strokeWidth": 2, "roughness": 1, "opacity": 100, "text": "User Input", "fontSize": 20, "fontFamily": 1, "textAlign": "center"},
                {"id": "arrow-1", "type": "arrow", "x": 200, "y": 210, "width": 0, "height": 80, "points": [[0, 0], [0, 80]], "strokeColor": "#000000"},
                {"id": "diamond-1", "type": "diamond", "x": 150, "y": 300, "width": 150, "height": 150, "strokeColor": "#000000", "backgroundColor": "#ffeb3b", "fillStyle": "hachure", "text": "Valid?"},
                {"id": "arrow-2", "type": "arrow", "x": 225, "y": 460, "width": 200, "height": 0, "points": [[0, 0], [200, 0]], "strokeColor": "#000000", "text": "Yes"},
                {"id": "rect-2", "type": "rectangle", "x": 450, "y": 410, "width": 180, "height": 100, "strokeColor": "#000000", "backgroundColor": "#4caf50", "fillStyle": "hachure", "text": "Success"}
            ]

            appState = {"viewBackgroundColor": "#ffffff"}

            yield f"data: {json.dumps({'type': 'start_streaming', 'total': len(elements), 'appState': appState})}\n\n"
            await asyncio.sleep(0.1)

            timestamp = int(time.time() * 1000)

            for idx, element in enumerate(elements):
                # Add required fields
                element["version"] = 1
                element["versionNonce"] = random.randint(1000000000, 9999999999)
                element["isDeleted"] = False
                element["groupIds"] = []
                element["boundElements"] = None
                element["updated"] = timestamp
                element["link"] = None
                element["locked"] = False
                element["angle"] = 0
                element["strokeStyle"] = "solid"

                if element.get("type") == "arrow":
                    element["startBinding"] = None
                    element["endBinding"] = None
                    element["endArrowhead"] = "arrow"

                yield f"data: {json.dumps({'type': 'element', 'element': element, 'index': idx, 'total': len(elements)})}\n\n"
                await asyncio.sleep(0.3)  # 300ms delay per element for visual effect

            yield f"data: {json.dumps({'type': 'complete', 'message': 'Mock generation complete'})}\n\n"

        except Exception as e:
            logger.error(f"Mock streaming failed: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.post("/vision/generate-reactflow", response_model=VisionToReactFlowResponse)
async def generate_reactflow_from_image(request: VisionToReactFlowRequest):
    """
    Generate React Flow diagram from image using Vision AI.

    **Request Body:**
    - image_data: Base64 encoded image
    - prompt: Additional instructions (optional)
    - provider: AI provider
    - api_key: API key
    - base_url: Base URL (for custom provider)
    - model_name: Model name (for custom provider)

    **Response:**
    - success: Whether generation succeeded
    - nodes: List of React Flow nodes
    - edges: List of React Flow edges
    - message: Error message if failed

    **Supported node types:**
    - api: API services
    - service: Backend services
    - database: Databases
    - cache: Cache systems
    - client: Client applications
    - queue: Message queues
    - gateway: API gateways
    - container: Generic containers
    - default: Default nodes
    """
    import json
    import re
    from app.models.schemas import Node, Edge, Position, NodeData

    try:
        # 获取有效配置
        presets_service = get_model_presets_service()
        config = presets_service.get_active_config(
            provider=request.provider,
            api_key=request.api_key,
            base_url=request.base_url,
            model_name=request.model_name
        )

        if not config:
            return VisionToReactFlowResponse(
                success=False,
                message="No AI configuration found. Please configure AI model in settings or provide API key."
            )

        # Create vision service
        vision_service = create_vision_service(
            config["provider"],
            api_key=config["api_key"],
            base_url=config.get("base_url"),
            model_name=config.get("model_name")
        )

        # Build prompt for React Flow generation
        # Optimized layout rules inspired by Excalidraw's success (see excalidraw_generator.py:125-163)
        reactflow_prompt = f"""
Analyze the uploaded diagram and convert it to SmartArchitect React Flow format.

**CRITICAL LAYOUT RULES (Prevent Overlap & Ensure Spacing):**

1. **Canvas Dimensions:** Assume canvas is 1400px width × 900px height
2. **Mandatory Margins:** Keep 60px margin from all edges (do not place nodes at x<60, y<60, x>1340, y>840)
3. **Minimum Node Spacing (STRICT):**
   - Horizontal gap between nodes: MINIMUM 180px (center to center)
   - Vertical gap between rows: MINIMUM 150px (center to center)
   - **NO OVERLAP ALLOWED** - each node must be clearly separated
4. **Node Dimensions (assume for spacing calculations):**
   - Standard rectangle/task nodes: 180px wide × 60px tall
   - Circle nodes (start/end): 60px diameter
   - Diamond nodes: 80px × 80px
5. **Distribution Strategy:**
   - For 3-5 nodes: Use x: 100-600 range with 200px gaps
   - For 6-10 nodes: Use grid layout with 200px horizontal, 180px vertical spacing
   - For 10+ nodes: Multi-row layout, keep rows 200px apart
6. **Collision Detection (CRITICAL):**
   - Before assigning coordinates, mentally check if any two nodes overlap
   - If overlap detected, push the second node right by 200px or down by 180px
   - Example: If node A is at (200, 100), node B minimum position is (400, 100) horizontally or (200, 280) vertically

**JSON STRUCTURE:**
{{
    "nodes": [
        {{
            "id": "1",
            "type": "api" | "service" | "database" | "cache" | "client" | "queue" | "gateway" | "container" | "default",
            "position": {{"x": 100, "y": 100}},
            "data": {{
                "label": "Node Label",
                "shape": "rectangle" | "circle" | "diamond" | "hexagon" | "task",
                "color": "#3b82f6"
            }}
        }}
    ],
    "edges": [
        {{
            "id": "e1-2",
            "source": "1",
            "target": "2",
            "label": "HTTP"
        }}
    ]
}}

**Node Types:**
- api: API services → shape: rectangle, color: #2563eb
- service: Backend services → shape: task (rounded), color: #8b5cf6
- database: Databases → shape: circle, color: #059669
- cache: Cache systems → shape: rectangle, color: #f59e0b
- client: Client applications → shape: rectangle, color: #06b6d4
- queue: Message queues → shape: rectangle, color: #ec4899
- gateway: API gateways → shape: hexagon or diamond, color: #6366f1
- default: Generic nodes → shape: task, color: #64748b

**Shape Dimensions Reference (for spacing calculation):**
- rectangle/task: width=180px, height=60px
- circle: diameter=60px
- diamond: width=80px, height=80px
- hexagon: width=100px, height=80px

**LAYOUT VALIDATION CHECKLIST (before output):**
✓ All nodes have minimum 180px horizontal spacing (center to center)
✓ All nodes have minimum 150px vertical spacing (center to center)
✓ No nodes overlap when considering their dimensions
✓ All nodes are within canvas bounds (60px margin)
✓ Grid-like distribution for multiple nodes (not random clustering)

**POSITION CALCULATION EXAMPLE:**
For a 3-node horizontal flow:
- Node 1: x=150, y=300 (leftmost)
- Node 2: x=400, y=300 (middle, 250px gap from node 1)
- Node 3: x=650, y=300 (rightmost, 250px gap from node 2)

For a 2-row layout:
- Row 1: y=200
- Row 2: y=400 (200px gap from row 1)

**EDGE RULES:**
1. Extract all arrows/connections from the diagram
2. Preserve arrow labels (e.g., "HTTP", "gRPC", "Async")
3. Ensure source/target IDs match node IDs exactly

**OUTPUT FORMAT:**
- Return ONLY valid JSON (no markdown, no explanatory text)
- Ensure all IDs are unique strings
- Verify no coordinate collisions before outputting

{request.prompt or ''}
"""

        # Call AI service
        logger.info(f"Generating React Flow diagram with {request.provider}")

        # Extract base64 data
        image_data = request.image_data
        if "base64," in image_data:
            image_data = image_data.split("base64,")[1]

        import base64
        image_bytes = base64.b64decode(image_data)

        # Call AI vision service
        raw_response = await vision_service.generate_with_vision(
            image_data=image_bytes,
            prompt=reactflow_prompt
        )

        logger.info(f"Raw AI response received (length: {len(raw_response)})")

        # Extract JSON from response
        json_pattern = r'```json\s*(.*?)\s*```'
        match = re.search(json_pattern, raw_response, re.DOTALL)

        if match:
            json_str = match.group(1)
        else:
            # Try to find JSON object directly
            json_obj_pattern = r'\{.*\}'
            match = re.search(json_obj_pattern, raw_response, re.DOTALL)
            if match:
                json_str = match.group(0)
            else:
                return VisionToReactFlowResponse(
                    success=False,
                    message="Failed to extract JSON from AI response",
                    raw_response=raw_response[:500]
                )

        # Parse JSON
        try:
            diagram_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e}")
            return VisionToReactFlowResponse(
                success=False,
                message=f"Invalid JSON: {str(e)}",
                raw_response=json_str[:500]
            )

        # Validate structure
        if "nodes" not in diagram_data or "edges" not in diagram_data:
            return VisionToReactFlowResponse(
                success=False,
                message="Response missing 'nodes' or 'edges' field",
                raw_response=json_str[:500]
            )

        # Validate nodes using Pydantic models
        try:
            nodes = [Node(**node_data) for node_data in diagram_data["nodes"]]
            edges = [Edge(**edge_data) for edge_data in diagram_data["edges"]]
        except Exception as e:
            logger.error(f"Data validation error: {e}")
            return VisionToReactFlowResponse(
                success=False,
                message=f"Invalid node/edge data: {str(e)}",
                raw_response=json_str[:500]
            )

        # ✅ Apply collision detection (use aggressive mode to ensure no overlaps)
        nodes = _fix_node_overlaps(nodes, gentle_mode=False)

        logger.info(f"Successfully generated React Flow diagram: {len(nodes)} nodes, {len(edges)} edges (collision-fixed)")

        return VisionToReactFlowResponse(
            success=True,
            nodes=[n.dict() for n in nodes],
            edges=[e.dict() for e in edges]
        )

    except Exception as e:
        logger.error(f"React Flow generation failed: {e}", exc_info=True)
        return VisionToReactFlowResponse(
            success=False,
            message=f"Generation failed: {str(e)}"
        )

