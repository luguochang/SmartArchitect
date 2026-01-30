"use client";

import { NodeProps } from "reactflow";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import {
  Server,
  Database,
  Globe,
  Shield,
  Layers,
  Cloud,
  Network,
  Cpu,
  Package,
  FileText,
} from "lucide-react";

// Category icon mapping
const CATEGORY_ICONS = {
  service: Server,
  database: Database,
  api: Globe,
  security: Shield,
  platform: Layers,
  infrastructure: Cloud,
  network: Network,
  compute: Cpu,
  storage: Package,
  default: FileText,
};

export function FrameNode({ id, data, selected }: NodeProps) {
  const {
    label,
    note,
    layerColor,
    tech_stack = [],
    category = "default",
    size = "medium",
  } = data || {};
  const { updateNodeLabel } = useArchitectStore.getState();

  const handleEdit = () => {
    const next = prompt("Rename node", label || "Component");
    if (next && next.trim()) {
      updateNodeLabel?.(id, next.trim());
    }
  };

  // Get category icon component
  const IconComponent =
    CATEGORY_ICONS[category as keyof typeof CATEGORY_ICONS] ||
    CATEGORY_ICONS.default;

  // Size configurations
  const sizeConfig = {
    small: { width: 180, height: 80, padding: "p-3" },
    medium: { width: 240, height: 100, padding: "p-4" },
    large: { width: 320, height: 140, padding: "p-5" },
  };

  const currentSize =
    sizeConfig[size as keyof typeof sizeConfig] || sizeConfig.medium;

  return (
    <div
      className={`rounded-xl border-2 transition-all duration-200 ${currentSize.padding} ${
        selected
          ? "border-emerald-400 shadow-xl scale-105"
          : "border-slate-300 dark:border-slate-700 shadow-lg hover:shadow-xl"
      }`}
      style={{
        width: currentSize.width,
        height: currentSize.height,
        background: `linear-gradient(135deg, ${layerColor || "#e2e8f0"}05, ${
          layerColor || "#e2e8f0"
        }15)`,
        backdropFilter: "blur(10px)",
        boxShadow: selected
          ? `0 0 0 3px ${layerColor || "#10b981"}40, 0 12px 32px rgba(0,0,0,0.15)`
          : "0 8px 24px rgba(0,0,0,0.08)",
      }}
      onDoubleClick={handleEdit}
    >
      {/* Header with icon and category badge */}
      <div className="flex items-start justify-between gap-2 mb-3">
        {/* Category Icon */}
        <div
          className="flex items-center justify-center rounded-lg p-2 flex-shrink-0"
          style={{
            background: `linear-gradient(135deg, ${layerColor || "#e2e8f0"}30, ${
              layerColor || "#e2e8f0"
            }50)`,
            color: layerColor || "#0f172a",
          }}
        >
          <IconComponent className="h-4 w-4" />
        </div>

        {/* Category/Layer Badge */}
        {(note || data?.layer) && (
          <span
            className="rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider"
            style={{
              background: `linear-gradient(135deg, ${layerColor || "#e2e8f0"}25, ${
                layerColor || "#e2e8f0"
              }40)`,
              color: layerColor || "#0f172a",
              border: `1px solid ${layerColor || "#e2e8f0"}50`,
            }}
          >
            {note || data?.layer}
          </span>
        )}
      </div>

      {/* Component Label */}
      <div className="mb-3">
        <h3
          className="text-sm font-bold leading-tight"
          style={{ color: layerColor || "#0f172a" }}
        >
          {label || "Component"}
        </h3>
      </div>

      {/* Tech Stack Badges */}
      {tech_stack && tech_stack.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {tech_stack.slice(0, 3).map((tech: string, idx: number) => (
            <span
              key={idx}
              className="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-medium"
              style={{
                background: `${layerColor || "#e2e8f0"}15`,
                color: layerColor || "#0f172a",
                border: `1px solid ${layerColor || "#e2e8f0"}30`,
              }}
            >
              {tech}
            </span>
          ))}
          {tech_stack.length > 3 && (
            <span
              className="inline-flex items-center rounded-md px-2 py-0.5 text-[10px] font-medium"
              style={{
                background: `${layerColor || "#e2e8f0"}10`,
                color: layerColor || "#0f172a",
              }}
            >
              +{tech_stack.length - 3}
            </span>
          )}
        </div>
      )}
    </div>
  );
}
