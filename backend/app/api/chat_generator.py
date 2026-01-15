from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

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
            yield "data: [CALL] contacting provider...\n\n"

            # Prefer true stream for OpenAI-compatible providers
            if selected_provider in ["siliconflow", "openai", "custom"]:
                vision_service = create_vision_service(
                    provider=selected_provider,
                    api_key=request.api_key,
                    base_url=request.base_url,
                    model_name=request.model_name
                )

                # Stream tokens
                accumulated = ""
                stream = vision_service.client.chat.completions.create(
                    model=vision_service.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=4096,
                    temperature=0.2,
                    stream=True,
                )
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

                    # Don't replace AI result with mock - return what AI generated
                    payload = ChatGenerationResponse(
                        nodes=nodes,
                        edges=edges,
                        mermaid_code=mermaid_code,
                        success=True,
                        message=f"Generated via {selected_provider} (stream)",
                    ).model_dump()
                    yield f"data: [RESULT] nodes={len(nodes)}, edges={len(edges)}\n\n"
                    yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
                    yield "data: [END] done\n\n"
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
            yield f"data: [RESULT] nodes={len(result.nodes)}, edges={len(result.edges)}\n\n"
            payload = result.model_dump()
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
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
