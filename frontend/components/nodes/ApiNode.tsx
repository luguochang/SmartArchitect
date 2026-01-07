"use client";

import { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Globe } from "lucide-react";

export const ApiNode = memo(({ data }: NodeProps) => {
  return (
    <div
      className="rounded-lg border-2 px-4 py-3 shadow-lg"
      style={{
        borderColor: "var(--api-border)",
        backgroundColor: "var(--api-background)",
        boxShadow: `0 10px 15px -3px ${
          getComputedStyle(document.documentElement).getPropertyValue("--api-shadow") ||
          "rgba(0, 0, 0, 0.1)"
        }`,
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{ backgroundColor: "var(--api-border)" }}
      />

      <div className="flex items-center gap-2">
        <Globe
          className="h-5 w-5"
          style={{ color: "var(--api-icon)" }}
        />
        <div>
          <div
            className="font-semibold"
            style={{
              color: "var(--api-text)",
              fontSize: "var(--font-size-node)",
              fontWeight: "var(--font-weight-bold)",
            }}
          >
            {data.label}
          </div>
          <div
            className="text-xs"
            style={{
              color: "var(--api-text)",
              opacity: 0.7,
              fontSize: "var(--font-size-label)",
            }}
          >
            API
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        style={{ backgroundColor: "var(--api-border)" }}
      />
    </div>
  );
});

ApiNode.displayName = "ApiNode";
