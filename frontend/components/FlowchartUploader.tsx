"use client";

import { useState, useCallback } from "react";
import { Upload, Loader2, CheckCircle2, AlertCircle, X } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";
import { fileToBase64 } from "@/lib/utils/imageConversion";
import { API_BASE_URL } from "@/lib/api-config";
import { MarkerType } from "reactflow";
import { useFlowchartStyleStore } from "@/lib/stores/flowchartStyleStore";


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

  const { modelConfig, setNodes, setEdges, canvasMode, setCanvasMode } = useArchitectStore((state) => ({
    modelConfig: state.modelConfig,
    setNodes: state.setNodes,
    setEdges: state.setEdges,
    canvasMode: state.canvasMode,
    setCanvasMode: state.setCanvasMode,
    chatHistory: state.chatHistory,
  }));

  // Helper to add messages to chat panel
  const addChatMessage = useCallback((role: "user" | "assistant", content: string) => {
    useArchitectStore.setState((state) => ({
      chatHistory: [...state.chatHistory, { role, content }]
    }));
  }, []);

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

      // Add user message to chat
      addChatMessage("user", `📤 上传流程图: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`);

      try {
        // 🔥 Convert file to base64 (same as Excalidraw)
        const base64Image = await fileToBase64(file);

        // 🔥 Use JSON body instead of FormData (same as Excalidraw)
        const requestBody = {
          image_data: base64Image,
          provider: modelConfig.provider || "gemini",
          preserve_layout: true,
          fast_mode: true,
          api_key: modelConfig.apiKey,
          base_url: modelConfig.baseUrl,
          model_name: modelConfig.modelName,
        };

        // 使用流式endpoint v2
        const response = await fetch(`${API_BASE_URL}/api/vision/analyze-flowchart-stream-v2`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(requestBody),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          const errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
          const errorDetails = JSON.stringify(errorData, null, 2);
          throw new Error(`${errorMessage}\n\n详细信息:\n${errorDetails}`);
        }

        if (!response.body) {
          throw new Error("Response body is null");
        }

        // 解析SSE流
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";
        let analysisResult: UploadResult | null = null;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || ""; // 保留最后一个不完整的行

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));

                if (data.type === "init" || data.type === "progress") {
                  // Add progress messages to chat panel
                  addChatMessage("assistant", data.message);
                } else if (data.type === "complete") {
                  // Final completion message
                  addChatMessage("assistant", data.message);
                  // Store the result
                  if (data.result) {
                    analysisResult = data.result;
                  }
                } else if (data.type === "error") {
                  const errorMsg = data.message || "Stream generation failed";
                  addChatMessage("assistant", `❌ ${errorMsg}`);
                  throw new Error(errorMsg);
                }
              } catch (e) {
                console.error("Failed to parse SSE data:", e, line);
              }
            }
          }
        }

        // Process result
        if (analysisResult) {
          console.log("[FlowchartUploader] Received data:", {
            nodes: analysisResult.nodes.length,
            edges: analysisResult.edges.length,
            sampleNode: analysisResult.nodes[0],
          });

          setResult(analysisResult);

          // 检查当前画布模式
          if (canvasMode !== "reactflow") {
            console.log("[FlowchartUploader] Switching to ReactFlow canvas mode");
            setCanvasMode("reactflow");
            addChatMessage("assistant", "🔄 已自动切换到 React Flow 画布模式");

            // 等待模式切换完成
            await new Promise(resolve => setTimeout(resolve, 200));
          }

          // 🔧 处理节点和边的样式（保留原始位置）
          console.log("[FlowchartUploader] Processing nodes and edges...");
          console.log("[FlowchartUploader] Raw nodes from AI:", analysisResult.nodes.slice(0, 3));

          const currentStyle = useFlowchartStyleStore.getState().currentPresentationStyle;
          const edgeType = useFlowchartStyleStore.getState().edgeType;

          // 🔥 检测节点重叠问题
          const checkOverlap = (nodes: any[]) => {
            let overlapCount = 0;
            const nodeWidth = 200; // 节点宽度
            const nodeHeight = 80; // 节点高度
            const minSpacing = 50; // 最小间距

            for (let i = 0; i < nodes.length; i++) {
              for (let j = i + 1; j < nodes.length; j++) {
                const dx = Math.abs(nodes[i].position.x - nodes[j].position.x);
                const dy = Math.abs(nodes[i].position.y - nodes[j].position.y);

                // 如果两个节点距离小于节点大小+最小间距，认为重叠
                if (dx < (nodeWidth + minSpacing) && dy < (nodeHeight + minSpacing)) {
                  overlapCount++;
                  console.log(`[Overlap] Node ${nodes[i].id} and ${nodes[j].id}: dx=${dx.toFixed(0)}, dy=${dy.toFixed(0)}`);
                }
              }
            }

            const totalPairs = nodes.length * (nodes.length - 1) / 2;
            const overlapRatio = totalPairs > 0 ? overlapCount / totalPairs : 0;
            console.log(`[FlowchartUploader] Overlap detection: ${overlapCount}/${totalPairs} pairs overlap, ratio: ${(overlapRatio * 100).toFixed(1)}%`);

            return overlapRatio > 0.15; // 如果超过15%的节点对重叠，认为需要重新布局
          };

          const hasOverlap = checkOverlap(analysisResult.nodes);

          if (hasOverlap) {
            console.warn("[FlowchartUploader] ⚠️ Detected significant overlap! Applying auto-layout...");
            addChatMessage("assistant", "⚠️ 检测到节点重叠，自动应用布局优化...");
          }

          // 1. 只添加样式，保留 AI 识别的原始位置
          const styledNodes = analysisResult.nodes.map((node: any) => {
            // 🔥 修复：确保 type 是有效的节点类型，shape 才是形状
            const validTypes = ['default', 'database', 'api', 'service', 'gateway', 'cache', 'queue', 'storage', 'client', 'frame', 'layerFrame'];
            const nodeType = validTypes.includes(node.type) ? node.type : 'default';

            return {
              ...node,
              type: nodeType,
              position: node.position,
              data: {
                ...node.data,
                shape: node.data?.shape || (node.type === 'task' ? 'task' : undefined),
                color: node.data?.color || (
                  node.data?.shape === "start-event" ? "#16a34a" :
                  node.data?.shape === "end-event" ? "#dc2626" :
                  node.data?.shape === "task" || node.type === "task" ? "#2563eb" :
                  undefined
                ),
              },
            };
          });

          // 2. 修复边的样式（改为实线，不使用 animated）
          const styledEdges = analysisResult.edges.map((edge: any) => ({
            ...edge,
            type: edgeType, // 使用当前样式的边类型
            animated: false, // 🔥 关键修复：不使用动画（虚线）
            markerEnd: {
              type: MarkerType.ArrowClosed,
              width: currentStyle.edge.markerSize,
              height: currentStyle.edge.markerSize,
              color: currentStyle.edge.strokeColor,
            },
            style: {
              stroke: currentStyle.edge.strokeColor,
              strokeWidth: currentStyle.edge.strokeWidth,
            },
            data: {
              ...edge.data,
              showGlow: currentStyle.edge.showGlow,
            },
          }));

          // 应用到画布
          console.log("[FlowchartUploader] Calling setNodes and setEdges...");
          setNodes(styledNodes);
          setEdges(styledEdges);

          // 延迟fitView以确保节点已渲染
          setTimeout(() => {
            console.log("[FlowchartUploader] Nodes should be visible now");
            window.dispatchEvent(new CustomEvent('flowchart-imported'));
          }, 100);

          // 显示警告（如果有）
          if (analysisResult.warnings && analysisResult.warnings.length > 0) {
            const warningMsg = `⚠️ ${analysisResult.warnings.length} 个节点的形状被映射`;
            addChatMessage("assistant", warningMsg);
          }
        } else {
          throw new Error("未收到分析结果");
        }
      } catch (err: any) {
        console.error("Upload error:", err);
        const errorMessage = err.message || "识别失败";
        const errorStack = err.stack ? `\n\n堆栈跟踪:\n${err.stack}` : '';
        const fullError = errorMessage + errorStack;
        setError(fullError);
        addChatMessage("assistant", `❌ 识别失败: ${errorMessage}`);
        toast.error("识别失败，请查看聊天记录中的详细错误信息");
      } finally {
        setUploading(false);
      }
    },
    [modelConfig, setNodes, setEdges, canvasMode, setCanvasMode, addChatMessage]
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
      // 重置input value，确保可以重新上传同一个文件
      e.target.value = '';
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
          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400 flex-shrink-0 mt-0.5" />
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-red-900 dark:text-red-100">
              识别失败
            </p>
            <pre className="mt-2 text-xs text-red-700 dark:text-red-300 whitespace-pre-wrap break-words font-mono bg-red-100 dark:bg-red-900/30 p-2 rounded max-h-60 overflow-y-auto">
{error}
            </pre>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800 dark:text-red-400 flex-shrink-0"
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
