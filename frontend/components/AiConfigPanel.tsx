"use client";

import { useState, useEffect } from "react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { Settings, CheckCircle2, AlertCircle, Eye, EyeOff } from "lucide-react";
import { toast } from "sonner";

/**
 * AI 配置面板 - 简化版
 * 只支持 Custom API，用户需要手动输入所有配置
 */
export function AiConfigPanel() {
  const { modelConfig, setModelConfig } = useArchitectStore();

  const [apiKey, setApiKey] = useState(modelConfig.apiKey || "");
  const [baseUrl, setBaseUrl] = useState(modelConfig.baseUrl || "");
  const [modelName, setModelName] = useState(modelConfig.modelName || "");
  const [showApiKey, setShowApiKey] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  // 检查配置是否完整
  const isConfigured = !!(modelConfig.apiKey && modelConfig.baseUrl && modelConfig.modelName);

  // 检查当前输入是否有效
  const isValid = !!(apiKey.trim() && baseUrl.trim() && modelName.trim());

  // 检测是否有未保存的更改
  useEffect(() => {
    const changed =
      apiKey !== modelConfig.apiKey ||
      baseUrl !== modelConfig.baseUrl ||
      modelName !== modelConfig.modelName;
    setHasChanges(changed);
  }, [apiKey, baseUrl, modelName, modelConfig]);

  const handleSave = () => {
    if (!isValid) {
      toast.error("请填写完整的配置信息");
      return;
    }

    setModelConfig({
      provider: "custom",
      apiKey: apiKey.trim(),
      baseUrl: baseUrl.trim(),
      modelName: modelName.trim(),
    });

    setHasChanges(false);
    toast.success("AI 配置已保存");
  };

  const handleReset = () => {
    setApiKey(modelConfig.apiKey || "");
    setBaseUrl(modelConfig.baseUrl || "");
    setModelName(modelConfig.modelName || "");
    setHasChanges(false);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-gradient-to-br from-blue-500 to-indigo-600 p-2 shadow-sm">
            <Settings className="h-4 w-4 text-white" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900 dark:text-white">
              Custom API (推荐)
            </h3>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              支持任何兼容 OpenAI 格式的 API
            </p>
          </div>
        </div>

        {/* 配置状态指示器 */}
        {isConfigured ? (
          <div className="flex items-center gap-1.5 rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700 dark:bg-green-900/30 dark:text-green-400">
            <CheckCircle2 className="h-3.5 w-3.5" />
            已配置
          </div>
        ) : (
          <div className="flex items-center gap-1.5 rounded-full bg-amber-100 px-2.5 py-1 text-xs font-medium text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
            <AlertCircle className="h-3.5 w-3.5" />
            未配置
          </div>
        )}
      </div>

      {/* 配置表单 */}
      <div className="space-y-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        {/* API Key */}
        <div>
          <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
            API Key <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <input
              type={showApiKey ? "text" : "password"}
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="sk-..."
              className="w-full rounded-lg border-2 border-slate-200 bg-white px-3 py-2 pr-10 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-500/20"
            />
            <button
              type="button"
              onClick={() => setShowApiKey(!showApiKey)}
              className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
            >
              {showApiKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          </div>
        </div>

        {/* Base URL */}
        <div>
          <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
            Base URL <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={baseUrl}
            onChange={(e) => setBaseUrl(e.target.value)}
            placeholder="https://api.example.com/v1"
            className="w-full rounded-lg border-2 border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-500/20"
          />
        </div>

        {/* Model Name */}
        <div>
          <label className="mb-1.5 block text-xs font-semibold text-slate-700 dark:text-slate-300">
            Model Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            value={modelName}
            onChange={(e) => setModelName(e.target.value)}
            placeholder="claude-sonnet-4-5-20250929"
            className="w-full rounded-lg border-2 border-slate-200 bg-white px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-blue-500 focus:ring-4 focus:ring-blue-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-blue-400 dark:focus:ring-blue-500/20"
          />
        </div>

        {/* 按钮组 */}
        <div className="flex gap-2 pt-2">
          <button
            onClick={handleSave}
            disabled={!isValid || !hasChanges}
            className="flex-1 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-4 py-2.5 text-sm font-bold text-white shadow-md transition hover:from-blue-700 hover:to-indigo-700 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-sm"
          >
            {hasChanges ? "保存配置" : "已保存"}
          </button>

          {hasChanges && (
            <button
              onClick={handleReset}
              className="rounded-lg border-2 border-slate-200 bg-white px-4 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            >
              重置
            </button>
          )}
        </div>
      </div>

      {/* 使用提示 */}
      <div className="rounded-lg bg-blue-50 p-3 dark:bg-blue-950">
        <p className="text-xs font-medium text-blue-900 dark:text-blue-100">
          💡 配置说明
        </p>
        <ul className="mt-2 space-y-1 text-xs text-blue-700 dark:text-blue-300">
          <li>• 支持国内中转站（推荐使用 Claude 模型）</li>
          <li>• 支持 OpenAI、Claude、Gemini 等官方 API</li>
          <li>• Base URL 格式：https://域名/v1</li>
          <li>• 配置后即可使用所有 AI 功能</li>
        </ul>
      </div>
    </div>
  );
}
