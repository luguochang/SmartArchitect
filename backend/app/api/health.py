from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查端点"""
    logger.info("Health check requested")
    return {
        "status": "healthy",
        "service": "SmartArchitect AI",
        "phase": "Phase 1 MVP",
    }
