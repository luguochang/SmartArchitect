export type HandleDirection = "top" | "right" | "bottom" | "left";
export type HandleRole = "source" | "target";

export const HANDLE_ID = {
  topSource: "top-source",
  topTarget: "top-target",
  rightSource: "right-source",
  rightTarget: "right-target",
  bottomSource: "bottom-source",
  bottomTarget: "bottom-target",
  leftSource: "left-source",
  leftTarget: "left-target",
} as const;

const LEGACY_HANDLE_ALIASES: Record<string, string> = {
  "target-top": HANDLE_ID.topTarget,
  "target-right": HANDLE_ID.rightTarget,
  "target-bottom": HANDLE_ID.bottomTarget,
  "target-left": HANDLE_ID.leftTarget,
  "source-top": HANDLE_ID.topSource,
  "source-right": HANDLE_ID.rightSource,
  "source-bottom": HANDLE_ID.bottomSource,
  "source-left": HANDLE_ID.leftSource,
  "in-top": HANDLE_ID.topTarget,
  "in-left": HANDLE_ID.leftTarget,
  "out-right-yes": HANDLE_ID.rightSource,
  "out-bottom-no": HANDLE_ID.bottomSource,
};

export function normalizeHandleId(handleId?: string | null): string | undefined {
  if (!handleId) return undefined;
  const id = handleId.trim();
  if (!id) return undefined;
  return LEGACY_HANDLE_ALIASES[id] || id;
}

export function inferCardinalHandles(dx: number, dy: number): {
  sourceHandle: string;
  targetHandle: string;
} {
  if (Math.abs(dx) >= Math.abs(dy)) {
    if (dx >= 0) {
      return { sourceHandle: HANDLE_ID.rightSource, targetHandle: HANDLE_ID.leftTarget };
    }
    return { sourceHandle: HANDLE_ID.leftSource, targetHandle: HANDLE_ID.rightTarget };
  }

  if (dy >= 0) {
    return { sourceHandle: HANDLE_ID.bottomSource, targetHandle: HANDLE_ID.topTarget };
  }
  return { sourceHandle: HANDLE_ID.topSource, targetHandle: HANDLE_ID.bottomTarget };
}

