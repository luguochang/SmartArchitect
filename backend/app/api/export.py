"""
Export API Router
Handles PPT, Slidev, and Speech Script generation
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from typing import Optional, List
import logging
from io import BytesIO
import json
import asyncio

from app.models.schemas import (
    ExportRequest,
    SpeechScriptRequest,
    SpeechScriptResponse,
    EnhancedSpeechScriptRequest,
    ScriptContent,
    ScriptMetadata,
    SaveDraftResponse,
    RefinedSectionResponse,
    ImprovementSuggestions,
)
from app.services.ppt_exporter import create_ppt_exporter
from app.services.slidev_exporter import create_slidev_exporter
from app.services.ai_vision import create_vision_service
from app.services.model_presets import get_model_presets_service
from app.services.speech_script_rag import get_rag_speech_script_generator
from app.services.script_editor import get_script_editor_service

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
        provider: AI provider (gemini, openai, claude, siliconflow, custom)
        api_key: API key for the provider

    Returns:
        SpeechScriptResponse with the generated script
    """
    try:
        logger.info(f"Generating {request.duration} speech script")

        # 获取有效配置
        presets_service = get_model_presets_service()
        config = presets_service.get_active_config(
            provider=provider,
            api_key=api_key
        )

        if not config:
            raise HTTPException(
                status_code=400,
                detail="No AI configuration found. Please configure AI model in settings or provide API key."
            )

        # Create AI vision service
        vision_service = create_vision_service(
            provider=config["provider"],
            api_key=config["api_key"],
            base_url=config.get("base_url"),
            model_name=config.get("model_name")
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


# ============================================================
# Enhanced Speech Script Generation with RAG and Streaming
# ============================================================


@router.post("/export/script-stream")
async def generate_script_stream(
    request: EnhancedSpeechScriptRequest,
    provider: Optional[str] = "gemini",
    api_key: Optional[str] = None,
    base_url: Optional[str] = None,
    model_name: Optional[str] = None
):
    """
    Generate professional speech script with streaming (Server-Sent Events)

    This endpoint uses the CO-STAR framework and RAG enhancement to generate
    high-quality speech scripts. Progress is streamed in real-time using SSE.

    Args:
        request: Enhanced script generation request with nodes, edges, duration, options
        provider: AI provider (gemini, openai, claude, siliconflow, custom)
        api_key: API key for the provider
        base_url: Base URL for custom provider
        model_name: Model name for the provider

    Returns:
        text/event-stream (SSE) with StreamEvent objects

    Event Types:
        - CONTEXT_SEARCH: RAG searching in progress
        - CONTEXT_FOUND: RAG results found
        - GENERATION_START: Script generation starting
        - TOKEN: Individual token generated
        - SECTION_COMPLETE: A section (intro/body/conclusion) completed
        - COMPLETE: Full script generation completed
        - ERROR: Error occurred
    """
    try:
        logger.info(
            f"Streaming {request.duration} speech script generation "
            f"(audience: {request.options.audience}, tone: {request.options.tone})"
        )

        async def event_generator():
            """Async generator for SSE events"""
            try:
                # Phase 1: 发送开始事件
                start_data = {'type': 'GENERATION_START', 'data': {'message': 'AI正在创作演讲稿...'}}
                yield f"data: {json.dumps(start_data, ensure_ascii=False)}\n\n"
                logger.info("[SCRIPT-STREAM] Sent GENERATION_START event")

                # 获取有效配置
                presets_service = get_model_presets_service()
                config = presets_service.get_active_config(
                    provider=provider,
                    api_key=api_key,
                    base_url=base_url,
                    model_name=model_name
                )

                if not config:
                    error_data = {'type': 'ERROR', 'data': {'message': 'No AI configuration found. Please configure AI model in settings.'}}
                    yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"
                    return

                # Create AI service for streaming
                from app.services.ai_vision import create_vision_service
                ai_service = create_vision_service(
                    provider=config["provider"],
                    api_key=config["api_key"],
                    base_url=config.get("base_url"),
                    model_name=config.get("model_name")
                )

                # Build prompt
                arch_desc = f"Architecture with {len(request.nodes)} components and {len(request.edges)} connections:\n\n"
                arch_desc += "Components:\n"
                for node in request.nodes:
                    arch_desc += f"- {node.data.label} (type: {node.type or 'default'})\n"
                arch_desc += "\nConnections:\n"
                for edge in request.edges:
                    source_node = next((n for n in request.nodes if n.id == edge.source), None)
                    target_node = next((n for n in request.nodes if n.id == edge.target), None)
                    if source_node and target_node:
                        label_text = f" ({edge.label})" if edge.label else ""
                        arch_desc += f"- {source_node.data.label} → {target_node.data.label}{label_text}\n"

                duration_prompts = {
                    "30s": "生成一个30秒的电梯演讲稿（约150字）。聚焦核心价值主张。",
                    "2min": "生成一个2分钟的演讲稿（约600字）。涵盖架构概览、核心组件和优势。",
                    "5min": "生成一个5分钟的详细演讲稿（约1500字）。包含开场、架构概览、组件细节、数据流和结论。"
                }

                prompt = f'''你是一位专业的技术演讲者，正在创建一份演讲稿。

{arch_desc}

{duration_prompts.get(request.duration, duration_prompts["2min"])}

要求：
1. 使用清晰、专业的中文表达
2. 用通俗易懂的方式解释技术概念
3. 突出架构的优势和设计决策
4. 段落之间过渡自然流畅
5. 以有力的结论收尾
6. 只返回演讲稿文本，不要返回JSON或其他格式

现在开始创作演讲稿：'''

                # Stream generation - 完全复制chat_generator的方式
                if provider in ["openai", "siliconflow", "custom"]:
                    logger.info(f"[SCRIPT-STREAM] Starting streaming with {provider}, model={ai_service.model_name}")

                    stream = ai_service.client.chat.completions.create(
                        model=ai_service.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=4000,
                        stream=True,
                    )

                    accumulated = ""
                    logger.info("[SCRIPT-STREAM] Stream created, starting iteration")

                    for chunk in stream:
                        # Guard against empty chunks
                        if not getattr(chunk, "choices", None):
                            continue
                        delta = chunk.choices[0].delta.content if chunk.choices[0].delta else None
                        if not delta:
                            continue

                        text = delta
                        accumulated += text
                        # 立即yield - 不要任何延迟
                        token_data = {'type': 'TOKEN', 'data': {'token': text}}
                        yield f"data: {json.dumps(token_data, ensure_ascii=False)}\n\n"

                    # 完成后发送COMPLETE事件
                    logger.info(f"[SCRIPT-STREAM] Streaming completed, total length: {len(accumulated)}")
                    sections = {
                        "intro": accumulated[:len(accumulated)//3] if accumulated else "",
                        "body": accumulated[len(accumulated)//3:len(accumulated)*2//3] if accumulated else "",
                        "conclusion": accumulated[len(accumulated)*2//3:] if accumulated else ""
                    }
                    complete_data = {
                        'type': 'COMPLETE',
                        'data': {
                            'script': {
                                'intro': sections['intro'],
                                'body': sections['body'],
                                'conclusion': sections['conclusion'],
                                'full_text': accumulated
                            },
                            'word_count': len(accumulated),
                            'estimated_seconds': int(len(accumulated) / 2.5)
                        }
                    }
                    yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"
                else:
                    # 降级到非流式
                    logger.info(f"[SCRIPT-STREAM] Provider {provider} doesn't support streaming, using non-streaming")
                    result = await ai_service.generate_speech_script(request.nodes, request.edges, request.duration)
                    token_data = {'type': 'TOKEN', 'data': {'token': result}}
                    yield f"data: {json.dumps(token_data, ensure_ascii=False)}\n\n"
                    sections = {"intro": result[:len(result)//3], "body": result[len(result)//3:len(result)*2//3], "conclusion": result[len(result)*2//3:]}
                    complete_data = {
                        'type': 'COMPLETE',
                        'data': {
                            'script': {
                                'intro': sections['intro'],
                                'body': sections['body'],
                                'conclusion': sections['conclusion'],
                                'full_text': result
                            },
                            'word_count': len(result),
                            'estimated_seconds': int(len(result) / 2.5)
                        }
                    }
                    yield f"data: {json.dumps(complete_data, ensure_ascii=False)}\n\n"

            except Exception as e:
                logger.error(f"[SCRIPT-STREAM] Stream generation error: {e}", exc_info=True)
                error_event = json.dumps(
                    {
                        "type": "ERROR",
                        "data": {"error": str(e)}
                    },
                    ensure_ascii=False
                )
                yield f"data: {error_event}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
                "Content-Encoding": "none",
                "Transfer-Encoding": "chunked",
            }
        )

    except Exception as e:
        logger.error(f"Script stream generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate script stream: {str(e)}"
        )


@router.put("/export/script/{script_id}/draft", response_model=SaveDraftResponse)
async def save_script_draft(
    script_id: str,
    content: ScriptContent,
    metadata: ScriptMetadata
):
    """
    Save speech script draft with version control

    Supports incremental updates and auto-save functionality from frontend.
    Each save increments the version number.

    Args:
        script_id: Unique script identifier (UUID)
        content: Script content (intro, body, conclusion, full_text)
        metadata: Script metadata (duration, word_count, rag_sources, etc.)

    Returns:
        SaveDraftResponse with script_id, version, saved_at
    """
    try:
        logger.info(f"Saving draft for script {script_id}, version {metadata.version}")

        editor = get_script_editor_service()
        response = await editor.save_draft(script_id, content, metadata)

        logger.info(f"Draft saved successfully: version {response.version}")
        return response

    except Exception as e:
        logger.error(f"Failed to save draft {script_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save draft: {str(e)}"
        )


@router.get("/export/script/{script_id}/draft")
async def load_script_draft(script_id: str):
    """
    Load speech script draft by ID

    Args:
        script_id: Unique script identifier

    Returns:
        ScriptDraft object with full content and metadata

    Raises:
        404: Script not found
    """
    try:
        logger.info(f"Loading draft for script {script_id}")

        editor = get_script_editor_service()
        draft = await editor.load_draft(script_id)

        if draft is None:
            raise HTTPException(
                status_code=404,
                detail=f"Script {script_id} not found"
            )

        logger.info(f"Draft loaded: version {draft.version}")
        return draft

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load draft {script_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load draft: {str(e)}"
        )


@router.post("/export/script/{script_id}/refine", response_model=RefinedSectionResponse)
async def refine_script_section(
    script_id: str,
    section: str,
    user_feedback: str,
    rag_context: Optional[dict] = None
):
    """
    Refine a specific section of the speech script based on user feedback

    Allows targeted improvements to intro, body, or conclusion sections.
    The AI will regenerate the section while preserving core information.

    Args:
        script_id: Script identifier
        section: Section to refine ("intro", "body", or "conclusion")
        user_feedback: User's refinement request (e.g., "增加数据支撑", "使用类比")
        rag_context: Optional additional RAG context

    Returns:
        RefinedSectionResponse with refined_text and changes_summary

    Raises:
        400: Invalid section name
        404: Script not found
    """
    try:
        # Validate section parameter
        if section not in ["intro", "body", "conclusion"]:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid section '{section}'. Must be 'intro', 'body', or 'conclusion'"
            )

        logger.info(f"Refining {section} section for script {script_id}")
        logger.info(f"User feedback: {user_feedback}")

        editor = get_script_editor_service()
        response = await editor.refine_section(
            script_id=script_id,
            section=section,
            user_feedback=user_feedback,
            rag_context=rag_context
        )

        logger.info(f"Section refined successfully. Changes: {response.changes_summary}")
        return response

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to refine section: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refine section: {str(e)}"
        )


@router.get("/export/script/{script_id}/suggestions", response_model=ImprovementSuggestions)
async def get_script_suggestions(
    script_id: str,
    focus_areas: Optional[List[str]] = None
):
    """
    Get AI-powered improvement suggestions for the speech script

    Analyzes the script and provides specific, actionable suggestions
    without directly modifying the content. Users can review and apply
    suggestions selectively.

    Args:
        script_id: Script identifier
        focus_areas: Optional focus areas (e.g., ["clarity", "engagement", "flow"])
                    Defaults to ["clarity", "engagement", "flow"]

    Returns:
        ImprovementSuggestions with:
            - overall_score: Quality score (1-10)
            - strengths: List of strong points
            - weaknesses: List of areas to improve
            - suggestions: Detailed improvement suggestions by section

    Raises:
        404: Script not found
    """
    try:
        if focus_areas is None:
            focus_areas = ["clarity", "engagement", "flow"]

        logger.info(f"Generating suggestions for script {script_id}")
        logger.info(f"Focus areas: {', '.join(focus_areas)}")

        editor = get_script_editor_service()
        suggestions = await editor.suggest_improvements(
            script_id=script_id,
            focus_areas=focus_areas
        )

        logger.info(
            f"Generated {len(suggestions.suggestions)} suggestions "
            f"(score: {suggestions.overall_score}/10)"
        )
        return suggestions

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to generate suggestions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate suggestions: {str(e)}"
        )
