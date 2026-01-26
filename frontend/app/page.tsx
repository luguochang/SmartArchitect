"use client";

import { ArchitectCanvas } from "@/components/ArchitectCanvas";
import { AiControlPanel } from "@/components/AiControlPanel";
import { Sidebar } from "@/components/Sidebar";
import ThemeSwitcher from "@/components/ThemeSwitcher";
import ModelPresetsManager from "@/components/ModelPresetsManager";
import { LayoutDashboard, Settings, Sparkles, Info } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { useState, useMemo } from "react";
import { toast } from "sonner";
import { PROVIDER_DEFAULTS } from "@/lib/config/providerDefaults";

export default function Home() {
  const { canvasMode, setCanvasMode, modelConfig, setModelConfig } = useArchitectStore();
  const [showPresetsManager, setShowPresetsManager] = useState(false);
  const [showConfigTooltip, setShowConfigTooltip] = useState(false);

  const apiReady = useMemo(() => Boolean(modelConfig.apiKey && modelConfig.apiKey.trim()), [modelConfig.apiKey]);

  // Get current provider display info
  const currentProviderInfo = useMemo(() => {
    const defaultConfig = PROVIDER_DEFAULTS[modelConfig.provider];
    return {
      displayName: defaultConfig?.displayName || modelConfig.provider,
      model: modelConfig.modelName || defaultConfig?.modelName || "未配置",
      baseUrl: modelConfig.baseUrl || defaultConfig?.baseUrl || "未配置"
    };
  }, [modelConfig]);

  return (
    <div className="flex h-screen w-screen flex-col bg-slate-50 dark:bg-slate-950">
      {/* 顶部导航栏 */}
      <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-6 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-3">
          <LayoutDashboard className="h-6 w-6 text-indigo-600" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">Archboard</h1>
        </div>
        <div className="flex items-center gap-3">
          {/* Current Config Display */}
          <div className="relative">
            <button
              onMouseEnter={() => setShowConfigTooltip(true)}
              onMouseLeave={() => setShowConfigTooltip(false)}
              className="flex items-center gap-1.5 rounded-lg bg-slate-100 px-2.5 py-1.5 text-xs font-medium text-slate-700 dark:bg-slate-800 dark:text-slate-300"
            >
              <Info className="h-3.5 w-3.5" />
              <span className="hidden sm:inline">{currentProviderInfo.displayName}</span>
            </button>

            {showConfigTooltip && (
              <div className="absolute top-full mt-2 right-0 z-50 w-80 rounded-lg border border-slate-200 bg-white p-3 shadow-xl dark:border-slate-700 dark:bg-slate-800">
                <div className="space-y-2 text-xs">
                  <div>
                    <span className="font-semibold text-slate-900 dark:text-white">当前配置：</span>
                    <span className="ml-1 text-slate-600 dark:text-slate-400">{currentProviderInfo.displayName}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-900 dark:text-white">模型：</span>
                    <code className="ml-1 rounded bg-slate-100 px-1.5 py-0.5 font-mono text-blue-600 dark:bg-slate-900 dark:text-blue-400">
                      {currentProviderInfo.model}
                    </code>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-900 dark:text-white">Base URL：</span>
                    <code className="ml-1 rounded bg-slate-100 px-1.5 py-0.5 font-mono text-emerald-600 dark:bg-slate-900 dark:text-emerald-400 break-all block mt-1">
                      {currentProviderInfo.baseUrl}
                    </code>
                  </div>
                  <div className="border-t border-slate-200 pt-2 dark:border-slate-700">
                    <span className="font-semibold text-slate-900 dark:text-white">状态：</span>
                    <span className={`ml-1 ${apiReady ? "text-green-600 dark:text-green-400" : "text-amber-600 dark:text-amber-400"}`}>
                      {apiReady ? "✓ API 已配置" : "⚠ 需要配置 API Key"}
                    </span>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* AI 配置按钮 - 最显眼位置 */}
          <button
            onClick={() => setShowPresetsManager(true)}
            className={`flex items-center gap-2 rounded-lg px-3 py-1.5 text-sm font-semibold shadow-sm transition ${
              apiReady
                ? "bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:from-emerald-600 hover:to-teal-600"
                : "bg-gradient-to-r from-amber-400 to-orange-500 text-white hover:from-amber-500 hover:to-orange-600 animate-pulse"
            }`}
            title={apiReady ? "AI 已配置，点击管理" : "⚠️ 请先配置 AI 模型"}
          >
            {apiReady ? (
              <>
                <Sparkles className="h-4 w-4" />
                <span className="hidden sm:inline">AI Configured</span>
              </>
            ) : (
              <>
                <Settings className="h-4 w-4" />
                <span className="hidden sm:inline">Configure AI</span>
              </>
            )}
          </button>

          <div className="flex rounded-full border border-slate-200 bg-white text-xs dark:border-slate-800 dark:bg-slate-800">
            <button
              onClick={() => setCanvasMode("reactflow")}
              className={`px-3 py-1 rounded-l-full ${canvasMode === "reactflow" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200" : "text-slate-600 dark:text-slate-300"}`}
            >
              Flow Canvas
            </button>
            <button
              onClick={() => setCanvasMode("excalidraw")}
              className={`px-3 py-1 rounded-r-full ${canvasMode === "excalidraw" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200" : "text-slate-600 dark:text-slate-300"}`}
            >
              Excalidraw
            </button>
          </div>
          <ThemeSwitcher />
        </div>
      </header>

      {/* 主内容区域 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 左侧工具栏 - 仅在 ReactFlow 模式显示 */}
        {canvasMode === "reactflow" && <Sidebar />}

        {/* 中间画布 */}
        <div className="flex flex-1 flex-col">
          <ArchitectCanvas />
        </div>

        {/* 右侧 AI 控制台 */}
        <div className="w-[420px] min-w-[360px] border-l border-slate-200 bg-white/70 backdrop-blur dark:border-slate-800 dark:bg-slate-900/70">
          <AiControlPanel />
        </div>
      </div>

      {/* Model Presets Manager Modal */}
      <ModelPresetsManager
        isOpen={showPresetsManager}
        onClose={() => setShowPresetsManager(false)}
        onSelectPreset={(preset) => {
          setModelConfig({
            provider: preset.provider,
            apiKey: preset.api_key,
            modelName: preset.model_name,
            baseUrl: preset.base_url || "",
          });
          toast.success(`使用配置: ${preset.name}`);
        }}
      />
    </div>
  );
}
