import json
import logging
import random
import time
from typing import Optional

from app.models.schemas import ExcalidrawScene
from app.services.ai_vision import create_vision_service

logger = logging.getLogger(__name__)


def repair_json(json_str: str) -> str:
    """
    Repair incomplete JSON by tracking bracket/brace stack and closing open structures.
    Based on FlowPilot's json-repair.ts implementation.

    Args:
        json_str: Potentially incomplete JSON string

    Returns:
        Repaired JSON string with closed brackets/braces
    """
    if not json_str:
        return "{}"

    trimmed = json_str.strip()
    if trimmed.endswith("}"):
        return trimmed  # Assume complete

    # Track bracket/brace stack
    stack = []
    is_string = False
    is_escaped = False

    for char in trimmed:
        if is_string:
            if char == '"' and not is_escaped:
                is_string = False
            elif char == '\\':
                is_escaped = not is_escaped
            else:
                is_escaped = False
        else:
            if char == '"':
                is_string = True
            elif char == '{':
                stack.append('}')
            elif char == '[':
                stack.append(']')
            elif char == '}':
                if stack and stack[-1] == '}':
                    stack.pop()
            elif char == ']':
                if stack and stack[-1] == ']':
                    stack.pop()

    # Build completion string
    completion = ""
    if is_string:
        completion += '"'  # Close open string
    while stack:
        completion += stack.pop()

    return trimmed + completion


