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
        Build Excalidraw generation prompt - balanced between quality and parsability.
        """
        return f"""
You are an Excalidraw Expert. Generate a COMPLETE hand-drawn style diagram based on the user's request.

CRITICAL OUTPUT FORMAT:
- Output ONLY valid JSON (no markdown fences, no explanations, no truncation)
- Start directly with {{ and end with }}
- Use proper commas between all array elements and properties
- NO trailing commas
- IMPORTANT: Generate the COMPLETE JSON structure - do NOT stop mid-generation

Required JSON structure (MUST be complete):
{{
  "elements": [...],
  "appState": {{"viewBackgroundColor": "#ffffff"}},
  "files": {{}}
}}

Element Requirements:
- Create 10-15 elements for rich, complete diagrams (use rectangles, ellipses, arrows, lines, text)
- Each element MUST have ALL these fields (no shortcuts):
  id, type, x, y, width, height, angle, strokeColor, backgroundColor,
  fillStyle, strokeWidth, strokeStyle, roughness, opacity, groupIds,
  frameId, roundness, seed, version, versionNonce, isDeleted,
  boundElements, updated, link, locked

- For arrows/lines, add: points (array of [x,y]), startBinding, endBinding
- For text elements, add: text, fontSize, fontFamily, textAlign, verticalAlign, baseline, containerId, originalText

Valid types: rectangle, diamond, ellipse, arrow, line, text

Layout Guidelines:
- Canvas size: {width}x{height}px
- Place elements within x:[100,{width-100}], y:[100,{height-100}]
- Distribute elements evenly across the canvas
- Use arrows to connect related shapes
- Add labels with text elements for clarity

Colors (hand-drawn style):
- strokeColor: "#1e1e1e", "#2563eb", "#dc2626", "#059669", "#8b5cf6"
- backgroundColor: "#a5d8ff", "#fde68a", "#bbf7d0", "#ddd6fe", "transparent"
- fillStyle: "hachure" or "solid"
- roughness: 1 (hand-drawn) or 0 (smooth)

User request: "{prompt}"

