from fastapi import APIRouter, HTTPException
from app.models.schemas import ModelConfig, ModelConfigResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 存储模型配置（实际应用中应该使用数据库或其他持久化方案）
_model_configs = {}


@router.post("/models/config", response_model=ModelConfigResponse)
async def configure_model(config: ModelConfig):
    """
    配置 AI 模型
    支持多种模型提供商：Gemini, OpenAI, Claude, Custom
    """
    try:
        # 验证配置
        if not config.api_key:
            raise HTTPException(status_code=400, detail="API key is required")

        if config.provider == "custom" and not config.base_url:
            raise HTTPException(
                status_code=400, detail="Base URL is required for custom provider"
            )

        # 存储配置（实际应该加密存储）
        _model_configs[config.provider] = config.model_dump()

        return ModelConfigResponse(
            success=True,
            message=f"Successfully configured {config.provider} model: {config.model_name}",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure model: {str(e)}")


@router.get("/models/config/{provider}")
async def get_model_config(provider: str):
    """获取指定提供商的模型配置（不返回敏感信息）"""
    if provider not in _model_configs:
        raise HTTPException(status_code=404, detail=f"No configuration found for {provider}")

    config = _model_configs[provider].copy()
    # 隐藏敏感信息
    config["api_key"] = "***" if config.get("api_key") else ""

    return {"success": True, "config": config}
