"use client";

import { memo } from "react";
import { BaseEdge, EdgeLabelRenderer, EdgeProps, getSmoothStepPath } from "reactflow";

/**
 * Orthogonal Edge Component
 *
 * Provides BPMN-standard orthogonal routing with horizontal and vertical segments.
 * Uses React Flow's smooth step path algorithm.
 */
export const OrthogonalEdge = memo((props: EdgeProps) => {
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

  // Use getSmoothStepPath for orthogonal routing
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 8,  // Adjust corner rounding (0 = sharp 90° corners, higher = more rounded)
  });

  const badge = data?.condition as string | undefined;
  const stroke = style?.stroke || "var(--edge-stroke, #000000)";
  const showGlow = data?.showGlow !== false;  // Default to false for professional mode

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke,
          strokeWidth: style?.strokeWidth || 2,
          opacity: selected ? 1 : 0.9,
          // Only apply glow effect if enabled
          filter: showGlow
            ? `drop-shadow(0 0 6px ${selected ? "rgba(99,102,241,0.7)" : "rgba(148,163,184,0.35)"})`
            : "none",
          transition: "stroke 0.2s ease, filter 0.2s ease",
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
            <span className="rounded bg-gray-800 px-2 py-1 text-[11px] font-medium text-white shadow-md">
              {badge}
            </span>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});

OrthogonalEdge.displayName = "OrthogonalEdge";
