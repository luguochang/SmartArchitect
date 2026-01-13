"use client";

import { useCallback, useMemo } from "react";
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
import { GlowEdge } from "./edges/GlowEdge";
import ExportMenu from "./ExportMenu";
import { Network, Sparkles } from "lucide-react";

function ArchitectCanvasInner() {
  const { nodes, edges, onNodesChange, onEdgesChange, setEdges } = useArchitectStore();
  const { fitView } = useReactFlow();

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
    // 简单的自动布局 - 未来可以集成 dagre
    fitView({ padding: 0.2 });
  }, [fitView]);

  return (
    <div className="relative h-full w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        connectOnClick
        connectionRadius={32}
        connectionMode="loose"
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
          <button
            onClick={handleAutoLayout}
            className="flex items-center gap-2 rounded-lg bg-white px-4 py-2 text-sm shadow-md hover:bg-slate-50 dark:bg-slate-800 dark:hover:bg-slate-700"
          >
            <Network className="h-4 w-4" />
            Auto Layout
          </button>
          <ExportMenu />
        </Panel>

        {/* AI 提示 */}
        <Panel position="bottom-center">
          <div className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white shadow-lg">
            <Sparkles className="h-4 w-4" />
            <span>AI 架构分析将在 Phase 2 集成</span>
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

// 导出包装后的组件
export function ArchitectCanvas() {
  return (
    <ReactFlowProvider>
      <ArchitectCanvasInner />
    </ReactFlowProvider>
  );
}

// 保持向后兼容
export const ArchitectCanvasWrapper = ArchitectCanvas;
