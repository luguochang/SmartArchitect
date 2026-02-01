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
  Square,
  Circle as CircleIcon,
  Diamond as DiamondIcon,
  Hexagon as HexagonIcon,
  Triangle as TriangleIcon,
  Star as StarIcon,
  Cloud as CloudIcon,
  Octagon,
  Database,
  FileText,
  Layers,
  Shield,
  Globe,
  Monitor,
  Server,
  Network,
  Container as ContainerIcon,
  Folder,
  Package,
  Cpu,
  Activity,
  Zap,
  Wifi,
  Lock,
  Users,
  Smartphone,
} from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { NodeShape, SHAPE_CONFIG } from "@/lib/utils/nodeShapes";
import { SvgShape } from "./SvgShapes";
import { useNodeStyle } from "@/lib/hooks/useNodeStyle";

const DEFAULT_SHAPE_CONFIG = {
  width: "140px",
  height: "80px",
  padding: "px-4 py-3",
  className: "glass-node rounded-lg bg-white",
  borderWidth: "2px",
  renderMethod: "css" as const,
};

const ICON_MAP: Record<string, any> = {
  "play-circle": PlayCircle,
  "stop-circle": StopCircle,
  "alert-circle": AlertCircle,
  "check-circle": CheckCircle,
  "x-circle": XCircle,
  "pause-circle": PauseCircle,
  square: Square,
  circle: CircleIcon,
  diamond: DiamondIcon,
  hexagon: HexagonIcon,
  triangle: TriangleIcon,
  star: StarIcon,
  cloud: CloudIcon,
  rectangle: Square,
  "rounded-rectangle": Box,
  process: Box,
  decision: DiamondIcon,
  data: Square,
  subprocess: Box,
  delay: AlertCircle,
  merge: Layers,
  "manual-input": Square,
  "manual-operation": Square,
  preparation: HexagonIcon,
  or: Octagon,
  container: ContainerIcon,
  frame: Square,
  "swimlane-horizontal": Layers,
  "swimlane-vertical": Layers,
  note: FileText,
  folder: Folder,
  package: Package,
  user: Users,
  users: Users,
  mobile: Smartphone,
  desktop: Monitor,
  tablet: Monitor,
  iot: Cpu,
  network: Network,
  "load-balancer": Activity,
  firewall: Lock,
  cdn: Network,
  database: Database,
  "file-text": FileText,
  layers: Layers,
  shield: Shield,
  globe: Globe,
  monitor: Monitor,
  server: Server,
  cpu: Cpu,
  activity: Activity,
  wifi: Wifi,
  lock: Lock,
  api: Globe,
  gateway: Shield,
  service: Box,
  cache: Zap,
  queue: Layers,
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
  const shapeConfig = SHAPE_CONFIG[shape] || DEFAULT_SHAPE_CONFIG;

  // 获取样式配置
  const nodeStyle = useNodeStyle(undefined, shape, (data as any)?.color);

  const borderColor = nodeStyle.borderColor;
  const backgroundColor = nodeStyle.container.backgroundColor;
  const iconType = (data as any)?.iconType || data.type;
  const IconComponent = iconType && ICON_MAP[iconType] ? ICON_MAP[iconType] : null;

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

  const renderOrthogonalHandles = (color: string) => (
    <>
      <Handle
        id="target-top"
        type="target"
        position={Position.Top}
        style={{ backgroundColor: color, top: 0, left: "50%", transform: "translate(-50%, -50%)" }}
      />
      <Handle
        id="target-left"
        type="target"
        position={Position.Left}
        style={{ backgroundColor: color, top: "50%", left: 0, transform: "translate(-50%, -50%)" }}
      />
      <Handle
        id="source-right"
        type="source"
        position={Position.Right}
        style={{ backgroundColor: color, top: "50%", right: 0, transform: "translate(50%, -50%)" }}
      />
      <Handle
        id="source-bottom"
        type="source"
        position={Position.Bottom}
        style={{ backgroundColor: color, bottom: 0, left: "50%", transform: "translate(-50%, 50%)" }}
      />
    </>
  );

  const renderCircularHandles = (color: string) => (
    <>
    <Handle
      id="target-top"
      type="target"
      position={Position.Top}
      style={{ backgroundColor: color, top: 0, left: "50%", transform: "translate(-50%, -50%)" }}
    />
    <Handle
      id="source-right"
      type="source"
      position={Position.Right}
      style={{ backgroundColor: color, top: "50%", right: 0, transform: "translate(50%, -50%)" }}
    />
    <Handle
      id="target-bottom"
      type="target"
      position={Position.Bottom}
      style={{ backgroundColor: color, bottom: 0, left: "50%", transform: "translate(-50%, 50%)" }}
    />
    <Handle
      id="source-left"
      type="source"
      position={Position.Left}
      style={{ backgroundColor: color, top: "50%", left: 0, transform: "translate(-50%, -50%)" }}
    />
  </>
);

  const renderCenterLabel = (fontSize?: number) => (
    <div
      style={{
        ...nodeStyle.typography,
        fontSize: fontSize ? `${fontSize}px` : nodeStyle.typography.fontSize,
        textAlign: "center",
      }}
    >
      {data.label}
    </div>
  );
  const renderIcon = (size = 20) => {
    if (!nodeStyle.showIcons) return null;
    if (IconComponent) {
      return <IconComponent style={{ color: borderColor, width: `${size}px`, height: `${size}px` }} />;
    }
    const fallback =
      (data as any)?.iconLabel ||
      (typeof data.label === "string" && data.label.trim() ? data.label.trim().charAt(0).toUpperCase() : "·");
    return (
      <span
        className="flex items-center justify-center text-xs font-semibold"
        style={{ color: borderColor, width: `${size}px`, height: `${size}px` }}
      >
        {fallback}
      </span>
    );
  };

  // Start Event – thin ring
  if (shape === "start-event") {
    const size = shapeConfig.width || "56px";
    const ringWidth = nodeStyle.container.borderWidth;

    return (
      <div
        className="glass-node relative flex items-center justify-center rounded-full transition-all duration-150"
        style={{
          width: size,
          height: size,
          border: `${ringWidth} solid ${borderColor}`,
          background: backgroundColor,
          boxShadow: nodeStyle.container.boxShadow,
        }}
      >
        {renderCircularHandles(borderColor)}
        {renderCenterLabel(12)}
      </div>
    );
  }

  // End Event – thick ring
  if (shape === "end-event") {
    const size = shapeConfig.width || "56px";
    const ringWidth = "4px"; // Thick ring for end event

    return (
      <div
        className="glass-node relative flex items-center justify-center rounded-full transition-all duration-150"
        style={{
          width: size,
          height: size,
          border: `${ringWidth} solid ${borderColor}`,
          background: backgroundColor,
          boxShadow: nodeStyle.container.boxShadow,
        }}
      >
        {renderCircularHandles(borderColor)}
        {renderCenterLabel(12)}
      </div>
    );
  }

  // Intermediate Event – double ring
  if (shape === "intermediate-event") {
    const size = shapeConfig.width || "56px";
    const ringWidth = toNumber(nodeStyle.container.borderWidth as string) ?? 2;
    const ringGap = toNumber((shapeConfig as any).ringGap) ?? 5;

    return (
      <div className="glass-node relative flex items-center justify-center" style={{ width: size, height: size }}>
        <div
          className="absolute inset-0 rounded-full"
          style={{
            border: `${ringWidth}px solid ${borderColor}`,
            background: backgroundColor,
            boxShadow: nodeStyle.container.boxShadow,
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
            background: backgroundColor,
            ...nodeStyle.typography,
          }}
        >
          {renderCenterLabel(12)}
        </div>
        {renderCircularHandles(borderColor)}
      </div>
    );
  }

  // Task – rounded card with accent bar
  if (shape === "task") {
    return (
      <div
        className="glass-node relative flex items-center gap-3"
        style={{
          ...nodeStyle.container,
          width: shapeConfig.width,
          height: shapeConfig.height,
          justifyContent: nodeStyle.showIcons ? "flex-start" : "center",
          padding: nodeStyle.showIcons ? "12px 16px 12px 22px" : "12px 16px",
        }}
      >
        {renderOrthogonalHandles(borderColor)}

        {/* 只在showIcons为true时显示装饰条 */}
        {nodeStyle.showIcons && (
          <span
            className="absolute left-3 top-1/2 -translate-y-1/2 h-10 w-[6px] rounded-full"
            style={{ backgroundColor: borderColor, opacity: 0.9 }}
          />
        )}

        {/* 只在showIcons为true时显示图标 */}
        {nodeStyle.showIcons && <div className="flex flex-col items-center gap-1">{renderIcon(20)}</div>}

        <div
          className="flex flex-col gap-1 w-full"
          style={{
            paddingLeft: nodeStyle.showIcons ? "4px" : "0",
            textAlign: nodeStyle.showIcons ? "left" : "center",
          }}
        >
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
                ...nodeStyle.typography,
                borderColor: borderColor,
              }}
            />
          ) : (
            <div onDoubleClick={handleDoubleClick} className="cursor-text" style={nodeStyle.typography}>
              {data.label}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Legacy circle
  if (shape === "circle") {
    return (
      <div
        className={`${shapeConfig.className} shadow-lg`}
        style={{
          width: shapeConfig.width,
          height: shapeConfig.height,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          borderColor: borderColor,
          borderWidth: nodeStyle.container.borderWidth,
          borderStyle: "solid",
          backgroundColor: backgroundColor,
          boxShadow: nodeStyle.container.boxShadow,
        }}
      >
        {renderCircularHandles(borderColor)}

        <div className="flex flex-col items-center justify-center text-center px-2">
          {isEditing ? (
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              autoFocus
              className="nodrag bg-transparent border-b outline-none text-center"
              style={{
                ...nodeStyle.typography,
                borderColor: borderColor,
                width: "70px",
              }}
            />
          ) : (
            <div onDoubleClick={handleDoubleClick} className="cursor-text" style={nodeStyle.typography}>
              {data.label}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Fallback rendering with SVG support
  const width = parseInt(shapeConfig.width || "140px");
  const height = parseInt(shapeConfig.height || "80px");

  // SVG-based shapes (diamond, hexagon, star, etc.)
  if (shapeConfig.renderMethod === "svg") {
    return (
      <div
        className="svg-shape-node"
        style={{
          position: "relative",
          width: shapeConfig.width,
          height: shapeConfig.height,
          backgroundColor: "transparent",
          border: "none",
          padding: 0,
          overflow: "visible",
        }}
      >
        {/* SVG shape background */}
        <SvgShape
          shape={shape}
          width={width}
          height={height}
          borderColor={borderColor}
          backgroundColor={backgroundColor}
          strokeWidth={2}
        />
        {/* Handles - separate in/out anchors */}
        {renderOrthogonalHandles(borderColor)}

        {/* Content overlay */}
        <div
          className="flex flex-col items-center justify-center text-center px-2"
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            width: "100%",
            height: "100%",
            pointerEvents: "auto",
          }}
        >
          {isEditing ? (
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              onBlur={handleBlur}
              onKeyDown={handleKeyDown}
              autoFocus
              className="nodrag bg-transparent border-b outline-none text-center mt-1"
              style={{
                ...nodeStyle.typography,
                borderColor: borderColor,
                width: `${Math.min(width - 20, 100)}px`,
              }}
            />
          ) : (
            <div
              onDoubleClick={handleDoubleClick}
              className="cursor-text mt-1"
              style={{
                ...nodeStyle.typography,
                maxWidth: `${width - 20}px`,
                wordBreak: "break-word",
              }}
            >
              {data.label}
            </div>
          )}
        </div>
      </div>
    );
  }

  // CSS-based shapes (rectangle, circle, rounded rectangle, etc.)
  return (
    <div
      className="glass-node"
      style={{
        ...nodeStyle.container,
        width: shapeConfig.width,
        height: shapeConfig.height,
        }}
      >
        {renderOrthogonalHandles(borderColor)}

        <div
          className="flex items-center gap-2"
          style={{
            justifyContent: nodeStyle.showIcons ? "flex-start" : "center",
            height: "100%",
          }}
        >
        <div
          style={{
            textAlign: nodeStyle.showIcons ? "left" : "center",
            flex: 1,
          }}
        >
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
            <div onDoubleClick={handleDoubleClick} className="cursor-text" style={nodeStyle.typography}>
              {data.label}
            </div>
          )}
        </div>
      </div>
    </div>
  );
});

DefaultNode.displayName = "DefaultNode";
