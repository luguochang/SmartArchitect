"use client";

import { useState, useCallback } from "react";
import { Upload, Loader2, AlertCircle, X } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";
import {
  validateImageFile,
  convertImageToExcalidrawStreaming,
  type ExcalidrawScene,
} from "@/lib/utils/imageConversion";

export function ExcalidrawUploader() {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<string>("");
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);
  const [elementCount, setElementCount] = useState(0);
  const [totalElements, setTotalElements] = useState(0);

  const { modelConfig, setExcalidrawScene } = useArchitectStore();

  const handleFile = useCallback(
    async (file: File) => {
      const validation = validateImageFile(file);
      if (!validation.valid) {
        toast.error(validation.error);
        return;
      }

      setUploading(true);
      setError(null);
      setProgress("Uploading image...");
      setElementCount(0);
      setTotalElements(0);

      try {
        const elements: any[] = [];
        let appState: any = { viewBackgroundColor: "#ffffff" };
        let sawCompleteEvent = false;

        for await (const chunk of convertImageToExcalidrawStreaming(
          file,
          (msg) => setProgress(msg),
          {
            provider: modelConfig.provider,
            apiKey: modelConfig.apiKey,
            baseUrl: modelConfig.baseUrl,
            modelName: modelConfig.modelName,
          }
        )) {
          if (chunk.type === "start_streaming") {
            setTotalElements(chunk.total || 0);
            appState = chunk.appState || { viewBackgroundColor: "#ffffff" };
            setProgress(`Streaming ${chunk.total || 0} elements...`);
            continue;
          }

          if (chunk.type === "element" && chunk.element) {
            elements.push(chunk.element);
            setElementCount(elements.length);

            const partialScene: ExcalidrawScene = {
              elements: [...elements],
              appState: appState || { viewBackgroundColor: "#ffffff" },
              files: {},
            };
            setExcalidrawScene(partialScene);
            continue;
          }

          if (chunk.type === "complete") {
            sawCompleteEvent = true;
            setProgress("Done!");
            continue;
          }

          if (chunk.type === "error") {
            const errorMsg = chunk.message || "Stream generation failed";
            const errorDetails = chunk.details
              ? `\n\nDetails:\n${JSON.stringify(chunk.details, null, 2)}`
              : "";
            throw new Error(errorMsg + errorDetails);
          }
        }

        if (!sawCompleteEvent && elements.length === 0) {
          throw new Error("Stream ended before any Excalidraw elements were produced.");
        }

        const finalScene: ExcalidrawScene = {
          elements: [...elements],
          appState: appState || { viewBackgroundColor: "#ffffff" },
          files: {},
        };
        setExcalidrawScene(finalScene);

        if (!sawCompleteEvent) {
          setProgress(`Completed with ${elements.length} elements`);
        }

        toast.success(`Successfully streamed ${elements.length} elements to Excalidraw!`);
      } catch (err: any) {
        console.error("Upload error:", err);
        const errorMessage = err?.message || "Recognition failed";
        const errorStack = err?.stack ? `\n\nStack:\n${err.stack}` : "";
        const fullError = errorMessage + errorStack;
        setError(fullError);
        toast.error("Recognition failed, check details");
      } finally {
        setUploading(false);
        setTimeout(() => {
          setProgress("");
          setElementCount(0);
          setTotalElements(0);
        }, 3000);
      }
    },
    [modelConfig, setExcalidrawScene]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      const files = e.dataTransfer.files;
      if (files && files[0]) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files[0]) {
        handleFile(files[0]);
      }
      e.target.value = "";
    },
    [handleFile]
  );

  return (
    <div className="space-y-4">
      <div className="rounded-lg border border-purple-200 bg-purple-50 p-3 text-sm dark:border-purple-900 dark:bg-purple-950">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-purple-600 dark:text-purple-400" />
          <div>
            <p className="font-medium text-purple-900 dark:text-purple-100">
              Current AI Provider: {modelConfig.provider || "custom"}
            </p>
            <p className="mt-1 text-xs text-purple-700 dark:text-purple-300">
              Streaming mode enabled - elements appear one by one
            </p>
          </div>
        </div>
      </div>

      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          relative rounded-xl border-2 border-dashed p-8 text-center transition-all
          ${
            dragActive
              ? "border-purple-500 bg-purple-50 dark:bg-purple-950"
              : "border-slate-300 bg-white dark:border-slate-600 dark:bg-slate-800"
          }
          ${uploading ? "pointer-events-none opacity-60" : "cursor-pointer hover:border-purple-400"}
        `}
      >
        <input
          type="file"
          accept="image/png,image/jpeg,image/jpg,image/webp"
          onChange={handleFileInput}
          className="hidden"
          id="excalidraw-upload-input"
          disabled={uploading}
        />

        <label htmlFor="excalidraw-upload-input" className="cursor-pointer">
          {uploading ? (
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-12 w-12 animate-spin text-purple-600" />
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                {progress || "Streaming elements..."}
              </p>
              {totalElements > 0 && (
                <div className="w-full max-w-xs">
                  <div className="mb-1 flex justify-between text-xs text-slate-600 dark:text-slate-400">
                    <span>Progress</span>
                    <span>
                      {elementCount} / {totalElements}
                    </span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-200 dark:bg-slate-700">
                    <div
                      className="h-full bg-purple-600 transition-all duration-300"
                      style={{ width: `${(elementCount / totalElements) * 100}%` }}
                    />
                  </div>
                </div>
              )}
              <p className="text-xs text-slate-500">
                Using {modelConfig.provider || "custom"} model
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <Upload className="h-12 w-12 text-slate-400" />
              <div>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  Upload Diagram Image
                </p>
                <p className="mt-1 text-xs text-slate-500">Or drag and drop file here</p>
              </div>
              <div className="mt-2 rounded-lg bg-slate-100 px-3 py-1 text-xs text-slate-600 dark:bg-slate-700 dark:text-slate-400">
                Supports PNG, JPG, WEBP, max 10MB
              </div>
            </div>
          )}
        </label>
      </div>

      {error && (
        <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950">
          <AlertCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-red-600 dark:text-red-400" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-red-900 dark:text-red-100">Recognition Failed</p>
            <pre className="mt-2 max-h-60 overflow-y-auto whitespace-pre-wrap break-words rounded bg-red-100 p-2 font-mono text-xs text-red-700 dark:bg-red-900/30 dark:text-red-300">
{error}
            </pre>
          </div>
          <button
            onClick={() => setError(null)}
            className="flex-shrink-0 text-red-600 hover:text-red-800 dark:text-red-400"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      <div className="rounded-lg bg-purple-50 p-4 dark:bg-purple-950">
        <p className="text-xs font-medium text-purple-900 dark:text-purple-100">Streaming Mode</p>
        <ul className="mt-2 space-y-1 text-xs text-purple-700 dark:text-purple-300">
          <li>- Elements appear one by one in real-time</li>
          <li>- Watch your diagram come to life</li>
          <li>- Works with architecture diagrams and flowcharts</li>
        </ul>
      </div>
    </div>
  );
}
