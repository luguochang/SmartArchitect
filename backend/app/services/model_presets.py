"""
模型预设配置管理服务

支持保存多个 AI 模型配置（如"个人 Gemini"、"公司 OpenAI"等），
解决频繁替换 API Key 体验差的问题。
"""

import json
import os
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.models.schemas import ModelPreset, ModelPresetCreate, ModelPresetUpdate

logger = logging.getLogger(__name__)


DEFAULT_PROVIDER = "custom"
DEFAULT_API_KEY = "sk-a2c00860412445a39c7758a5fbffb890"
DEFAULT_BASE_URL = "https://www.right.codes/codex/v1"
DEFAULT_MODEL_NAME = "gpt-5.2"
DEFAULT_PRESET_ID = "default-right-codes"
DEFAULT_PRESET_NAME = "Default Right Codes"


class ModelPresetsService:
    """模型预设配置管理服务"""

    def __init__(self, config_file: str = "model_presets.json"):
        """初始化服务

        Args:
            config_file: 配置文件路径（默认为 backend 目录下）
        """
        # 配置文件保存在 backend 目录
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), config_file)
        self.presets: Dict[str, ModelPreset] = {}
        self._load_presets()
        self._ensure_default_preset()

    def _load_presets(self):
        """从 JSON 文件加载预设配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for preset_data in data.get("presets", []):
                        normalized = self._normalize_preset_data(preset_data)
                        preset = ModelPreset(**normalized)
                        self.presets[preset.id] = preset
                logger.info(f"Loaded {len(self.presets)} model presets from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load presets from {self.config_file}: {e}")
                self.presets = {}
        else:
            logger.info(f"No existing presets file found at {self.config_file}, starting fresh")
            self.presets = {}

    @staticmethod
    def _normalize_preset_data(preset_data: Dict[str, Any]) -> Dict[str, Any]:
        """兼容历史字段：api_base/model -> base_url/model_name。"""
        normalized = dict(preset_data)

        if not normalized.get("base_url") and normalized.get("api_base"):
            normalized["base_url"] = normalized.get("api_base")

        if not normalized.get("model_name") and normalized.get("model"):
            normalized["model_name"] = normalized.get("model")

        if not normalized.get("provider"):
            normalized["provider"] = DEFAULT_PROVIDER

        return normalized

    def _save_presets(self):
        """保存预设配置到 JSON 文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)

            data = {
                "presets": [preset.model_dump() for preset in self.presets.values()],
                "last_updated": datetime.now().isoformat()
            }

            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(self.presets)} presets to {self.config_file}")
        except Exception as e:
            logger.error(f"Failed to save presets to {self.config_file}: {e}")
            raise

    def list_presets(self) -> List[ModelPreset]:
        """列出所有预设配置（不返回敏感信息）"""
        # 返回副本，隐藏 API key
        safe_presets = []
        for preset in self.presets.values():
            safe_preset = preset.model_copy()
            safe_preset.api_key = "***" if safe_preset.api_key else ""
            safe_presets.append(safe_preset)

        return safe_presets

    def get_preset(self, preset_id: str, include_api_key: bool = True) -> Optional[ModelPreset]:
        """获取指定预设配置

        Args:
            preset_id: 预设ID
            include_api_key: 是否包含 API key（默认包含）

        Returns:
            ModelPreset 或 None
        """
        preset = self.presets.get(preset_id)
        if preset and not include_api_key:
            safe_preset = preset.model_copy()
            safe_preset.api_key = "***"
            return safe_preset
        return preset

    def create_preset(self, preset_data: ModelPresetCreate) -> ModelPreset:
        """创建新的预设配置

        Args:
            preset_data: 预设配置数据

        Returns:
            创建的 ModelPreset

        Raises:
            ValueError: 如果名称已存在
        """
        # 生成唯一 ID（基于名称和时间戳）
        import re
        base_id = re.sub(r'[^a-z0-9-]', '', preset_data.name.lower().replace(' ', '-'))
        preset_id = f"{base_id}-{int(datetime.now().timestamp())}"

        # 检查名称是否已存在
        for existing in self.presets.values():
            if existing.name == preset_data.name:
                raise ValueError(f"Preset with name '{preset_data.name}' already exists")

        # 如果设置为默认，取消其他配置的默认状态
        if preset_data.is_default:
            for preset in self.presets.values():
                preset.is_default = False

        # 创建新预设
        now = datetime.now().isoformat()
        preset = ModelPreset(
            id=preset_id,
            name=preset_data.name,
            provider=preset_data.provider,
            api_key=preset_data.api_key,
            model_name=preset_data.model_name,
            base_url=preset_data.base_url,
            is_default=preset_data.is_default,
            created_at=now,
            updated_at=now
        )

        self.presets[preset_id] = preset
        self._save_presets()

        logger.info(f"Created new preset: {preset.name} ({preset_id})")
        return preset

    def update_preset(self, preset_id: str, update_data: ModelPresetUpdate) -> Optional[ModelPreset]:
        """更新预设配置

        Args:
            preset_id: 预设ID
            update_data: 更新数据

        Returns:
            更新后的 ModelPreset 或 None

        Raises:
            ValueError: 如果名称已存在
        """
        preset = self.presets.get(preset_id)
        if not preset:
            return None

        # 检查名称冲突
        if update_data.name:
            for pid, existing in self.presets.items():
                if pid != preset_id and existing.name == update_data.name:
                    raise ValueError(f"Preset with name '{update_data.name}' already exists")

        # 如果设置为默认，取消其他配置的默认状态
        if update_data.is_default:
            for p in self.presets.values():
                p.is_default = False

        # 更新字段
        if update_data.name is not None:
            preset.name = update_data.name
        if update_data.api_key is not None:
            preset.api_key = update_data.api_key
        if update_data.model_name is not None:
            preset.model_name = update_data.model_name
        if update_data.base_url is not None:
            preset.base_url = update_data.base_url
        if update_data.is_default is not None:
            preset.is_default = update_data.is_default

        preset.updated_at = datetime.now().isoformat()

        self._save_presets()

        logger.info(f"Updated preset: {preset.name} ({preset_id})")
        return preset

    def delete_preset(self, preset_id: str) -> bool:
        """删除预设配置

        Args:
            preset_id: 预设ID

        Returns:
            是否成功删除
        """
        if preset_id in self.presets:
            preset_name = self.presets[preset_id].name
            del self.presets[preset_id]
            self._save_presets()
            logger.info(f"Deleted preset: {preset_name} ({preset_id})")
            return True
        return False

    def get_default_preset(self) -> Optional[ModelPreset]:
        """获取默认预设配置"""
        for preset in self.presets.values():
            if preset.is_default:
                return preset
        return None

    def _ensure_default_preset(self):
        """确保系统默认配置固定为 right.codes/gpt-5.2。"""
        now = datetime.now().isoformat()
        has_changes = False

        default_preset = self.presets.get(DEFAULT_PRESET_ID)
        if default_preset is None:
            default_preset = ModelPreset(
                id=DEFAULT_PRESET_ID,
                name=DEFAULT_PRESET_NAME,
                provider=DEFAULT_PROVIDER,
                api_key=DEFAULT_API_KEY,
                model_name=DEFAULT_MODEL_NAME,
                base_url=DEFAULT_BASE_URL,
                is_default=True,
                created_at=now,
                updated_at=now
            )
            self.presets[DEFAULT_PRESET_ID] = default_preset
            has_changes = True
        else:
            if default_preset.name != DEFAULT_PRESET_NAME:
                default_preset.name = DEFAULT_PRESET_NAME
                has_changes = True
            if default_preset.provider != DEFAULT_PROVIDER:
                default_preset.provider = DEFAULT_PROVIDER
                has_changes = True
            if default_preset.api_key != DEFAULT_API_KEY:
                default_preset.api_key = DEFAULT_API_KEY
                has_changes = True
            if default_preset.base_url != DEFAULT_BASE_URL:
                default_preset.base_url = DEFAULT_BASE_URL
                has_changes = True
            if default_preset.model_name != DEFAULT_MODEL_NAME:
                default_preset.model_name = DEFAULT_MODEL_NAME
                has_changes = True
            if not default_preset.created_at:
                default_preset.created_at = now
                has_changes = True
            if has_changes:
                default_preset.updated_at = now

        for preset_id, preset in self.presets.items():
            should_be_default = preset_id == DEFAULT_PRESET_ID
            if preset.is_default != should_be_default:
                preset.is_default = should_be_default
                has_changes = True

        if has_changes:
            self._save_presets()
            logger.info("Default preset enforced: %s (%s)", DEFAULT_MODEL_NAME, DEFAULT_BASE_URL)
        else:
            logger.info("Default preset already up-to-date")

    def get_active_config(self,
                         provider: Optional[str] = None,
                         api_key: Optional[str] = None,
                         base_url: Optional[str] = None,
                         model_name: Optional[str] = None,
                         api_base: Optional[str] = None,
                         model: Optional[str] = None) -> Optional[dict]:
        """获取有效的 AI 配置

        优先级：
        1. 如果提供了完整的参数，直接使用
        2. 否则使用默认预设配置

        Args:
            provider: AI 提供商
            api_key: API 密钥
            base_url: API 基础 URL
            model_name: 模型名称
            api_base: base_url 的兼容字段
            model: model_name 的兼容字段

        Returns:
            包含配置信息的字典，如果没有有效配置则返回 None
        """
        resolved_provider = provider or DEFAULT_PROVIDER
        resolved_base_url = base_url or api_base
        resolved_model_name = model_name or model

        if resolved_provider == "custom":
            resolved_base_url = resolved_base_url or DEFAULT_BASE_URL
            resolved_model_name = resolved_model_name or DEFAULT_MODEL_NAME

        # 如果提供了 api_key，优先使用传入的参数
        if api_key:
            return {
                "provider": resolved_provider,
                "api_key": api_key,
                "base_url": resolved_base_url,
                "model_name": resolved_model_name
            }

        # 否则尝试使用默认预设
        default_preset = self.get_default_preset()
        if default_preset:
            return {
                "provider": default_preset.provider,
                "api_key": default_preset.api_key,
                "base_url": default_preset.base_url,
                "model_name": default_preset.model_name
            }

        return {
            "provider": DEFAULT_PROVIDER,
            "api_key": DEFAULT_API_KEY,
            "base_url": DEFAULT_BASE_URL,
            "model_name": DEFAULT_MODEL_NAME
        }

    @staticmethod
    def _config_signature(config: Dict[str, Any]) -> tuple:
        return (
            (config.get("provider") or "").strip().lower(),
            (config.get("api_key") or "").strip(),
            (config.get("base_url") or "").strip(),
            (config.get("model_name") or "").strip(),
        )

    def list_full_runtime_configs(self) -> List[Dict[str, Any]]:
        """Return full runtime configs (including keys) for routing/failover."""
        configs: List[Dict[str, Any]] = []
        for preset in self.presets.values():
            if not preset.api_key:
                continue
            configs.append({
                "provider": preset.provider or DEFAULT_PROVIDER,
                "api_key": preset.api_key,
                "base_url": preset.base_url or None,
                "model_name": preset.model_name or None,
            })
        return configs

    def get_failover_configs(
        self,
        primary_config: Optional[Dict[str, Any]],
        max_candidates: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Build alternate configs for automatic failover.
        The primary config is excluded from returned candidates.
        """
        if max_candidates <= 0:
            return []

        primary_sig = self._config_signature(primary_config or {})
        seen = {primary_sig}
        candidates: List[Dict[str, Any]] = []

        for config in self.list_full_runtime_configs():
            sig = self._config_signature(config)
            if sig in seen:
                continue
            seen.add(sig)
            candidates.append(config)
            if len(candidates) >= max_candidates:
                break

        return candidates


# 全局单例实例
_service_instance: Optional[ModelPresetsService] = None


def get_model_presets_service() -> ModelPresetsService:
    """获取模型预设服务单例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ModelPresetsService()
    return _service_instance
