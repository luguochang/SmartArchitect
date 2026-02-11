"use client";

/**
 * NodePreview - 节点库图标预览组件
 *
 * 专门用于左侧工具栏的节点图标展示，提供更好的视觉效果
 * 与画布上的 ShapeRenderer 分离，允许独立优化样式
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
import { NodeShape } from "@/lib/utils/nodeShapes";

// 图标映射表 - 与 ShapeRenderer 保持一致
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

export interface NodePreviewProps {
  shape: NodeShape;
  iconType?: string;
  color?: string;
  className?: string;
}

/**
 * NodePreview Component
 *
 * 为左侧工具栏提供美观的节点图标预览
 *
 * @param shape - 节点形状类型
 * @param iconType - 图标类型（可选）
 * @param color - 主题颜色
 * @param className - 额外的 CSS 类名
 */
export const NodePreview: React.FC<NodePreviewProps> = ({
  shape = "rectangle",
  iconType,
  color = "#2563eb",
  className = "",
}) => {
  // 获取图标组件
  const IconComponent = iconType && ICON_MAP[iconType]
    ? ICON_MAP[iconType]
    : ICON_MAP[shape] || Square;

  // 解析颜色为 RGB 用于渐变背景
  const rgbaBackground = hexToRgba(color, 0.08);
  const rgbaBorder = hexToRgba(color, 0.2);

  return (
    <div
      className={`
        relative flex items-center justify-center
        w-16 h-16 rounded-xl
        transition-all duration-200
        ${className}
      `}
      style={{
        background: `linear-gradient(135deg, ${rgbaBackground} 0%, ${hexToRgba(color, 0.03)} 100%)`,
        border: `1.5px solid ${rgbaBorder}`,
        boxShadow: `0 1px 3px rgba(0,0,0,0.05)`,
      }}
    >
      {/* 主图标 */}
      <IconComponent
        className="relative z-10"
        style={{
          color: color,
          width: "28px",
          height: "28px",
          strokeWidth: 2,
        }}
      />

      {/* 背景装饰圆点 */}
      <div
        className="absolute top-2 right-2 w-1.5 h-1.5 rounded-full opacity-30"
        style={{ backgroundColor: color }}
      />
      <div
        className="absolute bottom-2 left-2 w-1 h-1 rounded-full opacity-20"
        style={{ backgroundColor: color }}
      />
    </div>
  );
};

/**
 * 辅助函数：将 HEX 颜色转换为 RGBA
 */
function hexToRgba(hex: string, alpha: number): string {
  // 移除 # 符号
  hex = hex.replace(/^#/, "");

  // 支持缩写格式 (#RGB -> #RRGGBB)
  if (hex.length === 3) {
    hex = hex.split("").map(char => char + char).join("");
  }

  // 解析 RGB 值
  const r = parseInt(hex.slice(0, 2), 16);
  const g = parseInt(hex.slice(2, 4), 16);
  const b = parseInt(hex.slice(4, 6), 16);

  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
