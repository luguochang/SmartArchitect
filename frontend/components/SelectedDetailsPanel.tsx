"use client";

import { useEffect, useMemo, useState, useCallback } from "react";
import { Palette, Type } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { NodeShape, SHAPE_CONFIG } from "@/lib/utils/nodeShapes";

const SHAPE_OPTIONS: NodeShape[] = [
  "rectangle",
  "rounded-rectangle",
  "circle",
  "diamond",
  "task",
  "start-event",
  "end-event",
  "intermediate-event",
];

export function SelectedDetailsPanel() {
  const nodes = useArchitectStore((state) => state.nodes);
  const updateNodeData = useArchitectStore((state) => state.updateNodeData);

  const selectedNodes = useMemo(() => nodes.filter((n) => n.selected), [nodes]);
  const node = useMemo(() => selectedNodes[0], [selectedNodes]);

  const [label, setLabel] = useState("");
  const [color, setColor] = useState("");
  const [shape, setShape] = useState<NodeShape>("rectangle");
  const [width, setWidth] = useState<number | undefined>(undefined);
  const [height, setHeight] = useState<number | undefined>(undefined);

  const shapeOptions = useMemo(
    () => (shape && !SHAPE_OPTIONS.includes(shape) ? [shape, ...SHAPE_OPTIONS] : SHAPE_OPTIONS),
    [shape]
  );
  const displayColor = color?.trim() || "Themed (auto)";

  useEffect(() => {
    setLabel((node?.data as any)?.label || "");
    setColor((node?.data as any)?.color || "");
    setShape(((node?.data as any)?.shape as NodeShape) || "rectangle");
    setWidth((node?.data as any)?.width);
    setHeight((node?.data as any)?.height);
  }, [node?.id]);

  const commitField = useCallback(
    (field: "label" | "color" | "shape" | "width" | "height", value: string | number | undefined) => {
      if (!node) return;
      const nextValue = typeof value === "string" ? value?.trim() : value;
      updateNodeData(node.id, { [field]: nextValue || undefined });
    },
    [node, updateNodeData]
  );

  if (!node) {
    return (
      <div className="rounded-xl border border-dashed border-slate-200 bg-slate-50 p-4 text-sm text-slate-500 dark:border-slate-700 dark:bg-slate-800/50 dark:text-slate-400">
        Select a node to see details and styling hints.
      </div>
    );
  }

  return (
    <div className="space-y-3 rounded-lg border border-slate-200 bg-white/90 p-3 shadow-sm dark:border-slate-700 dark:bg-slate-900/80">
      <div className="flex items-center justify-between gap-2">
        <div className="min-w-0 flex-1">
          <div className="text-[11px] uppercase tracking-wide text-slate-500">Node</div>
          <input
            value={label}
            onChange={(e) => setLabel(e.target.value)}
            onBlur={() => commitField("label", label)}
            onKeyDown={(e) => e.key === "Enter" && (e.target as HTMLInputElement).blur()}
            className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-sm font-semibold text-slate-900 outline-none focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-white"
            placeholder="Untitled"
          />
        </div>
        <span className="shrink-0 rounded-full bg-indigo-50 px-2.5 py-1 text-[11px] font-semibold text-indigo-700 dark:bg-indigo-500/10 dark:text-indigo-200">
          {node.type || "default"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs text-slate-600 dark:text-slate-300">
        {node.type === "layerFrame" && (
          <>
            <div className="flex items-center gap-2">
              <Type className="h-4 w-4 text-slate-400" />
              <div className="flex-1">
                <div className="font-semibold text-slate-800 dark:text-white">Width</div>
                <input
                  type="number"
                  value={width ?? 1000}
                  onChange={(e) => setWidth(Number(e.target.value))}
                  onBlur={() => commitField("width", width ?? 1000)}
                  className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-800 outline-none focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Type className="h-4 w-4 text-slate-400" />
              <div className="flex-1">
                <div className="font-semibold text-slate-800 dark:text-white">Height</div>
                <input
                  type="number"
                  value={height ?? 180}
                  onChange={(e) => setHeight(Number(e.target.value))}
                  onBlur={() => commitField("height", height ?? 180)}
                  className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-800 outline-none focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                />
              </div>
            </div>
          </>
        )}

        <div className="flex items-center gap-2">
          <Type className="h-4 w-4 text-slate-400" />
          <div className="flex-1">
            <div className="font-semibold text-slate-800 dark:text-white">Shape</div>
            <select
              value={shape}
              onChange={(e) => {
                setShape(e.target.value as NodeShape);
                commitField("shape", e.target.value);
              }}
              className="mt-1 w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-800 outline-none focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
            >
              {shapeOptions.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="col-span-2 flex items-center gap-2">
          <Palette className="h-4 w-4 text-slate-400" />
          <div className="flex-1">
            <div className="font-semibold text-slate-800 dark:text-white">Color</div>
            <div className="mt-1 flex items-center gap-2 min-w-0">
              <input
                type="color"
                value={color && /^#([0-9a-fA-F]{3}){1,2}$/.test(color) ? color : "#2563eb"}
                onChange={(e) => {
                  setColor(e.target.value);
                  commitField("color", e.target.value);
                }}
                className="h-8 w-10 cursor-pointer rounded-md border border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-800"
              />
              <input
                value={color}
                onChange={(e) => setColor(e.target.value)}
                onBlur={() => commitField("color", color)}
                placeholder="Themed (auto)"
                className="flex-1 min-w-0 w-full rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-800 outline-none focus:border-indigo-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              />
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-md bg-slate-50 px-3 py-2 text-[11px] text-slate-600 dark:bg-slate-800/60 dark:text-slate-300">
        Shape: {shape} · Size {SHAPE_CONFIG[shape]?.width || "-"} x {SHAPE_CONFIG[shape]?.height || "-"} · Color {displayColor}
      </div>
    </div>
  );
}
