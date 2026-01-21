"use client";

import { useState, useEffect } from "react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { X, Sparkles, Save } from "lucide-react";

interface ModelConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ModelConfigModal({ isOpen, onClose }: ModelConfigModalProps) {
  const { modelConfig, setModelConfig } = useArchitectStore();
  const [localConfig, setLocalConfig] = useState(modelConfig);

  useEffect(() => {
    setLocalConfig(modelConfig);
  }, [modelConfig]);

  if (!isOpen) return null;

  const handleSave = async () => {
    // Save to local store (always happens)
    setModelConfig(localConfig);

    // Optionally test connection and save to backend
    if (localConfig.apiKey && localConfig.apiKey.trim()) {
      try {
        const response = await fetch("http://localhost:8000/api/models/config", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            provider: localConfig.provider,
            api_key: localConfig.apiKey,
            model_name: localConfig.modelName,
            base_url: localConfig.baseUrl || "",
          }),
        });

        if (response.ok) {
          console.log("✓ Model config synced to backend");
        } else {
          console.warn("Backend config sync failed (non-critical):", await response.text());
        }
      } catch (error) {
        console.warn("Backend config sync failed (non-critical):", error);
      }
    }

    onClose();
  };

  const modelProviders = [
    { value: "gemini", label: "Google Gemini", defaultModel: "gemini-2.5-flash", baseUrl: "" },
    { value: "openai", label: "OpenAI", defaultModel: "gpt-4-turbo", baseUrl: "" },
    { value: "claude", label: "Anthropic Claude", defaultModel: "claude-3-5-sonnet-20241022", baseUrl: "" },
    { value: "siliconflow", label: "SiliconFlow", defaultModel: "Qwen/Qwen2.5-7B-Instruct", baseUrl: "https://api.siliconflow.cn/v1" },
    { value: "custom", label: "Custom API", defaultModel: "custom-model", baseUrl: "" },
  ];

  const handleProviderChange = (provider: string) => {
    const selectedProvider = modelProviders.find((p) => p.value === provider);
    setLocalConfig({
      ...localConfig,
      provider: provider as any,
      modelName: selectedProvider?.defaultModel || "",
      baseUrl: selectedProvider?.baseUrl || "",
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-lg rounded-lg bg-white shadow-xl dark:bg-slate-900">
        {/* 标题栏 */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
              AI Model Configuration
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1 hover:bg-slate-100 dark:hover:bg-slate-800"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* 内容区域 */}
        <div className="space-y-4 px-6 py-4">
          {/* 模型提供商选择 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Model Provider
            </label>
            <select
              value={localConfig.provider}
              onChange={(e) => handleProviderChange(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2 dark:border-slate-700 dark:bg-slate-800"
            >
              {modelProviders.map((provider) => (
                <option key={provider.value} value={provider.value}>
                  {provider.label}
                </option>
              ))}
            </select>
          </div>

          {/* API Key */}
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
              API Key
            </label>
            <input
              type="password"
              value={localConfig.apiKey}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, apiKey: e.target.value })
              }
              placeholder="Enter your API key"
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2 dark:border-slate-700 dark:bg-slate-800"
            />
            <p className="mt-1 text-xs text-slate-500">
              Your API key is stored locally and never sent to our servers
            </p>
          </div>

          {/* 模型名称 */}
          <div>
            <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
              Model Name
            </label>
            <input
              type="text"
              value={localConfig.modelName}
              onChange={(e) =>
                setLocalConfig({ ...localConfig, modelName: e.target.value })
              }
              placeholder="e.g., gemini-2.5-flash"
              className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2 dark:border-slate-700 dark:bg-slate-800"
            />
          </div>

          {/* 自定义 Base URL（仅当选择 custom 时显示） */}
          {localConfig.provider === "custom" && (
            <div>
              <label className="mb-2 block text-sm font-medium text-slate-700 dark:text-slate-300">
                Base URL
              </label>
              <input
                type="url"
                value={localConfig.baseUrl || ""}
                onChange={(e) =>
                  setLocalConfig({ ...localConfig, baseUrl: e.target.value })
                }
                placeholder="https://api.example.com/v1"
                className="w-full rounded-lg border border-slate-300 bg-white px-4 py-2 dark:border-slate-700 dark:bg-slate-800"
              />
            </div>
          )}

          {/* 提示信息 */}
          <div className="rounded-lg bg-indigo-50 p-3 dark:bg-indigo-900/20">
            <p className="text-sm text-indigo-900 dark:text-indigo-200">
              <strong>💡 提示:</strong> 配置保存后立即生效，用于所有 AI 功能（流程图生成、截图识别、架构优化等）
            </p>
            <p className="mt-1 text-xs text-indigo-700 dark:text-indigo-300">
              配置会保存在浏览器本地，每次调用 AI 功能时自动使用
            </p>
          </div>
        </div>

        {/* 底部按钮 */}
        <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4 dark:border-slate-800">
          <button
            onClick={onClose}
            className="rounded-lg px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700"
          >
            <Save className="h-4 w-4" />
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
}
