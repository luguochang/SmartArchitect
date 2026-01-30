"use client";

import { Sparkles, Image, MessageSquare, Wand2, Palette } from "lucide-react";

export function EmptyCanvasState() {
  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
      <div className="text-center max-w-2xl px-8">
        {/* 主标题 */}
        <div className="mb-8">
          <div className="inline-block p-4 rounded-2xl bg-gradient-to-br from-indigo-500/10 to-purple-500/10 mb-4">
            <Sparkles className="w-16 h-16 text-indigo-600 dark:text-indigo-400" />
          </div>
          <h1 className="text-4xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400 bg-clip-text text-transparent mb-3">
            欢迎使用 Archboard AI
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            智能架构设计，让流程图创作变得简单有趣
          </p>
        </div>

        {/* 快速开始卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          {/* AI 聊天生成 */}
          <div className="group p-6 rounded-xl bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-2 border-slate-200 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-500 transition-all duration-300 hover:scale-105 hover:shadow-lg">
            <div className="flex flex-col items-center text-center">
              <div className="p-3 rounded-xl bg-gradient-to-br from-green-500/20 to-emerald-500/20 mb-3 group-hover:scale-110 transition-transform">
                <MessageSquare className="w-8 h-8 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-2">
                AI 聊天生成
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                用自然语言描述，AI 自动生成流程图
              </p>
            </div>
          </div>

          {/* 图片识别 */}
          <div className="group p-6 rounded-xl bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-2 border-slate-200 dark:border-slate-700 hover:border-purple-400 dark:hover:border-purple-500 transition-all duration-300 hover:scale-105 hover:shadow-lg">
            <div className="flex flex-col items-center text-center">
              <div className="p-3 rounded-xl bg-gradient-to-br from-purple-500/20 to-pink-500/20 mb-3 group-hover:scale-110 transition-transform">
                <Image className="w-8 h-8 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-2">
                图片识别
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                上传手绘草图，AI 转换为专业流程图
              </p>
            </div>
          </div>

          {/* 样式切换 */}
          <div className="group p-6 rounded-xl bg-white/50 dark:bg-slate-800/50 backdrop-blur-sm border-2 border-slate-200 dark:border-slate-700 hover:border-orange-400 dark:hover:border-orange-500 transition-all duration-300 hover:scale-105 hover:shadow-lg">
            <div className="flex flex-col items-center text-center">
              <div className="p-3 rounded-xl bg-gradient-to-br from-orange-500/20 to-amber-500/20 mb-3 group-hover:scale-110 transition-transform">
                <Palette className="w-8 h-8 text-orange-600 dark:text-orange-400" />
              </div>
              <h3 className="font-semibold text-slate-800 dark:text-slate-200 mb-2">
                5种专业样式
              </h3>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                一键切换 BPMN、企业、技术文档等风格
              </p>
            </div>
          </div>
        </div>

        {/* 提示文字 */}
        <div className="flex items-center justify-center gap-2 text-sm text-slate-500 dark:text-slate-400">
          <Wand2 className="w-4 h-4" />
          <span>从左侧工具栏开始，或拖拽节点到画布</span>
        </div>

        {/* 装饰性背景元素 */}
        <div className="absolute inset-0 -z-10 overflow-hidden pointer-events-none opacity-30">
          <div className="absolute top-1/4 left-1/4 w-64 h-64 bg-indigo-500/20 rounded-full blur-3xl"></div>
          <div className="absolute bottom-1/4 right-1/4 w-64 h-64 bg-purple-500/20 rounded-full blur-3xl"></div>
        </div>
      </div>
    </div>
  );
}
