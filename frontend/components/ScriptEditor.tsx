"use client";

import { useState, useEffect, useCallback } from "react";
import { X, Save, Sparkles, RotateCcw, Clock, FileText, Lightbulb, Check, Loader2, Zap, History, Eye } from "lucide-react";
import { toast } from "sonner";
import RefineDialog from "./RefineDialog";
import type {
  ScriptContent,
  ScriptMetadata,
  ScriptDuration,
  ImprovementSuggestions,
  ImprovementSuggestion,
  ScriptSection,
  SuggestionHistoryItem,
  SuggestionPreview,
} from "@/types/script";
import { getTargetWordCount, getWordCountStatus, formatReadingTime, formatSection } from "@/types/script";

interface ScriptEditorProps {
  scriptId: string;
  initialContent: ScriptContent;
  duration: ScriptDuration;
  isOpen: boolean;
  onClose: () => void;
}

export default function ScriptEditor({
  scriptId,
  initialContent,
  duration,
  isOpen,
  onClose,
}: ScriptEditorProps) {
  // Editor state
  const [content, setContent] = useState<ScriptContent>(initialContent);
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);

  // Refine dialog state
  const [refineSection, setRefineSection] = useState<ScriptSection | null>(null);
  const [refineFeedback, setRefineFeedback] = useState<string>("");  // 新增：预填充的反馈
  const [isRefining, setIsRefining] = useState(false);

  // Suggestions state
  const [suggestions, setSuggestions] = useState<ImprovementSuggestions | null>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

  // Batch apply state
  const [isBatchApplying, setIsBatchApplying] = useState(false);
  const [batchProgress, setBatchProgress] = useState({ current: 0, total: 0 });

  // Preview state
  const [preview, setPreview] = useState<SuggestionPreview | null>(null);
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);

  // History state
  const [history, setHistory] = useState<SuggestionHistoryItem[]>([]);
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);

  // Calculate stats
  const totalWordCount = (content.intro + content.body + content.conclusion).length;
  const targetWords = getTargetWordCount(duration);
  const wordCountStatus = getWordCountStatus(totalWordCount, duration);
  const estimatedSeconds = Math.round((totalWordCount / 150) * 60);

  // Auto-save with debounce
  useEffect(() => {
    if (!hasUnsavedChanges) return;

    const timeoutId = setTimeout(() => {
      handleSave();
    }, 2000); // Save after 2 seconds of inactivity

    return () => clearTimeout(timeoutId);
  }, [content, hasUnsavedChanges]);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const metadata: ScriptMetadata = {
        duration,
        word_count: totalWordCount,
        rag_sources: [],
        version: 0,
      };

      const response = await fetch(`/api/export/script/${scriptId}/draft`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content,
          metadata,
        }),
      });

      if (!response.ok) {
        throw new Error("保存失败");
      }

      const data = await response.json();
      setLastSaved(new Date(data.saved_at));
      setHasUnsavedChanges(false);
      toast.success("已自动保存");
    } catch (error) {
      console.error("Save error:", error);
      toast.error("保存失败");
    } finally {
      setIsSaving(false);
    }
  };

  const updateSection = (section: keyof ScriptContent, value: string) => {
    setContent((prev) => {
      const updated = { ...prev, [section]: value };
      // Update full_text
      updated.full_text = `[INTRO]\n${updated.intro}\n\n[BODY]\n${updated.body}\n\n[CONCLUSION]\n${updated.conclusion}`;
      return updated;
    });
    setHasUnsavedChanges(true);
  };

  const handleRefine = async (section: ScriptSection, feedback: string) => {
    setIsRefining(true);
    try {
      const response = await fetch(`/api/export/script/${scriptId}/refine`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          section,
          user_feedback: feedback,
        }),
      });

      if (!response.ok) {
        throw new Error("润色失败");
      }

      const data = await response.json();

      // Update content
      setContent((prev) => {
        const updated = { ...prev, [section]: data.refined_text };
        updated.full_text = `[INTRO]\n${updated.intro}\n\n[BODY]\n${updated.body}\n\n[CONCLUSION]\n${updated.conclusion}`;
        return updated;
      });

      setHasUnsavedChanges(true);
      toast.success(`${section} 章节已润色完成`);

      // Show changes summary
      if (data.changes_summary) {
        toast.info(`变更: ${data.changes_summary}`, { duration: 5000 });
      }
    } catch (error) {
      console.error("Refine error:", error);
      toast.error("润色失败");
    } finally {
      setIsRefining(false);
      setRefineSection(null);
    }
  };

  const loadSuggestions = async () => {
    setLoadingSuggestions(true);
    try {
      const response = await fetch(
        `/api/export/script/${scriptId}/suggestions?focus_areas=clarity,engagement,flow`
      );

      if (!response.ok) {
        throw new Error("获取建议失败");
      }

      const data = await response.json();
      setSuggestions(data);
    } catch (error) {
      console.error("Load suggestions error:", error);
      toast.error("获取AI建议失败");
    } finally {
      setLoadingSuggestions(false);
    }
  };

  // 批量应用所有建议
  const handleBatchApply = async () => {
    if (!suggestions || suggestions.suggestions.length === 0) {
      toast.error("没有可应用的建议");
      return;
    }

    const confirmed = confirm(
      `确定要批量应用所有 ${suggestions.suggestions.length} 条建议吗？\n这将按优先级顺序自动优化各个章节。`
    );

    if (!confirmed) return;

    setIsBatchApplying(true);

    // 按优先级排序：high > medium > low
    const priorityOrder = { high: 0, medium: 1, low: 2 };
    const sortedSuggestions = [...suggestions.suggestions].sort(
      (a, b) => priorityOrder[a.priority] - priorityOrder[b.priority]
    );

    setBatchProgress({ current: 0, total: sortedSuggestions.length });
    let successCount = 0;

    for (let i = 0; i < sortedSuggestions.length; i++) {
      const sug = sortedSuggestions[i];
      setBatchProgress({ current: i + 1, total: sortedSuggestions.length });

      try {
        const targetSection = (sug.section === "overall" ? "intro" : sug.section) as ScriptSection;
        const originalText = content[targetSection];

        toast.info(`正在应用建议 ${i + 1}/${sortedSuggestions.length}: ${sug.issue}`);

        // 调用refine API
        const response = await fetch(`/api/export/script/${scriptId}/refine`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            section: targetSection,
            user_feedback: sug.suggestion,
          }),
        });

        if (!response.ok) throw new Error("润色失败");

        const data = await response.json();
        const refinedText = data.refined_text;

        // 更新内容
        setContent((prev) => {
          const updated = { ...prev, [targetSection]: refinedText };
          updated.full_text = `[INTRO]\n${updated.intro}\n\n[BODY]\n${updated.body}\n\n[CONCLUSION]\n${updated.conclusion}`;
          return updated;
        });

        // 添加到历史记录
        const historyItem: SuggestionHistoryItem = {
          id: `${Date.now()}-${i}`,
          timestamp: new Date(),
          section: targetSection,
          suggestion: sug,
          originalText,
          refinedText,
          status: "success",
        };
        setHistory((prev) => [historyItem, ...prev]);

        setHasUnsavedChanges(true);
        successCount++;

        // 每条应用后延迟，避免请求过快
        if (i < sortedSuggestions.length - 1) {
          await new Promise((resolve) => setTimeout(resolve, 1000));
        }
      } catch (error) {
        console.error(`Failed to apply suggestion ${i + 1}:`, error);
        toast.error(`建议 ${i + 1} 应用失败: ${sug.issue}`);

        // 记录失败
        const historyItem: SuggestionHistoryItem = {
          id: `${Date.now()}-${i}`,
          timestamp: new Date(),
          section: sug.section as ScriptSection,
          suggestion: sug,
          originalText: "",
          refinedText: "",
          status: "failed",
        };
        setHistory((prev) => [historyItem, ...prev]);
      }
    }

    setIsBatchApplying(false);
    setBatchProgress({ current: 0, total: 0 });

    if (successCount > 0) {
      toast.success(`成功应用 ${successCount}/${sortedSuggestions.length} 条建议`);
      // 重新获取建议
      setTimeout(() => loadSuggestions(), 2000);
    }
  };

  // 预览建议效果
  const handlePreviewSuggestion = async (sug: ImprovementSuggestion) => {
    const targetSection = (sug.section === "overall" ? "intro" : sug.section) as ScriptSection;
    const originalText = content[targetSection];

    setPreview({
      suggestion: sug,
      originalText,
      previewText: "",
      isLoading: true,
    });
    setShowPreviewDialog(true);

    try {
      // 调用refine API预览
      const response = await fetch(`/api/export/script/${scriptId}/refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          section: targetSection,
          user_feedback: sug.suggestion,
        }),
      });

      if (!response.ok) throw new Error("预览生成失败");

      const data = await response.json();

      setPreview((prev) => prev ? {
        ...prev,
        previewText: data.refined_text,
        isLoading: false,
      } : null);
    } catch (error) {
      console.error("Preview error:", error);
      toast.error("预览生成失败");
      setShowPreviewDialog(false);
      setPreview(null);
    }
  };

  // 接受预览结果
  const handleAcceptPreview = () => {
    if (!preview) return;

    const targetSection = (preview.suggestion.section === "overall" ? "intro" : preview.suggestion.section) as ScriptSection;

    // 更新内容
    setContent((prev) => {
      const updated = { ...prev, [targetSection]: preview.previewText };
      updated.full_text = `[INTRO]\n${updated.intro}\n\n[BODY]\n${updated.body}\n\n[CONCLUSION]\n${updated.conclusion}`;
      return updated;
    });

    // 添加到历史记录
    const historyItem: SuggestionHistoryItem = {
      id: `${Date.now()}`,
      timestamp: new Date(),
      section: targetSection,
      suggestion: preview.suggestion,
      originalText: preview.originalText,
      refinedText: preview.previewText,
      status: "success",
    };
    setHistory((prev) => [historyItem, ...prev]);

    setHasUnsavedChanges(true);
    setShowPreviewDialog(false);
    setPreview(null);
    toast.success("已应用改进建议");
  };

  // 撤销历史记录中的某项
  const handleUndoHistoryItem = (itemId: string) => {
    const item = history.find((h) => h.id === itemId);
    if (!item || item.status !== "success") return;

    const confirmed = confirm(`确定要撤销对"${formatSection(item.section)}"章节的改动吗？`);
    if (!confirmed) return;

    // 恢复原文
    setContent((prev) => {
      const updated = { ...prev, [item.section]: item.originalText };
      updated.full_text = `[INTRO]\n${updated.intro}\n\n[BODY]\n${updated.body}\n\n[CONCLUSION]\n${updated.conclusion}`;
      return updated;
    });

    // 更新历史记录状态
    setHistory((prev) =>
      prev.map((h) =>
        h.id === itemId ? { ...h, status: "reverted" as const } : h
      )
    );

    setHasUnsavedChanges(true);
    toast.success(`已撤销对"${formatSection(item.section)}"的改动`);
  };

  const handleApplySuggestion = (section: string, suggestion: string) => {
    // 将 "overall" 映射到 "intro"（或可以让用户选择）
    const targetSection = (section === "overall" ? "intro" : section) as ScriptSection;

    // 设置预填充的反馈和章节
    setRefineFeedback(suggestion);
    setRefineSection(targetSection);
  };

  const handleClose = () => {
    if (hasUnsavedChanges) {
      if (confirm("有未保存的更改，确定要关闭吗？")) {
        onClose();
      }
    } else {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm" onClick={handleClose} />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div
          className="bg-white rounded-xl shadow-2xl w-full max-w-7xl max-h-[95vh] overflow-hidden pointer-events-auto flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gray-50">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
                <FileText className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">演讲稿编辑器</h2>
                <div className="flex items-center gap-4 mt-1">
                  <span className="text-sm text-gray-500">
                    {totalWordCount} 字 / {targetWords} 字目标
                  </span>
                  <span className="text-sm text-gray-500">
                    预计时长: {formatReadingTime(estimatedSeconds)}
                  </span>
                  {lastSaved && (
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <Check className="w-3 h-3" />
                      保存于 {lastSaved.toLocaleTimeString()}
                    </span>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* Save Status */}
              {isSaving && (
                <div className="flex items-center gap-2 text-sm text-gray-500">
                  <Loader2 className="w-4 h-4 animate-spin" />
                  保存中...
                </div>
              )}
              {hasUnsavedChanges && !isSaving && (
                <div className="text-sm text-amber-600">未保存</div>
              )}

              {/* History Button */}
              <button
                onClick={() => setShowHistoryPanel(!showHistoryPanel)}
                className="flex items-center gap-2 px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-lg hover:bg-gray-700 transition-colors relative"
              >
                <History className="w-4 h-4" />
                历史
                {history.filter(h => h.status === "success").length > 0 && (
                  <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                    {history.filter(h => h.status === "success").length}
                  </span>
                )}
              </button>

              {/* AI Suggestions Button */}
              <button
                onClick={loadSuggestions}
                disabled={loadingSuggestions}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white text-sm font-medium rounded-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
              >
                {loadingSuggestions ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Lightbulb className="w-4 h-4" />
                )}
                AI建议
              </button>

              <button
                onClick={handleClose}
                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-hidden flex">
            {/* Editor Columns */}
            <div className="flex-1 grid grid-cols-3 gap-4 p-6 overflow-y-auto">
              {/* Intro Column */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-green-500"></div>
                    开场部分
                  </h3>
                  <button
                    onClick={() => setRefineSection("intro")}
                    disabled={isRefining}
                    className="p-1.5 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
                    title="润色开场"
                  >
                    <Sparkles className="w-4 h-4 text-indigo-600" />
                  </button>
                </div>
                <textarea
                  value={content.intro}
                  onChange={(e) => updateSection("intro", e.target.value)}
                  className="w-full h-[calc(100vh-300px)] p-4 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm leading-relaxed"
                  placeholder="开场内容..."
                />
                <div className="text-xs text-gray-500">
                  {content.intro.length} 字
                </div>
              </div>

              {/* Body Column */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-blue-500"></div>
                    主体部分
                  </h3>
                  <button
                    onClick={() => setRefineSection("body")}
                    disabled={isRefining}
                    className="p-1.5 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
                    title="润色主体"
                  >
                    <Sparkles className="w-4 h-4 text-indigo-600" />
                  </button>
                </div>
                <textarea
                  value={content.body}
                  onChange={(e) => updateSection("body", e.target.value)}
                  className="w-full h-[calc(100vh-300px)] p-4 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm leading-relaxed"
                  placeholder="主体内容..."
                />
                <div className="text-xs text-gray-500">
                  {content.body.length} 字
                </div>
              </div>

              {/* Conclusion Column */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-orange-500"></div>
                    结尾部分
                  </h3>
                  <button
                    onClick={() => setRefineSection("conclusion")}
                    disabled={isRefining}
                    className="p-1.5 hover:bg-gray-100 rounded transition-colors disabled:opacity-50"
                    title="润色结尾"
                  >
                    <Sparkles className="w-4 h-4 text-indigo-600" />
                  </button>
                </div>
                <textarea
                  value={content.conclusion}
                  onChange={(e) => updateSection("conclusion", e.target.value)}
                  className="w-full h-[calc(100vh-300px)] p-4 border border-gray-200 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm leading-relaxed"
                  placeholder="结尾内容..."
                />
                <div className="text-xs text-gray-500">
                  {content.conclusion.length} 字
                </div>
              </div>
            </div>

            {/* Suggestions Sidebar */}
            {suggestions && (
              <div className="w-80 border-l border-gray-200 bg-gray-50 overflow-y-auto">
                <div className="p-6 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-semibold text-gray-900">AI 改进建议</h3>
                    <button
                      onClick={() => setSuggestions(null)}
                      className="p-1 hover:bg-gray-200 rounded transition-colors"
                    >
                      <X className="w-4 h-4 text-gray-500" />
                    </button>
                  </div>

                  {/* Overall Score */}
                  <div className="bg-white rounded-lg p-4 border border-gray-200">
                    <div className="text-xs text-gray-500 mb-1">整体质量</div>
                    <div className="flex items-center gap-3">
                      <div className="text-3xl font-bold text-indigo-600">
                        {suggestions.overall_score.toFixed(1)}
                      </div>
                      <div className="text-sm text-gray-400">/ 10.0</div>
                    </div>
                  </div>

                  {/* Strengths */}
                  {suggestions.strengths.length > 0 && (
                    <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                      <div className="text-xs font-medium text-green-900 mb-2">优点</div>
                      <ul className="space-y-1">
                        {suggestions.strengths.map((strength, idx) => (
                          <li key={idx} className="text-sm text-green-700 flex items-start gap-2">
                            <Check className="w-4 h-4 flex-shrink-0 mt-0.5" />
                            <span>{strength}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Weaknesses */}
                  {suggestions.weaknesses.length > 0 && (
                    <div className="bg-amber-50 rounded-lg p-4 border border-amber-200">
                      <div className="text-xs font-medium text-amber-900 mb-2">待改进</div>
                      <ul className="space-y-1">
                        {suggestions.weaknesses.map((weakness, idx) => (
                          <li key={idx} className="text-sm text-amber-700 flex items-start gap-2">
                            <span className="text-amber-500">•</span>
                            <span>{weakness}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Batch Apply Button */}
                  {suggestions.suggestions.length > 0 && (
                    <button
                      onClick={handleBatchApply}
                      disabled={isBatchApplying || isRefining}
                      className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-purple-600 to-indigo-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
                    >
                      {isBatchApplying ? (
                        <>
                          <Loader2 className="w-5 h-5 animate-spin" />
                          应用中 {batchProgress.current}/{batchProgress.total}
                        </>
                      ) : (
                        <>
                          <Zap className="w-5 h-5" />
                          全部应用 ({suggestions.suggestions.length}条)
                        </>
                      )}
                    </button>
                  )}

                  {/* Suggestions */}
                  <div className="space-y-3">
                    {suggestions.suggestions.map((sug, idx) => (
                      <div
                        key={idx}
                        className={`bg-white rounded-lg p-4 border-2 ${
                          sug.priority === "high"
                            ? "border-red-200"
                            : sug.priority === "medium"
                            ? "border-yellow-200"
                            : "border-gray-200"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <span className="text-xs font-medium text-gray-500 uppercase">
                            {sug.section}
                          </span>
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full ${
                              sug.priority === "high"
                                ? "bg-red-100 text-red-700"
                                : sug.priority === "medium"
                                ? "bg-yellow-100 text-yellow-700"
                                : "bg-gray-100 text-gray-700"
                            }`}
                          >
                            {sug.priority}
                          </span>
                        </div>
                        <div className="text-sm font-medium text-gray-900 mb-1">{sug.issue}</div>
                        <div className="text-sm text-gray-600 mb-3">{sug.suggestion}</div>

                        {/* 按钮组 */}
                        <div className="grid grid-cols-2 gap-2">
                          <button
                            onClick={() => handlePreviewSuggestion(sug)}
                            disabled={isBatchApplying || isRefining}
                            className="flex items-center justify-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                          >
                            <Eye className="w-4 h-4" />
                            预览
                          </button>
                          <button
                            onClick={() => handleApplySuggestion(sug.section, sug.suggestion)}
                            disabled={isBatchApplying || isRefining}
                            className="flex items-center justify-center gap-2 px-3 py-2 bg-indigo-50 hover:bg-indigo-100 text-indigo-700 text-sm font-medium rounded-lg transition-colors disabled:opacity-50"
                          >
                            <Sparkles className="w-4 h-4" />
                            应用
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Word Count Status Bar */}
          <div
            className={`px-6 py-3 border-t ${
              wordCountStatus === "good"
                ? "bg-green-50 border-green-200"
                : wordCountStatus === "too-short"
                ? "bg-amber-50 border-amber-200"
                : "bg-red-50 border-red-200"
            }`}
          >
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div
                  className={`w-2 h-2 rounded-full ${
                    wordCountStatus === "good"
                      ? "bg-green-500"
                      : wordCountStatus === "too-short"
                      ? "bg-amber-500"
                      : "bg-red-500"
                  }`}
                ></div>
                <span className="font-medium">
                  {wordCountStatus === "good"
                    ? "字数符合目标"
                    : wordCountStatus === "too-short"
                    ? "字数偏少"
                    : "内容丰富"}
                </span>
              </div>
              <div className="text-gray-600">
                参考范围: {Math.floor(targetWords * 0.5)} - {Math.ceil(targetWords * 2.0)} 字
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Refine Dialog */}
      {refineSection && (
        <RefineDialog
          section={refineSection}
          isOpen={!!refineSection}
          isRefining={isRefining}
          onRefine={handleRefine}
          onClose={() => {
            setRefineSection(null);
            setRefineFeedback("");  // 清除预填充的反馈
          }}
          initialFeedback={refineFeedback}  // 传入预填充的反馈
        />
      )}

      {/* Preview Dialog */}
      {showPreviewDialog && preview && (
        <>
          <div className="fixed inset-0 bg-black/60 z-[70] backdrop-blur-sm" onClick={() => setShowPreviewDialog(false)} />
          <div className="fixed inset-0 z-[70] flex items-center justify-center p-4 pointer-events-none">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl max-h-[90vh] overflow-hidden pointer-events-auto flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-indigo-50">
                <div>
                  <h2 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                    <Eye className="w-6 h-6 text-purple-600" />
                    建议预览
                  </h2>
                  <p className="text-sm text-gray-600 mt-1">
                    {formatSection(preview.suggestion.section as ScriptSection)} · {preview.suggestion.issue}
                  </p>
                </div>
                <button onClick={() => setShowPreviewDialog(false)} className="p-2 hover:bg-white/50 rounded-lg transition-colors">
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              {/* Content */}
              <div className="flex-1 overflow-y-auto p-6">
                {preview.isLoading ? (
                  <div className="flex flex-col items-center justify-center h-64 space-y-4">
                    <Loader2 className="w-12 h-12 text-purple-600 animate-spin" />
                    <p className="text-gray-600">AI 正在生成改进版本...</p>
                  </div>
                ) : (
                  <div className="grid grid-cols-2 gap-6">
                    {/* 原文 */}
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-gray-400"></div>
                        原文
                      </h3>
                      <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 min-h-[400px]">
                        <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800 leading-relaxed">
                          {preview.originalText}
                        </pre>
                        <div className="mt-3 text-xs text-gray-500">
                          {preview.originalText.length} 字
                        </div>
                      </div>
                    </div>

                    {/* 改进后 */}
                    <div>
                      <h3 className="text-sm font-semibold text-gray-700 mb-3 flex items-center gap-2">
                        <div className="w-2 h-2 rounded-full bg-green-500"></div>
                        改进后
                      </h3>
                      <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border-2 border-green-200 min-h-[400px]">
                        <pre className="whitespace-pre-wrap font-sans text-sm text-gray-900 leading-relaxed font-medium">
                          {preview.previewText}
                        </pre>
                        <div className="mt-3 text-xs text-green-700 font-medium">
                          {preview.previewText.length} 字 ({preview.previewText.length > preview.originalText.length ? '+' : ''}{preview.previewText.length - preview.originalText.length})
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* 建议详情 */}
                {!preview.isLoading && (
                  <div className="mt-6 bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <div className="text-sm font-medium text-blue-900 mb-2">
                      💡 改进建议
                    </div>
                    <p className="text-sm text-blue-700">{preview.suggestion.suggestion}</p>
                  </div>
                )}
              </div>

              {/* Footer */}
              {!preview.isLoading && (
                <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
                  <button
                    onClick={() => setShowPreviewDialog(false)}
                    className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    取消
                  </button>
                  <button
                    onClick={handleAcceptPreview}
                    className="px-6 py-2 bg-green-600 text-white text-sm font-medium rounded-lg hover:bg-green-700 transition-colors flex items-center gap-2"
                  >
                    <Check className="w-4 h-4" />
                    接受改进
                  </button>
                </div>
              )}
            </div>
          </div>
        </>
      )}

      {/* History Panel */}
      {showHistoryPanel && (
        <>
          <div className="fixed inset-0 bg-black/40 z-[60] backdrop-blur-sm" onClick={() => setShowHistoryPanel(false)} />
          <div className="fixed right-0 top-0 bottom-0 w-96 bg-white shadow-2xl z-[60] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gray-50">
              <div>
                <h2 className="text-lg font-bold text-gray-900 flex items-center gap-2">
                  <History className="w-5 h-5 text-gray-600" />
                  建议历史
                </h2>
                <p className="text-xs text-gray-500 mt-1">
                  {history.filter(h => h.status === "success").length} 条成功应用
                </p>
              </div>
              <button onClick={() => setShowHistoryPanel(false)} className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {history.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-full text-gray-400">
                  <History className="w-16 h-16 mb-4 opacity-30" />
                  <p className="text-sm">暂无历史记录</p>
                </div>
              ) : (
                history.map((item) => (
                  <div
                    key={item.id}
                    className={`bg-white rounded-lg p-4 border-2 ${
                      item.status === "success"
                        ? "border-green-200"
                        : item.status === "failed"
                        ? "border-red-200"
                        : "border-gray-300"
                    }`}
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                          item.status === "success"
                            ? "bg-green-100 text-green-700"
                            : item.status === "failed"
                            ? "bg-red-100 text-red-700"
                            : "bg-gray-100 text-gray-700"
                        }`}>
                          {formatSection(item.section)}
                        </span>
                        <span className="text-xs text-gray-500">
                          {new Date(item.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      {item.status === "success" && (
                        <button
                          onClick={() => handleUndoHistoryItem(item.id)}
                          className="p-1 hover:bg-gray-100 rounded transition-colors"
                          title="撤销"
                        >
                          <RotateCcw className="w-4 h-4 text-gray-600" />
                        </button>
                      )}
                    </div>

                    {/* Issue */}
                    <div className="text-sm font-medium text-gray-900 mb-1">
                      {item.suggestion.issue}
                    </div>

                    {/* Suggestion */}
                    <div className="text-xs text-gray-600 mb-2">
                      {item.suggestion.suggestion}
                    </div>

                    {/* Status */}
                    <div className={`flex items-center gap-1 text-xs ${
                      item.status === "success"
                        ? "text-green-600"
                        : item.status === "failed"
                        ? "text-red-600"
                        : "text-gray-600"
                    }`}>
                      {item.status === "success" && <Check className="w-3 h-3" />}
                      {item.status === "success" && "已应用"}
                      {item.status === "failed" && "应用失败"}
                      {item.status === "reverted" && "已撤销"}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Footer */}
            {history.length > 0 && (
              <div className="p-4 border-t border-gray-200 bg-gray-50">
                <button
                  onClick={() => {
                    if (confirm("确定要清空所有历史记录吗？")) {
                      setHistory([]);
                      toast.success("历史记录已清空");
                    }
                  }}
                  className="w-full px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  清空历史
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </>
  );
}
