import asyncio
import base64
import json
import re
from typing import Optional, Dict, Any, List
import logging

# AI SDK imports
try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from anthropic import Anthropic
except ImportError:
    Anthropic = None

from app.core.config import settings
from app.models.schemas import (
    ImageAnalysisResponse,
    Node,
    Edge,
    Position,
    NodeData,
    AIAnalysis,
    ArchitectureBottleneck,
    OptimizationSuggestion
)

logger = logging.getLogger(__name__)


class AIVisionService:
    """AI Vision 多模态图片分析服务"""

    def __init__(
        self,
        provider: str = "gemini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        self.provider = provider
        self.client = None
        self.custom_api_key = api_key
        self.custom_base_url = base_url
        self.custom_model_name = model_name
        default_model = (
            "claude-3-5-sonnet-20241022"
            if provider == "claude"
            else "Qwen/Qwen3-VL-32B-Thinking"
            if provider == "siliconflow"
            else "gpt-4o-mini"
        )
        self.model_name = model_name or default_model
        self.request_timeout = 60.0  # Increased from 8 to 60 seconds to handle slow AI responses
        # Allow fast fallback when running with placeholder keys (e.g., tests)
        self.mock_mode = api_key == "invalid"
        self._init_client()

    def _init_client(self):
        """初始化 AI 客户端"""
        try:
            if self.provider == "gemini":
                if not genai:
                    raise ImportError("google-generativeai not installed")
                # 优先使用传入的 api_key，否则使用环境变量
                api_key = self.custom_api_key or settings.GEMINI_API_KEY
                if not api_key:
                    raise ValueError("GEMINI_API_KEY not configured. Please set in UI or .env file")
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel("gemini-2.0-flash-exp")
                logger.info("Gemini client initialized")

            elif self.provider == "openai":
                if not OpenAI:
                    raise ImportError("openai not installed")
                # 优先使用传入的 api_key，否则使用环境变量
                api_key = self.custom_api_key or settings.OPENAI_API_KEY
                if not api_key:
                    raise ValueError("OPENAI_API_KEY not configured. Please set in UI or .env file")
                self.client = OpenAI(
                    api_key=api_key,
                    timeout=120.0,  # 2 minutes timeout
                    max_retries=2   # Limit retries
                )
                logger.info("OpenAI client initialized")

            elif self.provider == "claude":
                if not Anthropic:
                    raise ImportError("anthropic not installed")
                # 优先使用传入的 api_key，否则使用环境变量
                api_key = self.custom_api_key or settings.ANTHROPIC_API_KEY
                if not api_key:
                    raise ValueError("ANTHROPIC_API_KEY not configured. Please set in UI or .env file")
                self.client = Anthropic(api_key=api_key)
                logger.info("Claude client initialized")

            elif self.provider == "siliconflow":
                if not OpenAI:
                    raise ImportError("openai not installed")
                api_key = self.custom_api_key or settings.SILICONFLOW_API_KEY
                if not api_key:
                    raise ValueError("SILICONFLOW_API_KEY not configured. Please set in UI or .env file")
                base_url = self.custom_base_url or settings.SILICONFLOW_BASE_URL
                self.client = OpenAI(
                    api_key=api_key,
                    base_url=base_url,
                    timeout=240.0,  # 增加到 240 秒匹配 flowchart_timeout
                    max_retries=0   # 禁用重试（视觉模型处理慢，重试会导致超时）
                )
                logger.info(f"SiliconFlow client initialized with base_url: {base_url}")

            elif self.provider == "custom":
                # 自定义 provider
                # 如果模型名称包含 claude，使用 Anthropic SDK（兼容 Claude API 代理）
                # 否则使用 OpenAI SDK（兼容 OpenAI API）
                if not self.custom_api_key:
                    raise ValueError("Custom API key not provided")
                if not self.custom_base_url:
                    raise ValueError("Custom base URL not provided")

                # 检测是否是 Claude 模型
                is_claude_model = "claude" in self.model_name.lower()

                if is_claude_model:
                    # 使用 Anthropic SDK 处理 Claude 代理（如 linkflow.run）
                    if not Anthropic:
                        raise ImportError("anthropic not installed")

                    # Anthropic SDK 会自动添加 /v1 路径，所以需要去掉 base_url 中的 /v1
                    clean_base_url = self.custom_base_url.rstrip('/')
                    if clean_base_url.endswith('/v1'):
                        clean_base_url = clean_base_url[:-3]

                    self.client = Anthropic(
                        api_key=self.custom_api_key,
                        base_url=clean_base_url
                    )
                    logger.info(f"Custom Claude provider initialized with base_url: {clean_base_url} (original: {self.custom_base_url})")
                else:
                    # 使用 OpenAI SDK 处理 OpenAI 兼容的 API
                    if not OpenAI:
                        raise ImportError("openai not installed")
                    self.client = OpenAI(
                        api_key=self.custom_api_key,
                        base_url=self.custom_base_url,
                        timeout=120.0,
                        max_retries=2
                    )
                    logger.info(f"Custom provider initialized with base_url: {self.custom_base_url}")

            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

        except Exception as e:
            logger.error(f"Failed to initialize {self.provider} client: {e}")
            raise

    def _build_analysis_prompt(self, analyze_bottlenecks: bool = True) -> str:
        """构建针对架构图优化的 Prompt"""
        base_prompt = """
You are an expert software architect. Analyze this architecture diagram and extract the following information:

1. **Nodes**: Identify all components (services, APIs, databases, queues, caches, gateways, etc.)
   For each node, provide:
   - id: unique identifier (use kebab-case, e.g., "api-gateway", "user-service")
   - type: one of ["api", "service", "database", "queue", "cache", "gateway", "default"]
   - label: component name (user-friendly)
   - position: {x, y} coordinates (distribute evenly in a grid, starting from x:100, y:100, spacing 200px)

2. **Edges**: Identify all connections between components
   For each edge, provide:
   - id: unique identifier (e.g., "e1", "e2")
   - source: source node id
   - target: target node id
   - label: connection description (optional, e.g., "HTTP", "gRPC", "data flow")

3. **Mermaid Code**: Generate valid Mermaid.js flowchart code in "graph TD" format
   Use these node formats:
   - API: nodeId["Label"]
   - Service: nodeId[["Label"]]
   - Database: nodeId[("Label")]
   - Default: nodeId["Label"]

Example Mermaid output:
```
graph TD
    api-gateway["API Gateway"]
    user-service[["User Service"]]
    database[("PostgreSQL")]
    api-gateway --> |HTTP| user-service
    user-service --> database
```
"""

        if analyze_bottlenecks:
            base_prompt += """

4. **Architecture Analysis** (if analyze_bottlenecks=true):
   Identify potential issues:
   - Single points of failure (nodes with many dependencies but no redundancy)
   - Performance bottlenecks (high-traffic nodes without load balancing)
   - Scalability issues (monolithic components, tight coupling)
   - Security concerns (direct database access, missing authentication layers)

   For each bottleneck, provide:
   - node_id: affected node
   - type: issue category
   - severity: "critical", "high", "medium", or "low"
   - description: what's wrong
   - recommendation: how to fix it
"""

        base_prompt += """

CRITICAL: Return ONLY a valid JSON object with this EXACT structure (no markdown, no extra text):
{
  "nodes": [
    {
      "id": "api-gateway",
      "type": "api",
      "position": {"x": 250, "y": 100},
      "data": {"label": "API Gateway"}
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "api-gateway",
      "target": "user-service",
      "label": "HTTP"
    }
  ],
  "mermaid_code": "graph TD\\n    api-gateway[\\"API Gateway\\"]\\n    ...",
  "ai_analysis": {
    "bottlenecks": [
      {
        "node_id": "api-gateway",
        "type": "single_point_of_failure",
        "severity": "high",
        "description": "API Gateway has no redundancy",
        "recommendation": "Add load balancer and multiple instances"
      }
    ],
    "suggestions": [],
    "confidence": 0.85,
    "model_used": "gemini-2.0-flash-exp"
  }
}

Return ONLY the JSON. No markdown code blocks, no explanations.
"""

        return base_prompt

    def _build_flowchart_prompt_simple(self, preserve_layout: bool = True) -> str:
        """
        简化版流程图识别 Prompt - 用于图片识别快速模式

        特点：
        - 更短的提示词（减少 token 消耗）
        - 核心功能保留（节点识别、连线提取）
        - 处理时间约 60-120 秒
        """

        layout_hint = "preserve node positions" if preserve_layout else "use auto layout"

        prompt = f"""Analyze this flowchart image and extract nodes and edges.

**Node Types** (by shape):
- Circle → start-event (if text contains "Start"/"开始") or end-event (if "End"/"结束")
- Rectangle → task
- Diamond → decision
- Other shapes → default with shape attribute

**Output JSON** (no markdown wrapper):

{{
  "nodes": [
    {{"id": "node_1", "type": "start-event", "position": {{"x": 100, "y": 50}}, "data": {{"label": "Start", "shape": "circle"}}}},
    {{"id": "node_2", "type": "task", "position": {{"x": 100, "y": 200}}, "data": {{"label": "Task A", "shape": "rectangle"}}}}
  ],
  "edges": [
    {{"id": "edge_1", "source": "node_1", "target": "node_2", "label": ""}}
  ],
  "mermaid_code": "graph TD\\n    node_1((Start))\\n    node_2[Task A]\\n    node_1 --> node_2",
  "warnings": [],
  "analysis": {{"total_nodes": 2, "total_branches": 0}}
}}

**Requirements:**
- All nodes must have position (x, y)
- Extract text labels from nodes and edges
- {layout_hint}
- Return pure JSON only
"""

        return prompt

    def _build_flowchart_prompt_detailed(self, preserve_layout: bool = True) -> str:
        """
        详细版流程图识别 Prompt - 用于文本生成高质量模式

        特点：
        - 完整的形状识别规则
        - 详细的输出示例
        - 更高的识别准确度
        - 处理时间较长（200+ 秒）
        """

        # 支持的形状类型（从 SvgShapes.tsx 映射）
        supported_shapes = {
            "circle": "圆形 → start-event（开始）或 end-event（结束）",
            "rectangle": "矩形 → task（处理任务）",
            "diamond": "菱形 → decision（判断/决策）",
            "parallelogram": "平行四边形 → default with shape='parallelogram'（数据/输入输出）",
            "hexagon": "六边形 → default with shape='hexagon'（准备）",
            "trapezoid": "梯形 → default with shape='trapezoid'（手动操作）",
            "cylinder": "圆柱体 → database（数据库）",
            "document": "文档形 → default with shape='document'",
            "cloud": "云形 → default with shape='cloud'",
        }

        shapes_desc = "\\n".join([f"   - {shape}: {desc}" for shape, desc in supported_shapes.items()])

        layout_instruction = ""
        if preserve_layout:
            layout_instruction = """
4. **布局保留**：
   - 记录每个节点的相对位置（左上角坐标）
   - 参考原图的空间布局关系
   - x坐标从100开始，y坐标从50开始
   - 节点间距建议保持150-200px
"""
        else:
            layout_instruction = """
4. **自动布局**：
   - 忽略原图位置，使用标准布局
   - 从上到下、从左到右排列
   - x坐标从100开始，y坐标从50开始，每行间距200px
"""

        prompt = f"""
你是专业的流程图分析专家。请分析这张**流程图截图**，提取节点和连线关系。

## 识别规则

1. **节点类型识别**（根据形状判断）：
{shapes_desc}

   **重要：** 圆形节点需判断是开始还是结束：
   - 文本包含"开始"/"Start"/"启动" → type="start-event"
   - 文本包含"结束"/"End"/"完成" → type="end-event"
   - 无法判断时默认 → type="start-event"

2. **文本识别**：
   - 提取每个节点内的文本作为 label
   - 识别连线上的文本作为 edge.label
   - 如果节点无文本，label 设为 "未命名节点"

3. **连线识别**：
   - 识别箭头方向（起点节点 → 终点节点）
   - 判断连线类型：
     * 虚线 → animated: false（保持默认）
     * 实线 → animated: false
   - 提取判断分支标签（是/否、Yes/No、True/False、Y/N）

{layout_instruction}

## 输出格式（JSON）

返回 **纯 JSON 对象**，不要用 markdown 代码块包裹：

{{
  "nodes": [
    {{
      "id": "node_1",
      "type": "start-event",
      "position": {{"x": 100, "y": 50}},
      "data": {{
        "label": "开始",
        "shape": "circle"
      }}
    }},
    {{
      "id": "node_2",
      "type": "task",
      "position": {{"x": 100, "y": 200}},
      "data": {{
        "label": "执行任务A",
        "shape": "rectangle"
      }}
    }},
    {{
      "id": "node_3",
      "type": "decision",
      "position": {{"x": 100, "y": 350}},
      "data": {{
        "label": "条件判断",
        "shape": "diamond"
      }}
    }},
    {{
      "id": "node_4",
      "type": "end-event",
      "position": {{"x": 300, "y": 500}},
      "data": {{
        "label": "结束",
        "shape": "circle"
      }}
    }}
  ],
  "edges": [
    {{
      "id": "edge_1",
      "source": "node_1",
      "target": "node_2",
      "label": ""
    }},
    {{
      "id": "edge_2",
      "source": "node_2",
      "target": "node_3",
      "label": ""
    }},
    {{
      "id": "edge_3",
      "source": "node_3",
      "target": "node_4",
      "label": "是"
    }},
    {{
      "id": "edge_4",
      "source": "node_3",
      "target": "node_5",
      "label": "否"
    }}
  ],
  "mermaid_code": "graph TD\\n    node_1((开始))\\n    node_2[执行任务A]\\n    node_3{{条件判断}}\\n    node_4((结束))\\n    node_1 --> node_2\\n    node_2 --> node_3\\n    node_3 -->|是| node_4\\n    node_3 -->|否| node_5",
  "warnings": [
    {{"node_id": "node_X", "message": "原图为八边形，已映射为六边形（hexagon）"}}
  ],
  "analysis": {{
    "total_nodes": 4,
    "total_branches": 1,
    "flowchart_type": "业务流程图",
    "complexity": "简单",
    "description": "这是一个包含4个节点的简单流程图，从开始到结束经过一个判断节点"
  }}
}}

## 注意事项

- **所有节点必须有 position**（即使是自动布局也要给坐标）
- **edges 的 source 和 target 必须对应 nodes 的 id**
- **节点 id 必须唯一**（建议使用 node_1, node_2, node_3...）
- **不要输出 markdown 代码块**（如 ```json ... ```），直接输出 JSON
- **如果形状不在支持列表，选择最接近的形状，并在 warnings 中说明**
- **Mermaid 代码格式：**
  - 开始/结束节点：`nodeId((label))`
  - 处理节点：`nodeId[label]`
  - 判断节点：`nodeId{{label}}`
  - 连线：`node1 --> node2` 或 `node1 -->|label| node2`

现在开始分析图片，返回 JSON：
"""

        return prompt

    def _build_flowchart_prompt(self, preserve_layout: bool = True, fast_mode: bool = True) -> str:
        """
        构建流程图识别专用 Prompt

        参数：
        - preserve_layout: 是否保留原图布局
        - fast_mode: 是否使用快速模式（简化 prompt）
          - True: 用于图片识别（60-120秒）
          - False: 用于文本生成（200+秒，高质量）
        """
        if fast_mode:
            return self._build_flowchart_prompt_simple(preserve_layout)
        else:
            return self._build_flowchart_prompt_detailed(preserve_layout)

    async def analyze_architecture(
        self,
        image_data: bytes,
        analyze_bottlenecks: bool = True
    ) -> ImageAnalysisResponse:
        """分析架构图片"""
        prompt = self._build_analysis_prompt(analyze_bottlenecks)

        try:
            if self.provider == "gemini":
                result = await self._analyze_with_gemini(image_data, prompt)
            elif self.provider == "openai":
                result = await self._analyze_with_openai(image_data, prompt)
            elif self.provider == "claude":
                result = await self._analyze_with_claude(image_data, prompt)
            elif self.provider == "siliconflow":
                result = await self._analyze_with_siliconflow(image_data, prompt)
            elif self.provider == "custom":
                result = await self._analyze_with_custom(image_data, prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            return result

        except Exception as e:
            logger.error(f"Analysis failed with {self.provider}: {e}")
            raise

    async def analyze_flowchart(
        self,
        image_data: bytes,
        preserve_layout: bool = True,
        fast_mode: bool = True
    ) -> ImageAnalysisResponse:
        """
        分析流程图截图

        Args:
            image_data: 图片二进制数据
            preserve_layout: 是否保留原图布局
            fast_mode: 是否使用快速模式
                - True: 简化 prompt，60-120秒完成（图片识别推荐）
                - False: 详细 prompt，200+秒，高质量（文本生成推荐）

        Returns:
            ImageAnalysisResponse: 包含 nodes, edges, mermaid_code, warnings
        """
        prompt = self._build_flowchart_prompt(preserve_layout, fast_mode)

        # 根据 fast_mode 设置 max_tokens（足够大以避免JSON截断）
        max_tokens = 4096 if fast_mode else 8192

        # 设置超时时间
        self._flowchart_timeout = 240.0 if fast_mode else 300.0

        # 关键优化：设置 detail 参数（SiliconFlow 专用）
        self._image_detail = "low" if fast_mode else "high"

        try:
            logger.info(f"[FLOWCHART] Starting analysis with {self.provider}, preserve_layout={preserve_layout}, fast_mode={fast_mode}, max_tokens={max_tokens}, timeout={self._flowchart_timeout}s, detail={self._image_detail}")

            if self.provider == "gemini":
                result = await self._analyze_with_gemini(image_data, prompt, max_tokens)
            elif self.provider == "openai":
                result = await self._analyze_with_openai(image_data, prompt, max_tokens)
            elif self.provider == "claude":
                result = await self._analyze_with_claude(image_data, prompt, max_tokens)
            elif self.provider == "siliconflow":
                result = await self._analyze_with_siliconflow(image_data, prompt, max_tokens)
            elif self.provider == "custom":
                result = await self._analyze_with_custom(image_data, prompt, max_tokens)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            logger.info(f"[FLOWCHART] Analysis completed: {len(result.nodes)} nodes, {len(result.edges)} edges")

            # warnings 和 analysis 已经在 JSON 中，_build_response 会处理

            return result

        except Exception as e:
            logger.error(f"Flowchart analysis failed with {self.provider}: {e}", exc_info=True)
            raise

    async def _analyze_with_gemini(self, image_data: bytes, prompt: str, max_tokens: int = 4096) -> ImageAnalysisResponse:
        """使用 Gemini 分析"""
        try:
            logger.info(f"[GEMINI] Starting analysis, image size: {len(image_data)} bytes, max_tokens: {max_tokens}")

            # Gemini 支持直接传 bytes
            image_parts = [
                {
                    "mime_type": "image/jpeg",
                    "data": image_data
                }
            ]

            logger.info("[GEMINI] Calling Gemini API...")
            response = await self.client.generate_content_async(
                [prompt, image_parts[0]],
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": max_tokens
                }
            )

            logger.info(f"[GEMINI] Response received, type: {type(response)}")
            logger.info(f"[GEMINI] Response text length: {len(response.text) if hasattr(response, 'text') else 'N/A'}")

            # 提取 JSON
            result_json = self._extract_json_from_response(response.text)
            logger.info(f"[GEMINI] JSON extracted successfully")

            # 验证并构建响应
            result = self._build_response(result_json)
            logger.info(f"[GEMINI] Analysis completed: {len(result.nodes)} nodes, {len(result.edges)} edges")
            return result

        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}", exc_info=True)
            raise

    async def _analyze_with_openai(self, image_data: bytes, prompt: str, max_tokens: int = 4096) -> ImageAnalysisResponse:
        """使用 OpenAI GPT-4 Vision 分析"""
        try:
            logger.info(f"[OPENAI] Starting vision analysis, max_tokens: {max_tokens}")
            image_b64 = base64.b64encode(image_data).decode("utf-8")

            # 使用 asyncio.to_thread 包装同步调用
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.2
            )

            logger.info("[OPENAI] Response received, extracting JSON")
            result_json = self._extract_json_from_response(
                response.choices[0].message.content
            )

            return self._build_response(result_json)

        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}", exc_info=True)
            raise

    async def _analyze_with_claude(self, image_data: bytes, prompt: str, max_tokens: int = 4096) -> ImageAnalysisResponse:
        """使用 Claude 3.5 Sonnet 分析"""
        try:
            logger.info(f"[CLAUDE] Starting vision analysis, max_tokens: {max_tokens}")
            image_b64 = base64.b64encode(image_data).decode("utf-8")

            # 使用 asyncio.to_thread 包装同步调用
            response = await asyncio.to_thread(
                self.client.messages.create,
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=0.2,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_b64
                                }
                            }
                        ]
                    }
                ]
            )

            logger.info("[CLAUDE] Response received, extracting JSON")
            result_json = self._extract_json_from_response(
                response.content[0].text
            )

            return self._build_response(result_json)

        except Exception as e:
            logger.error(f"Claude analysis failed: {e}", exc_info=True)
            raise

    async def _analyze_with_siliconflow(self, image_data: bytes, prompt: str, max_tokens: int = 4096) -> ImageAnalysisResponse:
        """使用 SiliconFlow 视觉模型分析（如 Qwen3-VL）"""
        try:
            # 获取超时配置（如果是 flowchart 调用会设置此属性）
            timeout = getattr(self, '_flowchart_timeout', 180.0)
            # 获取 detail 参数（low/high，用于控制图片分辨率）
            detail = getattr(self, '_image_detail', 'high')

            logger.info(f"[SILICONFLOW] Starting vision analysis with model: {self.model_name}, max_tokens: {max_tokens}, timeout: {timeout}s, detail: {detail}")
            image_b64 = base64.b64encode(image_data).decode("utf-8")

            # 使用 asyncio.to_thread 包装同步调用，并增加超时时间
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model_name,  # 例如: Qwen/Qwen3-VL-32B-Thinking
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_b64}",
                                        "detail": detail  # 关键参数：low=快速，high=高质量
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=max_tokens,
                    temperature=0.2
                ),
                timeout=timeout
            )

            logger.info("[SILICONFLOW] Response received, extracting JSON")
            result_json = self._extract_json_from_response(
                response.choices[0].message.content
            )

            logger.info(f"[SILICONFLOW] Analysis completed successfully")
            return self._build_response(result_json)

        except asyncio.TimeoutError:
            logger.error(f"SiliconFlow vision analysis timeout after {timeout}s")
            raise ValueError(f"AI vision analysis timeout ({timeout/60:.1f} minutes). Please try again or use a different provider.")
        except Exception as e:
            logger.error(f"SiliconFlow vision analysis failed: {e}", exc_info=True)
            raise

    async def _analyze_with_custom(self, image_data: bytes, prompt: str, max_tokens: int = 4096) -> ImageAnalysisResponse:
        """使用自定义 provider 分析（支持 OpenAI 和 Claude 格式）"""
        try:
            logger.info(f"[CUSTOM] Starting vision analysis, max_tokens: {max_tokens}")
            image_b64 = base64.b64encode(image_data).decode("utf-8")

            # 使用自定义模型名称，默认为 gpt-4-vision-preview
            model = self.custom_model_name or "gpt-4-vision-preview"

            logger.info(f"[CUSTOM] Using model: {model}, base_url: {self.custom_base_url}")

            # 检测是否是 Claude 模型（检查模型名是否包含 claude）
            is_claude_model = "claude" in model.lower()

            if is_claude_model:
                # Claude API 使用 Anthropic 格式
                logger.info("[CUSTOM] Detected Claude model, using Anthropic image format")

                # 检测图片类型
                import imghdr
                media_type = imghdr.what(None, h=image_data)
                if media_type == "jpeg":
                    media_type = "image/jpeg"
                elif media_type == "png":
                    media_type = "image/png"
                elif media_type == "webp":
                    media_type = "image/webp"
                elif media_type == "gif":
                    media_type = "image/gif"
                else:
                    media_type = "image/jpeg"  # 默认 JPEG

                logger.info(f"[CUSTOM] Image media type: {media_type}")

                # 使用 Anthropic 消息格式
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": media_type,
                                        "data": image_b64
                                    }
                                },
                                {"type": "text", "text": prompt}
                            ]
                        }
                    ],
                    max_tokens=max_tokens,
                    temperature=0.2
                )
            else:
                # OpenAI 格式（默认）
                logger.info("[CUSTOM] Using OpenAI image_url format")
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_b64}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=max_tokens,
                    temperature=0.2
                )

            logger.info(f"[CUSTOM] Response type: {type(response)}")

            # 打印完整的响应内容
            try:
                if hasattr(response, 'model_dump'):
                    import json
                    response_dict = response.model_dump()
                    logger.info(f"[CUSTOM] Full response body:\n{json.dumps(response_dict, indent=2, ensure_ascii=False)}")
                else:
                    logger.info(f"[CUSTOM] Full response (str): {str(response)[:2000]}")
            except Exception as e:
                logger.error(f"[CUSTOM] Failed to dump response: {e}")

            logger.info(f"[CUSTOM] Response has 'output': {hasattr(response, 'output')}")
            logger.info(f"[CUSTOM] Response has 'choices': {hasattr(response, 'choices')}")

            if hasattr(response, 'output'):
                logger.info(f"[CUSTOM] response.output value: {response.output}")
            if hasattr(response, 'choices'):
                logger.info(f"[CUSTOM] response.choices value: {response.choices}")

            # 处理不同的响应格式
            content = None

            # Anthropic SDK 标准格式：response.content[0].text
            if is_claude_model and hasattr(response, 'content') and response.content:
                logger.info("[CUSTOM] Using Anthropic 'content' format")
                for content_block in response.content:
                    if hasattr(content_block, 'text'):
                        content = content_block.text
                        logger.info(f"[CUSTOM] Extracted from Anthropic format, length: {len(content)}")
                        break
                    elif isinstance(content_block, dict) and 'text' in content_block:
                        content = content_block['text']
                        logger.info(f"[CUSTOM] Extracted from Anthropic dict format, length: {len(content)}")
                        break

            # 某些中转站的格式：response.output[0].content[0].text
            elif hasattr(response, 'output') and response.output:
                logger.info("[CUSTOM] Using 'output' format")
                output_item = response.output[0]
                logger.info(f"[CUSTOM] output_item type: {type(output_item)}")

                # 处理字典格式
                if isinstance(output_item, dict):
                    logger.info("[CUSTOM] output_item is dict")
                    content_list = output_item.get('content', [])
                    logger.info(f"[CUSTOM] content_list length: {len(content_list)}")

                    for i, content_item in enumerate(content_list):
                        logger.info(f"[CUSTOM] content_item[{i}] type: {type(content_item)}")
                        if isinstance(content_item, dict) and 'text' in content_item:
                            content = content_item['text']
                            logger.info(f"[CUSTOM] Extracted content from dict, length: {len(content)}")
                            break

                # 处理对象格式
                elif hasattr(output_item, 'content') and output_item.content:
                    logger.info("[CUSTOM] output_item is object")
                    for i, content_item in enumerate(output_item.content):
                        logger.info(f"[CUSTOM] content_item[{i}] type: {type(content_item)}")

                        # 字典访问
                        if isinstance(content_item, dict) and 'text' in content_item:
                            content = content_item['text']
                            logger.info(f"[CUSTOM] Extracted from dict, length: {len(content)}")
                            break
                        # 对象访问
                        elif hasattr(content_item, 'text'):
                            content = content_item.text
                            logger.info(f"[CUSTOM] Extracted from attr, length: {len(content)}")
                            break

            # 标准 OpenAI 格式：response.choices[0].message.content
            elif hasattr(response, 'choices') and response.choices:
                logger.info("[CUSTOM] Using 'choices' format")
                content = response.choices[0].message.content
                logger.info(f"[CUSTOM] Extracted content length: {len(content) if content else 0}")

            # 如果还是字符串（不应该发生，但以防万一）
            elif isinstance(response, str):
                logger.info("[CUSTOM] Response is string")
                content = response

            if not content:
                logger.error(f"[CUSTOM] Failed to extract content")
                if hasattr(response, 'model_dump'):
                    logger.error(f"[CUSTOM] Response dump: {response.model_dump()}")
                raise ValueError("Unable to extract content from API response")

            # 检查是否因为长度限制被截断
            is_truncated = False
            if hasattr(response, 'choices') and response.choices:
                finish_reason = response.choices[0].finish_reason
                is_truncated = finish_reason == 'length'
                if is_truncated:
                    logger.warning(f"[CUSTOM] Response was truncated due to max_tokens limit (finish_reason='length')")

            result_json = self._extract_json_from_response(content, is_truncated=is_truncated)
            return self._build_response(result_json)

        except Exception as e:
            logger.error(f"Custom provider analysis failed: {e}")
            raise

    def _extract_json_from_response(self, text: str, is_truncated: bool = False) -> Dict[str, Any]:
        """Extract JSON from AI response with aggressive cleaning and multiple fallback strategies."""

        def _repair_truncated_json(raw: str) -> str:
            """尝试修复被截断的JSON"""
            # 移除markdown代码块标记
            cleaned = re.sub(r"```(?:json)?", "", raw).strip()

            # 提取JSON边界
            start = cleaned.find("{")
            if start != -1:
                cleaned = cleaned[start:]

            # 检查并修复截断的字符串
            # 如果最后一个字符不是闭合的，尝试补全
            if cleaned and not cleaned.endswith("}"):
                # 查找最后一个完整的结构
                # 尝试找到最后一个完整的数组或对象

                # 统计未闭合的括号
                open_brackets = cleaned.count("[") - cleaned.count("]")
                open_braces = cleaned.count("{") - cleaned.count("}")
                open_quotes = cleaned.count('"') - cleaned.count('\\"')

                # 如果有未闭合的引号，先闭合它
                if open_quotes % 2 != 0:
                    cleaned += '"'

                # 闭合未闭合的数组
                cleaned += "]" * open_brackets

                # 闭合未闭合的对象
                cleaned += "}" * open_braces

                logger.info(f"[JSON REPAIR] Fixed {open_quotes % 2} quotes, {open_brackets} brackets, {open_braces} braces")

            return cleaned

        def _sanitize_json(raw: str) -> str:
            """Aggressive JSON sanitization with multiple repair strategies."""
            # Strip markdown code blocks
            cleaned = re.sub(r"```(?:json)?", "", raw)

            # Extract JSON boundaries
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and end > start:
                cleaned = cleaned[start:end + 1]

            # Fix common JSON issues
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)  # Remove trailing commas
            cleaned = re.sub(r"'", '"', cleaned)  # Single quotes to double quotes
            cleaned = re.sub(r'(\w+):', r'"\1":', cleaned)  # Unquoted keys (basic fix)
            cleaned = cleaned.replace("\n", " ")  # Remove newlines

            return cleaned

        # Strategy 0: If truncated, try to repair first
        if is_truncated:
            try:
                logger.info("[JSON REPAIR] Attempting to repair truncated JSON")
                repaired = _repair_truncated_json(text)
                result = json.loads(repaired)
                logger.info("[JSON REPAIR] Successfully parsed repaired truncated JSON")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"[JSON REPAIR] Failed to parse repaired JSON: {e}")
                # Continue to other strategies

        # Strategy 1: Try direct JSON parse of full text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Strategy 2: Extract from ```json...``` blocks
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
        except json.JSONDecodeError:
            pass

        # Strategy 3: Extract from ```...``` blocks
        try:
            code_match = re.search(r'```\s*(\{.*?\})\s*```', text, re.DOTALL)
            if code_match:
                return json.loads(code_match.group(1))
        except json.JSONDecodeError:
            pass

        # Strategy 4: Find JSON object boundaries
        try:
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

        # Strategy 5: Aggressive sanitization
        try:
            sanitized = _sanitize_json(text)
            logger.warning(f"Using sanitized JSON (original failed): {sanitized[:200]}...")
            return json.loads(sanitized)
        except json.JSONDecodeError as e:
            logger.error(f"All JSON parse strategies failed: {e}")
            logger.error(f"Raw response (first 500 chars): {text[:500]}")
            logger.error(f"Raw response (last 500 chars): {text[-500:]}")
            raise ValueError(f"Invalid JSON response from AI after all repair attempts: {str(e)}")

    def _build_response(self, result_json: Dict[str, Any]) -> ImageAnalysisResponse:
        """构建响应对象"""
        try:
            # 解析节点
            nodes = [
                Node(
                    id=node["id"],
                    type=node.get("type", "default"),
                    position=Position(**node["position"]),
                    data=NodeData(
                        label=node["data"]["label"],
                        shape=node["data"].get("shape")  # 添加 shape 支持（流程图识别）
                    )
                )
                for node in result_json.get("nodes", [])
            ]

            # 解析边
            edges = [
                Edge(
                    id=edge["id"],
                    source=edge["source"],
                    target=edge["target"],
                    label=edge.get("label")
                )
                for edge in result_json.get("edges", [])
            ]

            # 解析 AI 分析（如果有）
            ai_analysis = None
            if "ai_analysis" in result_json and result_json["ai_analysis"]:
                ai_data = result_json["ai_analysis"]
                ai_analysis = AIAnalysis(
                    bottlenecks=[
                        ArchitectureBottleneck(**b)
                        for b in ai_data.get("bottlenecks", [])
                    ],
                    suggestions=[
                        OptimizationSuggestion(**s)
                        for s in ai_data.get("suggestions", [])
                    ],
                    confidence=ai_data.get("confidence"),
                    model_used=ai_data.get("model_used")
                )

            # 提取 warnings（流程图识别专用）
            warnings = result_json.get("warnings", [])

            # 提取 analysis（流程图分析）
            flowchart_analysis = result_json.get("analysis", {})

            return ImageAnalysisResponse(
                nodes=nodes,
                edges=edges,
                mermaid_code=result_json.get("mermaid_code", ""),
                success=True,
                ai_analysis=ai_analysis,
                warnings=warnings,  # 新增字段
                flowchart_analysis=flowchart_analysis  # 新增字段
            )

        except Exception as e:
            logger.error(f"Failed to build response: {e}")
            raise ValueError(f"Invalid response structure: {str(e)}")

    # ========== Vision-to-Text Generation (for Excalidraw/ReactFlow) ==========

    async def generate_with_vision(self, image_data: bytes, prompt: str) -> str:
        """
        Generate text response from image using vision AI.
        Returns raw text output (typically JSON) for diagram generation.

        Args:
            image_data: Image bytes
            prompt: Text prompt with instructions

        Returns:
            Raw text response from AI model
        """
        try:
            logger.info(f"[VISION GEN] Generating with {self.provider}")

            if self.provider == "gemini":
                return await self._generate_with_gemini_vision(image_data, prompt)
            elif self.provider == "openai":
                return await self._generate_with_openai_vision(image_data, prompt)
            elif self.provider == "claude":
                return await self._generate_with_claude_vision(image_data, prompt)
            elif self.provider == "siliconflow":
                return await self._generate_with_siliconflow_vision(image_data, prompt)
            elif self.provider == "custom":
                return await self._generate_with_custom_vision(image_data, prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

        except Exception as e:
            logger.error(f"Vision generation failed: {e}", exc_info=True)
            raise

    async def _generate_with_gemini_vision(self, image_data: bytes, prompt: str) -> str:
        """Gemini vision generation"""
        import PIL.Image
        import io

        image = PIL.Image.open(io.BytesIO(image_data))
        response = self.client.generate_content([prompt, image])
        return response.text

    async def _generate_with_openai_vision(self, image_data: bytes, prompt: str) -> str:
        """OpenAI vision generation"""
        import base64

        base64_image = base64.b64encode(image_data).decode()

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                    }
                ]
            }],
            max_tokens=16384,
            temperature=0.7
        )

        return response.choices[0].message.content

    async def _generate_with_claude_vision(self, image_data: bytes, prompt: str) -> str:
        """Claude vision generation"""
        import base64

        base64_image = base64.b64encode(image_data).decode()

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=16384,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }]
        )

        return response.content[0].text

    async def _generate_with_siliconflow_vision(self, image_data: bytes, prompt: str) -> str:
        """SiliconFlow vision generation"""
        import base64

        base64_image = base64.b64encode(image_data).decode()

        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                    }
                ]
            }],
            max_tokens=16384,
            temperature=0.7
        )

        return response.choices[0].message.content

    async def _generate_with_custom_vision(self, image_data: bytes, prompt: str) -> str:
        """Custom provider vision generation (auto-detect Claude vs OpenAI format)"""
        import base64

        base64_image = base64.b64encode(image_data).decode()

        # Check if this is a Claude-native endpoint (linkflow, anthropic)
        is_claude_format = (
            self.custom_base_url and
            ("linkflow" in self.custom_base_url.lower() or
             "anthropic" in self.custom_base_url.lower())
        )

        if is_claude_format:
            # Use Anthropic's native API format
            from anthropic import Anthropic

            # Remove /v1 suffix from base_url if present (Anthropic SDK adds it automatically)
            anthropic_base_url = self.custom_base_url.rstrip("/")
            if anthropic_base_url.endswith("/v1"):
                anthropic_base_url = anthropic_base_url[:-3]

            client = Anthropic(
                api_key=self.custom_api_key,
                base_url=anthropic_base_url
            )

            response = client.messages.create(
                model=self.model_name,
                max_tokens=16384,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image
                            }
                        }
                    ]
                }]
            )

            return response.content[0].text
        else:
            # Use OpenAI-compatible format
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{base64_image}"}
                        }
                    ]
                }],
                max_tokens=16384,
                temperature=0.7
            )

            return response.choices[0].message.content

    # ========== Unified Streaming Methods (for SSE streaming to frontend) ==========

    async def generate_with_stream(self, prompt: str):
        """
        Unified streaming generation entry point supporting all providers.
        Yields text tokens as they are generated by the LLM.

        Returns: AsyncGenerator[str, None]
        """
        import queue
        import threading

        try:
            if self.provider == "openai":
                # OpenAI native streaming - use queue for real-time streaming
                logger.info(f"[STREAM] OpenAI streaming with model: {self.model_name}")
                q = queue.Queue()

                def _openai_stream():
                    try:
                        logger.info(f"[STREAM] Initiating OpenAI stream with model={self.model_name}")
                        stream = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[{"role": "user", "content": prompt}],
                            stream=True,
                            temperature=0.2,
                            max_tokens=16384,  # Increased to 16K for complete Excalidraw JSON generation
                        )
                        logger.info("[STREAM] OpenAI stream created, starting iteration")
                        for chunk in stream:
                            delta = chunk.choices[0].delta.content
                            if delta:
                                q.put(("data", delta))
                        logger.info("[STREAM] OpenAI stream completed successfully")
                        q.put(("done", None))
                    except Exception as e:
                        logger.error(f"[STREAM] Exception in _openai_stream: {e}", exc_info=True)
                        q.put(("error", e))

                loop = asyncio.get_event_loop()
                # Start streaming in background thread
                loop.run_in_executor(None, _openai_stream)

                while True:
                    msg_type, data = await loop.run_in_executor(None, q.get)
                    if msg_type == "error":
                        raise data
                    elif msg_type == "done":
                        break
                    else:
                        yield data

            elif self.provider == "claude":
                # Claude streaming with context manager
                logger.info(f"[STREAM] Claude streaming with model: {self.model_name}")
                q = queue.Queue()

                def _claude_stream():
                    try:
                        logger.info(f"[STREAM] Initiating Claude stream with model={self.model_name}")
                        with self.client.messages.stream(
                            model=self.model_name,
                            max_tokens=16384,  # Increased to 16K for complete Excalidraw JSON generation
                            temperature=0.2,
                            messages=[{"role": "user", "content": prompt}],
                        ) as stream:
                            for text in stream.text_stream:
                                q.put(("data", text))
                        logger.info("[STREAM] Claude stream completed successfully")
                        q.put(("done", None))
                    except Exception as e:
                        logger.error(f"[STREAM] Exception in _claude_stream: {e}", exc_info=True)
                        q.put(("error", e))

                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, _claude_stream)

                while True:
                    msg_type, data = await loop.run_in_executor(None, q.get)
                    if msg_type == "error":
                        raise data
                    elif msg_type == "done":
                        break
                    else:
                        yield data

            elif self.provider == "gemini":
                # Gemini native async streaming
                response = await self.client.generate_content_async(
                    prompt,
                    generation_config={"temperature": 0.2},
                    stream=True,
                )
                async for chunk in response:
                    if chunk.text:
                        yield chunk.text

            elif self.provider == "siliconflow" or self.provider == "custom":
                # SiliconFlow/Custom (OpenAI-compatible) - use queue for real-time streaming
                logger.info(f"[STREAM] {self.provider} streaming with model: {self.model_name}")
                q = queue.Queue()

                def _compatible_stream():
                    try:
                        logger.info(f"[STREAM] Initiating {self.provider} stream")
                        stream = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[{"role": "user", "content": prompt}],
                            stream=True,
                            max_tokens=16384,
                            temperature=0.2,
                        )
                        logger.info(f"[STREAM] {self.provider} stream created, iterating chunks")
                        for chunk in stream:
                            if not getattr(chunk, "choices", None) or not chunk.choices:
                                continue
                            delta = chunk.choices[0].delta.content if chunk.choices[0].delta else None
                            if delta:
                                q.put(("data", delta))
                        logger.info(f"[STREAM] {self.provider} stream completed")
                        q.put(("done", None))
                    except Exception as e:
                        logger.error(f"[STREAM] Exception in {self.provider}_stream: {e}", exc_info=True)
                        q.put(("error", e))

                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, _compatible_stream)

                while True:
                    msg_type, data = await loop.run_in_executor(None, q.get)
                    if msg_type == "error":
                        raise data
                    elif msg_type == "done":
                        break
                    else:
                        yield data

            else:
                raise ValueError(f"Streaming not supported for provider: {self.provider}")

        except Exception as e:
            logger.error(f"Streaming failed for {self.provider}: {e}", exc_info=True)
            raise

    async def generate_with_vision_stream(self, image_data: bytes, prompt: str):
        """
        🔥 NEW: Streaming vision generation supporting image + text input.
        Uses multimodal streaming APIs (Claude/GPT-4 Vision support streaming).
        Yields tokens as they are generated.
        """
        import queue
        import threading

        try:
            # 检查是否是 Claude 模型（官方或 custom）
            is_claude_model = (
                self.provider == "claude" or
                (self.provider == "custom" and "claude" in self.model_name.lower())
            )

            if is_claude_model:
                # Claude Vision streaming with multimodal content
                logger.info(f"[VISION-STREAM] Claude streaming with model: {self.model_name}")
                q = queue.Queue()

                def _claude_vision_stream():
                    try:
                        import base64
                        # Detect image format
                        image_b64 = base64.b64encode(image_data).decode('utf-8')

                        # Determine media type from image bytes
                        media_type = "image/jpeg"
                        if image_data.startswith(b'\x89PNG'):
                            media_type = "image/png"
                        elif image_data.startswith(b'GIF'):
                            media_type = "image/gif"
                        elif image_data.startswith(b'\xff\xd8\xff'):
                            media_type = "image/jpeg"
                        elif image_data.startswith(b'RIFF') and b'WEBP' in image_data[:20]:
                            media_type = "image/webp"

                        # Build multimodal content
                        content = [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt,
                            }
                        ]

                        logger.info(f"[VISION-STREAM] Starting Claude vision stream")
                        with self.client.messages.stream(
                            model=self.model_name,
                            max_tokens=16384,
                            temperature=0.2,
                            messages=[{"role": "user", "content": content}],
                        ) as stream:
                            for text in stream.text_stream:
                                q.put(("data", text))
                        logger.info("[VISION-STREAM] Claude stream completed")
                        q.put(("done", None))
                    except Exception as e:
                        logger.error(f"[VISION-STREAM] Exception: {e}", exc_info=True)
                        q.put(("error", e))

                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, _claude_vision_stream)

                while True:
                    msg_type, data = await loop.run_in_executor(None, q.get)
                    if msg_type == "error":
                        raise data
                    elif msg_type == "done":
                        break
                    else:
                        yield data

            elif self.provider == "openai" or self.provider == "custom":
                # OpenAI GPT-4 Vision streaming
                logger.info(f"[VISION-STREAM] OpenAI streaming with model: {self.model_name}")
                q = queue.Queue()

                def _openai_vision_stream():
                    try:
                        import base64
                        image_b64 = base64.b64encode(image_data).decode('utf-8')

                        # Detect format
                        if image_data.startswith(b'\x89PNG'):
                            data_url = f"data:image/png;base64,{image_b64}"
                        elif image_data.startswith(b'\xff\xd8\xff'):
                            data_url = f"data:image/jpeg;base64,{image_b64}"
                        else:
                            data_url = f"data:image/jpeg;base64,{image_b64}"

                        content = [
                            {
                                "type": "image_url",
                                "image_url": {"url": data_url}
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]

                        logger.info("[VISION-STREAM] Starting OpenAI vision stream")
                        stream = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[{"role": "user", "content": content}],
                            stream=True,
                            temperature=0.2,
                            max_tokens=16384,
                        )

                        for chunk in stream:
                            delta = chunk.choices[0].delta.content
                            if delta:
                                q.put(("data", delta))
                        logger.info("[VISION-STREAM] OpenAI stream completed")
                        q.put(("done", None))
                    except Exception as e:
                        logger.error(f"[VISION-STREAM] Exception: {e}", exc_info=True)
                        q.put(("error", e))

                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, _openai_vision_stream)

                while True:
                    msg_type, data = await loop.run_in_executor(None, q.get)
                    if msg_type == "error":
                        raise data
                    elif msg_type == "done":
                        break
                    else:
                        yield data

            else:
                raise ValueError(f"Streaming vision not supported for provider: {self.provider}")

        except Exception as e:
            logger.error(f"Vision stream failed: {e}", exc_info=True)
            raise

    # ========== Phase 3: Text-only Prompt Methods (for Prompter System) ==========

    async def _analyze_with_gemini_text(self, prompt: str) -> dict:
        """使用 Gemini 处理纯文本提示（无图片）"""
        try:
            logger.info("[GEMINI TEXT] Starting text-only analysis")

            response = await self.client.generate_content_async(
                prompt,
                generation_config={
                    "temperature": 0.2,
                    "max_output_tokens": 16384  # Increased to 16K for complete Excalidraw JSON generation
                }
            )

            logger.info(f"[GEMINI TEXT] Response received")
            result_json = self._extract_json_from_response(response.text)
            logger.info(f"[GEMINI TEXT] JSON extracted successfully")

            return result_json

        except Exception as e:
            logger.error(f"Gemini text analysis failed: {e}", exc_info=True)
            raise

    async def _analyze_with_openai_text(self, prompt: str) -> dict:
        """使用 OpenAI 处理纯文本提示（无图片）"""
        try:
            logger.info("[OPENAI TEXT] Starting text-only analysis")

            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=16384,  # Increased to 16K for complete Excalidraw JSON generation
                temperature=0.2
            )

            result_json = self._extract_json_from_response(
                response.choices[0].message.content
            )

            logger.info(f"[OPENAI TEXT] JSON extracted successfully")
            return result_json

        except Exception as e:
            logger.error(f"OpenAI text analysis failed: {e}", exc_info=True)
            raise

    async def _analyze_with_claude_text(self, prompt: str) -> dict:
        """使用 Claude 处理纯文本提示（无图片）"""
        try:
            logger.info("[CLAUDE TEXT] Starting text-only analysis")

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=16384,  # Increased to 16K for complete Excalidraw JSON generation
                temperature=0.2,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            result_json = self._extract_json_from_response(
                response.content[0].text
            )

            logger.info(f"[CLAUDE TEXT] JSON extracted successfully")
            return result_json

        except Exception as e:
            logger.error(f"Claude text analysis failed: {e}", exc_info=True)
            raise

    async def _analyze_with_siliconflow_text(self, prompt: str) -> dict:
        """使用 SiliconFlow 处理纯文本提示（OpenAI 兼容 chat/completions）"""
        try:
            logger.info("[SILICONFLOW TEXT] Starting text-only analysis")

            # Detect if this is an Excalidraw prompt (needs more tokens for element arrays)
            is_excalidraw = "excalidraw" in prompt.lower() or "elements" in prompt.lower()
            max_tokens = 16384 if is_excalidraw else 2000  # Increased to 16K for complete Excalidraw generation

            logger.info(f"[SILICONFLOW TEXT] Using max_tokens={max_tokens}, is_excalidraw={is_excalidraw}")

            # SiliconFlow SDK 调用是同步的，包一层线程 + 超时，避免请求长时间挂起
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=max_tokens,
                    temperature=0.3,
                    top_p=0.7,
                    frequency_penalty=0.5,
                    stream=False,
                    # 强制返回纯 JSON 对象，避免模型输出额外说明文字
                    response_format={"type": "json_object"},
                ),
                timeout=self.request_timeout,
            )

            # 当 response_format 为 json_object 时，content 应已是 JSON 对象
            content = response.choices[0].message.content
            if isinstance(content, dict):
                result_json = content
            else:
                result_json = self._extract_json_from_response(content)

            logger.info("[SILICONFLOW TEXT] JSON extracted successfully")
            return result_json

        except Exception as e:
            logger.error(f"SiliconFlow text analysis failed: {e}", exc_info=True)
            raise

    async def _analyze_with_siliconflow_text_stream(self, prompt: str) -> str:
        """SiliconFlow streaming text -> concatenated text output."""
        try:
            logger.info("[SILICONFLOW STREAM] Starting text stream")

            def _stream():
                stream = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1200,
                    temperature=0.3,
                    top_p=0.7,
                    frequency_penalty=0.5,
                    stream=True,
                    response_format={"type": "text"},
                )
                text_acc = []
                for chunk in stream:
                    delta = chunk.choices[0].delta.content
                    if not delta:
                        continue
                    piece = "".join(delta)
                    text_acc.append(piece)
                return "".join(text_acc)

            full_text = await asyncio.wait_for(asyncio.to_thread(_stream), timeout=self.request_timeout)
            logger.info("[SILICONFLOW STREAM] Collected length=%s", len(full_text))
            if not full_text.strip():
                raise ValueError("Empty stream output")
            return full_text
        except Exception as e:
            logger.error(f"SiliconFlow streaming failed: {e}", exc_info=True)
            raise

    async def _analyze_with_custom_text(self, prompt: str) -> dict:
        """使用自定义 provider 处理纯文本提示（无图片）"""
        try:
            logger.info("[CUSTOM TEXT] Starting text-only analysis")

            response = self.client.chat.completions.create(
                model=self.custom_model_name or "gpt-3.5-turbo",
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=16384,  # Increased to 16K for complete Excalidraw JSON generation
                temperature=0.2
            )

            # Handle different response formats
            content = None
            if hasattr(response, 'choices') and response.choices:
                content = response.choices[0].message.content
            elif hasattr(response, 'output') and response.output:
                output_item = response.output[0]
                if isinstance(output_item, dict):
                    content_list = output_item.get('content', [])
                    for content_item in content_list:
                        if isinstance(content_item, dict) and 'text' in content_item:
                            content = content_item['text']
                            break

            if not content:
                raise ValueError("Unable to extract content from custom provider response")

            result_json = self._extract_json_from_response(content)
            logger.info(f"[CUSTOM TEXT] JSON extracted successfully")
            return result_json

        except Exception as e:
            logger.error(f"Custom text analysis failed: {e}", exc_info=True)
            raise

    def _build_mock_script(self, arch_desc: str, duration: str) -> str:
        """Local fallback script used when provider is unavailable or mocked."""
        intro = arch_desc.replace("\n", " ").strip()
        return (
            f"[Mock {duration} script] {intro}\n"
            "AI provider unavailable or invalid key. Connect a valid provider to generate a full presentation script."
        )

    # ========== Phase 4: Speech Script Generation ==========

    async def generate_speech_script(
        self,
        nodes: List,
        edges: List,
        duration: str = "2min"
    ) -> str:
        """Generate a presentation script for the architecture"""

        # Build architecture description
        arch_desc = f"Architecture with {len(nodes)} components and {len(edges)} connections:\\n\\n"

        arch_desc += "Components:\\n"
        for node in nodes:
            arch_desc += f"- {node.data.label} (type: {node.type or 'default'})\\n"

        arch_desc += "\\nConnections:\\n"
        for edge in edges:
            source_node = next((n for n in nodes if n.id == edge.source), None)
            target_node = next((n for n in nodes if n.id == edge.target), None)
            if source_node and target_node:
                label_text = f" ({edge.label})" if edge.label else ""
                arch_desc += f"- {source_node.data.label} → {target_node.data.label}{label_text}\\n"

        # Duration-specific prompts (中文输出)
        duration_prompts = {
            "30s": "生成一个30秒的电梯演讲稿（约150字）。聚焦核心价值主张。",
            "2min": "生成一个2分钟的演讲稿（约600字）。涵盖架构概览、核心组件和优势。",
            "5min": "生成一个5分钟的详细演讲稿（约1500字）。包含开场、架构概览、组件细节、数据流和结论。"
        }

        prompt = f'''你是一位专业的技术演讲者，正在创建一份演讲稿。

{arch_desc}

{duration_prompts.get(duration, duration_prompts["2min"])}

要求：
1. 使用清晰、专业的中文表达
2. 用通俗易懂的方式解释技术概念
3. 突出架构的优势和设计决策
4. 段落之间过渡自然流畅
5. 以有力的结论收尾
6. 只返回演讲稿文本，不要返回JSON或其他格式

现在开始创作演讲稿：'''

        if self.mock_mode:
            logger.warning("Mock mode enabled for speech script generation (placeholder API key)")
            return self._build_mock_script(arch_desc, duration)

        async def _generate_with_provider():
            if self.provider == "gemini":
                response = await self.client.generate_content_async(
                    prompt,
                    generation_config={"temperature": 0.7}
                )
                return response.text.strip()

            if self.provider == "openai":
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    timeout=self.request_timeout,
                )
                return response.choices[0].message.content.strip()

            if self.provider == "siliconflow":
                response = await asyncio.to_thread(
                    self.client.chat.completions.create,
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000,
                    timeout=self.request_timeout,
                )
                return response.choices[0].message.content.strip()

            if self.provider == "claude":
                response = await asyncio.to_thread(
                    self.client.messages.create,
                    model=self.model_name,
                    max_tokens=2000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text.strip()

            # custom provider (OpenAI-compatible)
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=4000,
                timeout=self.request_timeout,
            )
            return response.choices[0].message.content.strip()

        try:
            script = await asyncio.wait_for(_generate_with_provider(), timeout=self.request_timeout)
            logger.info(f"Generated {duration} speech script ({len(script)} characters)")
            return script

        except asyncio.TimeoutError:
            logger.warning("Speech script generation timed out; returning mock script")
            return self._build_mock_script(arch_desc, duration)
        except Exception as e:
            logger.error(f"Speech script generation failed: {e}", exc_info=True)
            return self._build_mock_script(arch_desc, duration)

    async def generate_speech_script_stream(
        self,
        nodes: List,
        edges: List,
        duration: str = "2min"
    ):
        """Generate a presentation script with streaming support"""
        # Build architecture description
        arch_desc = f"Architecture with {len(nodes)} components and {len(edges)} connections:\n\n"

        arch_desc += "Components:\n"
        for node in nodes:
            arch_desc += f"- {node.data.label} (type: {node.type or 'default'})\n"

        arch_desc += "\nConnections:\n"
        for edge in edges:
            source_node = next((n for n in nodes if n.id == edge.source), None)
            target_node = next((n for n in nodes if n.id == edge.target), None)
            if source_node and target_node:
                label_text = f" ({edge.label})" if edge.label else ""
                arch_desc += f"- {source_node.data.label} → {target_node.data.label}{label_text}\n"

        # Duration-specific prompts (中文输出)
        duration_prompts = {
            "30s": "生成一个30秒的电梯演讲稿（约150字）。聚焦核心价值主张。",
            "2min": "生成一个2分钟的演讲稿（约600字）。涵盖架构概览、核心组件和优势。",
            "5min": "生成一个5分钟的详细演讲稿（约1500字）。包含开场、架构概览、组件细节、数据流和结论。"
        }

        prompt = f'''你是一位专业的技术演讲者，正在创建一份演讲稿。

{arch_desc}

{duration_prompts.get(duration, duration_prompts["2min"])}

要求：
1. 使用清晰、专业的中文表达
2. 用通俗易懂的方式解释技术概念
3. 突出架构的优势和设计决策
4. 段落之间过渡自然流畅
5. 以有力的结论收尾
6. 只返回演讲稿文本，不要返回JSON或其他格式

现在开始创作演讲稿：'''

        if self.mock_mode:
            logger.warning("Mock mode enabled for speech script generation (placeholder API key)")
            yield self._build_mock_script(arch_desc, duration)
            return

        try:
            # OpenAI-compatible providers support streaming
            if self.provider in ["openai", "siliconflow", "custom"]:
                logger.info(f"Starting streaming speech script generation with {self.provider}")

                # 直接创建stream并同步迭代（参考chat_generator的实现）
                stream = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=4000,
                    stream=True,
                )

                # 同步迭代stream chunks
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content

            elif self.provider == "claude":
                logger.info("Starting streaming speech script generation with Claude")
                # Claude uses async streaming API
                async with self.client.messages.stream(
                    model=self.model_name,
                    max_tokens=4000,
                    temperature=0.7,
                    messages=[{"role": "user", "content": prompt}]
                ) as stream:
                    async for text in stream.text_stream:
                        yield text

            else:
                # Fallback to non-streaming for other providers (like Gemini)
                logger.info(f"Provider {self.provider} doesn't support streaming, using non-streaming")
                full_script = await self.generate_speech_script(nodes, edges, duration)
                # Yield in chunks for simulated streaming
                chunk_size = 20
                for i in range(0, len(full_script), chunk_size):
                    yield full_script[i:i+chunk_size]

        except Exception as e:
            logger.error(f"Streaming speech script generation failed: {e}", exc_info=True)
            yield self._build_mock_script(arch_desc, duration)


# 工厂函数
def create_vision_service(
    provider: str,
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None
) -> AIVisionService:
    """创建 Vision Service 实例"""
    return AIVisionService(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model_name=model_name
    )
