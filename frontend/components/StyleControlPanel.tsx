"use client";

import React from "react";
import { useFlowchartStyleStore } from "@/lib/stores/flowchartStyleStore";
import { FLOWCHART_PRESENTATION_STYLES, FONT_STYLE_OPTIONS } from "@/lib/themes/flowchartPresentationStyles";

/**
 * Style Control Panel
 *
 * UI component for switching between flowchart presentation styles and fonts.
 * Displays toggle buttons for each style option.
 */
export function StyleControlPanel() {
  const {
    presentationStyleId,
    fontStyleId,
    setPresentationStyle,
    setFontStyle,
    resetToDefaults,
  } = useFlowchartStyleStore();

  const presentationStyles = Object.values(FLOWCHART_PRESENTATION_STYLES);
  const fontStyles = Object.values(FONT_STYLE_OPTIONS);

  return (
    <div className="space-y-6">
      {/* Presentation Style Section */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
            流程图样式
          </h3>
          <button
            onClick={resetToDefaults}
            className="text-xs text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
            title="重置为默认样式"
          >
            重置
          </button>
        </div>
        <div className="space-y-2">
          {presentationStyles.map((style) => {
            const isActive = presentationStyleId === style.id;
            return (
              <button
                key={style.id}
                onClick={() => setPresentationStyle(style.id)}
                className={`
                  w-full rounded-lg border px-4 py-3 text-left transition-all
                  ${
                    isActive
                      ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20"
                      : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600"
                  }
                `}
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span
                        className={`text-sm font-medium ${
                          isActive
                            ? "text-indigo-900 dark:text-indigo-100"
                            : "text-gray-900 dark:text-gray-100"
                        }`}
                      >
                        {style.name}
                      </span>
                      {!style.node.showIcons && (
                        <span className="rounded bg-green-100 px-1.5 py-0.5 text-xs text-green-700 dark:bg-green-900/30 dark:text-green-300">
                          专业
                        </span>
                      )}
                    </div>
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      {style.description}
                    </p>
                  </div>
                  {isActive && (
                    <svg
                      className="h-5 w-5 text-indigo-600 dark:text-indigo-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>

                {/* Style preview badges */}
                <div className="mt-2 flex gap-2 text-xs text-gray-600 dark:text-gray-400">
                  <span className="rounded bg-gray-100 px-2 py-0.5 dark:bg-gray-700">
                    {style.node.showIcons ? "带图标" : "无图标"}
                  </span>
                  <span className="rounded bg-gray-100 px-2 py-0.5 dark:bg-gray-700">
                    {style.edge.type === "orthogonal" && "正交路由"}
                    {style.edge.type === "straight" && "直线"}
                    {style.edge.type === "smoothstep" && "平滑曲线"}
                    {style.edge.type === "step" && "阶梯"}
                  </span>
                  {style.edge.showGlow && (
                    <span className="rounded bg-gray-100 px-2 py-0.5 dark:bg-gray-700">
                      发光效果
                    </span>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* Font Style Section */}
      <section>
        <h3 className="mb-3 text-sm font-semibold text-gray-900 dark:text-gray-100">
          字体样式
        </h3>
        <div className="space-y-2">
          {fontStyles.map((font) => {
            const isActive = fontStyleId === font.id;
            return (
              <button
                key={font.id}
                onClick={() => setFontStyle(font.id)}
                className={`
                  w-full rounded-lg border px-4 py-2.5 text-left transition-all
                  ${
                    isActive
                      ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20"
                      : "border-gray-200 bg-white hover:border-gray-300 dark:border-gray-700 dark:bg-gray-800 dark:hover:border-gray-600"
                  }
                `}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <span
                      className={`text-sm font-medium ${
                        isActive
                          ? "text-indigo-900 dark:text-indigo-100"
                          : "text-gray-900 dark:text-gray-100"
                      }`}
                      style={{ fontFamily: font.fontFamily }}
                    >
                      {font.name}
                    </span>
                    <p className="mt-0.5 text-xs text-gray-500 dark:text-gray-400">
                      {font.description}
                    </p>
                  </div>
                  {isActive && (
                    <svg
                      className="h-5 w-5 text-indigo-600 dark:text-indigo-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </section>

      {/* Info Note */}
      <div className="rounded-lg bg-blue-50 p-3 dark:bg-blue-900/20">
        <p className="text-xs text-blue-700 dark:text-blue-300">
          💡 提示：专业样式不显示图标，采用正交路由，适合正式汇报和文档
        </p>
      </div>
    </div>
  );
}
