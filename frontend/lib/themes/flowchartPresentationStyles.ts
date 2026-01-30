/**
 * Flowchart Presentation Styles
 *
 * Defines professional presentation modes for React Flow flowcharts.
 * These styles control the visual appearance independent of color themes:
 * - Icon visibility (professional presentations don't show icons)
 * - Edge routing (orthogonal for BPMN standard)
 * - Node decoration styles (borders, shadows, etc.)
 * - Typography choices
 */

export interface FlowchartPresentationStyle {
  id: string;
  name: string;
  description: string;

  // Node styling
  node: {
    showIcons: boolean;
    borderWidth: string;
    borderRadius: string;
    boxShadow: string;
    padding: string;
    backgroundColor: string;  // base color, semantic types override this
    // Semantic type colors (start, end, task, decision)
    semanticColors: {
      start: { bg: string; border: string; };
      end: { bg: string; border: string; };
      task: { bg: string; border: string; };
      decision: { bg: string; border: string; };
    };
  };

  // Edge styling
  edge: {
    type: "orthogonal" | "straight" | "smoothstep" | "step";
    strokeWidth: number;
    strokeColor: string;
    markerSize: number;  // Arrow marker size
    showGlow: boolean;   // Drop shadow effect
  };

  // Typography
  typography: {
    fontFamily: string;
    fontSize: string;
    fontWeight: string;
    lineHeight: string;
  };
}

/**
 * BPMN Professional Style
 * - No icons, clean borders, semantic colors, orthogonal routing
 * - Suitable for professional business presentations and reports
 */
export const BPMN_PROFESSIONAL: FlowchartPresentationStyle = {
  id: "bpmn-professional",
  name: "BPMN 专业风格",
  description: "符合BPMN 2.0标准的专业风格，正交路由，无图标，语义化颜色",

  node: {
    showIcons: false,
    borderWidth: "2px",
    borderRadius: "4px",
    boxShadow: "none",
    padding: "12px 16px",
    backgroundColor: "#ffffff",
    semanticColors: {
      start: { bg: "#ffffff", border: "#16a34a" },  // Green for start
      end: { bg: "#ffffff", border: "#dc2626" },    // Red for end
      task: { bg: "#ffffff", border: "#2563eb" },   // Blue for tasks
      decision: { bg: "#ffffff", border: "#f59e0b" }, // Amber for decisions/gateways
    },
  },

  edge: {
    type: "orthogonal",
    strokeWidth: 2,
    strokeColor: "#000000",
    markerSize: 18,
    showGlow: false,
  },

  typography: {
    fontFamily: "system-ui, -apple-system, 'Segoe UI', sans-serif",
    fontSize: "14px",
    fontWeight: "500",
    lineHeight: "1.4",
  },
};

/**
 * Corporate Minimalist Style
 * - No icons, soft colors, subtle shadows, orthogonal routing
 * - Perfect for corporate slide decks and executive presentations
 */
export const CORPORATE_MINIMALIST: FlowchartPresentationStyle = {
  id: "corporate-minimalist",
  name: "企业简约风格",
  description: "简洁大气的企业风格，柔和配色，微妙阴影，适合述职汇报",

  node: {
    showIcons: false,
    borderWidth: "1px",
    borderRadius: "8px",
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.08)",
    padding: "14px 18px",
    backgroundColor: "#f9fafb",
    semanticColors: {
      start: { bg: "#ecfdf5", border: "#059669" },
      end: { bg: "#fee2e2", border: "#dc2626" },
      task: { bg: "#eff6ff", border: "#2563eb" },
      decision: { bg: "#fff7ed", border: "#f97316" },
    },
  },

  edge: {
    type: "orthogonal",
    strokeWidth: 2.5,
    strokeColor: "#64748b",
    markerSize: 16,
    showGlow: false,
  },

  typography: {
    fontFamily: "'Inter', 'Roboto', '微软雅黑', system-ui, sans-serif",
    fontSize: "13px",
    fontWeight: "400",
    lineHeight: "1.5",
  },
};

/**
 * Technical Documentation Style
 * - No icons, high contrast, monospace font, orthogonal routing
 * - Ideal for technical documentation and engineering specs
 */
export const TECHNICAL_DOCUMENTATION: FlowchartPresentationStyle = {
  id: "technical-documentation",
  name: "技术文档风格",
  description: "高对比度技术文档风格，等宽字体，适合工程规范和技术文档",

  node: {
    showIcons: false,
    borderWidth: "2px",
    borderRadius: "0px",
    boxShadow: "none",
    padding: "10px 14px",
    backgroundColor: "#ffffff",
    semanticColors: {
      start: { bg: "#ffffff", border: "#000000" },
      end: { bg: "#000000", border: "#000000" },   // Black fill for end
      task: { bg: "#ffffff", border: "#000000" },
      decision: { bg: "#ffffff", border: "#000000" },
    },
  },

  edge: {
    type: "orthogonal",
    strokeWidth: 2,
    strokeColor: "#000000",
    markerSize: 16,
    showGlow: false,
  },

  typography: {
    fontFamily: "'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
    fontSize: "12px",
    fontWeight: "400",
    lineHeight: "1.6",
  },
};

