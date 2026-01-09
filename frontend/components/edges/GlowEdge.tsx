"use client";

import { memo } from "react";
import { BaseEdge, EdgeLabelRenderer, EdgeProps, getBezierPath } from "reactflow";

export const GlowEdge = memo((props: EdgeProps) => {
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

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const badge = data?.condition as string | undefined;
  const stroke = style?.stroke || "var(--edge-stroke, #94a3b8)";

  return (
    <>
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke,
          strokeWidth: style?.strokeWidth || 2.5,
          opacity: selected ? 1 : 0.9,
          filter: `drop-shadow(0 0 6px ${selected ? "rgba(99,102,241,0.7)" : "rgba(148,163,184,0.35)"})`,
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
            <span className="rounded-full bg-indigo-600 px-2 py-1 text-[11px] font-semibold text-white shadow-lg">
              {badge}
            </span>
          </div>
        </EdgeLabelRenderer>
      )}
    </>
  );
});

GlowEdge.displayName = "GlowEdge";
