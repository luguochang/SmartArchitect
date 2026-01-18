from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import ExcalidrawGenerateRequest, ExcalidrawGenerateResponse
from app.services.excalidraw_generator import create_excalidraw_service
from app.services.ai_vision import create_vision_service
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/excalidraw/generate", response_model=ExcalidrawGenerateResponse)
async def generate_excalidraw_scene(request: ExcalidrawGenerateRequest):
    """
    Generate Excalidraw scene via AI.

    Falls back to mock scene if AI provider fails or returns invalid JSON.
    Uses Qwen/Qwen2.5-14B-Instruct as backup model for SiliconFlow.
    """
    try:
        logger.info(f"Excalidraw generation request: provider={request.provider}, prompt={request.prompt[:50]}...")

        # Validate provider and API key
        if not request.api_key and request.provider != "mock":
            logger.warning("No API key provided, will use mock fallback")

        service = create_excalidraw_service()
        scene = await service.generate_scene(
            prompt=request.prompt,
            style=request.style,
            width=request.width or 1200,
            height=request.height or 800,
            provider=request.provider,
            api_key=request.api_key,
            base_url=request.base_url,
            model_name=request.model_name,
        )

        success = not scene.appState.get("message", "").startswith("Fallback mock:")
        message = scene.appState.get("message") or "Scene generated successfully"
        logger.info(f"Excalidraw generation completed: {len(scene.elements)} elements, success={success}")

        return ExcalidrawGenerateResponse(scene=scene, success=success, message=message)
    except Exception as e:
        logger.error(f"Excalidraw scene generation failed critically: {e}", exc_info=True)
        # Return mock scene instead of raising error
        service = create_excalidraw_service()
        mock_scene = service._mock_scene()
        mock_scene.appState["message"] = f"Critical error: {str(e)[:100]}"
        return ExcalidrawGenerateResponse(
            scene=mock_scene,
            success=False,
            message=f"Error occurred, returned mock scene: {str(e)[:100]}"
        )


@router.post("/excalidraw/generate-stream")
async def generate_excalidraw_scene_stream(request: ExcalidrawGenerateRequest):
    """
    Generate Excalidraw scene via AI with streaming output (SSE).

    Streams the AI generation process token-by-token, allowing frontend
    to display real-time progress instead of showing a loading spinner.

    Event format:
    - data: [START] message\n\n
    - data: [CALL] message\n\n
    - data: [TOKEN] text_chunk\n\n
    - data: [RESULT] {"scene": {...}, "success": true, "message": "..."}\n\n
    - data: [END] done\n\n
    - data: [ERROR] error_message\n\n
    """
    async def event_stream():
        try:
            logger.info(f"[EXCALIDRAW-STREAM] Starting generation")
            logger.info(f"[EXCALIDRAW-STREAM] Provider: {request.provider}, Model: {request.model_name}")
            logger.info(f"[EXCALIDRAW-STREAM] Prompt: {request.prompt[:100]}...")

            yield "data: [START] Building Excalidraw prompt...\n\n"

            service = create_excalidraw_service()
            vision_service = create_vision_service(
                provider=request.provider or "siliconflow",
                api_key=request.api_key,
                base_url=request.base_url,
                model_name=request.model_name,
            )

            logger.info(f"[EXCALIDRAW-STREAM] Vision service created: provider={vision_service.provider}, model={vision_service.model_name}")

            # Build prompt
            prompt = service._build_prompt(
                request.prompt,
                request.style,
                request.width or 1200,
                request.height or 800
            )

            logger.info(f"[EXCALIDRAW-STREAM] Prompt built, length: {len(prompt)}")

            yield "data: [CALL] Generating scene with AI...\n\n"
            logger.info(f"[EXCALIDRAW-STREAM] Starting AI streaming...")

            # Stream tokens from AI
            accumulated = ""
            try:
                token_count = 0
                async for token in vision_service.generate_with_stream(prompt):
                    yield f"data: [TOKEN] {token}\n\n"
                    accumulated += token
                    token_count += 1
                    if token_count % 100 == 0:
                        logger.debug(f"[EXCALIDRAW-STREAM] Received {token_count} tokens, accumulated {len(accumulated)} chars")

                logger.info(f"[EXCALIDRAW-STREAM] Streaming completed: {len(accumulated)} characters, {token_count} tokens")

                # Parse and validate the accumulated JSON
                ai_data = service._safe_json(accumulated)
                scene = service._validate_scene(ai_data, request.width or 1200, request.height or 800)

                # Determine success based on message (mock scenes have specific messages)
                message = scene.appState.get("message", "")
                is_fallback = any(keyword in message for keyword in ["Fallback mock", "fallback scene", "mock fallback"])
                success = not is_fallback

                if not message or message == f"Generated via {request.provider}":
                    message = f"Scene generated successfully with {len(scene.elements)} elements"

                scene.appState["message"] = message

                # Send final result (scene is guaranteed to have elements now)
                response_data = {
                    "scene": scene.model_dump(),
                    "success": success,
                    "message": message
                }
                yield f"data: [RESULT] {json.dumps(response_data)}\n\n"
                yield "data: [END] done\n\n"

                logger.info(f"Excalidraw streaming completed: {len(scene.elements)} elements, success={success}")

            except Exception as stream_error:
                logger.error(f"Streaming generation failed: {stream_error}", exc_info=True)

                # Check if it's a 500 API error
                error_str = str(stream_error)
                is_api_500 = "500" in error_str or "InternalServerError" in error_str

                if is_api_500:
                    logger.warning("[EXCALIDRAW-STREAM] Detected API 500 error, returning mock scene instead of propagating error")

                # Fallback to mock scene (don't propagate error to client)
                mock_scene = service._mock_scene()
                mock_scene.appState["message"] = f"AI API unavailable (500), showing fallback scene"

                response_data = {
                    "scene": mock_scene.model_dump(),
                    "success": False,
                    "message": f"AI generation failed, showing mock scene. Error: {str(stream_error)[:100]}"
                }
                yield f"data: [RESULT] {json.dumps(response_data)}\n\n"
                yield "data: [END] done\n\n"
                logger.info("[EXCALIDRAW-STREAM] Sent mock scene as fallback")

        except Exception as e:
            logger.error(f"Excalidraw stream failed critically: {e}", exc_info=True)
            yield f"data: [ERROR] {str(e)}\n\n"

            # Send mock scene as final fallback
            try:
                service = create_excalidraw_service()
                mock_scene = service._mock_scene()
                mock_scene.appState["message"] = f"Critical error: {str(e)[:100]}"

                response_data = {
                    "scene": mock_scene.model_dump(),
                    "success": False,
                    "message": f"Critical error, mock scene: {str(e)[:100]}"
                }
                yield f"data: [RESULT] {json.dumps(response_data)}\n\n"
                yield "data: [END] done\n\n"
            except Exception:
                yield "data: [END] error\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )
