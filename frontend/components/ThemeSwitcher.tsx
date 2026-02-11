"use client";

import { useMemo, useState } from "react";
import { Palette, Check, Eye, Globe, Server, Database } from "lucide-react";
import { useTheme } from "@/lib/themes/ThemeContext";
import { ThemeCategory } from "@/lib/themes/types";

export default function ThemeSwitcher() {
  const { currentThemeId, setTheme, availableThemes } = useTheme();
  const [isOpen, setIsOpen] = useState(false);

  // 仅保留 Vibrant（活力风格）主题
  const vibrantThemes = useMemo(
    () => availableThemes.filter((theme) => theme.category === "vibrant"),
    [availableThemes]
  );

  // Group themes by category (这里只会有 vibrant)
  const themesByCategory = useMemo(() => {
    return vibrantThemes.reduce((acc, theme) => {
      if (!acc[theme.category]) acc[theme.category] = [];
      acc[theme.category].push(theme);
      return acc;
    }, {} as Record<ThemeCategory, typeof vibrantThemes>);
  }, [vibrantThemes]);

  const renderPreview = (themeId: string) => {
    const theme = vibrantThemes.find((t) => t.id === themeId);
    if (!theme) return null;

    const nodeBox = (
      label: string,
      Icon: typeof Globe,
      colors: { border: string; background: string; text: string }
    ) => (
      <div
        className="flex items-center justify-center rounded-md border overflow-hidden"
        style={{
          borderColor: colors.border,
          backgroundColor: colors.background,
          width: 46,
          height: 38,
        }}
        title={label}
      >
        <div
          className="flex h-6 w-6 items-center justify-center rounded-full"
          style={{ backgroundColor: colors.border, color: colors.background }}
        >
          <Icon className="h-3 w-3" />
        </div>
      </div>
    );

    return (
      <div
        className="mt-2 rounded-md border bg-slate-50 p-1"
        style={{ backgroundColor: theme.colors.canvas.background, borderColor: theme.colors.canvas.grid }}
      >
        <div className="grid grid-cols-3 gap-1 items-center justify-items-center">
          {nodeBox("API 服务", Globe, theme.colors.apiNode)}
          {nodeBox("业务节点", Server, theme.colors.serviceNode)}
          {nodeBox("数据库", Database, theme.colors.databaseNode)}
        </div>
        <div
          className="mt-2 h-1 rounded-full"
          style={{ background: theme.colors.edges.stroke }}
        />
      </div>
    );
  };

  return (
    <div className="relative">
      {/* Theme Switcher Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors shadow-sm"
        title="切换主题"
      >
        <Palette className="w-4 h-4 text-purple-600" />
        <span className="text-sm font-medium text-gray-700">主题</span>
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
              <h3 className="text-lg font-semibold text-gray-900">选择主题</h3>
              <p className="text-xs text-gray-500 mt-1">
                仅展示活力风格（{vibrantThemes.length} 个主题）
              </p>
              <p className="text-[11px] text-slate-400 flex items-center gap-1 mt-1">
                <Eye className="w-3 h-3" /> 预览节点色板，方便对比差异
              </p>
            </div>

            {/* Theme Grid by Category */}
            <div className="p-4 space-y-6">
              {Object.entries(themesByCategory).map(([category, themes]) => (
                <div key={category}>
                  <h4 className="text-sm font-semibold text-gray-700 mb-3">
                    活力风格
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
                          className={`relative p-3 rounded-lg border-2 transition-all text-left
                            ${isSelected
                              ? "border-purple-500 bg-purple-50"
                              : "border-gray-200 hover:border-purple-300 hover:shadow-sm"
                            }`}
                        >
                          {/* Theme Name */}
                          <div className="flex items-center justify-between gap-2">
                            <div>
                              <div className="text-sm font-semibold text-gray-900">
                                {theme.name}
                              </div>
                              <div className="text-xs text-gray-500 mt-0.5">
                                {theme.description}
                              </div>
                            </div>
                            {isSelected && (
                              <div className="w-5 h-5 bg-purple-500 rounded-full flex items-center justify-center">
                                <Check className="w-3 h-3 text-white" strokeWidth={3} />
                              </div>
                            )}
                          </div>

                          {/* Rich Preview */}
                          <div className="mt-2">{renderPreview(theme.id)}</div>
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