/**
 * Modern Flat Style
 * - No icons, colored fills, bold text, straight edges
 * - Modern and vibrant for creative presentations
 */
export const MODERN_FLAT: FlowchartPresentationStyle = {
  id: "modern-flat",
  name: "现代扁平风格",
  description: "现代扁平设计，彩色填充，粗体文字，适合创意演示",

  node: {
    showIcons: false,
    borderWidth: "0px",
    borderRadius: "12px",
    boxShadow: "none",
    backgroundColor: "#6366f1",  // Default indigo fill
    padding: "16px 20px",
    semanticColors: {
      start: { bg: "#10b981", border: "transparent" },  // Green fill
      end: { bg: "#ef4444", border: "transparent" },    // Red fill
      task: { bg: "#3b82f6", border: "transparent" },   // Blue fill
      decision: { bg: "#f59e0b", border: "transparent" }, // Amber fill
    },
  },

  edge: {
    type: "straight",
    strokeWidth: 3,
    strokeColor: "#6b7280",
    markerSize: 20,
    showGlow: false,
  },

  typography: {
    fontFamily: "system-ui, -apple-system, sans-serif",
    fontSize: "15px",
    fontWeight: "600",
    lineHeight: "1.3",
  },
};

/**
 * Default / Legacy Style
 * - Shows icons, curved edges, glassmorphism effects
 * - Matches current implementation (for backwards compatibility)
 */
export const LEGACY_DEFAULT: FlowchartPresentationStyle = {
  id: "legacy-default",
  name: "默认风格（带图标）",
  description: "当前默认样式，包含图标和渐变效果",

  node: {
    showIcons: true,
    borderWidth: "2px",
    borderRadius: "12px",
    boxShadow: "0 14px 30px -14px rgba(0,0,0,0.25)",
    padding: "12px 16px",
    backgroundColor: "#ffffff",
    semanticColors: {
      start: { bg: "#ecfdf5", border: "#10b981" },
      end: { bg: "#fee2e2", border: "#dc2626" },
      task: { bg: "#eff6ff", border: "#3b82f6" },
      decision: { bg: "#fff7ed", border: "#f97316" },
    },
  },

  edge: {
    type: "smoothstep",
    strokeWidth: 2.5,
    strokeColor: "#94a3b8",
    markerSize: 18,
    showGlow: true,
  },

  typography: {
    fontFamily: "Inter, system-ui, sans-serif",
    fontSize: "14px",
    fontWeight: "500",
    lineHeight: "1.4",
  },
};

/**
 * All available flowchart presentation styles
 */
export const FLOWCHART_PRESENTATION_STYLES: Record<string, FlowchartPresentationStyle> = {
  "bpmn-professional": BPMN_PROFESSIONAL,
  "corporate-minimalist": CORPORATE_MINIMALIST,
  "technical-documentation": TECHNICAL_DOCUMENTATION,
  "modern-flat": MODERN_FLAT,
  "legacy-default": LEGACY_DEFAULT,
};

/**
 * Font style options (can be mixed with any presentation style)
 */
export interface FontStyleOption {
  id: string;
  name: string;
  fontFamily: string;
  description: string;
}

export const FONT_STYLE_OPTIONS: Record<string, FontStyleOption> = {
  modern: {
    id: "modern",
    name: "现代无衬线",
    fontFamily: "'Inter', 'Roboto', '微软雅黑', system-ui, sans-serif",
    description: "清晰易读，适合商务汇报",
  },
  monospace: {
    id: "monospace",
    name: "等宽技术字体",
    fontFamily: "'Fira Code', 'JetBrains Mono', 'Consolas', monospace",
    description: "技术风格，适合技术文档",
  },
  system: {
    id: "system",
    name: "系统默认",
    fontFamily: "system-ui, -apple-system, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif",
    description: "通用兼容，最保守选择",
  },
};

/**
 * Helper function to get presentation style by ID
 */
export function getPresentationStyleById(id: string): FlowchartPresentationStyle | undefined {
  return FLOWCHART_PRESENTATION_STYLES[id];
}

/**
 * Helper function to get font style by ID
 */
export function getFontStyleById(id: string): FontStyleOption | undefined {
  return FONT_STYLE_OPTIONS[id];
}

/**
 * Default presentation style ID
 */
export const DEFAULT_PRESENTATION_STYLE_ID = "bpmn-professional";
export const DEFAULT_FONT_STYLE_ID = "modern";
