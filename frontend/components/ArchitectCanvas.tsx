"use client";

import { useCallback, useMemo } from "react";
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Panel,
  useReactFlow,
  ReactFlowProvider,
} from "reactflow";
import "reactflow/dist/style.css";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { DatabaseNode } from "./nodes/DatabaseNode";
import { ApiNode } from "./nodes/ApiNode";
import { ServiceNode } from "./nodes/ServiceNode";
import ExportMenu from "./ExportMenu";
import { Network, Sparkles } from "lucide-react";

function ArchitectCanvasInner() {
  const { nodes, edges, onNodesChange, onEdgesChange } = useArchitectStore();
  const { fitView } = useReactFlow();

  // 注册自定义节点类型
  const nodeTypes = useMemo(
    () => ({
      database: DatabaseNode,
      api: ApiNode,
      service: ServiceNode,
    }),
    []
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
        nodeTypes={nodeTypes}
        fitView
        style={{
          backgroundColor: "var(--canvas-background)",
        }}
      >
        <Background
          color="var(--canvas-grid)"
          gap={20}
        />
        <Controls />
        <MiniMap
          className="!bg-white dark:!bg-slate-800"
          maskColor="rgba(0, 0, 0, 0.1)"
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
