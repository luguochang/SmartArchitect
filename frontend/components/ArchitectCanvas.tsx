"use client";

import { useCallback, useMemo, useEffect, useRef, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Panel,
  useReactFlow,
  ReactFlowProvider,
  addEdge,
  Connection,
  MarkerType,
  ConnectionMode,
  Node,
  Edge,
} from "reactflow";
import "reactflow/dist/style.css";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { useFlowchartStyleStore } from "@/lib/stores/flowchartStyleStore";
import { FLOWCHART_PRESENTATION_STYLES, FONT_STYLE_OPTIONS } from "@/lib/themes/flowchartPresentationStyles";
import { DatabaseNode } from "./nodes/DatabaseNode";
import { ApiNode } from "./nodes/ApiNode";
import { ServiceNode } from "./nodes/ServiceNode";
import { GatewayNode } from "./nodes/GatewayNode";
import { CacheNode } from "./nodes/CacheNode";
import { QueueNode } from "./nodes/QueueNode";
import { StorageNode } from "./nodes/StorageNode";
import { ClientNode } from "./nodes/ClientNode";
import { DefaultNode } from "./nodes/DefaultNode";
import { FrameNode } from "./nodes/FrameNode";
import { LayerFrameNode } from "./nodes/LayerFrameNode";
import { GlowEdge } from "./edges/GlowEdge";
import { OrthogonalEdge } from "./edges/OrthogonalEdge";
import { StraightEdge } from "./edges/StraightEdge";
import ExportMenu from "./ExportMenu";
import { Network, Sparkles, ArrowDown, ArrowRight, ArrowUp, ArrowLeft, Github, Palette, Trash2 } from "lucide-react";
import ExcalidrawBoard from "./ExcalidrawBoard";
import { getLayoutedElements, estimateNodeSize, LayoutOptions } from "@/lib/utils/autoLayout";
import { toast } from "sonner";
import { EmptyCanvasState } from "./EmptyCanvasState";

type LayoutDirection = "TB" | "LR" | "BT" | "RL";

