"use client";

import { useState, useEffect, useCallback } from "react";
import { X, Save, Sparkles, RotateCcw, Clock, FileText, Lightbulb, Check, Loader2 } from "lucide-react";
import { toast } from "sonner";
import RefineDialog from "./RefineDialog";
import type {
  ScriptContent,
  ScriptMetadata,
  ScriptDuration,
  ImprovementSuggestions,
  ScriptSection,
} from "@/types/script";
import { getTargetWordCount, getWordCountStatus, formatReadingTime } from "@/types/script";

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
  const [isRefining, setIsRefining] = useState(false);

  // Suggestions state
  const [suggestions, setSuggestions] = useState<ImprovementSuggestions | null>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);

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
                        <div className="text-sm text-gray-600">{sug.suggestion}</div>
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
          onClose={() => setRefineSection(null)}
        />
      )}
    </>
  );
}
