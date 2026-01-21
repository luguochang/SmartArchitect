"use client";

import { ArchitectCanvas } from "@/components/ArchitectCanvas";
import { AiControlPanel } from "@/components/AiControlPanel";
import { Sidebar } from "@/components/Sidebar";
import ThemeSwitcher from "@/components/ThemeSwitcher";
import ModelPresetsManager from "@/components/ModelPresetsManager";
import { LayoutDashboard, Settings, Sparkles } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { useState, useMemo } from "react";
import { toast } from "sonner";

export default function Home() {
  const { canvasMode, setCanvasMode, modelConfig, setModelConfig } = useArchitectStore();
  const [showPresetsManager, setShowPresetsManager] = useState(false);

  const apiReady = useMemo(() => Boolean(modelConfig.apiKey && modelConfig.apiKey.trim()), [modelConfig.apiKey]);

  return (
    <div className="flex h-screen w-screen flex-col bg-slate-50 dark:bg-slate-950">
      {/* 顶部导航栏 */}
      <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-6 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-3">
          <LayoutDashboard className="h-6 w-6 text-indigo-600" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">Archboard</h1>
        </div>
        <div className="flex items-center gap-3">
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
