from fastapi import APIRouter, HTTPException
from app.models.schemas import ExcalidrawGenerateRequest, ExcalidrawGenerateResponse
from app.services.excalidraw_generator import create_excalidraw_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/excalidraw/generate", response_model=ExcalidrawGenerateResponse)
async def generate_excalidraw_scene(request: ExcalidrawGenerateRequest):
    try:
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
        return ExcalidrawGenerateResponse(scene=scene, success=True, message=scene.appState.get("message"))
    except Exception as e:
        logger.error(f"Excalidraw scene generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
