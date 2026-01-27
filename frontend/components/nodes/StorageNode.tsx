"use client";

import { memo, useState, useCallback } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { HardDrive } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";

export const StorageNode = memo(({ id, data }: NodeProps) => {
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
        borderColor: "var(--storage-border)",
        backgroundColor: "var(--storage-background)",
        boxShadow: "var(--storage-shadow, 0 10px 15px -3px rgba(0,0,0,0.1))",
      }}
    >
      {/* Input handles - Top and Left */}
      <Handle
        id="target-top"
        type="target"
        position={Position.Top}
        style={{
          backgroundColor: "var(--storage-border)",
          top: 0,
          left: "50%",
          transform: "translate(-50%, -50%)"
        }}
      />
      <Handle
        id="target-left"
        type="target"
        position={Position.Left}
        style={{
          backgroundColor: "var(--storage-border)",
          top: "50%",
          left: 0,
          transform: "translate(-50%, -50%)"
        }}
      />

      {/* Output handles - Right and Bottom */}
      <Handle
        id="source-right"
        type="source"
        position={Position.Right}
        style={{
          backgroundColor: "var(--storage-border)",
          top: "50%",
          right: 0,
          transform: "translate(50%, -50%)"
        }}
      />
      <Handle
        id="source-bottom"
        type="source"
        position={Position.Bottom}
        style={{
          backgroundColor: "var(--storage-border)",
          bottom: 0,
          left: "50%",
          transform: "translate(-50%, 50%)"
        }}
      />

      <span
        className="absolute left-2 top-2 h-[calc(100%-16px)] w-[5px] rounded-full opacity-80"
        style={{ backgroundColor: "var(--storage-border)" }}
      />

      <div className="flex items-center gap-3">
        <HardDrive className="h-5 w-5 transition-transform duration-200 hover:scale-110" style={{ color: "var(--storage-icon)" }} />
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
                color: "var(--storage-text)",
                borderColor: "var(--storage-border)",
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
                color: "var(--storage-text)",
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
              color: "var(--storage-text)",
              opacity: 0.7,
              fontSize: "var(--font-size-label)",
            }}
          >
            Storage
          </div>
        </div>
      </div>
    </div>
  );
});

StorageNode.displayName = "StorageNode";
