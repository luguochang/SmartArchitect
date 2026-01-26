"""
Model Presets Service - Manage AI model configurations
"""
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict
from datetime import datetime
from app.models.schemas import ModelPreset, ModelPresetCreate, ModelPresetUpdate

logger = logging.getLogger(__name__)


class ModelPresetsService:
    """Service for managing model preset configurations."""

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize service with optional storage path."""
        if storage_path is None:
            # Default storage in backend/data/model_presets.json
            self.storage_path = Path(__file__).parent.parent / "data" / "model_presets.json"
        else:
            self.storage_path = storage_path

        # Ensure directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # In-memory cache of presets
        self.presets: Dict[str, ModelPreset] = {}
        self._load_presets()

    def _load_presets(self):
        """Load presets from storage."""
        if not self.storage_path.exists():
            logger.info("No existing presets file found, starting with empty presets")
            self.presets = {}
            return

        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.presets = {
                    preset_id: ModelPreset(**preset_data)
                    for preset_id, preset_data in data.items()
                }
            logger.info(f"Loaded {len(self.presets)} model presets from {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to load presets: {e}")
            self.presets = {}

    def _save_presets(self):
        """Save presets to storage."""
        try:
            data = {
                preset_id: preset.model_dump()
                for preset_id, preset in self.presets.items()
            }
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved {len(self.presets)} presets to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save presets: {e}")
            raise

    def _generate_preset_id(self, name: str, provider: str) -> str:
        """Generate unique preset ID."""
        base_id = f"{provider}-{name}".lower().replace(" ", "-")
        preset_id = base_id
        counter = 1

        while preset_id in self.presets:
            preset_id = f"{base_id}-{counter}"
            counter += 1

        return preset_id

    def list_presets(self) -> List[ModelPreset]:
        """List all presets (without API keys)."""
        result = []
        for preset in self.presets.values():
            safe_preset = preset.model_copy()
            safe_preset.api_key = "***"
            result.append(safe_preset)
        return result

    def get_preset(self, preset_id: str, include_api_key: bool = False) -> Optional[ModelPreset]:
        """Get a specific preset by ID."""
        preset = self.presets.get(preset_id)
        if not preset:
            return None

        if include_api_key:
            return preset.model_copy()
        else:
            safe_preset = preset.model_copy()
            safe_preset.api_key = "***"
            return safe_preset

    def create_preset(self, preset_data: ModelPresetCreate) -> ModelPreset:
        """Create a new preset."""
        # Generate unique ID
        preset_id = self._generate_preset_id(preset_data.name, preset_data.provider)

        # If setting as default, unset other defaults
        if preset_data.is_default:
            for existing_preset in self.presets.values():
                existing_preset.is_default = False

        # Create preset
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
            updated_at=now,
        )

        self.presets[preset_id] = preset
        self._save_presets()

        logger.info(f"Created preset '{preset_id}' ({preset.name})")
        return preset

    def update_preset(self, preset_id: str, update_data: ModelPresetUpdate) -> Optional[ModelPreset]:
        """Update an existing preset."""
        preset = self.presets.get(preset_id)
        if not preset:
            return None

        # Update fields
        if update_data.name is not None:
            preset.name = update_data.name
        if update_data.api_key is not None:
            preset.api_key = update_data.api_key
        if update_data.model_name is not None:
            preset.model_name = update_data.model_name
        if update_data.base_url is not None:
            preset.base_url = update_data.base_url
        if update_data.is_default is not None:
            # If setting as default, unset other defaults
            if update_data.is_default:
                for existing_preset in self.presets.values():
                    if existing_preset.id != preset_id:
                        existing_preset.is_default = False
            preset.is_default = update_data.is_default

        preset.updated_at = datetime.now().isoformat()

        self._save_presets()
        logger.info(f"Updated preset '{preset_id}' ({preset.name})")
        return preset

    def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset."""
        if preset_id not in self.presets:
            return False

        del self.presets[preset_id]
        self._save_presets()
        logger.info(f"Deleted preset '{preset_id}'")
        return True

    def get_default_preset(self) -> Optional[ModelPreset]:
        """Get the default preset (if any)."""
        for preset in self.presets.values():
            if preset.is_default:
                return preset.model_copy()
        return None


# Singleton instance
_model_presets_service: Optional[ModelPresetsService] = None


def get_model_presets_service() -> ModelPresetsService:
    """Get or create the model presets service instance."""
    global _model_presets_service
    if _model_presets_service is None:
        _model_presets_service = ModelPresetsService()
    return _model_presets_service
