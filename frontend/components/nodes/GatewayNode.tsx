"use client";

import { memo, useState, useCallback } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Shield } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { NodeShape, SHAPE_CONFIG } from "@/lib/utils/nodeShapes";

const SHADOW_SOFT = "var(--bpmn-shadow-soft, 0 12px 30px -12px rgba(15, 23, 42, 0.25))";
const toNumber = (value?: string) => (value ? Number.parseInt(value, 10) : undefined);

export const GatewayNode = memo(({ id, data }: NodeProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [label, setLabel] = useState(data.label);
  const updateNodeLabel = useArchitectStore((state) => state.updateNodeLabel);

  const shape: NodeShape = (data.shape as NodeShape) || "diamond";
  const isDiamond = shape === "diamond";
  const shapeConfig = SHAPE_CONFIG[shape];

  const size = toNumber(shapeConfig.width as string) ?? 88;
  const borderColor = data.color || "var(--bpmn-gateway-ring, #fb923c)";
  const backgroundColor = "var(--bpmn-gateway-bg, #fff7ed)";

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

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter") {
        e.preventDefault();
        (e.target as HTMLInputElement).blur();
      } else if (e.key === "Escape") {
        setLabel(data.label);
        setIsEditing(false);
      }
    },
    [data.label]
  );

  if (isDiamond) {
    const padding = 6;
    const points = `${size / 2},${padding} ${size - padding},${size / 2} ${size / 2},${size - padding} ${padding},${size / 2}`;

    return (
      <div className="relative" style={{ width: `${size}px`, height: `${size}px` }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          style={{ filter: "drop-shadow(0 10px 18px rgba(15, 23, 42, 0.16))" }}
        >
          <polygon points={points} fill={backgroundColor} stroke={borderColor} strokeWidth={3} />
          <g stroke={borderColor} strokeWidth={3} strokeLinecap="round">
            <line x1={size * 0.34} y1={size * 0.34} x2={size * 0.66} y2={size * 0.66} />
            <line x1={size * 0.34} y1={size * 0.66} x2={size * 0.66} y2={size * 0.34} />
          </g>
        </svg>

        <Handle
          id="target-top"
          type="target"
          position={Position.Top}
          style={{
            backgroundColor: borderColor,
            position: "absolute",
            top: "6%",
            left: "50%",
            transform: "translate(-50%, 0%)",
          }}
        />
        <Handle
          id="target-right"
          type="target"
          position={Position.Right}
          style={{
            backgroundColor: borderColor,
            position: "absolute",
            top: "50%",
            right: "6%",
            transform: "translate(0%, -50%)",
          }}
        />
        <Handle
          id="target-bottom"
          type="target"
          position={Position.Bottom}
          style={{
            backgroundColor: borderColor,
            position: "absolute",
            bottom: "6%",
            left: "50%",
            transform: "translate(-50%, 0%)",
          }}
        />
        <Handle
          id="target-left"
          type="target"
          position={Position.Left}
          style={{
            backgroundColor: borderColor,
            position: "absolute",
            top: "50%",
            left: "6%",
            transform: "translate(0%, -50%)",
          }}
        />
        <Handle
          id="source-top"
          type="source"
          position={Position.Top}
          style={{
            backgroundColor: borderColor,
            position: "absolute",
            top: "6%",
            left: "50%",
            transform: "translate(-50%, 0%)",
          }}
        />
        <Handle
          id="source-right"
          type="source"
          position={Position.Right}
          style={{
            backgroundColor: borderColor,
            position: "absolute",
            top: "50%",
            right: "6%",
            transform: "translate(0%, -50%)",
          }}
        />
        <Handle
          id="source-bottom"
          type="source"
          position={Position.Bottom}
          style={{
            backgroundColor: borderColor,
            position: "absolute",
            bottom: "6%",
            left: "50%",
            transform: "translate(-50%, 0%)",
          }}
        />
        <Handle
          id="source-left"
          type="source"
          position={Position.Left}
          style={{
            backgroundColor: borderColor,
            position: "absolute",
            top: "50%",
            left: "6%",
            transform: "translate(0%, -50%)",
          }}
        />
      </div>
    );
  }

  return (
    <div
      className="rounded-lg border px-4 py-3 shadow-lg"
      style={{
        borderColor: "var(--gateway-border, var(--bpmn-gateway-ring, #fb923c))",
        backgroundColor: "var(--gateway-background, #fff7ed)",
        boxShadow: SHADOW_SOFT,
      }}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{ backgroundColor: "var(--gateway-border, var(--bpmn-gateway-ring, #fb923c))" }}
      />

      <div className="flex items-center gap-2">
        <Shield className="h-5 w-5 transition-transform duration-200 hover:scale-110" style={{ color: "var(--gateway-icon)" }} />
        <div>
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
                color: "var(--gateway-text)",
                borderColor: "var(--gateway-border)",
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
                color: "var(--gateway-text)",
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
              color: "var(--gateway-text)",
              opacity: 0.7,
              fontSize: "var(--font-size-label)",
            }}
          >
            Gateway
          </div>
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        style={{ backgroundColor: "var(--gateway-border, var(--bpmn-gateway-ring, #fb923c))" }}
      />
    </div>
  );
});

GatewayNode.displayName = "GatewayNode";
