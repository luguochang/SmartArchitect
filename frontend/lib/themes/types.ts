/**
 * Theme System Type Definitions
 * Defines color schemes, fonts, and styling for different architecture diagram themes
 */

export interface NodeColors {
  border: string;
  background: string;
  text: string;
  icon: string;
  shadow?: string;
}

export interface EdgeColors {
  stroke: string;
  strokeWidth: number;
  animated?: boolean;
  strokeDasharray?: string;
}

export interface CanvasColors {
  background: string;
  grid: string;
  gridSize?: number;
}

export interface ThemeColors {
  // Node type colors
  apiNode: NodeColors;
  serviceNode: NodeColors;
  databaseNode: NodeColors;
  gatewayNode: NodeColors;
  defaultNode: NodeColors;
  cacheNode: NodeColors;     // Yellow - Speed/Performance
  queueNode: NodeColors;     // Indigo - Message Flow
  storageNode: NodeColors;   // Slate - Infrastructure
  clientNode: NodeColors;    // Cyan - User Interface

  // Edge and canvas
  edges: EdgeColors;
  canvas: CanvasColors;

  // UI elements
  accent: string;
  muted: string;
}

export interface ThemeFonts {
  family: string;
  size: {
    node: string;
    label: string;
    edge: string;
  };
  weight: {
    normal: number;
    bold: number;
  };
}

export type ThemeCategory = "professional" | "tech" | "sketch" | "vibrant" | "minimal";

export interface Theme {
  id: string;
  name: string;
  description: string;
  category: ThemeCategory;
  colors: ThemeColors;
  fonts: ThemeFonts;
  preview?: string; // Optional preview image URL
}

export type ThemeId = string;
