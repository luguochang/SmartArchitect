"use client";

import { ArchitectCanvas } from "@/components/ArchitectCanvas";
import { AiControlPanel } from "@/components/AiControlPanel";
import { Sidebar } from "@/components/Sidebar";
import ThemeSwitcher from "@/components/ThemeSwitcher";
import { LayoutDashboard } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";

export default function Home() {
  const { canvasMode, setCanvasMode } = useArchitectStore();

  return (
    <div className="flex h-screen w-screen flex-col bg-slate-50 dark:bg-slate-950">
      {/* 顶部导航栏 */}
      <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-6 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-3">
          <LayoutDashboard className="h-6 w-6 text-indigo-600" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">Archboard</h1>
        </div>
        <div className="flex items-center gap-4">
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
        {/* 左侧工具栏 - Excalidraw 模式隐藏 */}
        {canvasMode === "reactflow" ? <Sidebar /> : <div className="w-[72px] md:w-[120px]" />}

        {/* 中间画布 */}
        <div className="flex flex-1 flex-col">
          <ArchitectCanvas />
        </div>

        {/* 右侧 AI 控制台 */}
        <div className="w-[420px] min-w-[360px] border-l border-slate-200 bg-white/70 backdrop-blur dark:border-slate-800 dark:bg-slate-900/70">
          <AiControlPanel />
        </div>
      </div>
    </div>
  );
}
