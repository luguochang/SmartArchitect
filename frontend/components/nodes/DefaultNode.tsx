"use client";

import { memo, useState, useCallback } from "react";
import { Handle, Position, NodeProps } from "reactflow";
import {
  Box,
  PlayCircle,
  StopCircle,
  AlertCircle,
  CheckCircle,
  XCircle,
  PauseCircle,
} from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { NodeShape, SHAPE_CONFIG } from "@/lib/utils/nodeShapes";

const ICON_MAP: Record<string, any> = {
  "play-circle": PlayCircle,
  "stop-circle": StopCircle,
  "alert-circle": AlertCircle,
  "check-circle": CheckCircle,
  "x-circle": XCircle,
  "pause-circle": PauseCircle,
  box: Box,
};

const EVENT_BG = "var(--bpmn-event-bg, #ffffff)";
const TASK_BG = "var(--bpmn-task-bg, #f8fafc)";
const TASK_BORDER = "var(--bpmn-task-border, #e2e8f0)";
const SHADOW_SOFT = "var(--bpmn-shadow-soft, 0 12px 30px -12px rgba(15, 23, 42, 0.25))";

const toNumber = (value?: string) => (value ? Number.parseInt(value, 10) : undefined);

export const DefaultNode = memo(({ id, data }: NodeProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [label, setLabel] = useState(data.label);
  const updateNodeLabel = useArchitectStore((state) => state.updateNodeLabel);

  const shape: NodeShape = (data.shape as NodeShape) || "rectangle";
  const shapeConfig = SHAPE_CONFIG[shape];

  const IconComponent = data.iconType && ICON_MAP[data.iconType] ? ICON_MAP[data.iconType] : null;
  const iconColor = data.color || "var(--default-icon)";
  const borderColor = data.color || "var(--default-border)";
  const iconFallbackLabel =
    (data as any)?.iconLabel ||
    (typeof data.label === "string" && data.label.trim() ? data.label.trim().charAt(0).toUpperCase() : "·");

  const renderIcon = (size = 20) =>
    IconComponent ? (
      <IconComponent style={{ color: iconColor, width: `${size}px`, height: `${size}px` }} />
    ) : (
      <span
        className="flex items-center justify-center rounded-full bg-white/80 text-xs font-semibold shadow-sm dark:bg-slate-800/80"
        style={{ color: iconColor, width: `${size}px`, height: `${size}px` }}
      >
        {iconFallbackLabel}
      </span>
    );

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

  const renderCircularHandles = (color: string) => (
    <>
      <Handle
        type="target"
        position={Position.Top}
        style={{ backgroundColor: color, top: 0, left: "50%", transform: "translate(-50%, -50%)" }}
      />
      <Handle
        type="source"
        position={Position.Right}
        style={{ backgroundColor: color, top: "50%", right: 0, transform: "translate(50%, -50%)" }}
      />
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ backgroundColor: color, bottom: 0, left: "50%", transform: "translate(-50%, 50%)" }}
      />
      <Handle
        type="source"
        position={Position.Left}
        style={{ backgroundColor: color, top: "50%", left: 0, transform: "translate(-50%, -50%)" }}
      />
    </>
  );

  // Start Event – thin ring
  if (shape === "start-event") {
    const size = shapeConfig.width || "56px";
    const ringWidth = shapeConfig.borderWidth || "2px";

    return (
      <div
        className="glass-node relative flex items-center justify-center rounded-full transition-all duration-150"
        style={{
          width: size,
          height: size,
          border: `${ringWidth} solid ${borderColor}`,
          background: EVENT_BG,
          boxShadow: SHADOW_SOFT,
        }}
      >
        {renderCircularHandles(borderColor)}
        {renderIcon(22)}
      </div>
    );
  }

  // End Event – thick ring
  if (shape === "end-event") {
    const size = shapeConfig.width || "56px";
    const ringWidth = shapeConfig.borderWidth || "4px";

    return (
      <div
        className="glass-node relative flex items-center justify-center rounded-full transition-all duration-150"
        style={{
          width: size,
          height: size,
          border: `${ringWidth} solid ${borderColor}`,
          background: EVENT_BG,
          boxShadow: SHADOW_SOFT,
        }}
      >
        {renderCircularHandles(borderColor)}
        {renderIcon(22)}
      </div>
    );
  }

  // Intermediate Event – double ring
  if (shape === "intermediate-event") {
    const size = shapeConfig.width || "56px";
    const ringWidth = toNumber(shapeConfig.borderWidth as string) ?? 2;
    const ringGap = toNumber((shapeConfig as any).ringGap) ?? 5;

    return (
      <div className="glass-node relative flex items-center justify-center" style={{ width: size, height: size }}>
        <div
          className="absolute inset-0 rounded-full"
          style={{
            border: `${ringWidth}px solid ${borderColor}`,
            background: EVENT_BG,
            boxShadow: SHADOW_SOFT,
          }}
        />
        <div
          className="absolute rounded-full flex items-center justify-center"
          style={{
            top: `${ringGap}px`,
            left: `${ringGap}px`,
            right: `${ringGap}px`,
            bottom: `${ringGap}px`,
            border: `${ringWidth}px solid ${borderColor}`,
            background: EVENT_BG,
          }}
        >
          {renderIcon(20)}
        </div>
        {renderCircularHandles(borderColor)}
      </div>
    );
  }

  // Task – rounded card with accent bar
  if (shape === "task") {
    return (
      <div
        className="glass-node relative flex items-center gap-3 rounded-[16px] border transition-all duration-150"
        style={{
          width: shapeConfig.width,
          height: shapeConfig.height,
          borderColor: borderColor || TASK_BORDER,
          background: TASK_BG,
          boxShadow: SHADOW_SOFT,
          padding: "12px 16px 12px 22px",
        }}
      >
        <Handle type="target" position={Position.Left} style={{ backgroundColor: borderColor }} />
        <Handle type="source" position={Position.Right} style={{ backgroundColor: borderColor }} />

        <span
          className="absolute left-3 top-1/2 -translate-y-1/2 h-10 w-[6px] rounded-full"
          style={{ backgroundColor: borderColor, opacity: 0.9 }}
        />

        <div className="flex flex-col items-center gap-1">
          <div className="rounded-lg bg-white/80 px-2 py-1 text-[11px] font-semibold text-slate-600 shadow-sm dark:bg-slate-800/80 dark:text-slate-200">
            TASK
          </div>
          {renderIcon(20)}
        </div>

        <div className="flex flex-col gap-1 w-full pl-1">
          {isEditing ? (
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              autoFocus
              className="nodrag bg-transparent border-b outline-none"
              style={{
                color: iconColor,
                borderColor: borderColor,
                fontSize: "13px",
                fontWeight: 600,
              }}
            />
          ) : (
            <div
              onDoubleClick={handleDoubleClick}
              className="cursor-text"
              style={{
                color: iconColor,
                fontSize: "13px",
                fontWeight: 600,
                lineHeight: 1.35,
              }}
            >
              {data.label}
            </div>
          )}
          <div
            className="text-xs"
            style={{
              color: "var(--muted-foreground)",
              opacity: 0.75,
              fontSize: "11px",
            }}
          >
            Task
          </div>
          <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400">
            <span className="rounded-full bg-slate-100 px-2 py-0.5 dark:bg-slate-800">Task</span>
            <span className="opacity-70">Type: {shape}</span>
          </div>
        </div>
      </div>
    );
  }

  // Legacy circle
  if (shape === "circle") {
    return (
      <div
        className={`${shapeConfig.className} border-2 shadow-lg`}
        style={{
          width: shapeConfig.width,
          height: shapeConfig.height,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          borderColor: borderColor,
          backgroundColor: "var(--default-background, #ffffff)",
          boxShadow: SHADOW_SOFT,
        }}
      >
        {renderCircularHandles(borderColor)}

        <div className="flex flex-col items-center justify-center text-center px-2">
          <IconComponent className="h-5 w-5 mb-1 transition-transform duration-200 hover:scale-110" style={{ color: iconColor }} />
          {isEditing ? (
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              autoFocus
              className="nodrag font-semibold bg-transparent border-b outline-none text-center"
              style={{
                color: "var(--default-text)",
                borderColor: "var(--default-border)",
                fontSize: "10px",
                fontWeight: "var(--font-weight-bold)",
                width: "70px",
              }}
            />
          ) : (
            <div
              onDoubleClick={handleDoubleClick}
              className="font-semibold cursor-text"
              style={{
                color: "var(--default-text)",
                fontSize: "10px",
                fontWeight: "var(--font-weight-bold)",
                lineHeight: "1.2",
              }}
            >
              {data.label}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Rectangle fallback
  return (
    <div
      className={`${shapeConfig.className} border-2 ${shapeConfig.padding} shadow-lg`}
      style={{
        borderColor: borderColor,
        backgroundColor: "var(--default-background, #ffffff)",
        boxShadow: SHADOW_SOFT,
      }}
    >
      <Handle type="target" position={Position.Left} style={{ backgroundColor: borderColor }} />

      <div className="flex items-center gap-2">
        <IconComponent className="h-5 w-5 transition-transform duration-200 hover:scale-110" style={{ color: iconColor }} />
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
                color: "var(--default-text)",
                borderColor: "var(--default-border)",
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
                color: "var(--default-text)",
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
              color: "var(--default-text)",
              opacity: 0.7,
              fontSize: "var(--font-size-label)",
            }}
          >
            Step
          </div>
        </div>
      </div>

      <Handle type="source" position={Position.Right} style={{ backgroundColor: borderColor }} />
    </div>
  );
});

DefaultNode.displayName = "DefaultNode";
