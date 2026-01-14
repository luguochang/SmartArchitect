// SVG Shapes for React Flow nodes
import React from "react";

export interface SvgShapeProps {
  shape: string;
  width: number;
  height: number;
  borderColor: string;
  backgroundColor: string;
  strokeWidth?: number;
  children?: React.ReactNode;
}

export const SvgShape: React.FC<SvgShapeProps> = ({
  shape,
  width,
  height,
  borderColor,
  backgroundColor,
  strokeWidth = 2,
  children,
}) => {
  const renderPath = () => {
    const w = width;
    const h = height;

    switch (shape) {
      case "diamond":
      case "decision":
      case "bpmn-gateway":
        // Diamond: 4 points
        return `M ${w / 2} 0 L ${w} ${h / 2} L ${w / 2} ${h} L 0 ${h / 2} Z`;

      case "hexagon":
      case "preparation":
        // Hexagon: 6 points
        const offset = w * 0.2;
        return `M ${offset} 0 L ${w - offset} 0 L ${w} ${h / 2} L ${w - offset} ${h} L ${offset} ${h} L 0 ${h / 2} Z`;

      case "triangle":
        // Triangle: 3 points (equilateral)
        return `M ${w / 2} 0 L ${w} ${h} L 0 ${h} Z`;

      case "parallelogram":
      case "data":
        // Parallelogram (slanted rectangle)
        const slant = w * 0.15;
        return `M ${slant} 0 L ${w} 0 L ${w - slant} ${h} L 0 ${h} Z`;

      case "trapezoid":
      case "manual-operation":
        // Trapezoid (wider at bottom)
        const topInset = w * 0.15;
        return `M ${topInset} 0 L ${w - topInset} 0 L ${w} ${h} L 0 ${h} Z`;

      case "manual-input":
        // Manual input (slanted top)
        const topSlant = h * 0.2;
        return `M 0 ${topSlant} L ${w} 0 L ${w} ${h} L 0 ${h} Z`;

      case "star":
        // 5-point star
        const cx = w / 2;
        const cy = h / 2;
        const outerRadius = Math.min(w, h) / 2;
        const innerRadius = outerRadius * 0.4;
        const points = 5;
        let starPath = "";
        for (let i = 0; i < points * 2; i++) {
          const radius = i % 2 === 0 ? outerRadius : innerRadius;
          const angle = (Math.PI / points) * i - Math.PI / 2;
          const x = cx + radius * Math.cos(angle);
          const y = cy + radius * Math.sin(angle);
          starPath += `${i === 0 ? "M" : "L"} ${x} ${y} `;
        }
        starPath += "Z";
        return starPath;

      case "cloud":
        // Cloud shape (approximated with bezier curves)
        return `M ${w * 0.25} ${h * 0.4}
                Q ${w * 0.15} ${h * 0.15} ${w * 0.35} ${h * 0.2}
                Q ${w * 0.5} ${h * 0.05} ${w * 0.65} ${h * 0.2}
                Q ${w * 0.85} ${h * 0.15} ${w * 0.75} ${h * 0.4}
                Q ${w * 0.9} ${h * 0.7} ${w * 0.65} ${h * 0.75}
                L ${w * 0.35} ${h * 0.75}
                Q ${w * 0.1} ${h * 0.7} ${w * 0.25} ${h * 0.4} Z`;

      case "document":
        // Document with wavy bottom
        return `M 0 0 L ${w} 0 L ${w} ${h * 0.85}
                Q ${w * 0.75} ${h * 0.95} ${w * 0.5} ${h * 0.85}
                Q ${w * 0.25} ${h * 0.75} 0 ${h * 0.85} Z`;

      case "delay":
        // Delay (rounded rectangle on right)
        const radius = h / 2;
        return `M 0 0 L ${w - radius} 0
                Q ${w} 0 ${w} ${radius}
                Q ${w} ${h} ${w - radius} ${h}
                L 0 ${h} Z`;

      case "merge":
      case "or":
        // Circle (fallback)
        const r = Math.min(w, h) / 2;
        return `M ${w / 2} ${r}
                A ${r} ${r} 0 1 1 ${w / 2} ${h - r}
                A ${r} ${r} 0 1 1 ${w / 2} ${r} Z`;

      case "folder":
        // Folder shape
        const tabWidth = w * 0.4;
        const tabHeight = h * 0.2;
        return `M 0 ${tabHeight} L 0 ${h} L ${w} ${h} L ${w} ${tabHeight} L ${tabWidth} ${tabHeight} L ${tabWidth * 0.8} 0 L 0 0 Z`;

      case "cylinder":
        // Cylinder (ellipse top + rectangle + ellipse bottom)
        const ellipseHeight = h * 0.15;
        return `M 0 ${ellipseHeight}
                L 0 ${h - ellipseHeight}
                Q 0 ${h} ${w / 2} ${h}
                Q ${w} ${h} ${w} ${h - ellipseHeight}
                L ${w} ${ellipseHeight}
                Q ${w} 0 ${w / 2} 0
                Q 0 0 0 ${ellipseHeight} Z`;

      case "network":
        // Network icon (diamond + circle)
        return `M ${w / 2} 0 L ${w} ${h / 2} L ${w / 2} ${h} L 0 ${h / 2} Z`;

      default:
        // Rectangle fallback
        return `M 0 0 L ${w} 0 L ${w} ${h} L 0 ${h} Z`;
    }
  };

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      style={{ position: "absolute", top: 0, left: 0, pointerEvents: "none" }}
    >
      <path
        d={renderPath()}
        fill={backgroundColor}
        stroke={borderColor}
        strokeWidth={strokeWidth}
        style={{
          filter: "drop-shadow(0 4px 6px rgba(0, 0, 0, 0.1))",
        }}
      />
    </svg>
  );
};
