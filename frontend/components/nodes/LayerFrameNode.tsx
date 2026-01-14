"use client";

import { NodeProps } from "reactflow";
import { useArchitectStore } from "@/lib/store/useArchitectStore";

export function LayerFrameNode({ id, data, selected }: NodeProps) {
  const { label, color, width = 1000, height = 180 } = data || {};
  const { updateNodeLabel } = useArchitectStore.getState();

  const handleEdit = () => {
    const next = prompt("Rename layer", label || "Layer");
    if (next && next.trim()) {
      updateNodeLabel?.(id, next.trim());
    }
  };

  return (
    <div
      className={`rounded-2xl border-2 ${selected ? "border-emerald-400" : "border-slate-300 dark:border-slate-700"} bg-white/40 dark:bg-slate-800/40 shadow-sm`}
      style={{
        width,
        height,
        boxShadow: "0 8px 24px rgba(0,0,0,0.05)",
      }}
      onDoubleClick={handleEdit}
    >
      <div className="flex items-center gap-2 px-4 py-2">
        <span
          className="rounded-full px-3 py-1 text-xs font-semibold"
          style={{
            background: `${color || "#e2e8f0"}22`,
            color: color || "#0f172a",
          }}
        >
          {label || "Layer"}
        </span>
      </div>
    </div>
  );
}
