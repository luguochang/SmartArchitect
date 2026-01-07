"use client";

import { useState } from "react";
import { Palette, Check } from "lucide-react";
import { useTheme } from "@/lib/themes/ThemeContext";
import { ThemeCategory } from "@/lib/themes/types";

const CATEGORY_LABELS: Record<ThemeCategory, string> = {
  professional: "Professional",
  tech: "Tech",
  sketch: "Sketch",
  vibrant: "Vibrant",
  minimal: "Minimal",
};

export default function ThemeSwitcher() {
  const { currentThemeId, setTheme, availableThemes } = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  // Group themes by category
  const themesByCategory = availableThemes.reduce((acc, theme) => {
    if (!acc[theme.category]) {
      acc[theme.category] = [];
    }
    acc[theme.category].push(theme);
    return acc;
  }, {} as Record<ThemeCategory, typeof availableThemes>);

  return (
    <div className="relative">
      {/* Theme Switcher Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors shadow-sm"
        title="Change Theme"
      >
        <Palette className="w-4 h-4 text-purple-600" />
        <span className="text-sm font-medium text-gray-700">Theme</span>
      </button>

      {/* Theme Picker Modal */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-40"
            onClick={() => setIsOpen(false)}
          />

          {/* Modal */}
          <div className="absolute top-full right-0 mt-2 w-96 max-h-[600px] overflow-y-auto bg-white rounded-lg shadow-xl border border-gray-200 z-50">
            {/* Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 z-10">
              <h3 className="text-lg font-semibold text-gray-900">Choose Theme</h3>
              <p className="text-xs text-gray-500 mt-1">
                {availableThemes.length} themes available
              </p>
            </div>

            {/* Theme Grid by Category */}
            <div className="p-4 space-y-6">
              {Object.entries(themesByCategory).map(([category, themes]) => (
                <div key={category}>
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">
                    {CATEGORY_LABELS[category as ThemeCategory]}
                  </h4>
                  <div className="grid grid-cols-2 gap-3">
                    {themes.map((theme) => {
                      const isSelected = currentThemeId === theme.id;

                      return (
                        <button
                          key={theme.id}
                          onClick={() => {
                            setTheme(theme.id);
                            setIsOpen(false);
                          }}
                          className={`
                            relative p-3 rounded-lg border-2 transition-all text-left
                            ${
                              isSelected
                                ? "border-purple-500 bg-purple-50"
                                : "border-gray-200 hover:border-purple-300 hover:shadow-sm"
                            }
                          `}
                        >
                          {/* Color Preview */}
                          <div className="flex gap-1 mb-2">
                            <div
                              className="w-6 h-6 rounded"
                              style={{ backgroundColor: theme.colors.apiNode.border }}
                              title="API"
                            />
                            <div
                              className="w-6 h-6 rounded"
                              style={{ backgroundColor: theme.colors.serviceNode.border }}
                              title="Service"
                            />
                            <div
                              className="w-6 h-6 rounded"
                              style={{ backgroundColor: theme.colors.databaseNode.border }}
                              title="Database"
                            />
                          </div>

                          {/* Theme Name */}
                          <div className="text-sm font-semibold text-gray-900">
                            {theme.name}
                          </div>
                          <div className="text-xs text-gray-500 mt-1">
                            {theme.description}
                          </div>

                          {/* Selected Indicator */}
                          {isSelected && (
                            <div className="absolute top-2 right-2">
                              <div className="w-5 h-5 bg-purple-500 rounded-full flex items-center justify-center">
                                <Check className="w-3 h-3 text-white" strokeWidth={3} />
                              </div>
                            </div>
                          )}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
