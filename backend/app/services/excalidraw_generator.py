import json
import logging
import random
import time
from typing import Optional

from app.models.schemas import ExcalidrawScene
from app.services.ai_vision import create_vision_service

logger = logging.getLogger(__name__)


class ExcalidrawGeneratorService:
    """Excalidraw scene generation via LLM with validation and mock fallback."""

    def _base_element(self, **kwargs):
        now = int(time.time() * 1000)
        base = {
            "id": f"{random.randint(1000,9999)}",
            "type": "rectangle",
            "x": 100,
            "y": 100,
            "width": 100,
            "height": 100,
            "angle": 0,
            "strokeColor": "#22d3ee",
            "backgroundColor": "transparent",
            "fillStyle": "solid",
            "strokeWidth": 2,
            "strokeStyle": "solid",
            "roughness": 1,
            "opacity": 100,
            "groupIds": [],
            "frameId": None,
            "roundness": None,
            "seed": random.randint(1, 10000000),
            "version": 1,
            "versionNonce": random.randint(1, 1000000000),
            "isDeleted": False,
            "boundElements": [],
            "updated": now,
            "link": None,
            "locked": False,
            "customData": None,
          }
        base.update(kwargs)
        return base

    def _build_prompt(self, prompt: str, style: Optional[str], width: int, height: int) -> str:
        theme = style or "neon cyber cat with glowing eyes, bold strokes, 8-color palette"
        return f"""
You are an Excalidraw scene generator. Return ONLY JSON with keys: elements (array), appState (object), files (object).

Rules:
- Canvas size hint: width={width}, height={height}, place content within x:[0,{width-200}], y:[0,{height-200}]
- Allowed element types: rectangle, ellipse, line, text (do NOT use freedraw/path unless absolutely needed)
- REQUIRED: use text labels to mark parts, e.g., "head", "ear", "eye", "body", "tail"
- For line include "points": [[x,y],...]
- Use strokeColor/backgroundColor from a fixed palette (max 6 colors): #22d3ee, #a855f7, #22c55e, #f97316, #eab308, #0ea5e9
- strokeWidth >= 3, opacity >= 60, avoid excessive transparency
- Limit elements to 20 max. Keep sizes between 40 and 200, avoid overlap
- appState may include viewBackgroundColor, scrollX, scrollY, zoom ({{"value":1}})
- Do NOT return markdown, backticks, or explanations.

Style: {theme}
User request: "{prompt}"

Return JSON only.
"""

    def _safe_json(self, payload):
        if payload is None:
            return {}
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, str):
            return json.loads(payload)
        if hasattr(payload, "model_dump"):
            return payload.model_dump()
        return json.loads(json.dumps(payload, default=str))

    def _validate_scene(self, ai_data: dict, width: int, height: int) -> ExcalidrawScene:
        elements = ai_data.get("elements", [])
        if not isinstance(elements, list):
            elements = []
        cleaned = []
        max_elems = 25
        for elem in elements[:max_elems]:
            if not isinstance(elem, dict):
                continue
            etype = elem.get("type") or "rectangle"
            if etype not in ["rectangle", "ellipse", "freedraw", "line", "text"]:
                continue
            # points required for line/freedraw
            if etype in ["line", "freedraw"] and not elem.get("points"):
                continue
            base = self._base_element(
                id=elem.get("id") or f"{random.randint(1000,9999)}",
                type=etype,
            )
            x = float(elem.get("x", base["x"]))
            y = float(elem.get("y", base["y"]))
            w = min(max(float(elem.get("width", base["width"])), 5), 400)
            h = min(max(float(elem.get("height", base["height"])), 5), 400)
            base["x"] = max(0, min(x, width - w))
            base["y"] = max(0, min(y, height - h))
            base["width"] = w
            base["height"] = h
            base["strokeColor"] = elem.get("strokeColor", base["strokeColor"])
            base["backgroundColor"] = elem.get("backgroundColor", base["backgroundColor"])
            base["fillStyle"] = elem.get("fillStyle", base["fillStyle"])
            base["strokeWidth"] = max(3, elem.get("strokeWidth", base["strokeWidth"]))
            base["strokeStyle"] = elem.get("strokeStyle", base["strokeStyle"])
            base["roughness"] = elem.get("roughness", base["roughness"])
            base["opacity"] = max(60, elem.get("opacity", base["opacity"]))
            if etype in ["line", "freedraw"]:
                base["points"] = elem.get("points")
            if etype == "text":
                base["text"] = elem.get("text") or "Label"
                base["fontSize"] = elem.get("fontSize", 20)
                base["fontFamily"] = elem.get("fontFamily", 1)
                base["textAlign"] = elem.get("textAlign", "center")
            cleaned.append(base)
        app_state = ai_data.get("appState") or {}
        files = ai_data.get("files") or {}
        app_state.setdefault("viewBackgroundColor", "#0f172a")
        app_state.setdefault("zoom", {"value": 1})
        return ExcalidrawScene(elements=cleaned, appState=app_state, files=files)

    def _mock_scene(self) -> ExcalidrawScene:
        # simple fallback: neon cat face
        face = self._base_element(
            id="cat-face",
            type="ellipse",
            x=200,
            y=200,
            width=260,
            height=220,
            strokeColor="#a855f7",
            backgroundColor="rgba(168,85,247,0.15)",
            roughness=1,
            strokeWidth=3,
          )
        ear_left = self._base_element(id="cat-ear-left", type="rectangle", x=210, y=140, width=70, height=70, strokeColor="#22d3ee", backgroundColor="rgba(34,211,238,0.2)")
        ear_right = self._base_element(id="cat-ear-right", type="rectangle", x=330, y=140, width=70, height=70, strokeColor="#22d3ee", backgroundColor="rgba(34,211,238,0.2)")
        eye_left = self._base_element(id="cat-eye-left", type="ellipse", x=250, y=250, width=40, height=50, strokeColor="#22c55e", backgroundColor="rgba(34,197,94,0.4)")
        eye_right = self._base_element(id="cat-eye-right", type="ellipse", x=330, y=250, width=40, height=50, strokeColor="#22c55e", backgroundColor="rgba(34,197,94,0.4)")
        nose = self._base_element(id="cat-nose", type="ellipse", x=300, y=310, width=22, height=16, strokeColor="#f59e0b", backgroundColor="rgba(245,158,11,0.7)")
        whisker_left = self._base_element(id="whisker-left", type="line", x=240, y=320, width=60, height=1, points=[[0,0],[60,-8]], strokeColor="#cbd5e1", backgroundColor="transparent")
        whisker_left2 = self._base_element(id="whisker-left-2", type="line", x=240, y=330, width=60, height=1, points=[[0,0],[60,8]], strokeColor="#cbd5e1", backgroundColor="transparent")
        whisker_right = self._base_element(id="whisker-right", type="line", x=340, y=320, width=60, height=1, points=[[0,0],[-60,-8]], strokeColor="#cbd5e1", backgroundColor="transparent")
        whisker_right2 = self._base_element(id="whisker-right-2", type="line", x=340, y=330, width=60, height=1, points=[[0,0],[-60,8]], strokeColor="#cbd5e1", backgroundColor="transparent")
        elements = [face, ear_left, ear_right, eye_left, eye_right, nose, whisker_left, whisker_left2, whisker_right, whisker_right2]
        app_state = {
            "viewBackgroundColor": "#0f172a",
            "currentItemStrokeColor": "#22d3ee",
            "currentItemBackgroundColor": "transparent",
            "currentItemFillStyle": "hachure",
            "currentItemStrokeWidth": 3,
            "currentItemRoughness": 1,
            "scrollX": 0,
            "scrollY": 0,
            "zoom": {"value": 1},
            "message": "mock fallback",
        }
        return ExcalidrawScene(elements=elements, appState=app_state, files={})

    async def generate_scene(
        self,
        prompt: str,
        style: Optional[str] = None,
        width: int = 1200,
        height: int = 800,
        provider: str = "siliconflow",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> ExcalidrawScene:
        """Generate scene via LLM with fallback to mock."""
        try:
            vision_service = create_vision_service(
                provider=provider,
                api_key=api_key,
                base_url=base_url,
                model_name=model_name,
            )
            # Excalidraw scenes may need more time; bump timeout to 45s if lower
            try:
                if hasattr(vision_service, "request_timeout"):
                    # SiliconFlow + large vision models can take longer; allow up to 120s
                    vision_service.request_timeout = max(
                        getattr(vision_service, "request_timeout", 8.0),
                        180.0,
                    )
            except Exception:
                pass

            system_prompt = self._build_prompt(prompt, style, width, height)

            if provider == "gemini":
                ai_raw = await vision_service._analyze_with_gemini_text(system_prompt)
            elif provider == "openai":
                ai_raw = await vision_service._analyze_with_openai_text(system_prompt)
            elif provider == "claude":
                ai_raw = await vision_service._analyze_with_claude_text(system_prompt)
            elif provider == "siliconflow":
                # Streaming was slow/unreliable in testing; prefer single non-stream call
                try:
                    ai_raw = await vision_service._analyze_with_siliconflow_text(system_prompt)
                except Exception:
                    # Fallback to a smaller, more JSON-stable model if provided model struggles
                    backup = "Qwen/Qwen2.5-14B-Instruct"
                    logger.warning("Primary SiliconFlow model failed; retrying with %s", backup)
                    vision_service.model_name = backup
                    ai_raw = await vision_service._analyze_with_siliconflow_text(system_prompt)
            else:
                ai_raw = await vision_service._analyze_with_custom_text(system_prompt)
            ai_data = self._safe_json(ai_raw)
            scene = self._validate_scene(ai_data, width, height)
            scene.appState["message"] = f"Generated via {provider}"
            if not scene.elements:
                raise ValueError("Empty scene")
            return scene
        except Exception as e:
            logger.error(f"LLM scene generation failed: {e}", exc_info=True)
            mock_scene = self._mock_scene()
            mock_scene.appState["message"] = f"Fallback mock: {e}"
            return mock_scene


def create_excalidraw_service() -> ExcalidrawGeneratorService:
    return ExcalidrawGeneratorService()
