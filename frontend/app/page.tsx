"use client";

import { ArchitectCanvas } from "@/components/ArchitectCanvas";
import { CodeEditor } from "@/components/CodeEditor";
import { Sidebar } from "@/components/Sidebar";
import ThemeSwitcher from "@/components/ThemeSwitcher";
import { Sparkles } from "lucide-react";
import { Toaster } from "sonner";

export default function Home() {
  return (
    <div className="flex h-screen w-screen flex-col bg-slate-50 dark:bg-slate-950">
      {/* Toast 通知 */}
      <Toaster
        position="top-right"
        richColors
        closeButton
        theme="light"
      />

      {/* 顶部导航栏 */}
      <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-6 dark:border-slate-800 dark:bg-slate-900">
        <div className="flex items-center gap-3">
          <Sparkles className="h-6 w-6 text-indigo-600" />
          <h1 className="text-xl font-bold text-slate-900 dark:text-white">
            SmartArchitect AI
          </h1>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-500">Phase 4: RAG + Export</span>
          <ThemeSwitcher />
        </div>
      </header>

      {/* 主内容区域 */}
      <div className="flex flex-1 overflow-hidden">
        {/* 左侧工具栏 */}
        <Sidebar />

        {/* 中间画布 */}
        <div className="flex-1 flex flex-col">
          <ArchitectCanvas />
        </div>

        {/* 右侧代码编辑器 */}
        <div className="w-1/3 border-l border-slate-200 dark:border-slate-800">
          <CodeEditor />
        </div>
      </div>
    </div>
  );
}
