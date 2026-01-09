"use client";

import { useMemo } from "react";
import { Palette, Tag, Type, Link as LinkIcon } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";

export function SelectedDetailsPanel() {
  const nodes = useArchitectStore((state) => state.nodes);
  const selectedNodes = useMemo(() => nodes.filter((n) => n.selected), [nodes]);

  const node = useMemo(() => selectedNodes[0], [selectedNodes]);

  if (!node) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-400">
        Select a node to see details and styling hints.
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xs uppercase tracking-wide text-slate-500">Node</div>
          <div className="text-base font-semibold text-slate-900 dark:text-white">{node.data?.label || "Untitled"}</div>
        </div>
        <span className="rounded-full bg-indigo-50 px-3 py-1 text-xs font-semibold text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-200">
          {node.type || "default"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs text-slate-600 dark:text-slate-300">
        <div className="flex items-center gap-2">
          <Type className="h-4 w-4 text-slate-400" />
          <div>
            <div className="font-semibold text-slate-800 dark:text-white">Shape</div>
            <div className="opacity-80">{node.data?.shape || "rectangle"}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Palette className="h-4 w-4 text-slate-400" />
          <div>
            <div className="font-semibold text-slate-800 dark:text-white">Color</div>
            <div className="opacity-80">{node.data?.color || "Themed"}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Tag className="h-4 w-4 text-slate-400" />
          <div>
            <div className="font-semibold text-slate-800 dark:text-white">Icon</div>
            <div className="opacity-80">{node.data?.iconType || "auto"}</div>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <LinkIcon className="h-4 w-4 text-slate-400" />
          <div>
            <div className="font-semibold text-slate-800 dark:text-white">Edges</div>
            <div className="opacity-80">Connectors inherit edge glow + arrows</div>
          </div>
        </div>
      </div>
    </div>
  );
}
