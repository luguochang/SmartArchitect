"use client";

import { useCallback } from "react";
import { Sparkles, Loader2 } from "lucide-react";
import { ImageUpload } from "./ImageUpload";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";

export function ImageUploader() {
  const {
    uploadedImage,
    imagePreviewUrl,
    isAnalyzing,
    analysisError,
    uploadImage,
    clearImage,
    analyzeImage,
    modelConfig,
  } = useArchitectStore();

  const handleImageSelect = useCallback(
    (file: File) => {
      uploadImage(file);
    },
    [uploadImage]
  );

  const handleAnalyze = useCallback(async () => {
    // 检查 API Key 配置
    if (!modelConfig.apiKey) {
      toast.error("API key not configured. Please configure in Settings first.");
      return;
    }

    try {
      await analyzeImage();
      toast.success("Architecture diagram analyzed successfully!");
      // 分析成功后清除图片
      setTimeout(() => clearImage(), 1000);
    } catch (error) {
      // 错误已在 store 中处理
      toast.error("Failed to analyze image. Please try again.");
    }
  }, [analyzeImage, modelConfig.apiKey, clearImage]);

  return (
    <div className="space-y-4">
      {/* Image Upload Component */}
      <ImageUpload
        onImageSelect={handleImageSelect}
        onClear={clearImage}
        previewUrl={imagePreviewUrl}
        isAnalyzing={isAnalyzing}
        error={analysisError}
      />

      {/* 提示信息 */}
      {!uploadedImage && (
        <div className="rounded-lg bg-indigo-50 p-3 dark:bg-indigo-900/20">
          <div className="flex gap-2">
            <Sparkles className="h-4 w-4 text-indigo-600 dark:text-indigo-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-medium text-indigo-900 dark:text-indigo-100">
                AI-Powered Architecture Analysis
              </p>
              <p className="text-xs text-indigo-700 dark:text-indigo-300 mt-1">
                Upload a screenshot or photo of your architecture diagram. The AI will identify components, extract connections, and generate editable Mermaid code.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* 模型信息和分析按钮 */}
      {uploadedImage && (
        <div className="space-y-3">
          <div className="text-xs text-slate-600 dark:text-slate-400">
            <p>
              Using:{" "}
              <span className="font-medium text-slate-900 dark:text-white">
                {modelConfig.provider === "gemini" && "Google Gemini"}
                {modelConfig.provider === "openai" && "OpenAI GPT-4 Vision"}
                {modelConfig.provider === "claude" && "Anthropic Claude"}
                {modelConfig.provider === "siliconflow" && "SiliconFlow"}
                {modelConfig.provider === "custom" && "Custom Model"}
              </span>
            </p>
          </div>

          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing || !modelConfig.apiKey}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isAnalyzing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Analyzing...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Analyze with AI
              </>
            )}
          </button>
        </div>
      )}

      {/* 错误信息 */}
      {analysisError && (
        <div className="rounded-lg bg-red-50 p-3 dark:bg-red-900/20">
          <p className="text-xs text-red-700 dark:text-red-300">{analysisError}</p>
        </div>
      )}
    </div>
  );
}
