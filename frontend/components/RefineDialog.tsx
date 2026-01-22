"use client";

import { useState } from "react";
import { X, Sparkles, Loader2 } from "lucide-react";
import type { ScriptSection } from "@/types/script";
import { QUICK_REFINEMENT_ACTIONS, formatSection } from "@/types/script";

interface RefineDialogProps {
  section: ScriptSection;
  isOpen: boolean;
  isRefining: boolean;
  onRefine: (section: ScriptSection, feedback: string) => void;
  onClose: () => void;
}

export default function RefineDialog({
  section,
  isOpen,
  isRefining,
  onRefine,
  onClose,
}: RefineDialogProps) {
  const [feedback, setFeedback] = useState("");

  const handleSubmit = () => {
    if (!feedback.trim()) {
      return;
    }
    onRefine(section, feedback);
  };

  const handleQuickAction = (actionFeedback: string) => {
    setFeedback(actionFeedback);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 z-[60] backdrop-blur-sm"
        onClick={onClose}
      />

      {/* Dialog */}
      <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 pointer-events-none">
        <div
          className="bg-white rounded-xl shadow-2xl w-full max-w-2xl pointer-events-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <h2 className="text-lg font-bold text-gray-900">
                  润色 {formatSection(section)} 章节
                </h2>
                <p className="text-sm text-gray-500">
                  描述您希望如何改进这个章节
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              disabled={isRefining}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Feedback Textarea */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                您的润色要求
              </label>
              <textarea
                value={feedback}
                onChange={(e) => setFeedback(e.target.value)}
                disabled={isRefining}
                placeholder="例如：开场太平淡，希望更有吸引力；或者：主体部分技术细节太多，希望更通俗易懂"
                className="w-full h-32 p-4 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent text-sm leading-relaxed disabled:bg-gray-50 disabled:text-gray-500"
                autoFocus
              />
              <div className="mt-2 text-xs text-gray-500">
                {feedback.length} / 500 字符
              </div>
            </div>

            {/* Quick Suggestions */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                快速建议（点击应用）
              </label>
              <div className="grid grid-cols-2 gap-2">
                {QUICK_REFINEMENT_ACTIONS.map((action) => (
                  <button
                    key={action.label}
                    onClick={() => handleQuickAction(action.feedback)}
                    disabled={isRefining}
                    className="flex items-center gap-3 p-3 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors text-left disabled:opacity-50 disabled:cursor-not-allowed group"
                  >
                    {action.icon && (
                      <span className="text-2xl flex-shrink-0">{action.icon}</span>
                    )}
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-gray-900 group-hover:text-purple-600 transition-colors">
                        {action.label}
                      </div>
                      <div className="text-xs text-gray-500 truncate">
                        {action.feedback.length > 30
                          ? action.feedback.substring(0, 30) + "..."
                          : action.feedback}
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {/* Examples Section */}
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <div className="text-xs font-medium text-blue-900 mb-2">
                💡 润色建议示例
              </div>
              <ul className="space-y-1.5 text-xs text-blue-700">
                <li>• "增加一个具体的数据或案例来支撑观点"</li>
                <li>• "用生动的类比让技术概念更易懂"</li>
                <li>• "调整语气，让表达更自信专业"</li>
                <li>• "简化长句，提高可读性"</li>
                <li>• "增加过渡句，让段落衔接更自然"</li>
              </ul>
            </div>

            {/* Refining Status */}
            {isRefining && (
              <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                <div className="flex items-center gap-3">
                  <Loader2 className="w-5 h-5 text-purple-600 animate-spin flex-shrink-0" />
                  <div>
                    <div className="text-sm font-medium text-purple-900">
                      AI 正在润色中...
                    </div>
                    <div className="text-xs text-purple-700 mt-1">
                      这可能需要几秒钟，请稍候
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
            <div className="text-sm text-gray-500">
              润色后将自动保存到编辑器
            </div>
            <div className="flex gap-3">
              <button
                onClick={onClose}
                disabled={isRefining}
                className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                取消
              </button>
              <button
                onClick={handleSubmit}
                disabled={!feedback.trim() || isRefining}
                className="px-6 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
              >
                {isRefining ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" />
                    润色中...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    开始润色
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
