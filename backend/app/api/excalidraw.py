import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import Any, Dict, List, Optional, Set
import logging
import json
import time

from app.models.schemas import ExcalidrawGenerateRequest, ExcalidrawGenerateResponse
from app.services.excalidraw_generator import create_excalidraw_service
from app.services.ai_vision import create_vision_service
from app.services.model_presets import get_model_presets_service

router = APIRouter()
logger = logging.getLogger(__name__)


_ALLOWED_EXCALIDRAW_TYPES = {
    "rectangle",
    "ellipse",
    "diamond",
    "line",
    "arrow",
    "freedraw",
    "text",
}


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _extract_array_objects(payload: str, array_key: str) -> List[Dict[str, Any]]:
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


def _element_stream_identity(element_payload: Dict[str, Any]) -> str:
    element_id = str(element_payload.get("id") or "").strip()
    if element_id:
        return f"id:{element_id}"
    etype = str(element_payload.get("type") or "").strip()
    x = element_payload.get("x")
    y = element_payload.get("y")
    text = str(element_payload.get("text") or "").strip()
    return f"type:{etype}|x:{x}|y:{y}|text:{text[:32]}"


def _normalize_partial_element(element_payload: Dict[str, Any], fallback_index: int) -> Optional[Dict[str, Any]]:
    if not isinstance(element_payload, dict):
        return None

    etype = str(element_payload.get("type") or "").strip().lower()
    if etype not in _ALLOWED_EXCALIDRAW_TYPES:
        return None

    element_id = str(element_payload.get("id") or "").strip() or f"partial-element-{fallback_index + 1}"
    now = int(time.time() * 1000)
    fallback_x = 80 + (fallback_index % 6) * 180
    fallback_y = 80 + (fallback_index // 6) * 140

    x = float(element_payload.get("x")) if _is_finite_number(element_payload.get("x")) else float(fallback_x)
    y = float(element_payload.get("y")) if _is_finite_number(element_payload.get("y")) else float(fallback_y)
    width = float(element_payload.get("width")) if _is_finite_number(element_payload.get("width")) else 120.0
    height = float(element_payload.get("height")) if _is_finite_number(element_payload.get("height")) else 80.0

    base: Dict[str, Any] = {
        "id": element_id,
        "type": etype,
        "x": x,
        "y": y,
        "width": max(1.0, width),
        "height": max(1.0, height),
        "angle": float(element_payload.get("angle")) if _is_finite_number(element_payload.get("angle")) else 0.0,
        "strokeColor": str(element_payload.get("strokeColor") or "#1f2937"),
        "backgroundColor": str(element_payload.get("backgroundColor") or "transparent"),
        "fillStyle": str(element_payload.get("fillStyle") or "solid"),
        "strokeWidth": int(element_payload.get("strokeWidth")) if _is_finite_number(element_payload.get("strokeWidth")) else 2,
        "strokeStyle": str(element_payload.get("strokeStyle") or "solid"),
        "roughness": int(element_payload.get("roughness")) if _is_finite_number(element_payload.get("roughness")) else 1,
        "opacity": int(element_payload.get("opacity")) if _is_finite_number(element_payload.get("opacity")) else 100,
        "groupIds": element_payload.get("groupIds") if isinstance(element_payload.get("groupIds"), list) else [],
        "frameId": element_payload.get("frameId"),
        "boundElements": element_payload.get("boundElements") if isinstance(element_payload.get("boundElements"), list) else [],
        "seed": int(element_payload.get("seed")) if _is_finite_number(element_payload.get("seed")) else (fallback_index + 1) * 7919,
        "version": int(element_payload.get("version")) if _is_finite_number(element_payload.get("version")) else 1,
        "versionNonce": int(element_payload.get("versionNonce")) if _is_finite_number(element_payload.get("versionNonce")) else (fallback_index + 1) * 104729,
        "isDeleted": False,
        "updated": int(element_payload.get("updated")) if _is_finite_number(element_payload.get("updated")) else now,
        "link": element_payload.get("link"),
        "locked": bool(element_payload.get("locked")) if isinstance(element_payload.get("locked"), bool) else False,
    }

    if etype in {"line", "arrow", "freedraw"}:
        raw_points = element_payload.get("points")
        if not isinstance(raw_points, list) or not raw_points:
            return None

        normalized_points = []
        for point in raw_points:
            if (
                not isinstance(point, list)
                or len(point) < 2
                or not _is_finite_number(point[0])
                or not _is_finite_number(point[1])
            ):
                return None
            normalized_points.append([float(point[0]), float(point[1])])

        xs = [p[0] for p in normalized_points]
        ys = [p[1] for p in normalized_points]
        base["points"] = normalized_points
        base["width"] = max(max(xs) - min(xs), 1.0)
        base["height"] = max(max(ys) - min(ys), 1.0)
        if etype == "arrow":
            start_head = element_payload.get("startArrowhead")
            end_head = element_payload.get("endArrowhead")
            if isinstance(start_head, str):
                base["startArrowhead"] = start_head
            if isinstance(end_head, str):
                base["endArrowhead"] = end_head

    if etype == "text":
        text_value = element_payload.get("text")
        if not isinstance(text_value, str) or not text_value.strip():
            return None
        base["text"] = text_value
        base["fontSize"] = int(element_payload.get("fontSize")) if _is_finite_number(element_payload.get("fontSize")) else 20
        base["fontFamily"] = int(element_payload.get("fontFamily")) if _is_finite_number(element_payload.get("fontFamily")) else 1
        base["textAlign"] = str(element_payload.get("textAlign") or "left")

    return base


def _classify_upstream_error(error: Exception) -> tuple[int, str]:
    text = str(error).lower()
    if "usage_limit" in text or "rate limit" in text or "quota" in text or "429" in text:
        return 429, "usage_limit_reached"
    if "unauthorized" in text or "invalid api key" in text or "authentication" in text or "401" in text:
        return 401, "authentication_failed"
    if "timeout" in text or "timed out" in text:
        return 504, "upstream_timeout"
    if "bad gateway" in text or "502" in text or "503" in text or "service unavailable" in text:
        return 503, "upstream_unavailable"
    return 500, "upstream_error"


def _build_config_candidates(request: ExcalidrawGenerateRequest) -> List[Dict[str, Any]]:
    presets_service = get_model_presets_service()
    primary = presets_service.get_active_config(
        provider=request.provider,
        api_key=request.api_key,
        base_url=request.base_url,
        model_name=request.model_name,
    )
    if not primary:
        return []

    candidates = [primary]
    candidates.extend(presets_service.get_failover_configs(primary_config=primary, max_candidates=3))
    return candidates


def _is_fallback_scene_message(message: str) -> bool:
    lowered = (message or "").lower()
    return "fallback" in lowered or "mock" in lowered


@router.post("/excalidraw/generate", response_model=ExcalidrawGenerateResponse)
async def generate_excalidraw_scene(request: ExcalidrawGenerateRequest):
    """Generate Excalidraw scene via AI with automatic provider failover."""
    service = create_excalidraw_service()
    config_candidates = _build_config_candidates(request)
    if not config_candidates:
        raise HTTPException(status_code=400, detail="No AI configuration found. Please configure model settings first.")

    attempt_errors: List[Dict[str, Any]] = []
    fallback_response: Optional[ExcalidrawGenerateResponse] = None

    for index, config in enumerate(config_candidates, start=1):
        provider = config.get("provider")
        model_name = config.get("model_name")
        try:
            logger.info(
                "[EXCALIDRAW] Attempt %s/%s provider=%s model=%s",
                index,
                len(config_candidates),
                provider,
                model_name,
            )
            scene = await service.generate_scene(
                prompt=request.prompt,
                style=request.style,
                width=request.width or 1200,
                height=request.height or 800,
                provider=provider,
                api_key=config.get("api_key"),
                base_url=config.get("base_url"),
                model_name=model_name,
            )
            message = scene.appState.get("message", "") if isinstance(scene.appState, dict) else ""
            is_fallback_scene = _is_fallback_scene_message(message)

            if is_fallback_scene:
                fallback_response = ExcalidrawGenerateResponse(
                    scene=scene,
                    success=False,
                    message=f"Attempt {index} returned fallback scene: {message or 'unknown reason'}",
                )
                logger.warning("[EXCALIDRAW] Attempt %s returned fallback scene, trying next config", index)
                continue

            return ExcalidrawGenerateResponse(
                scene=scene,
                success=True,
                message=f"Scene generated successfully via {provider}/{model_name}",
            )
        except Exception as error:
            status_code, error_code = _classify_upstream_error(error)
            attempt_errors.append({
                "provider": provider,
                "model_name": model_name,
                "status_code": status_code,
                "error_code": error_code,
                "detail": str(error),
            })
            logger.warning(
                "[EXCALIDRAW] Attempt %s failed (%s/%s): %s",
                index,
                status_code,
                error_code,
                error,
            )

    if fallback_response is not None:
        return fallback_response

    if attempt_errors:
        status_priority = [429, 401, 503, 504, 500]
        chosen_status = 500
        for status in status_priority:
            if any(err.get("status_code") == status for err in attempt_errors):
                chosen_status = status
                break
        summary = "; ".join(
            f"{err['provider']}/{err['model_name']} -> {err['status_code']}:{err['error_code']}"
            for err in attempt_errors
        )[:600]
        raise HTTPException(
            status_code=chosen_status,
            detail=f"Excalidraw generation failed after {len(attempt_errors)} attempts. Summary: {summary}",
        )

    raise HTTPException(status_code=500, detail="Excalidraw generation failed with unknown error.")


@router.post("/excalidraw/generate-stream")
async def generate_excalidraw_scene_stream(request: ExcalidrawGenerateRequest):
    """
    Stream Excalidraw generation with true object-level incremental updates.

    Event format:
    - data: [START] ...
    - data: [CALL] ...
    - data: [TOKEN] ...
    - data: [PARTIAL_ELEMENT] {...}
    - data: [PROGRESS] chars=... partial_elements=...
    - data: [RESULT] {"scene": {...}, "success": true/false, "message": "..."}
    - data: [END] done
    - data: [ERROR] ...
    """

    async def event_stream():
        service = create_excalidraw_service()
        config_candidates = _build_config_candidates(request)
        if not config_candidates:
            yield "data: [ERROR] No AI configuration found. Please configure model settings first.\n\n"
            return

        attempt_errors: List[Dict[str, Any]] = []
        fallback_response: Optional[Dict[str, Any]] = None

        for attempt_index, config in enumerate(config_candidates, start=1):
            provider = config.get("provider")
            model_name = config.get("model_name")
            try:
                yield f"data: [START] attempt={attempt_index}/{len(config_candidates)} provider={provider} model={model_name}\n\n"
                yield "data: [CALL] Generating Excalidraw scene...\n\n"

                vision_service = create_vision_service(
                    provider=provider,
                    api_key=config.get("api_key"),
                    base_url=config.get("base_url"),
                    model_name=model_name,
                )
                prompt = service._build_prompt(
                    request.prompt,
                    request.style,
                    request.width or 1200,
                    request.height or 800,
                )

                accumulated = ""
                chars_since_parse = 0
                parse_interval_chars = 120
                heartbeat_seconds = 8.0
                last_heartbeat = time.monotonic()
                seen_partial_keys: Set[str] = set()
                partial_elements_sent = 0
                first_token_timeout_seconds = 18.0
                token_batch = ""
                token_batch_chars = 180
                token_batch_interval_seconds = 0.2
                last_token_emit = time.monotonic()

                async def flush_token_batch(force: bool = False):
                    nonlocal token_batch
                    nonlocal last_token_emit
                    if not token_batch:
                        return
                    now = time.monotonic()
                    if force or len(token_batch) >= token_batch_chars or (now - last_token_emit) >= token_batch_interval_seconds:
                        yield f"data: [TOKEN] {token_batch}\n\n"
                        token_batch = ""
                        last_token_emit = now

                stream_iterator = vision_service.generate_with_stream(prompt).__aiter__()
                try:
                    first_token = await asyncio.wait_for(
                        stream_iterator.__anext__(),
                        timeout=first_token_timeout_seconds,
                    )
                except StopAsyncIteration as empty_stream:
                    raise ValueError("Empty stream output") from empty_stream

                async def process_token(token: str):
                    nonlocal accumulated
                    nonlocal chars_since_parse
                    nonlocal last_heartbeat
                    nonlocal partial_elements_sent
                    nonlocal token_batch
                    if not token:
                        return
                    accumulated += token
                    chars_since_parse += len(token)
                    token_batch += token
                    if "\n" in token:
                        async for event in flush_token_batch(force=True):
                            yield event
                    else:
                        async for event in flush_token_batch(force=False):
                            yield event

                    should_parse_partials = ("}" in token) or (chars_since_parse >= parse_interval_chars)
                    if should_parse_partials:
                        chars_since_parse = 0
                        for raw_element in _extract_array_objects(accumulated, "elements"):
                            identity = _element_stream_identity(raw_element)
                            if identity in seen_partial_keys:
                                continue
                            partial_element = _normalize_partial_element(raw_element, partial_elements_sent)
                            if not partial_element:
                                continue
                            seen_partial_keys.add(identity)
                            partial_elements_sent += 1
                            yield (
                                f"data: [PARTIAL_ELEMENT] {json.dumps(partial_element, ensure_ascii=False)}\n\n"
                            )

                    now = time.monotonic()
                    if now - last_heartbeat >= heartbeat_seconds:
                        yield (
                            "data: [PROGRESS] "
                            f"chars={len(accumulated)} partial_elements={partial_elements_sent}\n\n"
                        )
                        last_heartbeat = now

                async for event in process_token(first_token):
                    yield event
                async for token in stream_iterator:
                    async for event in process_token(token):
                        yield event
                async for event in flush_token_batch(force=True):
                    yield event

                ai_data = service._safe_json(accumulated)
                scene = service._validate_scene(ai_data, request.width or 1200, request.height or 800)
                message = scene.appState.get("message", "") if isinstance(scene.appState, dict) else ""
                is_fallback_scene = _is_fallback_scene_message(message)

                if is_fallback_scene and attempt_index < len(config_candidates):
                    yield (
                        "data: [WARN] "
                        f"attempt={attempt_index} returned fallback scene, trying next configuration\n\n"
                    )
                    fallback_response = {
                        "scene": scene.model_dump(),
                        "success": False,
                        "message": f"Fallback scene via {provider}/{model_name}: {message}",
                    }
                    continue

                response_data = {
                    "scene": scene.model_dump(),
                    "success": not is_fallback_scene,
                    "message": message or f"Scene generated via {provider}/{model_name}",
                }
                yield f"data: [RESULT] {json.dumps(response_data, ensure_ascii=False)}\n\n"
                yield "data: [END] done\n\n"
                return
            except Exception as error:
                status_code, error_code = _classify_upstream_error(error)
                attempt_errors.append({
                    "provider": provider,
                    "model_name": model_name,
                    "status_code": status_code,
                    "error_code": error_code,
                    "detail": str(error),
                })
                if attempt_index < len(config_candidates):
                    yield (
                        "data: [WARN] "
                        f"attempt={attempt_index} failed ({status_code}:{error_code}), failover to next configuration\n\n"
                    )
                    continue

        if fallback_response is not None:
            fallback_response["message"] = (
                f"{fallback_response.get('message', 'Fallback scene returned')}. "
                "All configured providers returned fallback output."
            )
            yield f"data: [RESULT] {json.dumps(fallback_response, ensure_ascii=False)}\n\n"
            yield "data: [END] done\n\n"
            return

        if attempt_errors:
            summary = "; ".join(
                f"{err['provider']}/{err['model_name']} -> {err['status_code']}:{err['error_code']}"
                for err in attempt_errors
            )[:600]
            yield f"data: [ERROR] Excalidraw generation failed after {len(attempt_errors)} attempts. {summary}\n\n"
            return

        yield "data: [ERROR] Excalidraw generation failed with unknown error.\n\n"

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
