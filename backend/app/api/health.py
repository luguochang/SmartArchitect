from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "service": "SmartArchitect AI",
        "phase": "Phase 1 MVP",
    }
