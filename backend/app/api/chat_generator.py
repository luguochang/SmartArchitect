import asyncio
from fastapi import APIRouter, HTTPException
from typing import Optional, Any, Dict, List, Set
import logging
import time

from app.models.schemas import (
    FlowTemplateList,
    ChatGenerationRequest,
    ChatGenerationResponse,
    CanvasSaveRequest,
    CanvasSaveResponse,
    CanvasSessionResponse,
    CanvasSessionData,
    CanvasSessionDeleteResponse,
    Node,
    Edge
)
from app.services.chat_generator import create_chat_generator_service, ARCHITECTURE_TEMPLATES
from app.services.session_manager import get_session_manager
from app.services.model_presets import get_model_presets_service
from fastapi.responses import StreamingResponse
import json
from app.services.ai_vision import create_vision_service

router = APIRouter()
logger = logging.getLogger(__name__)


_ALLOWED_NODE_TYPES = {
    "default": "default",
    "database": "database",
    "api": "api",
    "service": "service",
    "gateway": "gateway",
    "cache": "cache",
    "queue": "queue",
    "storage": "storage",
    "client": "client",
    "frame": "frame",
    "layerframe": "layerFrame",
}


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _extract_array_objects(payload: str, array_key: str) -> List[Dict[str, Any]]:
    """
    Incrementally extract complete JSON objects from an array key in a partial JSON buffer.
    Example: array_key="nodes" extracts objects from `"nodes": [ {...}, {...} ]`.
    """
    key_token = f"\"{array_key}\""
    key_pos = payload.find(key_token)
    if key_pos < 0:
        return []

    colon_pos = payload.find(":", key_pos + len(key_token))
    if colon_pos < 0:
        return []

    array_start = payload.find("[", colon_pos)
    if array_start < 0:
        return []

    results: List[Dict[str, Any]] = []
    in_string = False
    escaped = False
    array_depth = 0
    object_depth = 0
    object_start = -1

    for idx in range(array_start, len(payload)):
        char = payload[idx]

        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "\"":
                in_string = False
            continue

        if char == "\"":
            in_string = True
            continue

        if char == "[":
            array_depth += 1
            continue

        if char == "]":
            array_depth -= 1
            if array_depth <= 0 and object_depth == 0:
                break
            continue

        if char == "{":
            if array_depth >= 1:
                if object_depth == 0:
                    object_start = idx
                object_depth += 1
            continue

        if char == "}" and object_depth > 0:
            object_depth -= 1
            if object_depth == 0 and object_start != -1:
                snippet = payload[object_start:idx + 1]
                try:
                    parsed = json.loads(snippet)
                    if isinstance(parsed, dict):
                        results.append(parsed)
                except json.JSONDecodeError:
                    pass
                object_start = -1

    return results


def _node_stream_identity(node_payload: Dict[str, Any]) -> str:
    node_id = str(node_payload.get("id") or "").strip()
    if node_id:
        return f"id:{node_id}"

    data = node_payload.get("data")
    data = data if isinstance(data, dict) else {}
    label = str(data.get("label") or "").strip()
    position = node_payload.get("position")
    position = position if isinstance(position, dict) else {}
    return f"label:{label}|x:{position.get('x')}|y:{position.get('y')}"


def _edge_stream_identity(edge_payload: Dict[str, Any]) -> str:
    edge_id = str(edge_payload.get("id") or "").strip()
    if edge_id:
        return f"id:{edge_id}"
    source = str(edge_payload.get("source") or "").strip()
    target = str(edge_payload.get("target") or "").strip()
    label = str(edge_payload.get("label") or "").strip()
    return f"{source}->{target}|{label}"


