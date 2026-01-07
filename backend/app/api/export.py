"""
Export API Router
Handles PPT, Slidev, and Speech Script generation
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from typing import Optional
import logging
from io import BytesIO

from app.models.schemas import (
    ExportRequest,
    SpeechScriptRequest,
    SpeechScriptResponse,
)
from app.services.ppt_exporter import create_ppt_exporter
from app.services.slidev_exporter import create_slidev_exporter
from app.services.ai_vision import create_vision_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/export/ppt")
async def export_ppt(request: ExportRequest):
    """Export architecture as PowerPoint presentation

    Returns:
        PowerPoint file (.pptx)
    """
    try:
        logger.info(f"Exporting architecture to PPT: {request.title}")

        exporter = create_ppt_exporter()
        ppt_bytes = exporter.create_presentation(
            nodes=request.nodes,
            edges=request.edges,
            title=request.title,
        )

        # Return PPT file as download
        return StreamingResponse(
            BytesIO(ppt_bytes),
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            headers={
                "Content-Disposition": f'attachment; filename="{request.title.replace(" ", "_")}.pptx"'
            },
        )

    except Exception as e:
        logger.error(f"PPT export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export PPT: {str(e)}"
        )


@router.post("/export/slidev")
async def export_slidev(request: ExportRequest):
    """Export architecture as Slidev markdown presentation

    Returns:
        Slidev markdown file (.md)
    """
    try:
        logger.info(f"Exporting architecture to Slidev: {request.title}")

        exporter = create_slidev_exporter()
        slidev_markdown = exporter.create_slidev(
            nodes=request.nodes,
            edges=request.edges,
            mermaid_code=request.mermaid_code,
            title=request.title,
        )

        # Return markdown file as download
        return Response(
            content=slidev_markdown,
            media_type="text/markdown",
            headers={
                "Content-Disposition": f'attachment; filename="{request.title.replace(" ", "_")}_slidev.md"'
            },
        )

    except Exception as e:
        logger.error(f"Slidev export failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export Slidev: {str(e)}"
        )


@router.post("/export/script", response_model=SpeechScriptResponse)
async def generate_script(
    request: SpeechScriptRequest,
    provider: Optional[str] = "gemini",
    api_key: Optional[str] = None
):
    """Generate presentation speech script

    Args:
        request: Script generation request with nodes, edges, duration
        provider: AI provider (gemini, openai, claude, custom)
        api_key: API key for the provider

    Returns:
        SpeechScriptResponse with the generated script
    """
    try:
        logger.info(f"Generating {request.duration} speech script")

        # Create AI vision service
        vision_service = create_vision_service(
            provider=provider,
            api_key=api_key
        )

        # Generate script
        script = await vision_service.generate_speech_script(
            nodes=request.nodes,
            edges=request.edges,
            duration=request.duration
        )

        # Calculate word count
        word_count = len(script.split())

        logger.info(f"Generated script: {word_count} words")

        return SpeechScriptResponse(
            script=script,
            duration=request.duration,
            word_count=word_count,
            success=True
        )

    except Exception as e:
        logger.error(f"Script generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate script: {str(e)}"
        )


@router.get("/export/health")
async def export_health():
    """Export service health check

    Returns:
        Service status and available export formats
    """
    try:
        return {
            "status": "healthy",
            "available_formats": ["ppt", "slidev", "script"],
            "script_durations": ["30s", "2min", "5min"]
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }
