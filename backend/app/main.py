from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.middleware.logging_middleware import LoggerMiddleware
from app.api import health, mermaid, models, vision, prompter, export, rag, chat_generator, excalidraw, diagnosis

# 初始化日志系统（在创建 FastAPI app 之前）
setup_logging()

app = FastAPI(
    title="SmartArchitect AI API",
    description="AI-powered architecture design platform backend",
    version="0.5.0",
)

# 添加日志中间件（必须在 CORS 之前，确保捕获所有请求）
app.add_middleware(LoggerMiddleware)

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
app.include_router(vision.router, prefix="/api", tags=["vision"])
app.include_router(prompter.router, prefix="/api", tags=["prompter"])
app.include_router(export.router, prefix="/api", tags=["export"])
app.include_router(rag.router, prefix="/api", tags=["rag"])
app.include_router(chat_generator.router, prefix="/api", tags=["chat-generator"])
app.include_router(excalidraw.router, prefix="/api", tags=["excalidraw"])
app.include_router(diagnosis.router, prefix="/api", tags=["diagnosis"])


@app.get("/")
async def root():
    return {
        "message": "SmartArchitect AI API",
        "version": "0.5.0",
        "phase": "Phase 5: Chat Flowchart Generator",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
    )
