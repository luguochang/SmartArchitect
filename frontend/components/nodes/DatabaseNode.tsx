"use client";

import { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Database } from "lucide-react";

export const DatabaseNode = memo(({ data }: NodeProps) => {
  return (
    <div
      className="rounded-lg border-2 px-4 py-3 shadow-lg"
      style={{
        borderColor: "var(--database-border)",
        backgroundColor: "var(--database-background)",
        boxShadow: `0 10px 15px -3px ${
          getComputedStyle(document.documentElement).getPropertyValue("--database-shadow") ||
          "rgba(0, 0, 0, 0.1)"
        }`,
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{ backgroundColor: "var(--database-border)" }}
      />

      <div className="flex items-center gap-2">
        <Database
          className="h-5 w-5"
          style={{ color: "var(--database-icon)" }}
        />
        <div>
          <div
            className="font-semibold"
            style={{
              color: "var(--database-text)",
              fontSize: "var(--font-size-node)",
              fontWeight: "var(--font-weight-bold)",
            }}
          >
            {data.label}
          </div>
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
