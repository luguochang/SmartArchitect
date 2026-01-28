"use client";

import { useState, useCallback, useRef } from "react";
import { X, Upload, Image as ImageIcon, Loader2, CheckCircle2, AlertCircle, Sparkles } from "lucide-react";
import { toast } from "sonner";
import {
  validateImageFile,
  formatFileSize,
  type ExcalidrawScene,
  type ReactFlowDiagram,
} from "@/lib/utils/imageConversion";

interface ImageConversionModalProps {
  isOpen: boolean;
  onClose: () => void;
  mode: "excalidraw" | "reactflow";
  onSuccess: (result: ExcalidrawScene | ReactFlowDiagram) => void;
  title?: string;
  description?: string;
}

export function ImageConversionModal({
  isOpen,
  onClose,
  mode,
  onSuccess,
  title,
  description,
}: ImageConversionModalProps) {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [converting, setConverting] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [progress, setProgress] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const defaultTitle = mode === "excalidraw"
    ? "Import Diagram to Excalidraw"
    : "Import Diagram to Canvas";

  const defaultDescription = mode === "excalidraw"
    ? "Upload an architecture diagram or flowchart image. AI will convert it to editable Excalidraw format."
    : "Upload an architecture diagram. AI will identify components and create an editable React Flow diagram.";

  // 处理文件选择
  const handleFileChange = useCallback((selectedFile: File | null) => {
    if (!selectedFile) return;

    const validation = validateImageFile(selectedFile);
    if (!validation.valid) {
      toast.error(validation.error);
      return;
    }

    setFile(selectedFile);

    // 创建预览
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreviewUrl(e.target?.result as string);
    };
    reader.readAsDataURL(selectedFile);
  }, []);

  // 拖拽处理
  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  }, [handleFileChange]);

  // 转换图片
  const handleConvert = useCallback(async () => {
    if (!file) return;

    setConverting(true);
    setProgress("Uploading image...");

    try {
      // 动态导入转换函数
      const { convertImageToExcalidraw, convertImageToReactFlow } = await import(
        "@/lib/utils/imageConversion"
      );

      setProgress("AI is analyzing the diagram...");

      let result: ExcalidrawScene | ReactFlowDiagram;

      if (mode === "excalidraw") {
        result = await convertImageToExcalidraw(file);
        setProgress("Generating Excalidraw scene...");
      } else {
        result = await convertImageToReactFlow(file);
        setProgress("Creating React Flow nodes...");
      }

      setProgress("Done!");
      toast.success(`Successfully converted to ${mode === "excalidraw" ? "Excalidraw" : "React Flow"} format!`);

      // 通知父组件
      onSuccess(result);

      // 延迟关闭以显示成功状态
      setTimeout(() => {
        onClose();
        resetState();
      }, 1000);
    } catch (error: any) {
      console.error("Conversion failed:", error);
      toast.error(error.message || "Failed to convert image. Please try again.");
      setProgress("");
    } finally {
      setConverting(false);
    }
  }, [file, mode, onSuccess, onClose]);

  // 重置状态
  const resetState = useCallback(() => {
    setFile(null);
    setPreviewUrl(null);
    setConverting(false);
    setProgress("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, []);

  // 关闭Modal
  const handleClose = useCallback(() => {
    if (converting) return;
    onClose();
    resetState();
  }, [converting, onClose, resetState]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="relative w-full max-w-2xl mx-4 bg-white dark:bg-slate-900 rounded-xl shadow-2xl max-h-[90vh] overflow-auto">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-900 dark:text-white flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-indigo-600" />
              {title || defaultTitle}
            </h2>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              {description || defaultDescription}
            </p>
          </div>
          <button
            onClick={handleClose}
            disabled={converting}
            className="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <X className="h-5 w-5 text-slate-600 dark:text-slate-400" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Upload Area */}
          {!file && (
            <div
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
              className={`
                relative border-2 border-dashed rounded-xl p-12 text-center transition-all
                ${dragActive
                  ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20"
                  : "border-slate-300 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-600"
                }
              `}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/jpg,image/webp"
                onChange={(e) => handleFileChange(e.target.files?.[0] || null)}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
              />

              <div className="flex flex-col items-center gap-3">
                <div className="p-4 rounded-full bg-indigo-100 dark:bg-indigo-900/30">
                  <Upload className="h-8 w-8 text-indigo-600 dark:text-indigo-400" />
                </div>
                <div>
                  <p className="text-base font-medium text-slate-900 dark:text-white">
                    Drop your image here, or click to browse
                  </p>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
                    Supports PNG, JPG, WebP (max 10MB)
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Preview */}
          {file && previewUrl && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <ImageIcon className="h-5 w-5 text-slate-600 dark:text-slate-400" />
                  <div>
                    <p className="text-sm font-medium text-slate-900 dark:text-white">
                      {file.name}
                    </p>
                    <p className="text-xs text-slate-600 dark:text-slate-400">
                      {formatFileSize(file.size)}
                    </p>
                  </div>
                </div>
                {!converting && (
                  <button
                    onClick={resetState}
                    className="text-sm text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
                  >
                    Change
                  </button>
                )}
              </div>

              <div className="relative rounded-lg overflow-hidden border border-slate-200 dark:border-slate-700">
                <img
                  src={previewUrl}
                  alt="Preview"
                  className="w-full h-auto max-h-96 object-contain bg-slate-50 dark:bg-slate-800"
                />
              </div>

              {/* Progress */}
              {converting && progress && (
                <div className="flex items-center gap-3 p-4 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg">
                  {progress === "Done!" ? (
                    <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400 flex-shrink-0" />
                  ) : (
                    <Loader2 className="h-5 w-5 text-indigo-600 dark:text-indigo-400 animate-spin flex-shrink-0" />
                  )}
                  <p className="text-sm font-medium text-indigo-900 dark:text-indigo-100">
                    {progress}
                  </p>
                </div>
              )}

              {/* Info */}
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <div className="flex gap-2">
                  <AlertCircle className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                  <div className="text-xs text-blue-700 dark:text-blue-300">
                    <p className="font-medium mb-1">AI Processing Time</p>
                    <p>
                      Conversion may take 30-90 seconds depending on image complexity and AI model response time.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="sticky bottom-0 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700 px-6 py-4 flex justify-end gap-3">
          <button
            onClick={handleClose}
            disabled={converting}
            className="px-4 py-2 text-sm font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConvert}
            disabled={!file || converting}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {converting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Converting...
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" />
                Convert with AI
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
