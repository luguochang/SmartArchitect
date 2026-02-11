"use client";

/**
 * ShapeRenderer - 统一的节点形状渲染组件
 *
 * 用于在节点库预览和画布上渲染一致的节点形状
 * 支持所有节点类型：基础形状、流程图、BPMN、架构组件
 */

import React from "react";
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
  HardDrive,
} from "lucide-react";
import { NodeShape, SHAPE_CONFIG } from "@/lib/utils/nodeShapes";
import { SvgShape } from "./SvgShapes";

// 图标映射表
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
  storage: HardDrive,
  layerFrame: Layers,
  client: Monitor,
};

export interface ShapeRendererProps {
  shape: NodeShape;
  iconType?: string;
  label?: string;
  color?: string;
  size?: "small" | "medium" | "large";
  showLabel?: boolean;
  showIcon?: boolean;
  className?: string;
}

/**
 * ShapeRenderer Component
 *
 * @param shape - 节点形状类型
 * @param iconType - 图标类型（可选）
 * @param label - 节点标签（可选）
 * @param color - 自定义颜色（可选）
 * @param size - 渲染尺寸：small(预览), medium(默认), large(画布)
 * @param showLabel - 是否显示标签
 * @param showIcon - 是否显示图标
 */
export const ShapeRenderer: React.FC<ShapeRendererProps> = ({
  shape = "rectangle",
  iconType,
  label,
  color = "#2563eb",
  size = "small",
  showLabel = false,
  showIcon = true,
  className = "",
}) => {
  const shapeConfig = SHAPE_CONFIG[shape] || SHAPE_CONFIG["rectangle"];

  // 根据size调整尺寸
  const sizeScale = size === "small" ? 0.4 : size === "medium" ? 0.7 : 1;
  const width = parseInt(shapeConfig.width || "140px") * sizeScale;
  const height = parseInt(shapeConfig.height || "80px") * sizeScale;

  // 解析颜色
  const borderColor = color;
  const backgroundColor = applyAlpha(color, 0.12);

  // 获取图标组件
  const IconComponent = iconType && ICON_MAP[iconType] ? ICON_MAP[iconType] : ICON_MAP[shape];

  const iconSize = size === "small" ? 16 : size === "medium" ? 20 : 24;
  const fontSize = size === "small" ? 10 : size === "medium" ? 12 : 14;

  // 渲染图标
  const renderIcon = () => {
    if (!showIcon || !IconComponent) return null;
    return (
      <IconComponent
        style={{
          color: borderColor,
          width: `${iconSize}px`,
          height: `${iconSize}px`,
          flexShrink: 0,
        }}
      />
    );
  };

  // 渲染标签
  const renderLabel = () => {
    if (!showLabel || !label) return null;
    return (
      <span
        style={{
          fontSize: `${fontSize}px`,
          fontWeight: 500,
          color: borderColor,
          whiteSpace: "nowrap",
          overflow: "hidden",
          textOverflow: "ellipsis",
          maxWidth: size === "small" ? "60px" : "100%",
        }}
      >
        {label}
      </span>
    );
  };

  // BPMN Start Event
  if (shape === "start-event" || shape === "bpmn-start-event") {
    const circleSize = Math.min(width, height);
    return (
      <div
        className={`flex items-center justify-center rounded-full ${className}`}
        style={{
          width: `${circleSize}px`,
          height: `${circleSize}px`,
          border: `2px solid ${borderColor}`,
          background: backgroundColor,
          boxShadow: size !== "small" ? "0 2px 4px rgba(0,0,0,0.1)" : "none",
        }}
      >
        {renderIcon()}
      </div>
    );
  }

  // BPMN End Event
  if (shape === "end-event" || shape === "bpmn-end-event") {
    const circleSize = Math.min(width, height);
    return (
      <div
        className={`flex items-center justify-center rounded-full ${className}`}
        style={{
          width: `${circleSize}px`,
          height: `${circleSize}px`,
          border: `4px solid ${borderColor}`,
          background: backgroundColor,
          boxShadow: size !== "small" ? "0 2px 4px rgba(0,0,0,0.1)" : "none",
        }}
      >
        {renderIcon()}
      </div>
    );
  }

  // BPMN Intermediate Event
  if (shape === "intermediate-event" || shape === "bpmn-intermediate-event") {
    const circleSize = Math.min(width, height);
    const ringGap = size === "small" ? 3 : 5;
    return (
      <div
        className={`relative flex items-center justify-center ${className}`}
        style={{ width: `${circleSize}px`, height: `${circleSize}px` }}
      >
        <div
          className="absolute inset-0 rounded-full"
          style={{
            border: `2px solid ${borderColor}`,
            background: backgroundColor,
          }}
        />
        <div
          className="absolute rounded-full flex items-center justify-center"
          style={{
            top: `${ringGap}px`,
            left: `${ringGap}px`,
            right: `${ringGap}px`,
            bottom: `${ringGap}px`,
            border: `2px solid ${borderColor}`,
            background: backgroundColor,
          }}
        >
          {renderIcon()}
        </div>
      </div>
    );
  }

  // BPMN Task
  if (shape === "task" || shape === "bpmn-task") {
    return (
      <div
        className={`flex items-center gap-2 rounded-xl ${className}`}
        style={{
          width: `${width}px`,
          height: `${height}px`,
          border: `2px solid ${borderColor}`,
          background: backgroundColor,
          padding: size === "small" ? "4px 6px" : "8px 12px",
          boxShadow: size !== "small" ? "0 2px 4px rgba(0,0,0,0.1)" : "none",
        }}
      >
        {showIcon && (
          <span
            className="flex-shrink-0 h-full rounded"
            style={{
              width: "4px",
              backgroundColor: borderColor,
              opacity: 0.9,
            }}
          />
        )}
        {renderIcon()}
        {renderLabel()}
      </div>
    );
  }

  // Circle
  if (shape === "circle" || shape === "start" || shape === "end") {
    const circleSize = Math.min(width, height);
    const borderWidth = shape === "end" ? "3px" : "2px";
    return (
      <div
        className={`flex flex-col items-center justify-center gap-1 rounded-full ${className}`}
        style={{
          width: `${circleSize}px`,
          height: `${circleSize}px`,
          border: `${borderWidth} solid ${borderColor}`,
          background: backgroundColor,
          boxShadow: size !== "small" ? "0 2px 4px rgba(0,0,0,0.1)" : "none",
          padding: size === "small" ? "4px" : "8px",
        }}
      >
        {renderIcon()}
        {renderLabel()}
      </div>
    );
  }

  // SVG-based shapes (diamond, hexagon, star, etc.)
  if (shapeConfig.renderMethod === "svg") {
    return (
      <div
        className={`relative ${className}`}
        style={{
          width: `${width}px`,
          height: `${height}px`,
          backgroundColor: "transparent",
        }}
      >
        <SvgShape
          shape={shape}
          width={width}
          height={height}
          borderColor={borderColor}
          backgroundColor={backgroundColor}
          strokeWidth={2}
        />
        <div
          className="absolute inset-0 flex flex-col items-center justify-center gap-1"
          style={{ padding: size === "small" ? "4px" : "8px" }}
        >
          {renderIcon()}
          {renderLabel()}
        </div>
      </div>
    );
  }

  // CSS-based shapes (rectangle, rounded rectangle, etc.)
  const borderRadius = shapeConfig.className?.includes("rounded-2xl")
    ? "16px"
    : shapeConfig.className?.includes("rounded-xl")
    ? "12px"
    : shapeConfig.className?.includes("rounded-lg")
    ? "8px"
    : "4px";

  return (
    <div
      className={`flex flex-col items-center justify-center gap-1 ${className}`}
      style={{
        width: `${width}px`,
        height: `${height}px`,
        border: `2px solid ${borderColor}`,
        borderRadius,
        background: backgroundColor,
        padding: size === "small" ? "4px" : "8px 12px",
        boxShadow: size !== "small" ? "0 2px 4px rgba(0,0,0,0.1)" : "none",
      }}
    >
      {renderIcon()}
      {renderLabel()}
    </div>
  );
};

// 辅助函数：应用透明度
function applyAlpha(color: string, alpha: number): string {
  if (color.startsWith("#") && (color.length === 7 || color.length === 4)) {
    const hex =
      color.length === 4
        ? `#${color[1]}${color[1]}${color[2]}${color[2]}${color[3]}${color[3]}`
        : color;
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  return color;
}
