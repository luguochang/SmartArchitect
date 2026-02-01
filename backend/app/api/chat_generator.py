from fastapi import APIRouter, HTTPException
from typing import Optional
import logging
import asyncio

from app.models.schemas import (
    FlowTemplateList,
    ChatGenerationRequest,
    ChatGenerationResponse
)
from app.services.chat_generator import create_chat_generator_service
from fastapi.responses import StreamingResponse
import json
from app.services.ai_vision import create_vision_service

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


@router.post("/chat-generator/generate-stream")
async def generate_flowchart_stream(request: ChatGenerationRequest):
    """Streaming version of flowchart generation (SSE-like text/event-stream)."""

    async def event_stream():
        try:
            logger.info(f"[STREAM] Starting stream generation for: {request.user_input[:50]}")
            logger.info(f"[STREAM] Provider: {request.provider}, Model: {request.model_name}")

            service = create_chat_generator_service()
            selected_provider = request.provider or "gemini"

            # Determine effective diagram type
            effective_diagram_type = request.diagram_type or "flow"
            if request.template_id:
                tpl = service.get_template(request.template_id)
                if tpl and tpl.category == "architecture":
                    effective_diagram_type = "architecture"

            logger.info(f"Stream generation: diagram_type={effective_diagram_type}, provider={selected_provider}")

            prompt_request = request.model_copy(update={"diagram_type": effective_diagram_type})
            prompt = service._build_generation_prompt(prompt_request)

            yield "data: [START] building prompt\n\n"
            logger.info("[STREAM] Sent START event")
            yield "data: [CALL] contacting provider...\n\n"
            logger.info("[STREAM] Sent CALL event")

            # Prefer true stream for OpenAI-compatible providers
            if selected_provider in ["siliconflow", "openai", "custom"]:
                try:
                    vision_service = create_vision_service(
                        provider=selected_provider,
                        api_key=request.api_key,
                        base_url=request.base_url,
                        model_name=request.model_name
                    )

                    # Stream tokens
                    accumulated = ""
                    logger.info(f"[STREAM] Creating streaming request to {selected_provider} with model {vision_service.model_name}")

                    # 检测是否需要使用 raw HTTP（ikuncode.cc 会阻拦 SDK）
                    use_raw_http = (
                        selected_provider == "custom" and
                        vision_service.custom_base_url and
                        "ikuncode.cc" in vision_service.custom_base_url.lower()
                    )

                    if use_raw_http:
                        # ikuncode.cc：使用 raw HTTP streaming
                        logger.info("[STREAM] Detected ikuncode.cc, using raw HTTP streaming")
                        import httpx

                        # 清理 base_url
                        clean_base_url = vision_service.custom_base_url.rstrip('/')
                        if clean_base_url.endswith('/v1'):
                            clean_base_url = clean_base_url[:-3]

                        headers = {
                            "x-api-key": vision_service.custom_api_key,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        }

                        data = {
                            "model": vision_service.model_name,
                            "max_tokens": 4096,
                            "messages": [{"role": "user", "content": prompt}],
                            "stream": True
                        }

                        logger.info(f"[STREAM] Sending request to: {clean_base_url}/v1/messages")

                        # 直接在这里处理流式响应
                        async with httpx.AsyncClient(timeout=120.0) as http_client:
                            async with http_client.stream("POST", f"{clean_base_url}/v1/messages", headers=headers, json=data) as response:
                                if response.status_code != 200:
                                    error_text = await response.aread()
                                    logger.error(f"[STREAM] API error: {response.status_code} - {error_text}")
                                    yield f"data: [ERROR] API request failed: {response.status_code}\n\n"
                                    return

                                logger.info("[STREAM] Starting raw HTTP token streaming...")
                                current_event = None
                                buffer = ""

                                async for chunk in response.aiter_bytes():
                                    buffer += chunk.decode('utf-8')

                                    while '\n' in buffer:
                                        line, buffer = buffer.split('\n', 1)
                                        line = line.strip()

                                        if not line:
                                            continue

                                        if line.startswith("event: "):
                                            current_event = line[7:]
                                        elif line.startswith("data: "):
                                            data_str = line[6:]
                                            try:
                                                data_json = json.loads(data_str)
                                                if current_event == "content_block_delta":
                                                    delta = data_json.get("delta", {})
                                                    if delta.get("type") == "text_delta":
                                                        text = delta.get("text", "")
                                                        if text:
                                                            accumulated += text
                                                            yield f"data: [TOKEN] {text}\n\n"
                                            except json.JSONDecodeError:
                                                continue

                    else:
                        # 检测是否是 Claude 模型（linkflow.run 等）
                        is_claude_model = selected_provider == "custom" and vision_service.model_name and "claude" in vision_service.model_name.lower()

                        if is_claude_model:
                            # 使用 Anthropic streaming API
                            logger.info("[STREAM] Using Anthropic streaming API")
                            stream = vision_service.client.messages.stream(
                                model=vision_service.model_name,
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=4096,
                                temperature=0.2,
                            )
                        else:
                            # 使用 OpenAI streaming API
                            stream = vision_service.client.chat.completions.create(
                                model=vision_service.model_name,
                                messages=[{"role": "user", "content": prompt}],
                                max_tokens=4096,
                                temperature=0.2,
                                stream=True,
                            )
                except Exception as init_error:
                    logger.error(f"[STREAM] Failed to initialize streaming: {init_error}", exc_info=True)
                    yield f"data: [ERROR] Failed to initialize AI streaming: {str(init_error)}\n\n"
                    return

                # 只有非 raw HTTP 的情况才需要这里处理流式
                if not use_raw_http:
                    try:
                        if is_claude_model:
                            # Anthropic streaming API使用context manager
                            with stream as s:
                                for text in s.text_stream:
                                    accumulated += text
                                    yield f"data: [TOKEN] {text}\n\n"
                        else:
                            # OpenAI streaming API
                            for chunk in stream:
                                # Some providers may emit empty heartbeats; guard against missing choices
                                if not getattr(chunk, "choices", None):
                                    continue
                                delta = chunk.choices[0].delta.content if chunk.choices[0].delta else None
                                if not delta:
                                    continue
                                text = "".join(delta)
                                accumulated += text
                                yield f"data: [TOKEN] {text}\n\n"
                    except Exception as stream_error:
                        logger.error(f"[STREAM] Error during streaming: {stream_error}", exc_info=True)
                        yield f"data: [ERROR] Streaming interrupted: {str(stream_error)}\n\n"
                        return

                # Parse final JSON and normalize; if parse fails, fall back to non-stream path
                try:
                    if not accumulated.strip():
                        raise ValueError("Empty stream output")

                    logger.info(f"[STREAM] Accumulated response length: {len(accumulated)}")
                    logger.info(f"[STREAM] First 500 chars: {accumulated[:500]}")
                    ai_data = service._safe_json(accumulated)
                    logger.info(f"[STREAM] Parsed AI data keys: {list(ai_data.keys())}")

                    # Use correct normalization based on diagram type
                    if effective_diagram_type == "architecture":
                        nodes, edges, mermaid_code = service._normalize_architecture_graph(ai_data)
                        edges = []  # Architecture diagrams don't show edges
                    else:
                        nodes, edges, mermaid_code = service._normalize_ai_graph(ai_data)

                    logger.info(f"[STREAM] After normalization: {len(nodes)} nodes, {len(edges)} edges")

                    # 🎬 流式发送节点和边，实现真正的流式画图效果
                    # 1. 先发送完整数据用于前端布局计算
                    layout_data = {
                        "nodes": [n.model_dump() if hasattr(n, 'model_dump') else n for n in nodes],
                        "edges": [e.model_dump() if hasattr(e, 'model_dump') else e for e in edges],
                        "diagram_type": effective_diagram_type,
                        "mermaid_code": mermaid_code
                    }
                    yield f"data: [LAYOUT_DATA] {json.dumps(layout_data, ensure_ascii=False)}\n\n"
                    logger.info(f"[STREAM] Sent LAYOUT_DATA with {len(nodes)} nodes")

                    # 2. 短暂等待，让前端完成布局计算
                    await asyncio.sleep(0.15)

                    # 3. 逐个发送节点显示指令
                    yield f"data: [RESULT] nodes={len(nodes)}, edges={len(edges)}\n\n"
                    for i, node in enumerate(nodes):
                        node_data = node.model_dump() if hasattr(node, 'model_dump') else node
                        node_id = node_data.get('id')
                        yield f"data: [NODE_SHOW] {node_id}\n\n"
                        logger.info(f"[STREAM] Sent NODE_SHOW {i+1}/{len(nodes)}: {node_id}")
                        # 控制显示速度：200ms/节点
                        if i < len(nodes) - 1:
                            await asyncio.sleep(0.2)

                    # 4. 短暂延迟后开始显示边
                    await asyncio.sleep(0.3)

                    # 5. 逐个发送边显示指令
                    for i, edge in enumerate(edges):
                        edge_data = edge.model_dump() if hasattr(edge, 'model_dump') else edge
                        edge_id = edge_data.get('id')
                        yield f"data: [EDGE_SHOW] {edge_id}\n\n"
                        logger.info(f"[STREAM] Sent EDGE_SHOW {i+1}/{len(edges)}: {edge_id}")
                        # 控制显示速度：100ms/边
                        if i < len(edges) - 1:
                            await asyncio.sleep(0.1)

                    yield "data: [END] done\n\n"
                    logger.info("[STREAM] Completed progressive rendering")
                    return
                except Exception as parse_err:
                    logger.warning(f"[STREAM] JSON parse failed; falling back to non-stream: {parse_err}")
                    logger.exception(parse_err)
                    # explicitly fall through to non-stream path

            # Fallback: call existing generator (non-stream) but send staged events
            logger.info(f"[STREAM] Falling back to non-stream generate_flowchart()")
            result = await service.generate_flowchart(
                request=prompt_request,
                provider=selected_provider,
                api_key=request.api_key,
                base_url=request.base_url,
                model_name=request.model_name
            )

            # 🎬 同样使用流式发送
            # 1. 先发送布局数据
            layout_data = {
                "nodes": [n.model_dump() if hasattr(n, 'model_dump') else n for n in result.nodes],
                "edges": [e.model_dump() if hasattr(e, 'model_dump') else e for e in result.edges],
                "diagram_type": effective_diagram_type,
                "mermaid_code": result.mermaid_code
            }
            yield f"data: [LAYOUT_DATA] {json.dumps(layout_data, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.15)

            # 2. 逐个发送节点
            yield f"data: [RESULT] nodes={len(result.nodes)}, edges={len(result.edges)}\n\n"
            for i, node in enumerate(result.nodes):
                node_data = node.model_dump() if hasattr(node, 'model_dump') else node
                node_id = node_data.get('id')
                yield f"data: [NODE_SHOW] {node_id}\n\n"
                if i < len(result.nodes) - 1:
                    await asyncio.sleep(0.2)

            # 3. 延迟后发送边
            await asyncio.sleep(0.3)
            for i, edge in enumerate(result.edges):
                edge_data = edge.model_dump() if hasattr(edge, 'model_dump') else edge
                edge_id = edge_data.get('id')
                yield f"data: [EDGE_SHOW] {edge_id}\n\n"
                if i < len(result.edges) - 1:
                    await asyncio.sleep(0.1)

            yield "data: [END] done\n\n"
        except Exception as e:
            logger.error(f"Stream generation failed: {e}", exc_info=True)
            yield f"data: [ERROR] {str(e)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Content-Encoding": "none",
            "Transfer-Encoding": "chunked",
        },
    )
