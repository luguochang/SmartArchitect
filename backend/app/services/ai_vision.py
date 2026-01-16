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
            else "Qwen/Qwen3-VL-32B-Instruct"
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
                    timeout=120.0,  # 2 minutes timeout for streaming
                    max_retries=2   # Limit retries to prevent infinite loops
                )
                logger.info(f"SiliconFlow client initialized with base_url: {base_url}")

            elif self.provider == "custom":
                # 自定义 provider 使用 OpenAI SDK（支持 OpenAI 兼容的 API）
                if not OpenAI:
                    raise ImportError("openai not installed")
                if not self.custom_api_key:
                    raise ValueError("Custom API key not provided")
                if not self.custom_base_url:
                    raise ValueError("Custom base URL not provided")

                self.client = OpenAI(
                    api_key=self.custom_api_key,
                    base_url=self.custom_base_url,
                    timeout=120.0,  # 2 minutes timeout for streaming responses
                    max_retries=2   # Limit retries to fail fast on errors
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
                raise ValueError("SiliconFlow provider is text-only in current release. Use another provider for image analysis.")
            elif self.provider == "custom":
                result = await self._analyze_with_custom(image_data, prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")

            return result

        except Exception as e:
            logger.error(f"Analysis failed with {self.provider}: {e}")
            raise

    async def _analyze_with_gemini(self, image_data: bytes, prompt: str) -> ImageAnalysisResponse:
        """使用 Gemini 分析"""
        try:
            logger.info(f"[GEMINI] Starting analysis, image size: {len(image_data)} bytes")

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
                generation_config={"temperature": 0.2}
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

    async def _analyze_with_openai(self, image_data: bytes, prompt: str) -> ImageAnalysisResponse:
        """使用 OpenAI GPT-4 Vision 分析"""
        try:
            image_b64 = base64.b64encode(image_data).decode("utf-8")

            response = self.client.chat.completions.create(
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
                max_tokens=4096,
                temperature=0.2
            )

            result_json = self._extract_json_from_response(
                response.choices[0].message.content
            )

            return self._build_response(result_json)

        except Exception as e:
            logger.error(f"OpenAI analysis failed: {e}")
            raise

    async def _analyze_with_claude(self, image_data: bytes, prompt: str) -> ImageAnalysisResponse:
        """使用 Claude 3.5 Sonnet 分析"""
        try:
            image_b64 = base64.b64encode(image_data).decode("utf-8")

            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4096,
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

            result_json = self._extract_json_from_response(
                response.content[0].text
            )

            return self._build_response(result_json)

        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
            raise

    async def _analyze_with_custom(self, image_data: bytes, prompt: str) -> ImageAnalysisResponse:
        """使用自定义 provider 分析（OpenAI 兼容 API）"""
        try:
            image_b64 = base64.b64encode(image_data).decode("utf-8")

            # 使用自定义模型名称，默认为 gpt-4-vision-preview
            model = self.custom_model_name or "gpt-4-vision-preview"

            logger.info(f"[CUSTOM] Using model: {model}, base_url: {self.custom_base_url}")

            response = self.client.chat.completions.create(
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
                max_tokens=4096,
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

            # 某些中转站的格式：response.output[0].content[0].text
            if hasattr(response, 'output') and response.output:
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

            result_json = self._extract_json_from_response(content)
            return self._build_response(result_json)

        except Exception as e:
            logger.error(f"Custom provider analysis failed: {e}")
            raise

    def _extract_json_from_response(self, text: str) -> Dict[str, Any]:
        """Extract JSON from AI response with aggressive cleaning and multiple fallback strategies."""

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
                    data=NodeData(label=node["data"]["label"])
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

            return ImageAnalysisResponse(
                nodes=nodes,
                edges=edges,
                mermaid_code=result_json.get("mermaid_code", ""),
                success=True,
                ai_analysis=ai_analysis
            )

        except Exception as e:
            logger.error(f"Failed to build response: {e}")
            raise ValueError(f"Invalid response structure: {str(e)}")

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
                q = queue.Queue()

                def _openai_stream():
                    try:
                        stream = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[{"role": "user", "content": prompt}],
                            stream=True,
                            temperature=0.2,
                        )
                        for chunk in stream:
                            delta = chunk.choices[0].delta.content
                            if delta:
                                q.put(("data", delta))
                        q.put(("done", None))
                    except Exception as e:
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
                q = queue.Queue()

                def _claude_stream():
                    try:
                        with self.client.messages.stream(
                            model=self.model_name,
                            max_tokens=4096,
                            temperature=0.2,
                            messages=[{"role": "user", "content": prompt}],
                        ) as stream:
                            for text in stream.text_stream:
                                q.put(("data", text))
                        q.put(("done", None))
                    except Exception as e:
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

            elif self.provider == "siliconflow":
                # SiliconFlow (OpenAI-compatible) - use queue for real-time streaming
                q = queue.Queue()

                def _siliconflow_stream():
                    try:
                        stream = self.client.chat.completions.create(
                            model=self.model_name,
                            messages=[{"role": "user", "content": prompt}],
                            stream=True,
                            temperature=0.3,
                            top_p=0.7,
                            frequency_penalty=0.5,
                            max_tokens=4096,
                        )
                        for chunk in stream:
                            # Some providers emit empty heartbeat chunks - guard against missing choices
                            if not getattr(chunk, "choices", None):
                                continue
                            if not chunk.choices:
                                continue
                            delta = chunk.choices[0].delta.content if chunk.choices[0].delta else None
                            if not delta:
                                continue
                            q.put(("data", delta))
                        q.put(("done", None))
                    except Exception as e:
                        q.put(("error", e))

                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, _siliconflow_stream)

                while True:
                    msg_type, data = await loop.run_in_executor(None, q.get)
                    if msg_type == "error":
                        raise data
                    elif msg_type == "done":
                        break
                    else:
                        yield data

            elif self.provider == "custom":
                # Custom provider (OpenAI-compatible) - use queue for real-time streaming
                q = queue.Queue()

                def _custom_stream():
                    try:
                        stream = self.client.chat.completions.create(
                            model=self.custom_model_name or "gpt-3.5-turbo",
                            messages=[{"role": "user", "content": prompt}],
                            stream=True,
                            max_tokens=4096,
                            temperature=0.2,
                        )
                        for chunk in stream:
                            # Some providers emit empty heartbeat chunks - guard against missing choices
                            if not getattr(chunk, "choices", None):
                                continue
                            if not chunk.choices:
                                continue
                            delta = chunk.choices[0].delta.content if chunk.choices[0].delta else None
                            if not delta:
                                continue
                            q.put(("data", delta))
                        q.put(("done", None))
                    except Exception as e:
                        q.put(("error", e))

                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, _custom_stream)

                while True:
                    msg_type, data = await loop.run_in_executor(None, q.get)
                    if msg_type == "error":
                        raise data
                    elif msg_type == "done":
                        break
                    else:
                        yield data

            else:
                raise ValueError(f"Unsupported provider for streaming: {self.provider}")

        except Exception as e:
            logger.error(f"Streaming failed for {self.provider}: {e}", exc_info=True)
            raise

    # ========== Phase 3: Text-only Prompt Methods (for Prompter System) ==========

    async def _analyze_with_gemini_text(self, prompt: str) -> dict:
        """使用 Gemini 处理纯文本提示（无图片）"""
        try:
            logger.info("[GEMINI TEXT] Starting text-only analysis")

            response = await self.client.generate_content_async(
                prompt,
                generation_config={"temperature": 0.2}
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
                max_tokens=4096,
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
                max_tokens=4096,
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
            max_tokens = 4096 if is_excalidraw else 2000

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
                max_tokens=4096,
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

        # Duration-specific prompts
        duration_prompts = {
            "30s": "Generate a 30-second elevator pitch script (approximately 75 words). Focus on the key value proposition.",
            "2min": "Generate a 2-minute presentation script (approximately 300 words). Cover the architecture overview, key components, and benefits.",
            "5min": "Generate a 5-minute detailed presentation script (approximately 750 words). Include introduction, architecture overview, component details, data flow, and conclusion."
        }

        prompt = f'''You are a technical presenter creating a presentation script.

{arch_desc}

{duration_prompts.get(duration, duration_prompts["2min"])}

Requirements:
1. Use clear, professional language
2. Explain technical concepts in an accessible way
3. Highlight the architecture's strengths and design decisions
4. Include smooth transitions between topics
5. End with a strong conclusion
6. Return ONLY the script text, no JSON or additional formatting

Create the script now:'''

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
            payload = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7
            }

            response = await asyncio.to_thread(self.client.post, "/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                return data["choices"][0]["message"]["content"].strip()
            if "output" in data:
                return data["output"].strip()
            raise ValueError("Unexpected custom provider response format")

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
