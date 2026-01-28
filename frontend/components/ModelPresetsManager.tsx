"use client";

import React from "react";
import { X } from "lucide-react";
import { AiConfigPanel } from "./AiConfigPanel";

interface ModelPresetsManagerProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectPreset?: (preset: any) => void;
}

/**
 * AI 配置管理器 - 简化版
 * 只支持 Custom API，用户需要手动输入所有配置
 */
export default function ModelPresetsManager({
  isOpen,
  onClose,
}: ModelPresetsManagerProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-xl overflow-hidden rounded-xl bg-white shadow-2xl dark:bg-slate-900">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
          <div>
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">
              AI 配置
            </h2>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              配置 AI 模型以使用所有 AI 功能
            </p>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="max-h-[calc(90vh-140px)] overflow-y-auto p-6">
          <AiConfigPanel />
        </div>

        {/* Footer */}
        <div className="border-t border-slate-200 px-6 py-4 dark:border-slate-800">
          <button
            onClick={onClose}
            className="w-full rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-md transition hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg"
          >
            完成配置
          </button>
        </div>
      </div>
    </div>
  );
}
