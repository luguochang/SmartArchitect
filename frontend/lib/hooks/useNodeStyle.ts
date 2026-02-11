import { useMemo } from "react";
import { useFlowchartStyleStore } from "@/lib/stores/flowchartStyleStore";

/**
 * 节点样式Hook
 *
 * 为节点提供统一的样式配置，基于当前选择的flowchart presentation style
 */
export function useNodeStyle(nodeType?: string, shape?: string, customColor?: string) {
  const { currentPresentationStyle, currentFontStyle, showIcons } = useFlowchartStyleStore();

  const styles = useMemo(() => {
    // 确定语义类型（start, end, task, decision）
    const semanticType = getSemanticType(nodeType, shape);
    const semanticColors = currentPresentationStyle.node.semanticColors[semanticType] || {
      bg: currentPresentationStyle.node.backgroundColor,
      border: currentPresentationStyle.node.borderColor,
    };

    const normalizedColor = customColor?.trim();
    const borderColor = normalizedColor || semanticColors.border;
    const backgroundColor = normalizedColor
      ? applyAlpha(normalizedColor, 0.12)
      : semanticColors.bg;

    return {
      // 是否显示图标
      showIcons,

      // 节点容器样式
      container: {
        backgroundColor,
        borderColor,
        borderWidth: currentPresentationStyle.node.borderWidth,
        borderStyle: "solid" as const,
        borderRadius: currentPresentationStyle.node.borderRadius,
        boxShadow: currentPresentationStyle.node.boxShadow,
        padding: currentPresentationStyle.node.padding,
      },

      // 文字样式
      typography: {
        fontFamily: currentFontStyle.fontFamily,
        fontSize: currentPresentationStyle.typography.fontSize,
        fontWeight: currentPresentationStyle.typography.fontWeight,
        lineHeight: currentPresentationStyle.typography.lineHeight,
      },

      // 边框颜色（用于handles等）
      borderColor,
    };
  }, [currentPresentationStyle, currentFontStyle, nodeType, shape, customColor]);

  return styles;
}

/**
 * 根据节点类型和形状确定语义类型
 */
function getSemanticType(nodeType?: string, shape?: string): "start" | "end" | "task" | "decision" {
  // 检查节点类型
  if (nodeType === "start-event" || nodeType === "start" || shape === "start-event" || shape === "start") {
    return "start";
  }
  if (nodeType === "end-event" || nodeType === "end" || shape === "end-event" || shape === "end") {
    return "end";
  }
  if (nodeType === "gateway" || shape === "diamond" || shape === "gateway") {
    return "decision";
  }

  // 默认为任务节点
  return "task";
}

function applyAlpha(color: string, alpha: number) {
  if (color.startsWith("#") && (color.length === 7 || color.length === 4)) {
    const hex = color.length === 4
      ? `#${color[1]}${color[1]}${color[2]}${color[2]}${color[3]}${color[3]}`
      : color;
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
  }
  return color;
}
