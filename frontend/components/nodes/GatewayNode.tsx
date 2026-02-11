"use client";

import { memo, useState, useCallback } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import { Shield } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { NodeShape, SHAPE_CONFIG } from "@/lib/utils/nodeShapes";
import { useNodeStyle } from "@/lib/hooks/useNodeStyle";

const toNumber = (value?: string) => (value ? Number.parseInt(value, 10) : undefined);

export const GatewayNode = memo(({ id, data }: NodeProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [label, setLabel] = useState(data.label);
  const updateNodeLabel = useArchitectStore((state) => state.updateNodeLabel);

  // 获取样式配置
  const nodeStyle = useNodeStyle("gateway", data.shape, (data as any)?.color);

  const shape: NodeShape = (data.shape as NodeShape) || "diamond";
  const isDiamond = shape === "diamond";
  const shapeConfig = SHAPE_CONFIG[shape];

  const size = toNumber(shapeConfig.width as string) ?? 88;
  const borderColor = nodeStyle.borderColor;
  const backgroundColor = nodeStyle.container.backgroundColor;

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
      <div
        className="diamond-node svg-shape-node relative"
        style={{
          width: `${size}px`,
          height: `${size}px`,
          pointerEvents: 'auto',  // 确保鼠标事件正常
        }}
      >
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          style={{
            filter: "drop-shadow(0 10px 18px rgba(15, 23, 42, 0.16))",
            display: 'block',  // 避免 inline 元素的基线问题
          }}
        >
          <polygon points={points} fill={backgroundColor} stroke={borderColor} strokeWidth={3} />
          <g stroke={borderColor} strokeWidth={3} strokeLinecap="round">
            <line x1={size * 0.34} y1={size * 0.34} x2={size * 0.66} y2={size * 0.66} />
            <line x1={size * 0.34} y1={size * 0.66} x2={size * 0.66} y2={size * 0.34} />
          </g>
        </svg>

        {/* 判断节点专用连接点配置 - 清晰的入口和出口分离 */}
        {/* 入口: 上方和左侧 (用于流程流入) */}
        <Handle
          id="in-top"
          type="target"
          position={Position.Top}
          style={{
            backgroundColor: borderColor,
            position: "absolute",
            top: "3%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: "10px",
            height: "10px",
            border: `2px solid ${borderColor}`,
          }}
        />
        <Handle
          id="in-left"
          type="target"
          position={Position.Left}
          style={{
            backgroundColor: borderColor,
            position: "absolute",
            top: "50%",
            left: "3%",
            transform: "translate(-50%, -50%)",
            width: "10px",
            height: "10px",
            border: `2px solid ${borderColor}`,
          }}
        />

        {/* 出口: 右侧(Yes)和下方(No) - 判断节点的标准输出 */}
        <Handle
          id="out-right-yes"
          type="source"
          position={Position.Right}
          style={{
            backgroundColor: "#10b981",  // 绿色表示 Yes/True
            position: "absolute",
            top: "50%",
            right: "3%",
            transform: "translate(50%, -50%)",
            width: "10px",
            height: "10px",
            border: "2px solid #10b981",
          }}
        />
        <Handle
          id="out-bottom-no"
          type="source"
          position={Position.Bottom}
          style={{
            backgroundColor: "#ef4444",  // 红色表示 No/False
            position: "absolute",
            bottom: "3%",
            left: "50%",
            transform: "translate(-50%, 50%)",
            width: "10px",
            height: "10px",
            border: "2px solid #ef4444",
          }}
        />
      </div>
    );
  }

  return (
    <div
      className="gateway-node-box glass-node"
      style={nodeStyle.container}
    >
      <Handle
        type="target"
        position={Position.Left}
        style={{ backgroundColor: borderColor }}
      />

      {/* 只在非专业模式下显示装饰条 */}
      {nodeStyle.showIcons && (
        <span
          className="absolute left-2 top-2 h-[calc(100%-16px)] w-[5px] rounded-full opacity-80"
          style={{ backgroundColor: borderColor }}
        />
      )}

      <div className="flex items-center gap-3" style={{
        justifyContent: nodeStyle.showIcons ? "flex-start" : "center",
      }}>
        {/* 只在showIcons为true时显示图标 */}
        {nodeStyle.showIcons && (
          <Shield
            className="h-5 w-5 transition-transform duration-200 hover:scale-110"
            style={{ color: borderColor }}
          />
        )}

        <div className="flex-1" style={{
          textAlign: nodeStyle.showIcons ? "left" : "center",
        }}>
          {isEditing ? (
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              autoFocus
              className="nodrag bg-transparent border-b-2 outline-none"
              style={{
                ...nodeStyle.typography,
                borderColor: borderColor,
                width: `${Math.max(label.length, 8)}ch`,
              }}
            />
          ) : (
            <div
              onDoubleClick={handleDoubleClick}
              className="cursor-text"
              style={nodeStyle.typography}
            >
              {data.label}
            </div>
          )}
        </div>
      </div>

      <Handle
        type="source"
        position={Position.Right}
        style={{ backgroundColor: borderColor }}
      />
    </div>
  );
});

GatewayNode.displayName = "GatewayNode";