CRITICAL: Generate the COMPLETE JSON now. Make sure to close all arrays and objects properly. Do NOT stop mid-generation.
Output format: raw JSON only (no markdown fences, no ```json, just {{ ... }}):"""

    def _safe_json(self, payload):
        """Sanitize AI response into valid JSON dict with aggressive cleaning."""
        if payload is None:
            return {}
        if isinstance(payload, dict):
            return payload
        if hasattr(payload, "model_dump"):
            return payload.model_dump()

        if isinstance(payload, str):
            # FlowPilot-inspired code block extraction using regex
            text = payload.strip()

            # Extract from markdown code block if present (more robust than line-by-line)
            import re
            code_block_match = re.search(r'```(?:json)?\s*\n?([^`]*?)(?:```|$)', text, re.IGNORECASE | re.DOTALL)
            if code_block_match:
                text = code_block_match.group(1).strip()

            # If not in code block, find JSON object boundaries
            if not text.startswith("{"):
                start_idx = text.find("{")
                if start_idx >= 0:
                    text = text[start_idx:]

            # Find last closing brace
            if not text.endswith("}"):
                end_idx = text.rfind("}")
                if end_idx > 0:
                    text = text[:end_idx+1]

            # Try parsing as-is
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode failed: {e}. Attempting repair...")

                # Strategy 0: Use FlowPilot-inspired bracket tracking repair FIRST
                # This handles incomplete/unclosed JSON from streaming
                repaired_result = safe_parse_partial_json(text)
                if repaired_result is not None:
                    logger.info("JSON repaired successfully with bracket tracking")
                    return repaired_result

                # Strategy 1: Aggressive comma insertion for "} {" patterns
                # Common when AI forgets commas between array elements
                if "Expecting ',' delimiter" in str(e):
                    import re
                    # Fix missing commas between array elements: } { → }, {
                    text_with_commas = re.sub(r'}\s+{', '}, {', text)
                    # Fix missing commas between array items: }\n{ → },\n{
                    text_with_commas = re.sub(r'}\n\s*{', '},\n{', text_with_commas)
                    # Fix missing commas between properties: "key": value "key2" → "key": value, "key2"
                    text_with_commas = re.sub(r'"\s*\n\s*"', '",\n"', text_with_commas)
                    text_with_commas = re.sub(r'(\d+)\s+(")', r'\1, \2', text_with_commas)
                    text_with_commas = re.sub(r'(true|false|null)\s+(")', r'\1, \2', text_with_commas)

                    try:
                        result = json.loads(text_with_commas)
                        logger.info("JSON repaired by inserting commas via regex")
                        return result
                    except json.JSONDecodeError:
                        # Try bracket tracking on the comma-fixed version
                        repaired_result = safe_parse_partial_json(text_with_commas)
                        if repaired_result is not None:
                            logger.info("JSON repaired by combining comma fix + bracket tracking")
                            return repaired_result

                # Strategy 2: Find the last valid closing brace for "elements" array
                # Many LLMs fail mid-generation, leaving incomplete JSON
                try:
                    # Find where "elements" array ends
                    elements_start = text.find('"elements"')
                    if elements_start > 0:
                        # Find the closing ] after elements array
                        bracket_count = 0
                        elements_end = -1
                        in_elements = False
                        for i in range(elements_start, len(text)):
                            if text[i] == '[':
                                in_elements = True
                                bracket_count += 1
                            elif text[i] == ']':
                                bracket_count -= 1
                                if bracket_count == 0 and in_elements:
                                    elements_end = i
                                    break

                        if elements_end > 0:
                            # Reconstruct JSON with valid closure
                            truncated = text[:elements_end+1] + '], "appState": {}, "files": {}}'
                            return json.loads(truncated)
                except Exception:
                    pass

                # Strategy 3: Fix common JSON syntax errors
                try:
                    # Remove newlines that might break parsing
                    text_normalized = text.replace("\n", " ")

                    # Fix missing commas between object properties
                    # Pattern: "key": value "key2": value2  →  "key": value, "key2": value2
                    import re
                    text_normalized = re.sub(r'"\s*"', '", "', text_normalized)

                    # Fix missing commas between array elements
                    # Pattern: } {  →  }, {
                    text_normalized = re.sub(r'\}\s*\{', '}, {', text_normalized)

                    # Fix trailing commas
                    text_normalized = text_normalized.replace(",]", "]").replace(",}", "}")

                    # Fix single quotes
                    text_normalized = text_normalized.replace("'", '"')

                    return json.loads(text_normalized)
                except json.JSONDecodeError:
                    pass

                # Strategy 4: Last resort - extract elements array only
                try:
                    elements_match = re.search(r'"elements"\s*:\s*\[(.*?)\]', text, re.DOTALL)
                    if elements_match:
                        elements_text = elements_match.group(1)
                        # Try to build a minimal valid JSON
                        reconstructed = f'{{"elements": [{elements_text}], "appState": {{}}, "files": {{}}}}'
                        return json.loads(reconstructed)
                except Exception:
                    pass

                # Log full payload for debugging
                logger.error(f"All JSON repair strategies failed. Payload length: {len(payload)}")
                logger.error(f"First 500 chars: {payload[:500]}")
                logger.error(f"Last 500 chars: {payload[-500:]}")

                # Return None to trigger fallback to mock scene
                # DO NOT return empty dict as it will cause downstream issues
                return None

        # Last resort: convert to JSON string and parse
        try:
            return json.loads(json.dumps(payload, default=str))
        except Exception:
            return {}

    def _validate_scene(self, ai_data: dict, width: int, height: int) -> ExcalidrawScene:
        """
        Validate and clean Excalidraw scene data with deep element validation.
        Based on FlowPilot's sanitizeData implementation.

        Returns mock scene if ai_data is None or invalid.
        """
        # Handle None or invalid input - return mock scene immediately
        if ai_data is None or not isinstance(ai_data, dict):
            logger.warning("Invalid ai_data provided to _validate_scene, returning mock scene")
            return self._mock_scene()

        elements = ai_data.get("elements", [])
        if not isinstance(elements, list):
            elements = []

        cleaned = []
        max_elems = 25
        seen_ids = set()  # Track unique IDs

        for elem in elements[:max_elems]:
            # Deep validation: filter out invalid elements
            if not isinstance(elem, dict):
                logger.debug(f"Skipping non-dict element: {type(elem)}")
                continue

            # Type and ID must be strings (MANDATORY)
            etype = elem.get("type")
            elem_id = elem.get("id")
            if not isinstance(etype, str) or not isinstance(elem_id, str):
                logger.debug(f"Skipping element with invalid type/id: type={type(etype)}, id={type(elem_id)}")
                continue

            # Ensure ID uniqueness
            if elem_id in seen_ids:
                logger.warning(f"Duplicate ID detected: {elem_id}, regenerating...")
                elem_id = f"{elem_id}-{random.randint(1000,9999)}"
            seen_ids.add(elem_id)

            # Validate element type
            if etype not in ["rectangle", "ellipse", "diamond", "freedraw", "line", "arrow", "text"]:
                logger.debug(f"Skipping unsupported element type: {etype}")
                continue

            # CRITICAL: Linear elements MUST have valid points array
            if etype in ["line", "arrow", "draw", "freedraw"]:
                points = elem.get("points", [])
                if not isinstance(points, list) or len(points) == 0:
                    logger.debug(f"Skipping {etype} element without points array")
                    continue

                # Validate each point is [number, number] format
                are_points_valid = all(
                    isinstance(p, list) and len(p) >= 2 and
                    isinstance(p[0], (int, float)) and isinstance(p[1], (int, float))
                    for p in points
                )
                if not are_points_valid:
                    logger.debug(f"Skipping {etype} with invalid points format")
                    continue

            # Text elements MUST have text property
            if etype == "text":
                if not isinstance(elem.get("text"), str):
                    logger.debug(f"Skipping text element without text property")
                    continue

            # Create base element with defaults
            base = self._base_element(
                id=elem_id,
                type=etype,
            )

            # For line/arrow elements, normalize points
            if etype in ["line", "arrow", "freedraw"]:
                points = elem.get("points", [])
                if points:
                    # Normalize line: calculate bounding box and adjust coordinates
                    xs = [float(p[0]) for p in points]
                    ys = [float(p[1]) for p in points]
                    min_x, max_x = min(xs), max(xs)
                    min_y, max_y = min(ys), max(ys)

                    # Adjust x,y to top-left, shift points to be relative
                    original_x = float(elem.get("x", 100))
                    original_y = float(elem.get("y", 100))
                    normalized_x = original_x + min_x
                    normalized_y = original_y + min_y
                    normalized_points = [[x - min_x, y - min_y] for x, y in points]

                    # Width/height from bounding box
                    w = max(max_x - min_x, 1)
                    h = max(max_y - min_y, 1)

                    base["x"] = max(0, min(normalized_x, width - w))
                    base["y"] = max(0, min(normalized_y, height - h))
                    base["width"] = w
                    base["height"] = h
                    base["points"] = normalized_points

                    # Arrow-specific properties
                    if etype == "arrow":
                        if "startBinding" in elem and isinstance(elem["startBinding"], dict):
                            base["startBinding"] = elem["startBinding"]
                        if "endBinding" in elem and isinstance(elem["endBinding"], dict):
                            base["endBinding"] = elem["endBinding"]
                else:
                    continue  # Skip invalid line without points
            else:
                # Regular element handling
                x = float(elem.get("x", base["x"]))
                y = float(elem.get("y", base["y"]))
                w = min(max(float(elem.get("width", base["width"])), 5), 400)
                h = min(max(float(elem.get("height", base["height"])), 5), 400)
                base["x"] = max(0, min(x, width - w))
                base["y"] = max(0, min(y, height - h))
                base["width"] = w
                base["height"] = h

            # Apply element-specific properties with validation
            if "strokeColor" in elem and isinstance(elem["strokeColor"], str):
                base["strokeColor"] = elem["strokeColor"]
            if "backgroundColor" in elem and isinstance(elem["backgroundColor"], str):
                base["backgroundColor"] = elem["backgroundColor"]
            if "fillStyle" in elem and isinstance(elem["fillStyle"], str):
                base["fillStyle"] = elem["fillStyle"]
            if "strokeWidth" in elem and isinstance(elem["strokeWidth"], (int, float)):
                base["strokeWidth"] = max(1, float(elem["strokeWidth"]))
            if "strokeStyle" in elem and isinstance(elem["strokeStyle"], str):
                base["strokeStyle"] = elem["strokeStyle"]
            if "roughness" in elem and isinstance(elem["roughness"], (int, float)):
                base["roughness"] = float(elem["roughness"])
            if "opacity" in elem and isinstance(elem["opacity"], (int, float)):
                base["opacity"] = max(0, min(100, float(elem["opacity"])))
            if "angle" in elem and isinstance(elem["angle"], (int, float)):
                base["angle"] = float(elem["angle"])

            # Text-specific properties
            if etype == "text":
                base["text"] = elem.get("text", "Label")
                if "fontSize" in elem and isinstance(elem["fontSize"], (int, float)):
                    base["fontSize"] = int(elem["fontSize"])
                else:
                    base["fontSize"] = 20
                base["fontFamily"] = elem.get("fontFamily", 1)
                base["textAlign"] = elem.get("textAlign", "center")

            # Ensure groupIds and boundElements are arrays
            if not isinstance(base.get("groupIds"), list):
                base["groupIds"] = []
            if not isinstance(base.get("boundElements"), list):
                base["boundElements"] = []

            cleaned.append(base)

        # If no valid elements after cleaning, return mock scene
        if not cleaned:
            logger.warning("No valid elements after cleaning, returning mock scene")
            mock = self._mock_scene()
            mock.appState["message"] = "AI generated invalid elements, showing fallback scene"
            return mock

        # Validate and clean appState
        app_state = ai_data.get("appState") or {}
        if not isinstance(app_state, dict):
            app_state = {}

        # Remove collaborators to avoid "forEach is not a function" error
        if "collaborators" in app_state:
            del app_state["collaborators"]

        # Ensure zoom is properly formatted
        app_state.setdefault("zoom", {"value": 1})

        files = ai_data.get("files") or {}
        if not isinstance(files, dict):
            files = {}

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

        # IMPORTANT: Excalidraw line elements must be "normalized"
        # - points are relative to x,y
        # - width/height must match the bounding box of points
        # - x,y is the top-left corner
        whisker_left = self._base_element(
            id="whisker-left",
            type="line",
            x=240,
            y=312,  # adjusted so points are non-negative
            width=60,
            height=8,  # max_y - min_y = 0 - (-8) = 8
            points=[[0, 8], [60, 0]],  # relative coordinates, adjusted
            strokeColor="#cbd5e1",
            backgroundColor="transparent"
        )
        whisker_left2 = self._base_element(
            id="whisker-left-2",
            type="line",
            x=240,
            y=330,
            width=60,
            height=8,
            points=[[0, 0], [60, 8]],  # relative coordinates
            strokeColor="#cbd5e1",
            backgroundColor="transparent"
        )
        whisker_right = self._base_element(
            id="whisker-right",
            type="line",
            x=280,  # adjusted: original 340 - 60 = 280
            y=312,  # adjusted
            width=60,
            height=8,
            points=[[60, 8], [0, 0]],  # relative coordinates, reversed
            strokeColor="#cbd5e1",
            backgroundColor="transparent"
        )
        whisker_right2 = self._base_element(
            id="whisker-right-2",
            type="line",
            x=280,  # adjusted
            y=330,
            width=60,
            height=8,
            points=[[60, 0], [0, 8]],  # relative coordinates, reversed
            strokeColor="#cbd5e1",
            backgroundColor="transparent"
        )

        elements = [face, ear_left, ear_right, eye_left, eye_right, nose, whisker_left, whisker_left2, whisker_right, whisker_right2]
        app_state = {
            # Don't override user's background color preference
            # "viewBackgroundColor": "#0f172a",
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
