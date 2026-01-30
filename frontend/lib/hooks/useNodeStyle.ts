import { useMemo } from "react";
import { useFlowchartStyleStore } from "@/lib/stores/flowchartStyleStore";

/**
 * 节点样式Hook
 *
 * 为节点提供统一的样式配置，基于当前选择的flowchart presentation style
 */
export function useNodeStyle(nodeType?: string, shape?: string) {
  const { currentPresentationStyle, currentFontStyle, showIcons } = useFlowchartStyleStore();

  const styles = useMemo(() => {
    // 确定语义类型（start, end, task, decision）
    const semanticType = getSemanticType(nodeType, shape);
    const semanticColors = currentPresentationStyle.node.semanticColors[semanticType] || {
      bg: currentPresentationStyle.node.backgroundColor,
      border: currentPresentationStyle.node.borderColor,
    };

    return {
      // 是否显示图标
      showIcons,

      // 节点容器样式
      container: {
        backgroundColor: semanticColors.bg,
        borderColor: semanticColors.border,
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
      borderColor: semanticColors.border,
    };
  }, [currentPresentationStyle, currentFontStyle, showIcons, nodeType, shape]);

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
