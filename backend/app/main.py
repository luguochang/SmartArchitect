from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import health, mermaid, models

app = FastAPI(
    title="SmartArchitect AI API",
    description="AI-powered architecture design platform backend",
    version="0.1.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(mermaid.router, prefix="/api", tags=["mermaid"])
app.include_router(models.router, prefix="/api", tags=["models"])


@app.get("/")
async def root():
    return {
        "message": "SmartArchitect AI API",
        "version": "0.1.0",
        "phase": "Phase 1 MVP",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )
