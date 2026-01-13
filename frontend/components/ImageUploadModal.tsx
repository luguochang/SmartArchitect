"use client";

import { useState, useCallback } from "react";
import { X, Sparkles, ImageIcon } from "lucide-react";
import { ImageUpload } from "./ImageUpload";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";

interface ImageUploadModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ImageUploadModal({ isOpen, onClose }: ImageUploadModalProps) {
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
      // 分析成功后关闭模态框
      onClose();
    } catch (error) {
      // 错误已在 store 中处理
      toast.error("Failed to analyze image. Please try again.");
    }
  }, [analyzeImage, modelConfig.apiKey, onClose]);

  const handleClose = useCallback(() => {
    if (!isAnalyzing) {
      clearImage();
      onClose();
    }
  }, [clearImage, isAnalyzing, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-3xl rounded-lg bg-white shadow-2xl dark:bg-slate-900 m-4">
        {/* 标题栏 */}
        <div className="flex items-center justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <ImageIcon className="h-5 w-5 text-indigo-600" />
            <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
              Upload Architecture Diagram
            </h2>
          </div>
          <button
            onClick={handleClose}
            disabled={isAnalyzing}
            className="rounded-lg p-1 hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* 内容区域 */}
        <div className="p-6">
          <ImageUpload
            onImageSelect={handleImageSelect}
            onClear={clearImage}
            previewUrl={imagePreviewUrl}
            isAnalyzing={isAnalyzing}
            error={analysisError}
          />

          {/* 提示信息 */}
          {!uploadedImage && (
            <div className="mt-4 rounded-lg bg-indigo-50 p-4 dark:bg-indigo-900/20">
              <div className="flex gap-3">
                <Sparkles className="h-5 w-5 text-indigo-600 dark:text-indigo-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-indigo-900 dark:text-indigo-100">
                    AI-Powered Architecture Analysis
                  </p>
                  <p className="text-sm text-indigo-700 dark:text-indigo-300 mt-1">
                    Upload a screenshot or photo of your architecture diagram. Our AI will:
                  </p>
                  <ul className="text-sm text-indigo-700 dark:text-indigo-300 mt-2 space-y-1 ml-4 list-disc">
                    <li>Identify all components (APIs, services, databases, etc.)</li>
                    <li>Extract connections and relationships</li>
                    <li>Generate editable Mermaid code</li>
                    <li>Analyze potential bottlenecks and suggest optimizations</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* 模型信息 */}
          {uploadedImage && !isAnalyzing && (
            <div className="mt-4 text-sm text-slate-600 dark:text-slate-400">
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
          )}
        </div>

        {/* 底部按钮 */}
        <div className="flex justify-end gap-3 border-t border-slate-200 px-6 py-4 dark:border-slate-800">
          <button
            onClick={handleClose}
            disabled={isAnalyzing}
            className="rounded-lg px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800 disabled:opacity-50"
          >
            Cancel
          </button>
          {uploadedImage && (
            <button
              onClick={handleAnalyze}
              disabled={isAnalyzing || !modelConfig.apiKey}
              className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Sparkles className="h-4 w-4" />
              {isAnalyzing ? "Analyzing..." : "Analyze with AI"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
