"use client";

import { ArchitectCanvas } from "@/components/ArchitectCanvas";
import { AiControlPanel } from "@/components/AiControlPanel";
import { Sidebar } from "@/components/Sidebar";
import ThemeSwitcher from "@/components/ThemeSwitcher";
import ModelPresetsManager from "@/components/ModelPresetsManager";
import { LayoutDashboard, Settings, Sparkles, Info, Github } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { useState, useMemo, useEffect } from "react";
import { API_ENDPOINTS } from "@/lib/api-config";

export default function Home() {
  const { canvasMode, setCanvasMode, modelConfig, setModelConfig } = useArchitectStore();
  const [showPresetsManager, setShowPresetsManager] = useState(false);
  const [showConfigTooltip, setShowConfigTooltip] = useState(false);

  // 🔧 自动加载默认配置（页面加载时）
  useEffect(() => {
    const loadDefaultConfig = async () => {
      try {
        const response = await fetch(API_ENDPOINTS.modelPresets);
        if (response.ok) {
          const data = await response.json();
          const defaultPreset = data.presets?.find((p: any) => p.is_default);

          if (defaultPreset) {
            // 获取完整配置（包含真实 API key）
            const fullConfigResponse = await fetch(API_ENDPOINTS.modelPresetFull(defaultPreset.id));
            if (fullConfigResponse.ok) {
              const fullData = await fullConfigResponse.json();
              const fullPreset = fullData.preset;

              // 自动设置到 store
              setModelConfig({
                provider: fullPreset.provider,
                apiKey: fullPreset.api_key,
                baseUrl: fullPreset.base_url || "",
                modelName: fullPreset.model_name,
              });

              console.log("✅ 自动加载默认配置:", fullPreset.name);
            }
          }
        }
      } catch (error) {
        console.error("加载默认配置失败:", error);
      }
    };

    loadDefaultConfig();
  }, []); // 只在组件挂载时执行一次

  const apiReady = useMemo(() => Boolean(modelConfig.apiKey && modelConfig.apiKey.trim()), [modelConfig.apiKey]);

  // Get current configuration display info
  const currentConfigInfo = useMemo(() => {
    return {
      displayName: "Custom API",
      model: modelConfig.modelName || "未配置",
      baseUrl: modelConfig.baseUrl || "未配置"
    };
  }, [modelConfig]);

  return (
    <div className="flex min-h-screen w-full flex-col overflow-hidden bg-slate-50 dark:bg-slate-950">
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
              <span className="hidden sm:inline">{currentConfigInfo.displayName}</span>
            </button>

            {showConfigTooltip && (
              <div className="absolute top-full mt-2 right-0 z-50 w-96 rounded-lg border border-slate-200 bg-white p-3 shadow-xl dark:border-slate-700 dark:bg-slate-800">
                <div className="space-y-2 text-xs">
                  <div>
                    <span className="font-semibold text-slate-900 dark:text-white">当前配置：</span>
                    <span className="ml-1 text-slate-600 dark:text-slate-400">{currentConfigInfo.displayName}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-900 dark:text-white">模型：</span>
                    <code className="ml-1 rounded bg-slate-100 px-1.5 py-0.5 font-mono text-blue-600 dark:bg-slate-900 dark:text-blue-400">
                      {currentConfigInfo.model}
                    </code>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-900 dark:text-white">Base URL：</span>
                    <code className="ml-1 rounded bg-slate-100 px-1.5 py-0.5 font-mono text-emerald-600 dark:bg-slate-900 dark:text-emerald-400 break-all block mt-1">
                      {currentConfigInfo.baseUrl}
                    </code>
                  </div>
                  <div className="border-t border-slate-200 pt-2 dark:border-slate-700">
                    <span className="font-semibold text-slate-900 dark:text-white">状态：</span>
                    <span className={`ml-1 ${apiReady ? "text-green-600 dark:text-green-400" : "text-amber-600 dark:text-amber-400"}`}>
                      {apiReady ? "✓ API 已配置" : "⚠ 需要配置 API Key"}
                    </span>
                  </div>
                  <div className="border-t border-slate-200 pt-2 mt-2 dark:border-slate-700">
                    <div className="rounded-md bg-indigo-50 p-2 dark:bg-indigo-900/20">
                      <p className="text-xs text-indigo-700 dark:text-indigo-300 leading-relaxed">
                        <span className="font-semibold">💡 推荐配置：</span> 使用国内中转站 + Claude 模型，生成效果更好，格式完全兼容。
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 社交链接 */}
          <a
            href="https://github.com/luguochang/SmartArchitect"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-medium text-white shadow-sm hover:bg-slate-800 transition-colors dark:bg-slate-800 dark:hover:bg-slate-700"
            title="访问 GitHub 仓库"
          >
            <Github className="h-3.5 w-3.5" />
            <span>GitHub</span>
          </a>

          <a
            href="https://blog.csdn.net/luguochang"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1.5 rounded-lg bg-gradient-to-r from-red-500 to-red-600 px-3 py-1.5 text-xs font-medium text-white shadow-sm hover:from-red-600 hover:to-red-700 transition-colors"
            title="访问 CSDN 博客"
          >
            <span className="text-sm font-bold">C</span>
            <span>CSDN</span>
          </a>

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
              data-testid="mode-reactflow"
              className={`px-3 py-1 rounded-l-full ${canvasMode === "reactflow" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200" : "text-slate-600 dark:text-slate-300"}`}
            >
              Flow Canvas
            </button>
            <button
              onClick={() => setCanvasMode("excalidraw")}
              data-testid="mode-excalidraw"
              className={`px-3 py-1 rounded-r-full ${canvasMode === "excalidraw" ? "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-200" : "text-slate-600 dark:text-slate-300"}`}
            >
              Excalidraw
            </button>
          </div>
          <ThemeSwitcher />
        </div>
      </header>

      {/* 主内容区域 */}
      <div className="flex min-w-0 flex-1 overflow-hidden gap-3 px-3 py-3 bg-gradient-to-br from-slate-50 via-slate-100 to-indigo-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950">
        {/* 左侧工具栏 - 仅在 ReactFlow 模式显示 */}
        {canvasMode === "reactflow" && <Sidebar />}

        {/* 中间画布 */}
        <div className="flex min-w-0 flex-1 flex-col">
          <div className="relative flex-1 overflow-hidden rounded-2xl border border-slate-200 bg-white/90 shadow-xl backdrop-blur dark:border-slate-800 dark:bg-slate-900/80">
            <ArchitectCanvas />
          </div>
        </div>

        {/* 右侧 AI 控制台 */}
        <div className="w-[360px] min-w-[320px] shrink-0 overflow-hidden rounded-xl border border-slate-200 bg-white/90 px-3 py-3 shadow-lg backdrop-blur-lg dark:border-slate-800 dark:bg-slate-900/85">
          <AiControlPanel />
        </div>
      </div>

      {/* Model Presets Manager Modal */}
      <ModelPresetsManager
        isOpen={showPresetsManager}
        onClose={() => setShowPresetsManager(false)}
      />
    </div>
  );
}
