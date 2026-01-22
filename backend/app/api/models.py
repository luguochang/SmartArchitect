from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    ModelConfig,
    ModelConfigResponse,
    ModelPresetCreate,
    ModelPresetUpdate,
    ModelPresetListResponse,
    ModelPresetResponse
)
from app.services.model_presets import get_model_presets_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# 存储模型配置（实际应用中应该使用数据库或其他持久化方案）
_model_configs = {}


@router.post("/models/config", response_model=ModelConfigResponse)
async def configure_model(config: ModelConfig):
    """
    配置 AI 模型（旧版 API，保持向后兼容）
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


# ========== 新版预设配置管理 API ==========

@router.get("/models/presets", response_model=ModelPresetListResponse)
async def list_model_presets():
    """列出所有模型预设配置（不返回敏感信息）"""
    try:
        service = get_model_presets_service()
        presets = service.list_presets()
        return ModelPresetListResponse(success=True, presets=presets)
    except Exception as e:
        logger.error(f"Failed to list presets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list presets: {str(e)}")


@router.get("/models/presets/{preset_id}", response_model=ModelPresetResponse)
async def get_model_preset(preset_id: str):
    """获取指定预设配置（不返回 API key）"""
    try:
        service = get_model_presets_service()
        preset = service.get_preset(preset_id, include_api_key=False)

        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")

        return ModelPresetResponse(success=True, preset=preset)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get preset: {str(e)}")


@router.get("/models/presets/{preset_id}/full", response_model=ModelPresetResponse)
async def get_model_preset_full(preset_id: str):
    """获取指定预设配置（包含完整 API key，用于实际使用）"""
    try:
        service = get_model_presets_service()
        preset = service.get_preset(preset_id, include_api_key=True)

        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")

        return ModelPresetResponse(success=True, preset=preset)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get preset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get preset: {str(e)}")


@router.post("/models/presets", response_model=ModelPresetResponse)
async def create_model_preset(preset_data: ModelPresetCreate):
    """创建新的模型预设配置"""
    try:
        service = get_model_presets_service()
        preset = service.create_preset(preset_data)

        # 返回时隐藏 API key
        safe_preset = preset.model_copy()
        safe_preset.api_key = "***"

        return ModelPresetResponse(
            success=True,
            preset=safe_preset,
            message=f"Created preset '{preset.name}'"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create preset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create preset: {str(e)}")


@router.patch("/models/presets/{preset_id}", response_model=ModelPresetResponse)
async def update_model_preset(preset_id: str, update_data: ModelPresetUpdate):
    """更新模型预设配置"""
    try:
        service = get_model_presets_service()
        preset = service.update_preset(preset_id, update_data)

        if not preset:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")

        # 返回时隐藏 API key
        safe_preset = preset.model_copy()
        safe_preset.api_key = "***"

        return ModelPresetResponse(
            success=True,
            preset=safe_preset,
            message=f"Updated preset '{preset.name}'"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update preset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update preset: {str(e)}")


@router.delete("/models/presets/{preset_id}")
async def delete_model_preset(preset_id: str):
    """删除模型预设配置"""
    try:
        service = get_model_presets_service()
        success = service.delete_preset(preset_id)

        if not success:
            raise HTTPException(status_code=404, detail=f"Preset '{preset_id}' not found")

        return {"success": True, "message": f"Deleted preset '{preset_id}'"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete preset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete preset: {str(e)}")


@router.get("/models/presets/default/current", response_model=ModelPresetResponse)
async def get_default_preset():
    """获取默认预设配置（不返回 API key）"""
    try:
        service = get_model_presets_service()
        preset = service.get_default_preset()

        if not preset:
            return ModelPresetResponse(
                success=False,
                message="No default preset configured"
            )

        # 隐藏 API key
        safe_preset = preset.model_copy()
        safe_preset.api_key = "***"

        return ModelPresetResponse(success=True, preset=safe_preset)
    except Exception as e:
        logger.error(f"Failed to get default preset: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get default preset: {str(e)}")
