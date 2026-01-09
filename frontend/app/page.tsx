"use client";

import { ArchitectCanvas } from "@/components/ArchitectCanvas";
import { AiControlPanel } from "@/components/AiControlPanel";
import { Sidebar } from "@/components/Sidebar";
import ThemeSwitcher from "@/components/ThemeSwitcher";
import { Sparkles } from "lucide-react";

export default function Home() {
  return (
    <div className="flex h-screen w-screen flex-col bg-slate-50 dark:bg-slate-950">
      {/* 顶部导航栏 */}
      <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-6 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-3">
          <Sparkles className="h-6 w-6 text-indigo-600" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">SmartArchitect AI</h1>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-500">Phase 5: BPMN + AI Actions</span>
          <ThemeSwitcher />
        </div>
      </header>

      {/* 主内容区域 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 左侧工具栏 */}
        <Sidebar />

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
