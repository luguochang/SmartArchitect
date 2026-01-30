"use client";

import { memo } from "react";
import { BaseEdge, EdgeLabelRenderer, EdgeProps, getStraightPath } from "reactflow";

/**
 * Straight Edge Component
 *
 * Provides simple straight-line connections without curves or steps.
 * Used for modern, minimalist flowchart styles.
 */
export const StraightEdge = memo((props: EdgeProps) => {
  const {
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    markerEnd,
    style,
    data,
    selected,
  } = props;

  // Use getStraightPath for direct line connections
  const [edgePath, labelX, labelY] = getStraightPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
  });

  const badge = data?.condition as string | undefined;
  const stroke = style?.stroke || "var(--edge-stroke, #6b7280)";

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke,
          strokeWidth: style?.strokeWidth || 3,
          opacity: selected ? 1 : 0.8,
          filter: "none",  // No glow for clean, modern look
          transition: "stroke 0.2s ease, opacity 0.2s ease",
          ...style,
        }}
      />

      {badge && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: "absolute",
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: "all",
            }}
          >
            <span className="rounded-lg bg-gray-900 px-2.5 py-1 text-xs font-semibold text-white shadow-md">
              {badge}
            </span>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});

StraightEdge.displayName = "StraightEdge";