def safe_parse_partial_json(json_str: str) -> Optional[dict]:
    """
    Safely parse potentially incomplete JSON with automatic repair.

    Args:
        json_str: JSON string (may be incomplete)

    Returns:
        Parsed dict or None if unrepairable
    """
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        try:
            repaired = repair_json(json_str)
            return json.loads(repaired)
        except Exception as e:
            logger.debug(f"JSON repair failed: {e}")
            return None


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
        """
        Build Excalidraw generation prompt - inspired by FlowPilot's concise approach.
        Simple, clear instructions lead to more stable AI output.
        """
        return f"""You are an Excalidraw expert. Produce a finished, readable diagram as pure JSON (no prose).

OUTPUT FORMAT (must be valid JSON):
{{
  "elements": [...],
  "appState": {{}},
  "files": {{}}
}}

CRITICAL RULES:
1) For "line"/"arrow": include "points" (e.g. [[0,0],[50,50]]) and set "startArrowhead"/"endArrowhead" when directional.
2) Every element must have: id (string), type, x, y, width, height, angle, strokeColor, backgroundColor, fillStyle, strokeWidth, strokeStyle, roughness, opacity, groupIds (array), boundElements (array), seed, version, versionNonce, isDeleted=false.
3) Use "arrow" to connect shapes; prefer "text" for labels (include "text", "fontSize", "textAlign").
4) Do NOT return images/icons; use basic shapes and arrows only. Ensure the JSON is closed (ends with "}}").

REQUIRED ELEMENT MIX:
- Total 28-84 elements depending on complexity.
- At least 12 shape nodes (rectangle/ellipse/diamond) for the main content.
- At least 14 connectors (arrow/line) linking the shapes into a complete flow.
- Ensure every major shape participates in at least one incoming or outgoing connector.
- Use 6-14 text labels to annotate decisions, branches, critical paths, and failure handling.
- For complex requests, include at least 1-2 branch merges and at least 1 loop-back connector.
- Output elements in this order: (1) core shapes, (2) connectors, (3) text labels.

LAYOUT:
- Canvas: {width}x{height}px. Keep a 40px margin; avoid overlap; distribute nodes evenly left-to-right/top-to-bottom.
- If request is "complex" or "production-level", use at least 75% of canvas area.
- Make connectors clean and direct; avoid zero-length points.

STYLE (hand-drawn):
- strokeColor: choose from ["#1e1e1e","#2563eb","#dc2626","#059669"]
- backgroundColor: choose from ["transparent","#a5d8ff","#fde68a","#bbf7d0"]
- fillStyle: "hachure" or "solid"; roughness: 1 for sketch feel; strokeWidth: 2.
- Use compact JSON (minimal whitespace) and short element ids to reduce streaming latency.

USER REQUEST: "{prompt}"

Return ONLY the JSON structure above. Generate the full set of elements; do not stop early."""

    def _safe_json(self, payload):
        """
        Sanitize AI response into valid JSON dict with FlowPilot-inspired simple strategy.

        Strategy:
        1. Extract JSON from markdown code blocks or find { } boundaries
        2. Try direct parsing
        3. If failed, use simple bracket tracking repair (FlowPilot method)
        4. If still failed, return None to trigger mock scene fallback

        This simplified approach is more reliable than aggressive multi-strategy repair.
        """
        if payload is None:
            return None
        if isinstance(payload, dict):
            return payload
        if hasattr(payload, "model_dump"):
            return payload.model_dump()

        if isinstance(payload, str):
            text = payload.strip()
            import re

            # Step 1: Extract from markdown code block if present
            code_block_match = re.search(r'```(?:json)?\s*\n?([^`]*?)(?:```|$)', text, re.IGNORECASE | re.DOTALL)
            if code_block_match:
                text = code_block_match.group(1).strip()

            # Step 2: Find JSON object boundaries { ... }
            if not text.startswith("{"):
                start_idx = text.find("{")
                if start_idx >= 0:
                    text = text[start_idx:]
                else:
                    logger.warning("No JSON object found in payload")
                    return None

            # Find last closing brace (simple heuristic)
            if not text.endswith("}"):
                end_idx = text.rfind("}")
                if end_idx > 0:
                    text = text[:end_idx+1]

            # Step 3: Try direct parsing (fast path)
            try:
                result = json.loads(text)
                logger.debug("JSON parsed successfully without repair")
                return result
            except json.JSONDecodeError as e:
                logger.info(f"JSON parse failed: {e}. Attempting simple repair...")

            # Step 4: Use FlowPilot's simple bracket tracking repair
            repaired_result = safe_parse_partial_json(text)
            if repaired_result is not None:
                logger.info("JSON repaired successfully with FlowPilot bracket tracking")
                return repaired_result

            # Step 5: One additional strategy - fix missing commas between array elements
            # This is a common AI mistake: } { without comma
            if "Expecting ',' delimiter" in str(e):
                text_with_commas = re.sub(r'}\s+{', '}, {', text)
                text_with_commas = re.sub(r'}\n\s*{', '},\n{', text_with_commas)

                repaired_result = safe_parse_partial_json(text_with_commas)
                if repaired_result is not None:
                    logger.info("JSON repaired by fixing missing commas")
                    return repaired_result

            # Final fallback: Log and return None to trigger mock scene
            logger.warning(f"All JSON repair strategies failed. Payload length: {len(payload)}")
            logger.debug(f"First 300 chars: {payload[:300]}")
            logger.debug(f"Last 300 chars: {payload[-300:]}")
            return None

        # Last resort for non-string types
        try:
            return json.loads(json.dumps(payload, default=str))
        except Exception as ex:
            logger.error(f"Failed to convert payload to JSON: {ex}")
            return None

    def _validate_scene(self, ai_data: dict, width: int, height: int) -> ExcalidrawScene:
        """
        Validate and clean Excalidraw scene data.

        Returns a professional fallback scene if input is invalid or unusable.
        """
        if ai_data is None or not isinstance(ai_data, dict):
            logger.warning("Invalid ai_data provided to _validate_scene, returning fallback scene")
            return self._mock_scene()

        elements = ai_data.get("elements", [])
        if not isinstance(elements, list):
            elements = []

        cleaned = []
        max_elems = 120  # keep larger diagrams from being truncated
        seen_ids = set()
        allowed_types = {"rectangle", "ellipse", "diamond", "freedraw", "line", "arrow", "text"}

        for elem in elements[:max_elems]:
            if not isinstance(elem, dict):
                logger.warning("Skipping non-dict element: %s", type(elem))
                continue

            etype = elem.get("type")
            elem_id = elem.get("id")
            if not isinstance(etype, str) or not isinstance(elem_id, str):
                logger.warning(
                    "Skipping element with invalid type/id: type=%s, id=%s",
                    type(etype),
                    type(elem_id),
                )
                continue

            if elem_id in seen_ids:
                logger.warning("Duplicate element id detected: %s, regenerating", elem_id)
                elem_id = f"{elem_id}-{random.randint(1000,9999)}"
            seen_ids.add(elem_id)

            if etype not in allowed_types:
                logger.warning("Skipping unsupported element type: %s", etype)
                continue

            if etype in {"line", "arrow", "draw", "freedraw"}:
                points = elem.get("points", [])
                if not isinstance(points, list) or len(points) == 0:
                    logger.warning("Skipping %s element '%s' without points array", etype, elem_id)
                    continue
                valid_points = all(
                    isinstance(p, list)
                    and len(p) >= 2
                    and isinstance(p[0], (int, float))
                    and isinstance(p[1], (int, float))
                    for p in points
                )
                if not valid_points:
                    logger.warning("Skipping %s element '%s' with invalid points format", etype, elem_id)
                    continue

            if etype == "text" and not isinstance(elem.get("text"), str):
                logger.warning("Skipping text element '%s' without text property", elem_id)
                continue

            logger.debug("Validated element '%s' (type: %s)", elem_id, etype)
            base = self._base_element(id=elem_id, type=etype)

            if etype in {"line", "arrow", "freedraw"}:
                points = elem.get("points", [])
                xs = [float(p[0]) for p in points]
                ys = [float(p[1]) for p in points]
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)

                original_x = float(elem.get("x", 100))
                original_y = float(elem.get("y", 100))
                normalized_x = original_x + min_x
                normalized_y = original_y + min_y
                normalized_points = [[x - min_x, y - min_y] for x, y in points]

                w = max(max_x - min_x, 1)
                h = max(max_y - min_y, 1)
                base["x"] = max(0, min(normalized_x, width - w))
                base["y"] = max(0, min(normalized_y, height - h))
                base["width"] = w
                base["height"] = h
                base["points"] = normalized_points

                if etype == "arrow":
                    if isinstance(elem.get("startBinding"), dict):
                        base["startBinding"] = elem["startBinding"]
                    if isinstance(elem.get("endBinding"), dict):
                        base["endBinding"] = elem["endBinding"]
            else:
                x = float(elem.get("x", base["x"]))
                y = float(elem.get("y", base["y"]))
                w = min(max(float(elem.get("width", base["width"])), 5), 400)
                h = min(max(float(elem.get("height", base["height"])), 5), 400)
                base["x"] = max(0, min(x, width - w))
                base["y"] = max(0, min(y, height - h))
                base["width"] = w
                base["height"] = h

            if isinstance(elem.get("strokeColor"), str):
                base["strokeColor"] = elem["strokeColor"]
            if isinstance(elem.get("backgroundColor"), str):
                base["backgroundColor"] = elem["backgroundColor"]
            if isinstance(elem.get("fillStyle"), str):
                base["fillStyle"] = elem["fillStyle"]
            if isinstance(elem.get("strokeWidth"), (int, float)):
                base["strokeWidth"] = max(1, float(elem["strokeWidth"]))
            if isinstance(elem.get("strokeStyle"), str):
                base["strokeStyle"] = elem["strokeStyle"]
            if isinstance(elem.get("roughness"), (int, float)):
                base["roughness"] = float(elem["roughness"])
            if isinstance(elem.get("opacity"), (int, float)):
                base["opacity"] = max(0, min(100, float(elem["opacity"])))
            if isinstance(elem.get("angle"), (int, float)):
                base["angle"] = float(elem["angle"])

            if etype == "text":
                base["text"] = elem.get("text", "Label")
                if isinstance(elem.get("fontSize"), (int, float)):
                    base["fontSize"] = int(elem["fontSize"])
                else:
                    base["fontSize"] = 20
                base["fontFamily"] = elem.get("fontFamily", 1)
                base["textAlign"] = elem.get("textAlign", "center")

            if not isinstance(base.get("groupIds"), list):
                base["groupIds"] = []
            if not isinstance(base.get("boundElements"), list):
                base["boundElements"] = []

            cleaned.append(base)

        if not cleaned:
            logger.warning(
                "No valid elements after cleaning (started with %s raw elements), returning fallback scene",
                len(elements),
            )
            mock = self._mock_scene()
            mock.appState["message"] = "AI generated invalid elements, showing fallback scene"
            return mock

        logger.info(
            "Validation complete: %s/%s elements passed (filtered %s)",
            len(cleaned),
            len(elements[:max_elems]),
            len(elements[:max_elems]) - len(cleaned),
        )

        app_state = ai_data.get("appState") or {}
        if not isinstance(app_state, dict):
            app_state = {}
        app_state.pop("collaborators", None)
        app_state.setdefault("zoom", {"value": 1})

        files = ai_data.get("files") or {}
        if not isinstance(files, dict):
            files = {}

        return ExcalidrawScene(elements=cleaned, appState=app_state, files=files)

    def _mock_scene(self) -> ExcalidrawScene:
        """Professional fallback scene used when AI output is invalid."""
        start = self._base_element(
            id="fallback-start",
            type="ellipse",
            x=120,
            y=280,
            width=90,
            height=90,
            strokeColor="#2563eb",
            backgroundColor="#dbeafe",
            strokeWidth=2,
        )
        process = self._base_element(
            id="fallback-process",
            type="rectangle",
            x=300,
            y=280,
            width=220,
            height=90,
            strokeColor="#1f2937",
            backgroundColor="#f3f4f6",
            strokeWidth=2,
        )
        decision = self._base_element(
            id="fallback-decision",
            type="diamond",
            x=610,
            y=255,
            width=140,
            height=140,
            strokeColor="#b45309",
            backgroundColor="#fef3c7",
            strokeWidth=2,
        )
        end = self._base_element(
            id="fallback-end",
            type="ellipse",
            x=860,
            y=280,
            width=90,
            height=90,
            strokeColor="#059669",
            backgroundColor="#d1fae5",
            strokeWidth=2,
        )
        a1 = self._base_element(
            id="fallback-arrow-1",
            type="arrow",
            x=210,
            y=325,
            width=90,
            height=1,
            points=[[0, 0], [90, 0]],
            endArrowhead="arrow",
            strokeColor="#1f2937",
            backgroundColor="transparent",
            strokeWidth=2,
        )
        a2 = self._base_element(
            id="fallback-arrow-2",
            type="arrow",
            x=520,
            y=325,
            width=90,
            height=1,
            points=[[0, 0], [90, 0]],
            endArrowhead="arrow",
            strokeColor="#1f2937",
            backgroundColor="transparent",
            strokeWidth=2,
        )
        a3 = self._base_element(
            id="fallback-arrow-3",
            type="arrow",
            x=750,
            y=325,
            width=110,
            height=1,
            points=[[0, 0], [110, 0]],
            endArrowhead="arrow",
            strokeColor="#1f2937",
            backgroundColor="transparent",
            strokeWidth=2,
        )

        labels = [
            self._base_element(id="fallback-text-start", type="text", x=145, y=314, width=40, height=24, text="Start", fontSize=20),
            self._base_element(id="fallback-text-process", type="text", x=342, y=314, width=140, height=24, text="Process", fontSize=20),
            self._base_element(id="fallback-text-decision", type="text", x=642, y=314, width=80, height=24, text="Decision", fontSize=20),
            self._base_element(id="fallback-text-end", type="text", x=892, y=314, width=30, height=24, text="End", fontSize=20),
        ]

        elements = [start, process, decision, end, a1, a2, a3, *labels]
        app_state = {
            "currentItemStrokeColor": "#1f2937",
            "currentItemBackgroundColor": "transparent",
            "currentItemFillStyle": "hachure",
            "currentItemStrokeWidth": 2,
            "currentItemRoughness": 1,
            "scrollX": 0,
            "scrollY": 0,
            "zoom": {"value": 1},
            "message": "fallback scene",
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
        """Generate scene via LLM with fallback to mock (no upstream stack for callers)."""
        try:
            vision_service = create_vision_service(
                provider=provider,
                api_key=api_key,
                base_url=base_url,
                model_name=model_name,
            )
            # Excalidraw scenes may need more time; bump timeout to 180s
            try:
                if hasattr(vision_service, "request_timeout"):
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

            # Update message based on whether it's a fallback
            current_message = scene.appState.get("message", "")
            if "fallback" not in current_message.lower() and "mock" not in current_message.lower():
                scene.appState["message"] = f"Generated via {provider}"

            # Scene is guaranteed to have elements now (either AI or mock)
            return scene
        except Exception as e:
            logger.error(f"Excalidraw generation failed: {e}", exc_info=True)
            # Return mock scene with error message instead of propagating stack
            mock_scene = self._mock_scene()
            mock_scene.appState["message"] = f"Fallback mock: {str(e)[:120]}"
            return mock_scene


def create_excalidraw_service() -> ExcalidrawGeneratorService:
    return ExcalidrawGeneratorService()