function ArchitectCanvasInner() {
  const { nodes, edges, onNodesChange, onEdgesChange, setEdges, setNodes, diagramType, deleteCanvasSession, setIncrementalMode } = useArchitectStore();
  const { presentationStyleId, setPresentationStyle, fontStyleId, setFontStyle } = useFlowchartStyleStore();
  const { fitView, project } = useReactFlow();
  const [layoutDirection, setLayoutDirection] = useState<LayoutDirection>("LR"); // 默认左到右
  const styleOptions = useMemo(() => Object.values(FLOWCHART_PRESENTATION_STYLES), []);
  const fontOptions = useMemo(() => Object.values(FONT_STYLE_OPTIONS), []);
  const [styleDockOpen, setStyleDockOpen] = useState(false);

  // Get current flowchart presentation style
  const { currentPresentationStyle, edgeType } = useFlowchartStyleStore();

  // 追踪上一次的样式，避免不必要的更新
  const prevStyleRef = useRef({ edgeType, edge: currentPresentationStyle.edge });

  // 监听样式变化，自动更新所有现有的边
  useEffect(() => {
    // 检查edges是否为数组且不为空
    if (!Array.isArray(edges) || edges.length === 0) return;

    // 检查样式是否真的改变了
    const prevStyle = prevStyleRef.current;
    const styleChanged =
      prevStyle.edgeType !== edgeType ||
      prevStyle.edge.strokeColor !== currentPresentationStyle.edge.strokeColor ||
      prevStyle.edge.strokeWidth !== currentPresentationStyle.edge.strokeWidth ||
      prevStyle.edge.markerSize !== currentPresentationStyle.edge.markerSize ||
      prevStyle.edge.showGlow !== currentPresentationStyle.edge.showGlow;

    if (!styleChanged) return;

    console.log("[ArchitectCanvas] Style changed, updating", edges.length, "edges...");

    // 更新ref
    prevStyleRef.current = { edgeType, edge: currentPresentationStyle.edge };

    const updatedEdges = edges.map((edge) => ({
      ...edge,
      type: edgeType,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        width: currentPresentationStyle.edge.markerSize,
        height: currentPresentationStyle.edge.markerSize,
        color: currentPresentationStyle.edge.strokeColor,
      },
      style: {
        ...edge.style,
        stroke: currentPresentationStyle.edge.strokeColor,
        strokeWidth: currentPresentationStyle.edge.strokeWidth,
      },
      data: {
        ...edge.data,
        showGlow: currentPresentationStyle.edge.showGlow,
      },
    }));

    setEdges(updatedEdges);
  }, [edges, edgeType, currentPresentationStyle.edge, setEdges]);

  // 监听流程图导入事件
  useEffect(() => {
    const handleFlowchartImport = () => {
      console.log("[ArchitectCanvas] Flowchart imported, fitting view...");
      setTimeout(() => {
        fitView({ padding: 0.2, duration: 400 });
      }, 150);
    };

    window.addEventListener('flowchart-imported', handleFlowchartImport);
    return () => window.removeEventListener('flowchart-imported', handleFlowchartImport);
  }, [fitView]);

  // 当nodes改变时也记录日志
  useEffect(() => {
    console.log("[ArchitectCanvas] Nodes updated:", nodes.length);
  }, [nodes]);

  // 注册自定义节点类型
  const nodeTypes = useMemo(
    () => ({
      default: DefaultNode,
      database: DatabaseNode,
      api: ApiNode,
      service: ServiceNode,
      gateway: GatewayNode,
      cache: CacheNode,
      queue: QueueNode,
      storage: StorageNode,
      client: ClientNode,
      frame: FrameNode,
      layerFrame: LayerFrameNode,
    }),
    []
  );

  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  // 网格对齐辅助函数 - 对齐到最近的网格点
  const snapToGrid = useCallback((position: { x: number; y: number }, gridSize = 20) => {
    return {
      x: Math.round(position.x / gridSize) * gridSize,
      y: Math.round(position.y / gridSize) * gridSize,
    };
  }, []);

  const onDrop = useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();
      const raw = event.dataTransfer.getData("application/reactflow");
      if (!raw) return;

      let parsed: any;
      try {
        parsed = JSON.parse(raw);
      } catch {
        return;
      }

      const bounds = (event.currentTarget as HTMLElement).getBoundingClientRect();
      const rawPosition = project({
        x: event.clientX - bounds.left,
        y: event.clientY - bounds.top,
      });

      // 🔥 自动网格对齐（可通过Shift键禁用）
      const position = event.shiftKey ? rawPosition : snapToGrid(rawPosition, 20);

      const newNode = {
        id: `node-${Date.now()}`,
        type: parsed.type || "default",
        position,
        data: {
          label: parsed.label || "New Node",
          ...(parsed.shape && { shape: parsed.shape }),
          ...(parsed.color && { color: parsed.color }),
          ...(parsed.iconType && { iconType: parsed.iconType }),
        },
      };

      setNodes([...nodes, newNode]);

      // 提供视觉反馈
      toast.success(`已添加 ${parsed.label || "节点"}`, {
        duration: 1500,
        position: "bottom-right",
      });
    },
    [nodes, project, setNodes, snapToGrid]
  );

  const edgeTypes = useMemo(
    () => ({
      glow: GlowEdge,
      orthogonal: OrthogonalEdge,
      straight: StraightEdge,
      // Also register smoothstep as an alias for orthogonal
      smoothstep: OrthogonalEdge,
      step: OrthogonalEdge,
    }),
    []
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      // Determine edge type based on current presentation style
      const selectedEdgeType = edgeType; // "orthogonal" | "straight" | "smoothstep" | "step"

      const newEdge = {
        ...connection,
        id: `${connection.source}-${connection.target}`,
        type: selectedEdgeType,
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: currentPresentationStyle.edge.markerSize,
          height: currentPresentationStyle.edge.markerSize,
          color: currentPresentationStyle.edge.strokeColor,
        },
        style: {
          stroke: currentPresentationStyle.edge.strokeColor,
          strokeWidth: currentPresentationStyle.edge.strokeWidth,
        },
        data: {
          showGlow: currentPresentationStyle.edge.showGlow,
        },
      };
      setEdges(addEdge(newEdge, edges));
    },
    [edges, setEdges, edgeType, currentPresentationStyle]
  );

  const handleAutoLayout = useCallback(() => {
    // Estimate node sizes for better layout
    const nodesWithSize = nodes.map((node) => {
      const size = estimateNodeSize(node);
      return {
        ...node,
        width: size.width,
        height: size.height,
      };
    });

    // Apply dagre layout algorithm with user-selected direction
    const layoutedNodes = getLayoutedElements(nodesWithSize, edges, {
      direction: layoutDirection,
      ranksep: layoutDirection === "TB" || layoutDirection === "BT" ? 100 : 150,
      nodesep: layoutDirection === "TB" || layoutDirection === "BT" ? 80 : 100,
    });

    // Update nodes with new positions
    setNodes(layoutedNodes);

    // Fit view after layout with some padding
    setTimeout(() => {
      fitView({ padding: 0.2, duration: 400 });
    }, 0);
  }, [nodes, edges, setNodes, fitView, layoutDirection]);

  const getLayoutIcon = () => {
    switch (layoutDirection) {
      case "TB": return <ArrowDown className="h-4 w-4" />;
      case "LR": return <ArrowRight className="h-4 w-4" />;
      case "BT": return <ArrowUp className="h-4 w-4" />;
      case "RL": return <ArrowLeft className="h-4 w-4" />;
    }
  };

  const getLayoutLabel = () => {
    switch (layoutDirection) {
      case "TB": return "上→下";
      case "LR": return "左→右";
      case "BT": return "下→上";
      case "RL": return "右→左";
    }
  };

  // 自动 fit view 当节点数量变化时
  useEffect(() => {
    if (nodes.length > 0) {
      // 延迟 fit view 确保节点已渲染
      const timer = setTimeout(() => {
        fitView({ padding: 0.1, duration: 300 });
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [nodes.length, fitView]);

  // 处理键盘删除事件（Delete 和 Backspace）
  const handleNodesDelete = useCallback((nodesToDelete: Node[]) => {
    // 节点删除由 onNodesChange 自动处理
    console.log("Deleted nodes:", nodesToDelete.map(n => n.id));
  }, []);

  const handleEdgesDelete = useCallback((edgesToDelete: Edge[]) => {
    // 边删除由 onEdgesChange 自动处理
    console.log("Deleted edges:", edgesToDelete.map(e => e.id));
  }, []);

  // 处理边的点击事件 - 提供额外的交互反馈
  const handleEdgeClick = useCallback((event: React.MouseEvent, edge: Edge) => {
    console.log("Edge clicked:", edge.id);
    // 边会自动被选中,用户可以按 Delete 删除
  }, []);

  // 🔥 快捷键支持
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Cmd/Ctrl + A: 全选所有节点
      if ((event.metaKey || event.ctrlKey) && event.key === "a") {
        event.preventDefault();
        console.log("Select all nodes");
        // React Flow 已有内置全选支持
      }

      // Cmd/Ctrl + L: 自动布局
      if ((event.metaKey || event.ctrlKey) && event.key === "l") {
        event.preventDefault();
        handleAutoLayout();
        toast.success("已应用自动布局", { duration: 1500 });
      }

      // Cmd/Ctrl + F: Fit View
      if ((event.metaKey || event.ctrlKey) && event.key === "f") {
        event.preventDefault();
        fitView({ padding: 0.2, duration: 400 });
        toast.success("已适配视图", { duration: 1500 });
      }

      // Cmd/Ctrl + Shift + C: 清空画布
      if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key === "C") {
        event.preventDefault();
        if (confirm("确定要清空画布吗？")) {
          setNodes([]);
          setEdges([]);
          // 🆕 清空画布时删除会话
          deleteCanvasSession();
          setIncrementalMode(false);
          toast.info("画布已清空", { duration: 1500 });
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleAutoLayout, fitView, setNodes, setEdges, deleteCanvasSession, setIncrementalMode]);

  return (
    <div className="relative h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodesDelete={handleNodesDelete}
        onEdgesDelete={handleEdgesDelete}
        onEdgeClick={handleEdgeClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        connectOnClick
        connectionRadius={32}
        connectionMode={ConnectionMode.Loose}
        deleteKeyCode={["Backspace", "Delete"]}
        multiSelectionKeyCode={["Meta", "Shift"]}
        selectionKeyCode={["Shift"]}
        elementsSelectable={true}
        nodesConnectable={true}
        nodesDraggable={true}
        edgesUpdatable={true}
        edgesFocusable={true}
        defaultEdgeOptions={{
          type: edgeType,
          markerEnd: {
            type: MarkerType.ArrowClosed,
            width: currentPresentationStyle.edge.markerSize,
            height: currentPresentationStyle.edge.markerSize,
          },
          style: {
            stroke: currentPresentationStyle.edge.strokeColor,
            strokeWidth: currentPresentationStyle.edge.strokeWidth,
          },
        }}
        fitView
        onDrop={onDrop}
        onDragOver={onDragOver}
        style={{
          background: "radial-gradient(circle at 20% 20%, rgba(99,102,241,0.08), transparent 35%), radial-gradient(circle at 80% 30%, rgba(16,185,129,0.08), transparent 35%), var(--canvas-background)",
        }}
      >
        <Background
          color="var(--canvas-grid)"
          gap={18}
          size={0.75}
        />
        <Controls className="!bg-white/90 !rounded-lg !shadow-md dark:!bg-slate-900/90" />
        <MiniMap
          className="!bg-white/80 !rounded-lg !shadow-md dark:!bg-slate-900/80"
          maskColor="rgba(0, 0, 0, 0.08)"
        />

        {/* 空状态欢迎界面 */}
        {nodes.length === 0 && <EmptyCanvasState />}

        {/* 工具栏 */}
        <Panel position="top-right" className="flex gap-2">
          <button
            onClick={() => {
              setNodes([]);
              setEdges([]);
              // 🆕 清空画布时删除会话
              deleteCanvasSession();
              setIncrementalMode(false);
            }}
            className="flex items-center gap-2 rounded-lg border border-red-200 bg-white px-3 py-2 text-xs font-semibold text-red-600 shadow-sm hover:border-red-300 hover:bg-red-50 dark:border-red-500/50 dark:bg-slate-800 dark:text-red-300 dark:hover:border-red-400 dark:hover:bg-red-500/10"
            title="清除画布上的所有节点和连线"
          >
            <Trash2 className="h-4 w-4" />
            清空画布
          </button>

          <button
            onClick={() => setStyleDockOpen((v) => !v)}
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:border-indigo-300 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-indigo-400"
            title="切换流程图样式 / 字体"
          >
            <Palette className="h-4 w-4 text-indigo-500" />
            画布风格
          </button>

          {/* Style switcher dock */}
          <div className="relative">
            {styleDockOpen && (
              <div className="absolute right-0 mt-2 w-72 rounded-xl border border-slate-200 bg-white/95 p-3 text-xs shadow-2xl dark:border-slate-700 dark:bg-slate-900/95">
                <div className="mb-2 flex items-center justify-between text-[11px] font-semibold text-slate-700 dark:text-slate-200">
                  <span>流程图样式</span>
                  <button
                    onClick={() => setStyleDockOpen(false)}
                    className="rounded-full px-2 py-0.5 text-[10px] text-slate-500 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  >
                    收起
                  </button>
                </div>
                <div className="space-y-2">
                  <div className="grid grid-cols-2 gap-2">
                    {styleOptions.map((style) => {
                      const active = presentationStyleId === style.id;
                      return (
                        <button
                          key={style.id}
                          onClick={() => setPresentationStyle(style.id)}
                          className={`rounded-lg border px-2 py-2 text-left text-[11px] transition ${
                            active
                              ? "border-indigo-500 bg-indigo-50 text-indigo-900 shadow-sm dark:border-indigo-400 dark:bg-indigo-900/30 dark:text-indigo-100"
                              : "border-slate-200 bg-white hover:border-indigo-300 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-indigo-400 dark:text-slate-200"
                          }`}
                          title={style.description}
                        >
                          <div className="font-semibold">{style.name}</div>
                          <div className="text-[10px] text-slate-500 line-clamp-2 dark:text-slate-400">{style.description}</div>
                        </button>
                      );
                    })}
                  </div>

                  <div className="space-y-1">
                    <div className="text-[11px] font-semibold text-slate-700 dark:text-slate-200">字体样式</div>
                    <div className="grid grid-cols-2 gap-2">
                      {fontOptions.map((font) => {
                        const active = fontStyleId === font.id;
                        return (
                          <button
                            key={font.id}
                            onClick={() => setFontStyle(font.id)}
                            className={`rounded-lg border px-2 py-2 text-left text-[11px] transition ${
                              active
                                ? "border-emerald-500 bg-emerald-50 text-emerald-900 shadow-sm dark:border-emerald-400 dark:bg-emerald-900/30 dark:text-emerald-100"
                                : "border-slate-200 bg-white hover:border-emerald-300 hover:text-emerald-700 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-emerald-400 dark:text-slate-200"
                            }`}
                            style={{ fontFamily: font.fontFamily }}
                            title={font.description}
                          >
                            <div className="font-semibold">{font.name}</div>
                            <div className="text-[10px] text-slate-500 line-clamp-2 dark:text-slate-400">{font.description}</div>
                          </button>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* 布局方向选择器 - 只在 flow 模式显示 */}
          {diagramType === "flow" && (
            <>
              <div className="flex items-center gap-1 rounded-lg bg-white px-2 py-1 shadow-md dark:bg-slate-800">
                <button
                  onClick={() => setLayoutDirection("LR")}
                  className={`p-2 rounded transition-colors ${
                    layoutDirection === "LR"
                      ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-900 dark:text-indigo-400"
                      : "hover:bg-slate-100 dark:hover:bg-slate-700"
                  }`}
                  title="左→右"
                >
                  <ArrowRight className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setLayoutDirection("TB")}
                  className={`p-2 rounded transition-colors ${
                    layoutDirection === "TB"
                      ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-900 dark:text-indigo-400"
                      : "hover:bg-slate-100 dark:hover:bg-slate-700"
                  }`}
                  title="上→下"
                >
                  <ArrowDown className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setLayoutDirection("RL")}
                  className={`p-2 rounded transition-colors ${
                    layoutDirection === "RL"
                      ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-900 dark:text-indigo-400"
                      : "hover:bg-slate-100 dark:hover:bg-slate-700"
                  }`}
                  title="右→左"
                >
                  <ArrowLeft className="h-4 w-4" />
                </button>
                <button
                  onClick={() => setLayoutDirection("BT")}
                  className={`p-2 rounded transition-colors ${
                    layoutDirection === "BT"
                      ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-900 dark:text-indigo-400"
                      : "hover:bg-slate-100 dark:hover:bg-slate-700"
                  }`}
                  title="下→上"
                >
                  <ArrowUp className="h-4 w-4" />
                </button>
              </div>

              {/* Auto Layout 按钮 */}
              <button
                onClick={handleAutoLayout}
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white shadow-md hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 transition-colors"
              >
                <Network className="h-4 w-4" />
                <span>布局 {getLayoutLabel()}</span>
              </button>
            </>
          )}

          <ExportMenu />
        </Panel>
      </ReactFlow>
    </div>
  );
}

// 导出包装后的组件
export function ArchitectCanvas() {
  const { canvasMode } = useArchitectStore();

  if (canvasMode === "excalidraw") {
    return (
      <div className="h-full w-full bg-slate-50 dark:bg-slate-900">
        <ExcalidrawBoard />
      </div>
    );
  }

  return (
    <ReactFlowProvider>
      <ArchitectCanvasInner />
    </ReactFlowProvider>
  );
}

// 保持向后兼容
export const ArchitectCanvasWrapper = ArchitectCanvas;
