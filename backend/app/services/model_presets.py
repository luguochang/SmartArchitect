"""
模型预设配置管理服务

支持保存多个 AI 模型配置（如"个人 Gemini"、"公司 OpenAI"等），
解决频繁替换 API Key 体验差的问题。
"""

import json
import os
from typing import List, Optional, Dict
from datetime import datetime
import logging

from app.models.schemas import ModelPreset, ModelPresetCreate, ModelPresetUpdate

logger = logging.getLogger(__name__)


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

    def _load_presets(self):
        """从 JSON 文件加载预设配置"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for preset_data in data.get("presets", []):
                        preset = ModelPreset(**preset_data)
                        self.presets[preset.id] = preset
                logger.info(f"Loaded {len(self.presets)} model presets from {self.config_file}")
            except Exception as e:
                logger.error(f"Failed to load presets from {self.config_file}: {e}")
                self.presets = {}
        else:
            logger.info(f"No existing presets file found at {self.config_file}, starting fresh")
            self.presets = {}

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


# 全局单例实例
_service_instance: Optional[ModelPresetsService] = None


def get_model_presets_service() -> ModelPresetsService:
    """获取模型预设服务单例"""
    global _service_instance
    if _service_instance is None:
        _service_instance = ModelPresetsService()
    return _service_instance
