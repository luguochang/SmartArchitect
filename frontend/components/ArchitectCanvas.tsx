"use client";

import { useCallback, useMemo, useEffect } from "react";
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
} from "reactflow";
import "reactflow/dist/style.css";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
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
import ExportMenu from "./ExportMenu";
import { Network, Sparkles, ArrowDown, ArrowRight, ArrowUp, ArrowLeft, Github } from "lucide-react";
import ExcalidrawBoard from "./ExcalidrawBoard";
import { getLayoutedElements, estimateNodeSize, LayoutOptions } from "@/lib/utils/autoLayout";
import { useState } from "react";
import { toast } from "sonner";

type LayoutDirection = "TB" | "LR" | "BT" | "RL";

function ArchitectCanvasInner() {
  const { nodes, edges, onNodesChange, onEdgesChange, setEdges, setNodes, diagramType } = useArchitectStore();
  const { fitView } = useReactFlow();
  const [layoutDirection, setLayoutDirection] = useState<LayoutDirection>("LR"); // 默认左到右

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

  const edgeTypes = useMemo(
    () => ({
      glow: GlowEdge,
    }),
    []
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      const newEdge = {
        ...connection,
        id: `${connection.source}-${connection.target}`,
        type: "glow",
        animated: true,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 18,
          height: 18,
          color: "var(--edge-stroke)",
        },
        style: {
          stroke: "var(--edge-stroke, #94a3b8)",
          strokeWidth: Number(
            getComputedStyle(document.documentElement).getPropertyValue("--edge-stroke-width") || 2
          ),
        },
      };
      setEdges(addEdge(newEdge, edges));
    },
    [edges, setEdges]
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
          type: "glow",
          markerEnd: { type: MarkerType.ArrowClosed, width: 18, height: 18 },
          style: { stroke: "var(--edge-stroke, #94a3b8)", strokeWidth: 2.5 },
        }}
        fitView
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

        {/* 工具栏 */}
        <Panel position="top-right" className="flex gap-2">
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
