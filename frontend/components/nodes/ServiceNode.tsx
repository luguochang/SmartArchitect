"use client";

import { memo } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Box } from "lucide-react";

export const ServiceNode = memo(({ data }: NodeProps) => {
  return (
    <div
      className="rounded-lg border-2 px-4 py-3 shadow-lg"
      style={{
        borderColor: "var(--service-border)",
        backgroundColor: "var(--service-background)",
        boxShadow: `0 10px 15px -3px ${
          getComputedStyle(document.documentElement).getPropertyValue("--service-shadow") ||
          "rgba(0, 0, 0, 0.1)"
        }`,
      }}
    >
      <Handle
        type="target"
        position={Position.Top}
        style={{ backgroundColor: "var(--service-border)" }}
      />

      <div className="flex items-center gap-2">
        <Box
          className="h-5 w-5"
          style={{ color: "var(--service-icon)" }}
        />
        <div>
          <div
            className="font-semibold"
            style={{
              color: "var(--service-text)",
              fontSize: "var(--font-size-node)",
              fontWeight: "var(--font-weight-bold)",
            }}
          >
            {data.label}
          </div>
          <div
            className="text-xs"
            style={{
              color: "var(--service-text)",
              opacity: 0.7,
              fontSize: "var(--font-size-label)",
            }}
          >
            Service
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        style={{ backgroundColor: "var(--service-border)" }}
      />
    </div>
  );
});

ServiceNode.displayName = "ServiceNode";
