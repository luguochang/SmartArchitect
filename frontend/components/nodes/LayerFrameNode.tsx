"use client";

import { NodeProps } from "reactflow";
import { useArchitectStore } from "@/lib/store/useArchitectStore";

export function LayerFrameNode({ id, data, selected }: NodeProps) {
  const {
    label,
    color,
    width = 1000,
    height = 180,
    layout = "horizontal",
    columns = 4,
    itemsCount = 0,
  } = data || {};
  const { updateNodeLabel } = useArchitectStore.getState();

  const handleEdit = () => {
    const next = prompt("Rename layer", label || "Layer");
    if (next && next.trim()) {
      updateNodeLabel?.(id, next.trim());
    }
  };

  // Enhanced styling with gradient background
  const gradientBg = `linear-gradient(135deg, ${color || "#e2e8f0"}08, ${color || "#e2e8f0"}18)`;

  // Grid layout support
  const isGrid = layout === "grid";
  const containerStyles = isGrid ? {
    display: "grid",
    gridTemplateColumns: `repeat(${columns}, minmax(220px, 1fr))`,
    gap: "20px",
    padding: "60px 30px 30px 30px",
  } : {
    display: "flex",
    flexWrap: "wrap" as const,
    gap: "20px",
    padding: "60px 30px 30px 30px",
  };

  return (
    <div
      className={`rounded-2xl border-2 ${
        selected
          ? "border-emerald-400 shadow-xl"
          : "border-slate-300 dark:border-slate-700 shadow-lg"
      } bg-white/50 dark:bg-slate-800/50 relative transition-all duration-200`}
      style={{
        width,
        height,
        background: gradientBg,
        boxShadow: selected
          ? `0 0 0 3px ${color || "#10b981"}40, 0 12px 32px rgba(0,0,0,0.1)`
          : "0 8px 24px rgba(0,0,0,0.06)",
      }}
      onDoubleClick={handleEdit}
    >
      {/* Layer Header with Enhanced Badge */}
      <div className="absolute top-0 left-0 right-0 flex items-center justify-between px-4 py-3 border-b border-slate-200/50 dark:border-slate-700/50">
        <div className="flex items-center gap-3">
          <span
            className="rounded-full px-4 py-1.5 text-sm font-semibold shadow-sm"
            style={{
              background: `linear-gradient(135deg, ${color || "#e2e8f0"}30, ${color || "#e2e8f0"}50)`,
              color: color || "#0f172a",
              border: `1px solid ${color || "#e2e8f0"}40`,
            }}
          >
            {label || "Layer"}
          </span>

          {/* Item count indicator for grid layout */}
          {isGrid && itemsCount > 0 && (
            <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
              {itemsCount} {itemsCount === 1 ? "component" : "components"}
            </span>
          )}
        </div>

        {/* Layout indicator */}
        {isGrid && (
          <span className="text-xs text-slate-400 dark:text-slate-500 font-mono">
            {columns} columns
          </span>
        )}
      </div>

      {/* Content area - will contain child FrameNodes positioned by React Flow */}
      <div style={containerStyles} className="relative">
        {/* Child nodes will be rendered here by React Flow when using parent-child relationships */}
        {/* For now, this div provides the grid layout container */}
      </div>
    </div>
  );
}
