from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Query
from typing import Optional
import logging

from app.models.schemas import (
    ImageAnalysisResponse,
    VisionToExcalidrawRequest,
    VisionToExcalidrawResponse,
    VisionToReactFlowRequest,
    VisionToReactFlowResponse
)
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
        # Create vision service
        vision_service = create_vision_service(
            request.provider,
            api_key=request.api_key,
            base_url=request.base_url,
            model_name=request.model_name
        )

        # Build prompt for Excalidraw generation
        excalidraw_prompt = f"""
Analyze the uploaded image and convert it to Excalidraw JSON format.

Output a valid JSON object with this structure:
{{
    "elements": [
        {{
            "id": "unique-id",
            "type": "rectangle" | "ellipse" | "diamond" | "arrow" | "text",
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
            "textAlign": "center"
        }}
    ],
    "appState": {{
        "viewBackgroundColor": "#ffffff"
    }}
}}

Rules:
1. For each shape in the image, create a corresponding element
2. For boxes/rectangles: use type="rectangle"
3. For circles: use type="ellipse"
4. For diamonds: use type="diamond"
5. For arrows/connections: use type="arrow" with points array [[x1,y1], [x2,y2]]
6. For text labels: either embed text in shapes or create separate text elements
7. Preserve spatial layout (x, y coordinates relative to canvas size {request.width}x{request.height})
8. Use unique IDs (e.g., "rect-1", "arrow-2", "text-3")
9. Output ONLY the JSON, no explanatory text

Canvas dimensions: {request.width}px width, {request.height}px height

{request.prompt or ''}
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

        logger.info(f"Successfully generated Excalidraw scene with {len(scene_data['elements'])} elements")

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
        # Create vision service
        vision_service = create_vision_service(
            request.provider,
            api_key=request.api_key,
            base_url=request.base_url,
            model_name=request.model_name
        )

        # Build prompt for React Flow generation
        reactflow_prompt = f"""
Analyze the uploaded diagram and convert it to SmartArchitect React Flow format.

Output a JSON object with this structure:
{{
    "nodes": [
        {{
            "id": "1",
            "type": "api" | "service" | "database" | "cache" | "client" | "queue" | "gateway" | "container" | "default",
            "position": {{"x": 100, "y": 100}},
            "data": {{
                "label": "Node Label",
                "shape": "rectangle" | "circle" | "diamond" | "hexagon" | "start-event" | "end-event",
                "iconType": "server" | "database" | "zap" | "monitor" | "list" | "cloud" | "package",
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

Available node types:
- api: API services (iconType: server, shape: rectangle)
- service: Backend services (iconType: settings, shape: rectangle)
- database: Databases (iconType: database, shape: circle or rectangle)
- cache: Cache systems (iconType: zap, shape: rectangle)
- client: Client applications (iconType: monitor, shape: rectangle)
- queue: Message queues (iconType: list, shape: rectangle)
- gateway: API gateways (iconType: cloud, shape: hexagon)
- container: Generic containers (iconType: package, shape: rectangle)
- default: Default nodes (shape: rectangle)

Available shapes:
- rectangle: Standard boxes
- circle: Circular nodes
- diamond: Decision/gateway nodes
- hexagon: Integration points
- start-event: BPMN start (green circle)
- end-event: BPMN end (red circle)

Rules:
1. Analyze each component and map to appropriate node type
2. Use descriptive labels
3. Preserve spatial layout with x, y coordinates
4. Ensure all edge source/target IDs match node IDs
5. Output ONLY the JSON, no extra text

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

        logger.info(f"Successfully generated React Flow diagram: {len(nodes)} nodes, {len(edges)} edges")

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

