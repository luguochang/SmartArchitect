"use client";

import { useState, useCallback } from "react";
import { Upload, Loader2, CheckCircle2, AlertCircle, X } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";

interface UploadResult {
  nodes: any[];
  edges: any[];
  warnings?: Array<{ node_id: string; message: string }>;
  flowchart_analysis?: {
    total_nodes: number;
    total_branches: number;
    complexity: string;
    flowchart_type: string;
  };
}

export function FlowchartUploader() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const { modelConfig, setNodes, setEdges, canvasMode, setCanvasMode } = useArchitectStore();

  const handleFile = useCallback(
    async (file: File) => {
      // 验证文件类型
      const validTypes = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
      if (!validTypes.includes(file.type)) {
        toast.error("仅支持 PNG、JPG、WEBP 格式");
        return;
      }

      // 验证文件大小（10MB）
      if (file.size > 10 * 1024 * 1024) {
        toast.error("文件过大，最大支持10MB");
        return;
      }

      setUploading(true);
      setError(null);
      setResult(null);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("provider", modelConfig.provider || "gemini");
      formData.append("preserve_layout", "true");
      formData.append("fast_mode", "true");  // 启用快速模式
      if (modelConfig.apiKey) {
        formData.append("api_key", modelConfig.apiKey);
      }
      if (modelConfig.baseUrl) {
        formData.append("base_url", modelConfig.baseUrl);
      }
      if (modelConfig.modelName) {
        formData.append("model_name", modelConfig.modelName);
      }

      try {
        // 显示进度提示
        toast.info("正在识别流程图...", { duration: 60000 });

        // 模拟进度提示（每10秒更新一次）
        const progressToasts = [
          setTimeout(() => toast.info("🔍 正在分析图片结构..."), 10000),
          setTimeout(() => toast.info("📊 正在识别节点和连线..."), 20000),
          setTimeout(() => toast.info("⚙️ 正在生成流程图数据..."), 30000),
          setTimeout(() => toast.info("✨ 即将完成..."), 40000),
        ];

        const response = await fetch("http://localhost:8000/api/vision/analyze-flowchart", {
          method: "POST",
          body: formData,
        });

        // 清除所有进度提示
        progressToasts.forEach(clearTimeout);

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "识别失败");
        }

        const data: UploadResult = await response.json();

        console.log("[FlowchartUploader] Received data:", {
          nodes: data.nodes.length,
          edges: data.edges.length,
          sampleNode: data.nodes[0],
        });

        setResult(data);

        // 检查当前画布模式
        if (canvasMode !== "reactflow") {
          console.log("[FlowchartUploader] Switching to ReactFlow canvas mode");
          setCanvasMode("reactflow");
          toast.info("已自动切换到 React Flow 画布模式");

          // 等待模式切换完成
          await new Promise(resolve => setTimeout(resolve, 200));
        }

        // 应用到画布
        console.log("[FlowchartUploader] Calling setNodes and setEdges...");
        setNodes(data.nodes);
        setEdges(data.edges);

        // 延迟fitView以确保节点已渲染
        setTimeout(() => {
          console.log("[FlowchartUploader] Nodes should be visible now");
          // 触发一个事件通知画布刷新
          window.dispatchEvent(new CustomEvent('flowchart-imported'));
        }, 100);

        // 成功提示
        toast.success(
          `识别成功！共 ${data.nodes.length} 个节点，${data.edges.length} 条连线`
        );

        // 显示警告（如果有）
        if (data.warnings && data.warnings.length > 0) {
          toast.warning(`注意：${data.warnings.length} 个节点的形状被映射`);
        }
      } catch (err: any) {
        console.error("Upload error:", err);
        setError(err.message || "识别失败");
        toast.error(err.message || "识别失败，请重试");
      } finally {
        setUploading(false);
      }
    },
    [modelConfig, setNodes, setEdges, canvasMode, setCanvasMode]
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
    },
    [handleFile]
  );

  return (
    <div className="space-y-4">
      {/* Provider 状态提示 */}
      <div className="rounded-lg p-3 text-sm bg-blue-50 border border-blue-200 dark:bg-blue-950 dark:border-blue-900">
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-blue-600 dark:text-blue-400" />
          <div>
            <p className="font-medium text-blue-900 dark:text-blue-100">
              当前 AI Provider: {modelConfig.provider || "Gemini"}
            </p>
            <p className="mt-1 text-xs text-blue-700 dark:text-blue-300">
              {modelConfig.provider === "siliconflow" && modelConfig.modelName
                ? `✓ 使用 ${modelConfig.modelName} 进行识别`
                : "✓ 支持流程图截图识别"}
            </p>
          </div>
        </div>
      </div>

      {/* 上传区域 */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          relative rounded-xl border-2 border-dashed p-8 text-center transition-all
          ${
            dragActive
              ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950"
              : "border-slate-300 bg-white dark:border-slate-600 dark:bg-slate-800"
          }
          ${uploading ? "pointer-events-none opacity-60" : "cursor-pointer hover:border-indigo-400"}
        `}
      >
        <input
          type="file"
          accept="image/png,image/jpeg,image/jpg,image/webp"
          onChange={handleFileInput}
          className="hidden"
          id="flowchart-upload-input"
          disabled={uploading}
        />

        <label htmlFor="flowchart-upload-input" className="cursor-pointer">
          {uploading ? (
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-12 w-12 animate-spin text-indigo-600" />
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                正在识别流程图...
              </p>
              <p className="text-xs text-slate-500">
                使用 {modelConfig.provider || "Gemini"} 模型分析中
              </p>
              <p className="text-xs text-amber-600 dark:text-amber-400 font-medium">
                预计需要 40-60 秒，请耐心等待
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <Upload className="h-12 w-12 text-slate-400" />
              <div>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  上传流程图截图
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  或拖拽文件到此处
                </p>
              </div>
              <div className="mt-2 rounded-lg bg-slate-100 px-3 py-1 text-xs text-slate-600 dark:bg-slate-700 dark:text-slate-400">
                支持 PNG、JPG、WEBP，最大 10MB
              </div>
            </div>
          )}
        </label>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950">
          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-900 dark:text-red-100">
              识别失败
            </p>
            <p className="mt-1 text-xs text-red-700 dark:text-red-300">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800 dark:text-red-400"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* 成功结果 */}
      {result && (
        <div className="space-y-3 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900 dark:bg-green-950">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
            <div className="flex-1">
              <p className="text-sm font-medium text-green-900 dark:text-green-100">
                识别成功！
              </p>
              <p className="mt-1 text-xs text-green-700 dark:text-green-300">
                {result.nodes.length} 个节点，{result.edges.length} 条连线
              </p>
            </div>
            <button
              onClick={() => setResult(null)}
              className="text-green-600 hover:text-green-800 dark:text-green-400"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* 流程图分析 */}
          {result.flowchart_analysis && (
            <div className="mt-3 rounded-lg bg-white p-3 dark:bg-slate-800">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-500">类型：</span>
                  <span className="ml-1 font-medium text-slate-900 dark:text-white">
                    {result.flowchart_analysis.flowchart_type}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">复杂度：</span>
                  <span className="ml-1 font-medium text-slate-900 dark:text-white">
                    {result.flowchart_analysis.complexity}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">分支数：</span>
                  <span className="ml-1 font-medium text-slate-900 dark:text-white">
                    {result.flowchart_analysis.total_branches}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* 警告信息 */}
          {result.warnings && result.warnings.length > 0 && (
            <div className="mt-3 space-y-1">
              <p className="text-xs font-medium text-amber-900 dark:text-amber-100">
                识别警告：
              </p>
              {result.warnings.map((warning, idx) => (
                <p key={idx} className="text-xs text-amber-700 dark:text-amber-300">
                  • {warning.message}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 使用提示 */}
      <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-950">
        <p className="text-xs font-medium text-blue-900 dark:text-blue-100">
          💡 支持的流程图工具
        </p>
        <ul className="mt-2 space-y-1 text-xs text-blue-700 dark:text-blue-300">
          <li>• Visio 导出的流程图</li>
          <li>• ProcessOn 截图</li>
          <li>• Draw.io / diagrams.net</li>
          <li>• 白板手绘流程图照片</li>
          <li>• 其他标准流程图工具</li>
        </ul>
      </div>
    </div>
  );
}
