"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";
import { Theme, ThemeId } from "./types";
import { THEME_PRESETS, DEFAULT_THEME_ID, getThemeById } from "./presets";

interface ThemeContextType {
  currentTheme: Theme;
  currentThemeId: ThemeId;
  setTheme: (themeId: ThemeId) => void;
  availableThemes: Theme[];
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

/**
 * Apply theme CSS custom properties to the document root
 */
function applyThemeToDOM(theme: Theme): void {
  const root = document.documentElement;
  const { colors, fonts } = theme;

  // API Node colors
  root.style.setProperty("--api-border", colors.apiNode.border);
  root.style.setProperty("--api-background", colors.apiNode.background);
  root.style.setProperty("--api-text", colors.apiNode.text);
  root.style.setProperty("--api-icon", colors.apiNode.icon);
  root.style.setProperty("--api-shadow", colors.apiNode.shadow || "none");

  // Service Node colors
  root.style.setProperty("--service-border", colors.serviceNode.border);
  root.style.setProperty("--service-background", colors.serviceNode.background);
  root.style.setProperty("--service-text", colors.serviceNode.text);
  root.style.setProperty("--service-icon", colors.serviceNode.icon);
  root.style.setProperty("--service-shadow", colors.serviceNode.shadow || "none");

  // Database Node colors
  root.style.setProperty("--database-border", colors.databaseNode.border);
  root.style.setProperty("--database-background", colors.databaseNode.background);
  root.style.setProperty("--database-text", colors.databaseNode.text);
  root.style.setProperty("--database-icon", colors.databaseNode.icon);
  root.style.setProperty("--database-shadow", colors.databaseNode.shadow || "none");

  // Gateway Node colors
  root.style.setProperty("--gateway-border", colors.gatewayNode.border);
  root.style.setProperty("--gateway-background", colors.gatewayNode.background);
  root.style.setProperty("--gateway-text", colors.gatewayNode.text);
  root.style.setProperty("--gateway-icon", colors.gatewayNode.icon);
  root.style.setProperty("--gateway-shadow", colors.gatewayNode.shadow || "none");

  // Default Node colors
  root.style.setProperty("--default-border", colors.defaultNode.border);
  root.style.setProperty("--default-background", colors.defaultNode.background);
  root.style.setProperty("--default-text", colors.defaultNode.text);
  root.style.setProperty("--default-icon", colors.defaultNode.icon);
  root.style.setProperty("--default-shadow", colors.defaultNode.shadow || "none");

  // Cache Node colors
  root.style.setProperty("--cache-border", colors.cacheNode.border);
  root.style.setProperty("--cache-background", colors.cacheNode.background);
  root.style.setProperty("--cache-text", colors.cacheNode.text);
  root.style.setProperty("--cache-icon", colors.cacheNode.icon);
  root.style.setProperty("--cache-shadow", colors.cacheNode.shadow || "none");

  // Queue Node colors
  root.style.setProperty("--queue-border", colors.queueNode.border);
  root.style.setProperty("--queue-background", colors.queueNode.background);
  root.style.setProperty("--queue-text", colors.queueNode.text);
  root.style.setProperty("--queue-icon", colors.queueNode.icon);
  root.style.setProperty("--queue-shadow", colors.queueNode.shadow || "none");

  // Storage Node colors
  root.style.setProperty("--storage-border", colors.storageNode.border);
  root.style.setProperty("--storage-background", colors.storageNode.background);
  root.style.setProperty("--storage-text", colors.storageNode.text);
  root.style.setProperty("--storage-icon", colors.storageNode.icon);
  root.style.setProperty("--storage-shadow", colors.storageNode.shadow || "none");

  // Client Node colors
  root.style.setProperty("--client-border", colors.clientNode.border);
  root.style.setProperty("--client-background", colors.clientNode.background);
  root.style.setProperty("--client-text", colors.clientNode.text);
  root.style.setProperty("--client-icon", colors.clientNode.icon);
  root.style.setProperty("--client-shadow", colors.clientNode.shadow || "none");

  // Edge colors
  root.style.setProperty("--edge-stroke", colors.edges.stroke);
  root.style.setProperty("--edge-stroke-width", colors.edges.strokeWidth.toString());

  // Canvas colors
  root.style.setProperty("--canvas-background", colors.canvas.background);
  root.style.setProperty("--canvas-grid", colors.canvas.grid);

  // Accent and muted
  root.style.setProperty("--theme-accent", colors.accent);
  root.style.setProperty("--theme-muted", colors.muted);

  // Fonts
  root.style.setProperty("--font-family", fonts.family);
  root.style.setProperty("--font-size-node", fonts.size.node);
  root.style.setProperty("--font-size-label", fonts.size.label);
  root.style.setProperty("--font-size-edge", fonts.size.edge);
  root.style.setProperty("--font-weight-normal", fonts.weight.normal.toString());
  root.style.setProperty("--font-weight-bold", fonts.weight.bold.toString());
}

interface ThemeProviderProps {
  children: ReactNode;
  defaultThemeId?: ThemeId;
}

export function ThemeProvider({ children, defaultThemeId = DEFAULT_THEME_ID }: ThemeProviderProps) {
  const [currentThemeId, setCurrentThemeId] = useState<ThemeId>(defaultThemeId);
  const [currentTheme, setCurrentTheme] = useState<Theme>(
    getThemeById(defaultThemeId) || THEME_PRESETS[0]
  );

  // Load theme from localStorage on mount
  useEffect(() => {
    const savedThemeId = localStorage.getItem("smartarchitect-theme");
    if (savedThemeId) {
      const savedTheme = getThemeById(savedThemeId);
      if (savedTheme) {
        setCurrentThemeId(savedThemeId);
        setCurrentTheme(savedTheme);
      }
    }
  }, []);

  // Apply theme to DOM whenever it changes
  useEffect(() => {
    applyThemeToDOM(currentTheme);
  }, [currentTheme]);

  const setTheme = (themeId: ThemeId) => {
    const newTheme = getThemeById(themeId);
    if (newTheme) {
      setCurrentThemeId(themeId);
      setCurrentTheme(newTheme);
      localStorage.setItem("smartarchitect-theme", themeId);
    }
  };

  const value: ThemeContextType = {
    currentTheme,
    currentThemeId,
    setTheme,
    availableThemes: THEME_PRESETS,
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

/**
 * Hook to use the theme context
 */
export function useTheme(): ThemeContextType {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
