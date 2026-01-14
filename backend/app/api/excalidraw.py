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
            yield "data: [START] Building Excalidraw prompt...\n\n"

            service = create_excalidraw_service()
            vision_service = create_vision_service(
                provider=request.provider or "siliconflow",
                api_key=request.api_key,
                base_url=request.base_url,
                model_name=request.model_name,
            )

            # Build prompt
            prompt = service._build_prompt(
                request.prompt,
                request.style,
                request.width or 1200,
                request.height or 800
            )

            yield "data: [CALL] Generating scene with AI...\n\n"
            logger.info(f"Excalidraw streaming: provider={request.provider}, prompt={request.prompt[:50]}...")

            # Stream tokens from AI
            accumulated = ""
            try:
                async for token in vision_service.generate_with_stream(prompt):
                    yield f"data: [TOKEN] {token}\n\n"
                    accumulated += token

                logger.info(f"Excalidraw stream completed: {len(accumulated)} characters")

                # Parse and validate the accumulated JSON
                ai_data = service._safe_json(accumulated)
                scene = service._validate_scene(ai_data, request.width or 1200, request.height or 800)

                # Determine success
                success = not scene.appState.get("message", "").startswith("Fallback mock:")
                message = scene.appState.get("message") or f"Generated via {request.provider}"
                scene.appState["message"] = message

                if not scene.elements:
                    raise ValueError("Empty scene returned by AI")

                # Send final result
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

                # Fallback to mock scene
                mock_scene = service._mock_scene()
                mock_scene.appState["message"] = f"Fallback mock: {str(stream_error)[:100]}"

                response_data = {
                    "scene": mock_scene.model_dump(),
                    "success": False,
                    "message": f"AI generation failed, showing mock scene: {str(stream_error)[:100]}"
                }
                yield f"data: [RESULT] {json.dumps(response_data)}\n\n"
                yield "data: [END] done\n\n"

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
