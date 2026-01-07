"use client";

import { useState, useCallback, useRef } from "react";
import { Upload, X, Loader2, AlertCircle } from "lucide-react";
import { toast } from "sonner";

interface ImageUploadProps {
  onImageSelect: (file: File) => void;
  onClear: () => void;
  previewUrl?: string | null;
  isAnalyzing?: boolean;
  error?: string | null;
}

export function ImageUpload({
  onImageSelect,
  onClear,
  previewUrl,
  isAnalyzing = false,
  error = null,
}: ImageUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // 支持的文件格式
  const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
  const MAX_SIZE = 10 * 1024 * 1024; // 10MB

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return "Unsupported file format. Please upload PNG, JPG, or WEBP images.";
    }
    if (file.size > MAX_SIZE) {
      return "File too large. Maximum size is 10MB.";
    }
    return null;
  };

  const handleFile = useCallback(
    (file: File) => {
      const error = validateFile(file);
      if (error) {
        toast.error(error);
        return;
      }

      onImageSelect(file);
      toast.success("Image uploaded successfully!");
    },
    [onImageSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);

      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  const handleClick = useCallback(() => {
    fileInputRef.current?.click();
  }, []);

  const handleClear = useCallback(() => {
    onClear();
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [onClear]);

  return (
    <div className="space-y-4">
      {!previewUrl ? (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={handleClick}
          className={`
            relative flex min-h-[300px] cursor-pointer flex-col items-center justify-center
            rounded-lg border-2 border-dashed transition-all
            ${
              isDragging
                ? "border-indigo-600 bg-indigo-50 dark:bg-indigo-900/20"
                : "border-slate-300 bg-slate-50 hover:border-indigo-500 hover:bg-indigo-50/50 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-indigo-600"
            }
          `}
        >
          <Upload className={`h-12 w-12 mb-4 ${
            isDragging ? "text-indigo-600" : "text-slate-400"
          }`} />

          <p className="text-center text-lg font-medium text-slate-700 dark:text-slate-300">
            {isDragging ? "Drop your image here" : "Upload Architecture Diagram"}
          </p>

          <p className="mt-2 text-center text-sm text-slate-500 dark:text-slate-400">
            Drag & drop or click to browse
          </p>

          <p className="mt-4 text-xs text-slate-400 dark:text-slate-500">
            Supported formats: PNG, JPG, WEBP • Max size: 10MB
          </p>

          <input
            ref={fileInputRef}
            type="file"
            accept={ALLOWED_TYPES.join(",")}
            onChange={handleFileInputChange}
            className="hidden"
          />
        </div>
      ) : (
        <div className="relative">
          {/* 图片预览 */}
          <div className="relative overflow-hidden rounded-lg border-2 border-slate-200 dark:border-slate-700">
            <img
              src={previewUrl}
              alt="Architecture diagram preview"
              className="max-h-[400px] w-full object-contain bg-slate-50 dark:bg-slate-800"
            />

            {/* 分析中的遮罩 */}
            {isAnalyzing && (
              <div className="absolute inset-0 flex items-center justify-center bg-black/50 backdrop-blur-sm">
                <div className="text-center">
                  <Loader2 className="h-12 w-12 animate-spin text-white mx-auto mb-4" />
                  <p className="text-white font-medium">Analyzing with AI...</p>
                  <p className="text-white/80 text-sm mt-1">This may take a few seconds</p>
                </div>
              </div>
            )}

            {/* 清除按钮 */}
            {!isAnalyzing && (
              <button
                onClick={handleClear}
                className="absolute top-2 right-2 rounded-full bg-red-600 p-2 text-white shadow-lg hover:bg-red-700 transition-colors"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>

          {/* 错误提示 */}
          {error && (
            <div className="mt-4 flex items-start gap-2 rounded-lg border border-red-200 bg-red-50 p-3 dark:border-red-800 dark:bg-red-900/20">
              <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0" />
              <div>
                <p className="text-sm font-medium text-red-900 dark:text-red-100">
                  Analysis Failed
                </p>
                <p className="text-sm text-red-700 dark:text-red-300 mt-1">
                  {error}
                </p>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
