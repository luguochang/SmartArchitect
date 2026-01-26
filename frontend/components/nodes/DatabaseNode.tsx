"use client";

import { memo, useState, useCallback } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Database } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";

export const DatabaseNode = memo(({ id, data }: NodeProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [label, setLabel] = useState(data.label);
  const updateNodeLabel = useArchitectStore((state) => state.updateNodeLabel);

  const handleDoubleClick = useCallback(() => {
    setIsEditing(true);
  }, []);

  const handleBlur = useCallback(() => {
    setIsEditing(false);
    if (label.trim() && label !== data.label) {
      updateNodeLabel(id, label.trim());
    } else {
      setLabel(data.label);
    }
  }, [id, label, data.label, updateNodeLabel]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      e.preventDefault();
      (e.target as HTMLInputElement).blur();
    } else if (e.key === "Escape") {
      setLabel(data.label);
      setIsEditing(false);
    }
  }, [data.label]);

  return (
    <div
      className="glass-node relative rounded-xl border-2 px-4 py-3 shadow-lg"
      style={{
        borderColor: "var(--database-border)",
        background: `linear-gradient(135deg, ${"var(--database-background)"} 0%, rgba(255,255,255,0.9) 100%)`,
        boxShadow: "var(--database-shadow, 0 14px 30px -14px rgba(0,0,0,0.25))",
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{ backgroundColor: "var(--database-border)" }}
      />

      <span
        className="absolute left-2 top-2 h-[calc(100%-16px)] w-[5px] rounded-full opacity-80"
        style={{ backgroundColor: "var(--database-border)" }}
      />
      <div className="flex items-center gap-3">
        <Database className="h-5 w-5 transition-transform duration-200 hover:scale-110" style={{ color: "var(--database-icon)" }} />
        <div className="flex-1">
          {isEditing ? (
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              autoFocus
              className="nodrag font-semibold bg-transparent border-b-2 outline-none"
              style={{
                color: "var(--database-text)",
                borderColor: "var(--database-border)",
                fontSize: "var(--font-size-node)",
                fontWeight: "var(--font-weight-bold)",
                width: `${Math.max(label.length, 8)}ch`,
              }}
            />
          ) : (
            <div
              onDoubleClick={handleDoubleClick}
              className="font-semibold cursor-text"
              style={{
                color: "var(--database-text)",
                fontSize: "var(--font-size-node)",
                fontWeight: "var(--font-weight-bold)",
              }}
            >
              {data.label}
            </div>
          )}
          <div
            className="text-xs"
            style={{
              color: "var(--database-text)",
              opacity: 0.7,
              fontSize: "var(--font-size-label)",
            }}
          >
            Database
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        style={{ backgroundColor: "var(--database-border)" }}
      />
    </div>
  );
});

DatabaseNode.displayName = "DatabaseNode";
