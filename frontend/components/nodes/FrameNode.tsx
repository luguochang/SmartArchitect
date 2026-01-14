"use client";

import { NodeProps } from "reactflow";
import { useArchitectStore } from "@/lib/store/useArchitectStore";

export function FrameNode({ id, data, selected }: NodeProps) {
  const { label, note, layerColor } = data || {};
  const { updateNodeLabel } = useArchitectStore.getState();

  const handleEdit = () => {
    const next = prompt("Rename node", label || "Component");
    if (next && next.trim()) {
      updateNodeLabel?.(id, next.trim());
    }
  };

  return (
    <div
      className={`min-w-[200px] rounded-xl border-2 bg-white/90 p-3 shadow-sm dark:bg-slate-900/90 ${
        selected ? "border-emerald-400 shadow-md" : "border-slate-300 dark:border-slate-700"
      }`}
      style={{
        boxShadow: "0 10px 30px rgba(0,0,0,0.06)",
      }}
      onDoubleClick={handleEdit}
    >
      <div className="flex items-center justify-between gap-2">
        <span
          className="rounded-full px-2 py-1 text-[11px] font-semibold text-slate-800 dark:text-slate-100"
          style={{ background: `${layerColor || "#e2e8f0"}22`, color: layerColor || "#0f172a" }}
        >
          {note || data?.layer || "Layer"}
        </span>
      </div>
      <div className="mt-2 text-sm font-semibold text-slate-900 dark:text-white">{label || "Component"}</div>
    </div>
  );
}
