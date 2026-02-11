"use client";

import { useState, useEffect, useRef } from "react";
import { X, Sparkles, Clock, Users, Target, Loader2, Check, AlertCircle, FileText } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";
import type {
  ScriptDuration,
  ScriptTone,
  ScriptAudience,
  ScriptOptions,
  StreamEvent,
  ScriptContent,
} from "@/types/script";

interface ScriptGeneratorProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete: (scriptId: string, content: ScriptContent, duration: ScriptDuration) => void;
}

export default function ScriptGenerator({
  isOpen,
  onClose,
  onComplete,
}: ScriptGeneratorProps) {
  const { nodes, edges, modelConfig } = useArchitectStore();

  // Configuration state
  const [duration, setDuration] = useState<ScriptDuration>("2min");
  const [tone, setTone] = useState<ScriptTone>("professional");
  const [audience, setAudience] = useState<ScriptAudience>("mixed");
  const [focusAreas, setFocusAreas] = useState<string[]>(["scalability", "performance"]);

  // Generation state
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStep, setCurrentStep] = useState<string>("");
  const [progressLog, setProgressLog] = useState<string[]>([]);
  const [generatedText, setGeneratedText] = useState<string>("");
  const [sources, setSources] = useState<string[]>([]);
  const [isComplete, setIsComplete] = useState(false);

  const textAreaRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Auto-scroll to bottom as text generates
  useEffect(() => {
    if (textAreaRef.current && isGenerating) {
      textAreaRef.current.scrollTop = textAreaRef.current.scrollHeight;
    }
  }, [generatedText, isGenerating]);

  const availableFocusAreas = [
    { id: "scalability", label: "可扩展性" },
    { id: "performance", label: "性能" },
    { id: "security", label: "安全性" },
    { id: "reliability", label: "可靠性" },
    { id: "cost", label: "成本优化" },
    { id: "maintainability", label: "可维护性" },
  ];

  const toggleFocusArea = (areaId: string) => {
    setFocusAreas((prev) =>
      prev.includes(areaId)
        ? prev.filter((a) => a !== areaId)
        : [...prev, areaId]
    );
  };

  const handleGenerate = async () => {
    if (!modelConfig.apiKey) {
      toast.error("请先配置API密钥");
      return;
    }

    if (nodes.length === 0) {
      toast.error("请先创建架构图");
      return;
    }

    setIsGenerating(true);
    setIsComplete(false);
    setGeneratedText("");
    setProgressLog([]);
    setSources([]);
    setCurrentStep("正在连接...");

    // Create abort controller for cancellation
    abortControllerRef.current = new AbortController();

    try {
      const requestBody = {
        nodes,
        edges,
        duration,
        options: {
          tone,
          audience,
          focus_areas: focusAreas,
        } as ScriptOptions,
      };

      // Build query params with all model config
      const params = new URLSearchParams({
        provider: modelConfig.provider,
        api_key: modelConfig.apiKey,
      });

      // Add optional params for custom provider
      if (modelConfig.provider === "custom" && modelConfig.baseUrl) {
        params.append("base_url", modelConfig.baseUrl);
      }
      if (modelConfig.modelName) {
        params.append("model_name", modelConfig.modelName);
      }

      // Call streaming API
      const response = await fetch(
        `/api/export/script-stream?${params.toString()}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
          signal: abortControllerRef.current.signal,
        }
      );

      if (!response.ok) {
        throw new Error("生成失败");
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (!line.trim() || !line.startsWith("data: ")) continue;

          try {
            const eventData = JSON.parse(line.slice(6));
            const event = eventData as StreamEvent;

            switch (event.type) {
              case "CONTEXT_SEARCH":
                setCurrentStep("搜索知识库...");
                setProgressLog((prev) => [...prev, "🔍 搜索相关文档和最佳实践"]);
                break;

              case "CONTEXT_FOUND":
                const chunksFound = event.data.chunks_found || 0;
                const patterns = event.data.patterns || [];
                setCurrentStep(`找到 ${chunksFound} 个相关文档`);
                setProgressLog((prev) => [
                  ...prev,
                  `✓ 找到 ${chunksFound} 个相关文档`,
                  ...(patterns.length > 0 ? [`  检测到模式: ${patterns.join(", ")}`] : []),
                ]);
                if (event.data.sources) {
                  setSources(event.data.sources);
                }
                break;

              case "GENERATION_START":
                setCurrentStep("开始生成演讲稿...");
                setProgressLog((prev) => [...prev, "✨ 正在生成专业演讲稿"]);
                break;

              case "TOKEN":
                const token = event.data.token || "";
                setGeneratedText((prev) => prev + token);
                break;

              case "SECTION_COMPLETE":
                const section = event.data.section || "";
                setProgressLog((prev) => [...prev, `✓ 完成 ${section} 部分`]);
                break;

              case "COMPLETE":
                const scriptData = event.data.script;
                const wordCount = event.data.word_count || 0;
                const estimatedSeconds = event.data.estimated_seconds || 0;

                setCurrentStep("生成完成！正在保存...");
                setProgressLog((prev) => [
                  ...prev,
                  `✓ 生成完成 (${wordCount} 字, 预计 ${Math.round(estimatedSeconds / 60)} 分钟)`,
                ]);

                setIsComplete(true);
                setIsGenerating(false);

                // Generate script ID
                const scriptId = `script-${Date.now()}`;

                // Show success toast
                toast.success(`演讲稿生成成功！(${wordCount} 字)`);

                // Save draft to backend before opening editor
                (async () => {
                  try {
                    setCurrentStep("正在保存草稿...");
                    setProgressLog((prev) => [...prev, `💾 保存草稿到服务器...`]);

                    const saveResponse = await fetch(`/api/export/script/${scriptId}/draft`, {
                      method: "PUT",
                      headers: {
                        "Content-Type": "application/json",
                      },
                      body: JSON.stringify({
                        content: scriptData,
                        metadata: {
                          duration: duration,
                          word_count: wordCount,
                          rag_sources: [],
                          version: 0,
                        },
                      }),
                    });

                    if (!saveResponse.ok) {
                      throw new Error("保存草稿失败");
                    }

                    setCurrentStep("保存成功！");
                    setProgressLog((prev) => [...prev, `✓ 草稿已保存`]);
                    toast.success("草稿已保存到服务器");

                    // Auto-transition to editor after 1 second
                    setTimeout(() => {
                      onComplete(scriptId, scriptData, duration);
                    }, 1000);
                  } catch (saveError: any) {
                    console.error("Failed to save draft:", saveError);
                    setProgressLog((prev) => [...prev, `⚠️ 保存失败: ${saveError.message}`]);
                    toast.error("保存草稿失败，但仍可编辑", { duration: 5000 });

                    // Still open editor even if save fails (user can retry from editor)
                    setTimeout(() => {
                      onComplete(scriptId, scriptData, duration);
                    }, 2000);
                  }
                })();
                break;

              case "ERROR":
                throw new Error(event.data.error || "生成过程中出错");
            }
          } catch (parseError) {
            console.warn("Failed to parse event:", line, parseError);
          }
        }
      }
    } catch (error: any) {
      if (error.name === "AbortError") {
        toast.info("生成已取消");
        setCurrentStep("已取消");
      } else {
        console.error("Script generation error:", error);
        toast.error("生成失败: " + error.message);
        setCurrentStep("生成失败");
        setProgressLog((prev) => [...prev, `❌ 错误: ${error.message}`]);
      }
      setIsGenerating(false);
    }
  };

  const handleCancel = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsGenerating(false);
  };

  const handleClose = () => {
    if (isGenerating) {
      handleCancel();
    }
    onClose();
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 pointer-events-none">
        <div
          className="bg-white rounded-xl shadow-2xl w-full max-w-4xl max-h-[90vh] overflow-hidden pointer-events-auto flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-indigo-100 flex items-center justify-center">
                <Sparkles className="w-5 h-5 text-indigo-600" />
              </div>
              <div>
                <h2 className="text-xl font-bold text-gray-900">生成专业演讲稿</h2>
                <p className="text-sm text-gray-500">基于架构图生成高质量演讲内容</p>
              </div>
            </div>
            <button
              onClick={handleClose}
              disabled={isGenerating}
              className="p-2 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
            >
              <X className="w-5 h-5 text-gray-500" />
            </button>
          </div>

          {/* Content */}
          <div className="flex-1 overflow-y-auto p-6 space-y-6">
            {!isGenerating && !isComplete && (
              <>
                {/* Duration Selection */}
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
                    <Clock className="w-4 h-4" />
                    演讲时长
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(["30s", "2min", "5min"] as ScriptDuration[]).map((d) => (
                      <button
                        key={d}
                        onClick={() => setDuration(d)}
                        className={`p-4 rounded-lg border-2 transition-all ${
                          duration === d
                            ? "border-indigo-600 bg-indigo-50"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        <div className="text-lg font-bold text-gray-900">
                          {d === "30s" ? "30秒" : d === "2min" ? "2分钟" : "5分钟"}
                        </div>
                        <div className="text-xs text-gray-500 mt-1">
                          {d === "30s" ? "电梯演讲" : d === "2min" ? "快速介绍" : "深入讲解"}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Audience Selection */}
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
                    <Users className="w-4 h-4" />
                    目标受众
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(["executive", "technical", "mixed"] as ScriptAudience[]).map((a) => (
                      <button
                        key={a}
                        onClick={() => setAudience(a)}
                        className={`p-4 rounded-lg border-2 transition-all ${
                          audience === a
                            ? "border-indigo-600 bg-indigo-50"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        <div className="text-sm font-medium text-gray-900">
                          {a === "executive" ? "高管层" : a === "technical" ? "技术团队" : "混合受众"}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Tone Selection */}
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
                    <FileText className="w-4 h-4" />
                    语气风格
                  </label>
                  <div className="grid grid-cols-3 gap-3">
                    {(["professional", "casual", "technical"] as ScriptTone[]).map((t) => (
                      <button
                        key={t}
                        onClick={() => setTone(t)}
                        className={`p-4 rounded-lg border-2 transition-all ${
                          tone === t
                            ? "border-indigo-600 bg-indigo-50"
                            : "border-gray-200 hover:border-gray-300"
                        }`}
                      >
                        <div className="text-sm font-medium text-gray-900">
                          {t === "professional" ? "专业正式" : t === "casual" ? "轻松随意" : "技术深入"}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Focus Areas */}
                <div>
                  <label className="flex items-center gap-2 text-sm font-medium text-gray-700 mb-3">
                    <Target className="w-4 h-4" />
                    重点领域（可多选）
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {availableFocusAreas.map((area) => (
                      <button
                        key={area.id}
                        onClick={() => toggleFocusArea(area.id)}
                        className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                          focusAreas.includes(area.id)
                            ? "bg-indigo-600 text-white"
                            : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                        }`}
                      >
                        {area.label}
                      </button>
                    ))}
                  </div>
                </div>
              </>
            )}

            {/* Generation Progress */}
            {(isGenerating || isComplete) && (
              <div className="space-y-4">
                {/* Current Status */}
                <div className="flex items-center gap-3 p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                  {isGenerating ? (
                    <Loader2 className="w-5 h-5 text-indigo-600 animate-spin flex-shrink-0" />
                  ) : (
                    <Check className="w-5 h-5 text-green-600 flex-shrink-0" />
                  )}
                  <span className="text-sm font-medium text-gray-900">{currentStep}</span>
                </div>

                {/* Progress Log */}
                {progressLog.length > 0 && (
                  <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                    <div className="text-xs font-mono text-gray-600 space-y-1">
                      {progressLog.map((log, idx) => (
                        <div key={idx} className="leading-relaxed">
                          {log}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Generated Text (Typewriter Effect) */}
                {generatedText && (
                  <div
                    ref={textAreaRef}
                    className="bg-white rounded-lg p-6 border border-gray-200 max-h-96 overflow-y-auto"
                  >
                    <pre className="whitespace-pre-wrap font-sans text-sm text-gray-800 leading-relaxed">
                      {generatedText}
                      {isGenerating && <span className="animate-pulse">▊</span>}
                    </pre>
                  </div>
                )}

                {/* Sources */}
                {sources.length > 0 && (
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <div className="text-sm font-medium text-blue-900 mb-2">
                      📚 引用来源 ({sources.length})
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {sources.map((source, idx) => (
                        <span
                          key={idx}
                          className="px-3 py-1 bg-white rounded-full text-xs text-blue-700 border border-blue-300"
                        >
                          {source}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Completion Message */}
                {isComplete && (
                  <div className="bg-green-50 rounded-lg p-4 border border-green-200">
                    <div className="flex items-start gap-3">
                      <Check className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" />
                      <div>
                        <div className="text-sm font-medium text-green-900 mb-1">
                          生成完成！正在跳转到编辑器...
                        </div>
                        <div className="text-xs text-green-700">
                          您可以在编辑器中进一步润色和修改演讲稿
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Footer */}
          <div className="flex items-center justify-between p-6 border-t border-gray-200 bg-gray-50">
            <div className="text-sm text-gray-500">
              {!isGenerating && !isComplete && `当前架构: ${nodes.length} 个组件`}
            </div>
            <div className="flex gap-3">
              {!isGenerating && !isComplete && (
                <>
                  <button
                    onClick={handleClose}
                    className="px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    取消
                  </button>
                  <button
                    onClick={handleGenerate}
                    disabled={focusAreas.length === 0}
                    className="px-6 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                  >
                    <Sparkles className="w-4 h-4" />
                    开始生成
                  </button>
                </>
              )}
              {isGenerating && (
                <button
                  onClick={handleCancel}
                  className="px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  取消生成
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
