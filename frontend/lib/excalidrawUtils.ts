/**
 * Excalidraw data sanitization utilities
 * Based on FlowPilot's sanitizeData implementation
 */

/**
 * Repair incomplete JSON by tracking bracket/brace stack.
 * Based on FlowPilot's repairJson function.
 */
export function repairJson(jsonStr: string): string {
  if (!jsonStr) return "{}";
  const trimmed = jsonStr.trim();
  if (trimmed.endsWith("}")) return trimmed; // Assume complete

  // Simple heuristic stack to close braces/brackets
  let stack: string[] = [];
  let isString = false;
  let isEscaped = false;

  for (const char of trimmed) {
    if (isString) {
      if (char === '"' && !isEscaped) {
        isString = false;
      } else if (char === "\\") {
        isEscaped = !isEscaped;
      } else {
        isEscaped = false;
      }
    } else {
      if (char === '"') {
        isString = true;
      } else if (char === "{") {
        stack.push("}");
      } else if (char === "[") {
        stack.push("]");
      } else if (char === "}") {
        if (stack[stack.length - 1] === "}") stack.pop();
      } else if (char === "]") {
        if (stack[stack.length - 1] === "]") stack.pop();
      }
    }
  }

  let completion = "";
  if (isString) completion += '"'; // Close open string
  while (stack.length > 0) {
    completion += stack.pop();
  }

  return trimmed + completion;
}

/**
 * Safely parse potentially incomplete JSON with automatic repair.
 */
export function safeParsePartialJson(jsonStr: string): any {
  try {
    return JSON.parse(jsonStr);
  } catch (e) {
    try {
      const repaired = repairJson(jsonStr);
      return JSON.parse(repaired);
    } catch (e2) {
      return null; // giving up
    }
  }
}

export interface ExcalidrawElement {
  id: string;
  type: string;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  angle?: number;
  strokeColor?: string;
  backgroundColor?: string;
  fillStyle?: string;
  strokeWidth?: number;
  strokeStyle?: string;
  roughness?: number;
  opacity?: number;
  points?: number[][];
  text?: string;
  fontSize?: number;
  fontFamily?: number;
  textAlign?: string;
  groupIds?: string[];
  boundElements?: any[];
  startBinding?: any;
  endBinding?: any;
  [key: string]: any;
}

export interface ExcalidrawScene {
  elements: ExcalidrawElement[];
  appState: any;
  files?: any;
}

/**
 * Sanitize Excalidraw scene data to prevent rendering crashes.
 *
 * Key validations:
 * - Filters out null/undefined/non-object elements
 * - Ensures type and id are strings
 * - Validates points array for linear elements (line, arrow, draw, freedraw)
 * - Ensures text elements have text property
 * - Sets default values for missing properties
 * - Removes collaborators from appState
 *
 * @param data Raw Excalidraw scene data
 * @returns Sanitized scene data safe for rendering
 */
export function sanitizeExcalidrawData(data: any): ExcalidrawScene | null {
  if (!data) return null;

  // Deep clone to avoid mutating original
  const sanitized = { ...data };

  // Ensure elements is an array and filter out invalid items
  if (!Array.isArray(sanitized.elements)) {
    sanitized.elements = [];
  } else {
    // Filter out null/undefined/non-object elements
    sanitized.elements = sanitized.elements
      .filter((el: any) => {
        // Must be a valid object
        if (!el || typeof el !== "object" || Array.isArray(el)) {
          console.debug("[Excalidraw] Skipping non-object element:", typeof el);
          return false;
        }

        // Type and ID must be strings
        if (typeof el.type !== "string" || typeof el.id !== "string") {
          console.debug("[Excalidraw] Skipping element with invalid type/id:", {
            type: typeof el.type,
            id: typeof el.id,
          });
          return false;
        }

        // Linear elements MUST have points array
        if (["line", "arrow", "draw", "freedraw"].includes(el.type)) {
          if (!Array.isArray(el.points) || el.points.length === 0) {
            console.debug(`[Excalidraw] Skipping ${el.type} without points array`);
            return false;
          }

          // Check if points are valid [x, y] arrays
          const arePointsValid = el.points.every(
            (p: any) =>
              Array.isArray(p) &&
              p.length >= 2 &&
              typeof p[0] === "number" &&
              typeof p[1] === "number"
          );

          if (!arePointsValid) {
            console.debug(`[Excalidraw] Skipping ${el.type} with invalid points format`);
            return false;
          }
        }

        // Text elements must have text string
        if (el.type === "text") {
          if (typeof el.text !== "string") {
            console.debug("[Excalidraw] Skipping text element without text property");
            return false;
          }
        }

        return true;
      })
      .map((el: any) => {
        // Clone to avoid mutation and ensure defaults
        const newEl = { ...el };

        // Ensure groupIds is an array
        if (!Array.isArray(newEl.groupIds)) {
          newEl.groupIds = [];
        }

        // Ensure boundElements is an array
        if (!Array.isArray(newEl.boundElements)) {
          newEl.boundElements = [];
        }

        // Set default properties if missing to prevent crashes
        if (typeof newEl.angle !== "number") newEl.angle = 0;
        if (typeof newEl.strokeColor !== "string") newEl.strokeColor = "#000000";
        if (typeof newEl.backgroundColor !== "string")
          newEl.backgroundColor = "transparent";
        if (typeof newEl.fillStyle !== "string") newEl.fillStyle = "hachure";
        if (typeof newEl.strokeWidth !== "number") newEl.strokeWidth = 1;
        if (typeof newEl.strokeStyle !== "string") newEl.strokeStyle = "solid";
        if (typeof newEl.roughness !== "number") newEl.roughness = 1;
        if (typeof newEl.opacity !== "number") newEl.opacity = 100;

        return newEl;
      });
  }

  // Clean appState
  if (sanitized.appState) {
    // Remove collaborators from appState to avoid "forEach is not a function" error
    // This can happen if it comes as a plain object/array instead of Map
    const { collaborators, ...rest } = sanitized.appState;
    sanitized.appState = rest;
  } else {
    sanitized.appState = {};
  }

  // Ensure files is an object
  if (!sanitized.files || typeof sanitized.files !== "object") {
    sanitized.files = {};
  }

  return sanitized;
}

/**
 * Validate element bounds for scrollToContent functionality.
 * Only elements with valid numeric bounds should be considered.
 *
 * @param element Excalidraw element
 * @returns true if element has valid bounds
 */
export function hasValidBounds(element: ExcalidrawElement): boolean {
  return (
    typeof element.x === "number" &&
    typeof element.y === "number" &&
    typeof element.width === "number" &&
    typeof element.height === "number" &&
    !Number.isNaN(element.x) &&
    !Number.isNaN(element.y) &&
    !Number.isNaN(element.width) &&
    !Number.isNaN(element.height)
  );
}

/**
 * Filter elements with valid bounds for scrollToContent.
 *
 * @param elements Array of Excalidraw elements
 * @returns Array of elements with valid bounds
 */
export function getElementsWithValidBounds(
  elements: ExcalidrawElement[]
): ExcalidrawElement[] {
  return elements.filter(hasValidBounds);
}