def _normalize_partial_node(node_payload: Dict[str, Any], fallback_index: int) -> Optional[Dict[str, Any]]:
    if not isinstance(node_payload, dict):
        return None

    node_id = str(node_payload.get("id") or "").strip() or f"partial-node-{fallback_index + 1}"
    raw_node_type = str(node_payload.get("type") or "").strip().lower()
    if raw_node_type in _ALLOWED_NODE_TYPES:
        node_type = _ALLOWED_NODE_TYPES[raw_node_type]
    elif raw_node_type in {"gateway", "decision"}:
        node_type = "gateway"
    else:
        node_type = "default"

    raw_position = node_payload.get("position")
    raw_position = raw_position if isinstance(raw_position, dict) else {}
    fallback_x = 120 + (fallback_index % 4) * 260
    fallback_y = 120 + (fallback_index // 4) * 180
    x = float(raw_position["x"]) if _is_finite_number(raw_position.get("x")) else float(fallback_x)
    y = float(raw_position["y"]) if _is_finite_number(raw_position.get("y")) else float(fallback_y)

    raw_data = node_payload.get("data")
    raw_data = dict(raw_data) if isinstance(raw_data, dict) else {}
    label = str(raw_data.get("label") or "").strip() or node_id
    raw_data["label"] = label
    if "shape" not in raw_data:
        if raw_node_type in {"start", "start-event"}:
            raw_data["shape"] = "start-event"
        elif raw_node_type in {"end", "end-event"}:
            raw_data["shape"] = "end-event"
        elif raw_node_type in {"decision", "gateway"}:
            raw_data["shape"] = "diamond"
        elif raw_node_type in {"task", "process", "subprocess"}:
            raw_data["shape"] = "task"

    return {
        "id": node_id,
        "type": node_type,
        "position": {"x": x, "y": y},
        "data": raw_data,
    }


def _classify_upstream_error(error: Exception) -> tuple[int, str]:
    if isinstance(error, HTTPException):
        if error.status_code == 429:
            return 429, "usage_limit_reached"
        if error.status_code == 401:
            return 401, "authentication_failed"
        if error.status_code in {502, 503}:
            return 503, "upstream_unavailable"
        if error.status_code == 504:
            return 504, "upstream_timeout"
        if error.status_code >= 500:
            return error.status_code, "upstream_error"
        return error.status_code, "request_error"

    text = str(error).lower()
    if "usage_limit" in text or "rate limit" in text or "quota" in text or "429" in text:
        return 429, "usage_limit_reached"
    if "unauthorized" in text or "invalid api key" in text or "authentication" in text or "401" in text:
        return 401, "authentication_failed"
    if "timeout" in text or "timed out" in text:
        return 504, "upstream_timeout"
    if "bad gateway" in text or "502" in text or "503" in text or "service unavailable" in text:
        return 503, "upstream_unavailable"
    if "empty stream output" in text:
        return 502, "empty_stream_output"
    if "json" in text and ("parse" in text or "decode" in text or "invalid" in text):
        return 502, "invalid_stream_payload"
    return 500, "upstream_error"


def _build_stream_config_candidates(
    provider: str,
    api_key: Optional[str],
    base_url: Optional[str],
    model_name: Optional[str],
) -> List[Dict[str, Any]]:
    presets_service = get_model_presets_service()
    primary = presets_service.get_active_config(
        provider=provider,
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
    )
    if not primary:
        return []

    candidates = [primary]
    failover_fn = getattr(presets_service, "get_failover_configs", None)
    if callable(failover_fn):
        try:
            candidates.extend(failover_fn(primary_config=primary, max_candidates=3))
        except Exception as error:
            logger.warning("[STREAM] Failed to load failover configs: %s", error)
    return candidates


def _normalize_partial_edge(edge_payload: Dict[str, Any], fallback_index: int) -> Optional[Dict[str, Any]]:
    if not isinstance(edge_payload, dict):
        return None

    source = str(edge_payload.get("source") or "").strip()
    target = str(edge_payload.get("target") or "").strip()
    if not source or not target:
        return None

    edge_id = str(edge_payload.get("id") or "").strip() or f"partial-edge-{fallback_index + 1}"
    normalized: Dict[str, Any] = {
        "id": edge_id,
        "source": source,
        "target": target,
    }

    label = edge_payload.get("label")
    if isinstance(label, (str, int, float)):
        label_text = str(label).strip()
        if label_text:
            normalized["label"] = label_text

    return normalized


@router.get("/chat-generator/templates", response_model=FlowTemplateList)
async def get_flow_templates():
    """鑾峰彇鎵€鏈夋祦绋嬪浘绀轰緥妯℃澘

    Returns:
        FlowTemplateList: 鍖呭惈棰勮妯℃澘锛圤OM鎺掓煡銆佽鍗曟祦绋嬬瓑锛?
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
    """鏍规嵁鐢ㄦ埛鎻忚堪鐢熸垚娴佺▼鍥?

    Args:
        request: 鍖呭惈鐢ㄦ埛杈撳叆銆佹ā鏉?ID銆乸rovider銆丄PI key 绛夐厤缃?

    Returns:
        ChatGenerationResponse: 鐢熸垚鐨勬祦绋嬪浘鑺傜偣銆佽竟銆丮ermaid 浠ｇ爜
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

            logger.info(
                "[STREAM] Generation mode: diagram_type=%s, provider=%s",
                effective_diagram_type,
                selected_provider,
            )

            prompt_request = request.model_copy(update={"diagram_type": effective_diagram_type})
            prompt = service._build_generation_prompt(prompt_request)

            config_candidates = _build_stream_config_candidates(
                provider=selected_provider,
                api_key=request.api_key,
                base_url=request.base_url,
                model_name=request.model_name,
            )
            if not config_candidates:
                yield "data: [ERROR] No AI configuration found. Please configure model settings first.\n\n"
                return

            seen_partial_node_keys: Set[str] = set()
            seen_partial_edge_keys: Set[str] = set()
            partial_nodes_sent = 0
            partial_edges_sent = 0
            attempt_errors: List[Dict[str, Any]] = []
            parse_interval_chars = 96
            heartbeat_seconds = 6.0
            first_token_timeout_seconds = 18.0

            for attempt_index, config in enumerate(config_candidates, start=1):
                attempt_provider = config.get("provider") or selected_provider
                attempt_model = config.get("model_name") or ""
                selected_provider = attempt_provider

                yield f"data: [START] attempt={attempt_index}/{len(config_candidates)} building prompt\n\n"
                yield (
                    "data: [CALL] contacting provider "
                    f"{attempt_provider}/{attempt_model or '-'}...\n\n"
                )

                try:
                    vision_service = create_vision_service(
                        provider=attempt_provider,
                        api_key=config.get("api_key"),
                        base_url=config.get("base_url"),
                        model_name=config.get("model_name"),
                    )
                except Exception as init_error:
                    status_code, error_code = _classify_upstream_error(init_error)
                    attempt_errors.append(
                        {
                            "provider": attempt_provider,
                            "model_name": attempt_model,
                            "status_code": status_code,
                            "error_code": error_code,
                            "detail": str(init_error),
                        }
                    )
                    logger.error("[STREAM] Failed to initialize streaming client: %s", init_error, exc_info=True)
                    if attempt_index < len(config_candidates):
                        yield (
                            "data: [WARN] "
                            f"attempt={attempt_index} init_failed ({status_code}:{error_code}), failover to next configuration\n\n"
                        )
                        continue
                    break

                accumulated = ""
                chars_since_parse = 0
                last_heartbeat = time.monotonic()
                token_batch = ""
                token_batch_chars = 160
                token_batch_interval_seconds = 0.2
                last_token_emit = time.monotonic()

                def flush_token_batch(force: bool = False) -> List[str]:
                    nonlocal token_batch
                    nonlocal last_token_emit
                    events: List[str] = []
                    now = time.monotonic()
                    if not token_batch:
                        return events
                    if force or len(token_batch) >= token_batch_chars or (now - last_token_emit) >= token_batch_interval_seconds:
                        events.append(f"data: [TOKEN] {token_batch}\n\n")
                        token_batch = ""
                        last_token_emit = now
                    return events

                def build_events_from_token(text: str) -> List[str]:
                    nonlocal accumulated
                    nonlocal chars_since_parse
                    nonlocal last_heartbeat
                    nonlocal partial_nodes_sent
                    nonlocal partial_edges_sent
                    nonlocal token_batch

                    events: List[str] = []
                    if not text:
                        return events

                    accumulated += text
                    token_batch += text
                    if "\n" in text:
                        events.extend(flush_token_batch(force=True))
                    else:
                        events.extend(flush_token_batch(force=False))
                    chars_since_parse += len(text)

                    should_parse_partials = ("}" in text) or (chars_since_parse >= parse_interval_chars)
                    if should_parse_partials:
                        chars_since_parse = 0

                        for raw_node in _extract_array_objects(accumulated, "nodes"):
                            identity = _node_stream_identity(raw_node)
                            if identity in seen_partial_node_keys:
                                continue

                            partial_node = _normalize_partial_node(raw_node, partial_nodes_sent)
                            if not partial_node:
                                continue

                            seen_partial_node_keys.add(identity)
                            partial_nodes_sent += 1
                            events.append(
                                f"data: [PARTIAL_NODE] {json.dumps(partial_node, ensure_ascii=False)}\n\n"
                            )

                        for raw_edge in _extract_array_objects(accumulated, "edges"):
                            identity = _edge_stream_identity(raw_edge)
                            if identity in seen_partial_edge_keys:
                                continue

                            partial_edge = _normalize_partial_edge(raw_edge, partial_edges_sent)
                            if not partial_edge:
                                continue

                            seen_partial_edge_keys.add(identity)
                            partial_edges_sent += 1
                            events.append(
                                f"data: [PARTIAL_EDGE] {json.dumps(partial_edge, ensure_ascii=False)}\n\n"
                            )

                    now = time.monotonic()
                    if now - last_heartbeat >= heartbeat_seconds:
                        events.append(
                            "data: [PROGRESS] "
                            f"chars={len(accumulated)} partial_nodes={partial_nodes_sent} partial_edges={partial_edges_sent}\n\n"
                        )
                        last_heartbeat = now

                    return events

                stream_failed = False
                parse_failed = False

                try:
                    logger.info(
                        "[STREAM] Starting provider token stream: provider=%s model=%s",
                        vision_service.provider,
                        vision_service.model_name,
                    )
                    stream_iterator = vision_service.generate_with_stream(prompt).__aiter__()
                    try:
                        first_token = await asyncio.wait_for(
                            stream_iterator.__anext__(),
                            timeout=first_token_timeout_seconds,
                        )
                    except StopAsyncIteration as empty_stream:
                        raise ValueError("Empty stream output") from empty_stream

                    for event in build_events_from_token(first_token):
                        yield event

                    async for token in stream_iterator:
                        for event in build_events_from_token(token):
                            yield event
                    for event in flush_token_batch(force=True):
                        yield event
                except Exception as stream_error:
                    stream_failed = True
                    for event in flush_token_batch(force=True):
                        yield event
                    status_code, error_code = _classify_upstream_error(stream_error)
                    attempt_errors.append(
                        {
                            "provider": attempt_provider,
                            "model_name": attempt_model,
                            "status_code": status_code,
                            "error_code": error_code,
                            "detail": str(stream_error),
                        }
                    )
                    logger.error("[STREAM] Streaming interrupted: %s", stream_error, exc_info=True)
                    if attempt_index < len(config_candidates):
                        yield (
                            "data: [WARN] "
                            f"attempt={attempt_index} stream_failed ({status_code}:{error_code}), failover to next configuration\n\n"
                        )
                        continue

                if not stream_failed:
                    try:
                        if not accumulated.strip():
                            raise ValueError("Empty stream output")

                        ai_data = service._safe_json(accumulated)
                        if effective_diagram_type == "architecture":
                            arch_type = request.architecture_type or "layered"
                            nodes, edges, mermaid_code = service._normalize_architecture_graph(ai_data, arch_type)
                            template = ARCHITECTURE_TEMPLATES.get(arch_type, ARCHITECTURE_TEMPLATES["layered"])
                            if not template.get("show_edges", False):
                                edges = []
                        else:
                            nodes, edges, mermaid_code = service._normalize_ai_graph(ai_data)

                        logger.info(
                            "[STREAM] Final normalization complete: %s nodes, %s edges",
                            len(nodes),
                            len(edges),
                        )

                        layout_data = {
                            "nodes": [n.model_dump() if hasattr(n, "model_dump") else n for n in nodes],
                            "edges": [e.model_dump() if hasattr(e, "model_dump") else e for e in edges],
                            "diagram_type": effective_diagram_type,
                            "mermaid_code": mermaid_code,
                        }
                        yield f"data: [LAYOUT_DATA] {json.dumps(layout_data, ensure_ascii=False)}\n\n"
                        yield f"data: [RESULT] nodes={len(nodes)}, edges={len(edges)}\n\n"

                        # Compatibility fallback for old clients.
                        if partial_nodes_sent == 0 and partial_edges_sent == 0:
                            for node in nodes:
                                node_data = node.model_dump() if hasattr(node, "model_dump") else node
                                node_id = node_data.get("id")
                                if node_id:
                                    yield f"data: [NODE_SHOW] {node_id}\n\n"
                            for edge in edges:
                                edge_data = edge.model_dump() if hasattr(edge, "model_dump") else edge
                                edge_id = edge_data.get("id")
                                if edge_id:
                                    yield f"data: [EDGE_SHOW] {edge_id}\n\n"

                        yield "data: [END] done\n\n"
                        logger.info(
                            "[STREAM] Completed. partial_nodes=%s partial_edges=%s provider=%s model=%s",
                            partial_nodes_sent,
                            partial_edges_sent,
                            attempt_provider,
                            attempt_model,
                        )
                        return
                    except Exception as parse_error:
                        parse_failed = True
                        status_code, error_code = _classify_upstream_error(parse_error)
                        attempt_errors.append(
                            {
                                "provider": attempt_provider,
                                "model_name": attempt_model,
                                "status_code": status_code,
                                "error_code": error_code,
                                "detail": str(parse_error),
                            }
                        )
                        logger.warning("[STREAM] Parse failed after stream: %s", parse_error, exc_info=True)

                if attempt_index < len(config_candidates):
                    reason = "parse_failed" if parse_failed else "stream_failed"
                    yield (
                        "data: [WARN] "
                        f"attempt={attempt_index} {reason}, failover to next configuration\n\n"
                    )
                    continue

                # Last attempt fallback: use non-stream path to avoid blank result.
                logger.info("[STREAM] Last attempt reached; fallback to non-stream generate_flowchart()")
                try:
                    result = await service.generate_flowchart(
                        request=prompt_request,
                        provider=attempt_provider,
                        api_key=config.get("api_key"),
                        base_url=config.get("base_url"),
                        model_name=config.get("model_name"),
                    )

                    layout_data = {
                        "nodes": [n.model_dump() if hasattr(n, "model_dump") else n for n in result.nodes],
                        "edges": [e.model_dump() if hasattr(e, "model_dump") else e for e in result.edges],
                        "diagram_type": effective_diagram_type,
                        "mermaid_code": result.mermaid_code,
                    }
                    yield f"data: [LAYOUT_DATA] {json.dumps(layout_data, ensure_ascii=False)}\n\n"
                    yield f"data: [RESULT] nodes={len(result.nodes)}, edges={len(result.edges)}\n\n"

                    if partial_nodes_sent == 0 and partial_edges_sent == 0:
                        for node in result.nodes:
                            node_data = node.model_dump() if hasattr(node, "model_dump") else node
                            node_id = node_data.get("id")
                            if node_id:
                                yield f"data: [NODE_SHOW] {node_id}\n\n"
                        for edge in result.edges:
                            edge_data = edge.model_dump() if hasattr(edge, "model_dump") else edge
                            edge_id = edge_data.get("id")
                            if edge_id:
                                yield f"data: [EDGE_SHOW] {edge_id}\n\n"

                    yield "data: [END] done\n\n"
                    return
                except Exception as fallback_error:
                    status_code, error_code = _classify_upstream_error(fallback_error)
                    attempt_errors.append(
                        {
                            "provider": attempt_provider,
                            "model_name": attempt_model,
                            "status_code": status_code,
                            "error_code": f"fallback_{error_code}",
                            "detail": str(fallback_error),
                        }
                    )
                    logger.error("[STREAM] Non-stream fallback failed: %s", fallback_error, exc_info=True)

            if attempt_errors:
                summary = "; ".join(
                    f"{err['provider']}/{err['model_name']} -> {err['status_code']}:{err['error_code']}"
                    for err in attempt_errors
                )[:800]
                yield f"data: [ERROR] Stream generation failed after {len(attempt_errors)} errors. {summary}\n\n"
                return

            yield "data: [ERROR] Stream generation failed with unknown error.\n\n"
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

# ============================================================
# Canvas Session Management (澧為噺鐢熸垚浼氳瘽绠＄悊)
# ============================================================

@router.post("/chat-generator/session/save", response_model=CanvasSaveResponse)
async def save_canvas_session(request: CanvasSaveRequest):
    """
    淇濆瓨褰撳墠鐢诲竷鍒颁細璇?

    Args:
        request: 鍖呭惈 session_id (鍙€?, nodes, edges

    Returns:
        CanvasSaveResponse: 鍖呭惈 session_id, node_count, edge_count
    """
    try:
        logger.info(
            f"Saving canvas session: session_id={request.session_id}, "
            f"nodes={len(request.nodes)}, edges={len(request.edges)}"
        )

        session_manager = get_session_manager()

        # 鍒涘缓鎴栨洿鏂颁細璇?
        session_id = session_manager.create_or_update_session(
            session_id=request.session_id,
            nodes=request.nodes,
            edges=request.edges
        )

        logger.info(f"Canvas session saved: {session_id}")

        return CanvasSaveResponse(
            success=True,
            session_id=session_id,
            message="Canvas session saved successfully",
            node_count=len(request.nodes),
            edge_count=len(request.edges)
        )

    except ValueError as ve:
        # 浼氳瘽杩囧ぇ鎴栧叾浠栭獙璇侀敊璇?
        logger.error(f"Failed to save session: {ve}")
        raise HTTPException(status_code=413, detail=str(ve))

    except Exception as e:
        logger.error(f"Failed to save canvas session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save session: {str(e)}"
        )


@router.get("/chat-generator/session/{session_id}", response_model=CanvasSessionResponse)
async def get_canvas_session(session_id: str):
    """
    鑾峰彇浼氳瘽鏁版嵁

    Args:
        session_id: 浼氳瘽 ID

    Returns:
        CanvasSessionResponse: 鍖呭惈 nodes, edges, node_count, edge_count 绛?
    """
    try:
        logger.info(f"Retrieving canvas session: {session_id}")

        session_manager = get_session_manager()
        session_data = session_manager.get_session(session_id)

        if not session_data:
            logger.warning(f"Session not found or expired: {session_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Session not found or expired: {session_id}"
            )

        # 杞崲涓哄搷搴旀牸寮?
        nodes = [Node(**n) for n in session_data["nodes"]]
        edges = [Edge(**e) for e in session_data["edges"]]

        session_response = CanvasSessionData(
            nodes=nodes,
            edges=edges,
            node_count=session_data["node_count"],
            edge_count=session_data["edge_count"],
            timestamp=session_data["timestamp"].isoformat(),
            created_at=session_data["created_at"].isoformat()
        )

        logger.info(
            f"Session retrieved: {session_id} "
            f"({session_data['node_count']} nodes, {session_data['edge_count']} edges)"
        )

        return CanvasSessionResponse(
            success=True,
            session=session_response
        )

    except HTTPException:
        raise

    except Exception as e:
        logger.error(f"Failed to get canvas session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session: {str(e)}"
        )


@router.delete("/chat-generator/session/{session_id}", response_model=CanvasSessionDeleteResponse)
async def delete_canvas_session(session_id: str):
    """
    鍒犻櫎浼氳瘽锛堢敤鎴锋竻绌虹敾甯冩椂璋冪敤锛?

    Args:
        session_id: 浼氳瘽 ID

    Returns:
        CanvasSessionDeleteResponse: 鍒犻櫎缁撴灉
    """
    try:
        logger.info(f"Deleting canvas session: {session_id}")

        session_manager = get_session_manager()
        existed = session_manager.delete_session(session_id)

        if existed:
            logger.info(f"Session deleted: {session_id}")
            return CanvasSessionDeleteResponse(
                success=True,
                message=f"Session deleted: {session_id}"
            )
        else:
            logger.warning(f"Session not found for deletion: {session_id}")
            return CanvasSessionDeleteResponse(
                success=True,
                message=f"Session not found: {session_id}"
            )

    except Exception as e:
        logger.error(f"Failed to delete canvas session: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


