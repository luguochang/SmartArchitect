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

const ARCHITECT_NODE_TYPES = {
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
};

const ARCHITECT_EDGE_TYPES = {
  glow: GlowEdge,
  orthogonal: OrthogonalEdge,
  straight: StraightEdge,
  // Keep aliases for model output and legacy payloads.
  smoothstep: OrthogonalEdge,
  step: OrthogonalEdge,
};

function ArchitectCanvasInner() {
  const {
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    setEdges,
    setNodes,
    diagramType,
    deleteCanvasSession,
    setIncrementalMode,
    isGeneratingFlowchart,
  } = useArchitectStore();
  const { presentationStyleId, setPresentationStyle, fontStyleId, setFontStyle } = useFlowchartStyleStore();
  const { fitView, project } = useReactFlow();
  const [layoutDirection, setLayoutDirection] = useState<LayoutDirection>("LR"); // 榛樿宸﹀埌鍙?
  const styleOptions = useMemo(() => Object.values(FLOWCHART_PRESENTATION_STYLES), []);
  const fontOptions = useMemo(() => Object.values(FONT_STYLE_OPTIONS), []);
  const [styleDockOpen, setStyleDockOpen] = useState(false);

  // Get current flowchart presentation style
  const { currentPresentationStyle, edgeType } = useFlowchartStyleStore();
  const wasGeneratingRef = useRef(false);

  // 杩借釜涓婁竴娆＄殑鏍峰紡锛岄伩鍏嶄笉蹇呰鐨勬洿鏂?
  const prevStyleRef = useRef({ edgeType, edge: currentPresentationStyle.edge });

  // 鐩戝惉鏍峰紡鍙樺寲锛岃嚜鍔ㄦ洿鏂版墍鏈夌幇鏈夌殑杈?
  useEffect(() => {
    // 妫€鏌dges鏄惁涓烘暟缁勪笖涓嶄负绌?
    if (!Array.isArray(edges) || edges.length === 0) return;

    // 妫€鏌ユ牱寮忔槸鍚︾湡鐨勬敼鍙樹簡
    const prevStyle = prevStyleRef.current;
    const styleChanged =
      prevStyle.edgeType !== edgeType ||
      prevStyle.edge.strokeColor !== currentPresentationStyle.edge.strokeColor ||
      prevStyle.edge.strokeWidth !== currentPresentationStyle.edge.strokeWidth ||
      prevStyle.edge.markerSize !== currentPresentationStyle.edge.markerSize ||
      prevStyle.edge.showGlow !== currentPresentationStyle.edge.showGlow;

    if (!styleChanged) return;

    console.log("[ArchitectCanvas] Style changed, updating", edges.length, "edges...");

    // 鏇存柊ref
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

  // 鐩戝惉娴佺▼鍥惧鍏ヤ簨浠?
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

  // 褰搉odes鏀瑰彉鏃朵篃璁板綍鏃ュ織
  useEffect(() => {
    console.log("[ArchitectCanvas] Nodes updated:", nodes.length);
  }, [nodes]);

  // 娉ㄥ唽鑷畾涔夎妭鐐圭被鍨?
  const onDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  // 缃戞牸瀵归綈杈呭姪鍑芥暟 - 瀵归綈鍒版渶杩戠殑缃戞牸鐐?
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

      // 馃敟 鑷姩缃戞牸瀵归綈锛堝彲閫氳繃Shift閿鐢級
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

      // 鎻愪緵瑙嗚鍙嶉
      toast.success(`宸叉坊鍔?${parsed.label || "鑺傜偣"}`, {
        duration: 1500,
        position: "bottom-right",
      });
    },
    [nodes, project, setNodes, snapToGrid]
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

    const isVertical = layoutDirection === "TB" || layoutDirection === "BT";
    const isArchitecture = diagramType === "architecture";

    const layoutOptions: LayoutOptions = {
      direction: layoutDirection,
      ranksep: isArchitecture ? (isVertical ? 190 : 260) : (isVertical ? 120 : 180),
      nodesep: isArchitecture ? (isVertical ? 150 : 210) : (isVertical ? 95 : 130),
    };

    // Apply dagre layout algorithm with user-selected direction
    const layoutedNodes = getLayoutedElements(nodesWithSize, edges, layoutOptions);

    // Update nodes with new positions
    setNodes(layoutedNodes);

    // Fit view after layout with some padding
    setTimeout(() => {
      fitView({ padding: 0.2, duration: 400 });
    }, 0);
  }, [nodes, edges, setNodes, fitView, layoutDirection, diagramType]);

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
      case "TB": return "Top-Bottom";
      case "LR": return "Left-Right";
      case "BT": return "Bottom-Top";
      case "RL": return "Right-Left";
    }
  };

  // 鑷姩 fit view 褰撹妭鐐规暟閲忓彉鍖栨椂
  useEffect(() => {
    if (isGeneratingFlowchart) {
      wasGeneratingRef.current = true;
      return;
    }

    if (nodes.length > 0) {
      const delay = wasGeneratingRef.current ? 180 : 100;
      const timer = setTimeout(() => {
        fitView({ padding: 0.12, duration: 320, minZoom: 0.24, maxZoom: 1.1 });
        wasGeneratingRef.current = false;
      }, delay);
      return () => clearTimeout(timer);
    }

    wasGeneratingRef.current = false;
  }, [nodes.length, fitView, isGeneratingFlowchart]);

  // 澶勭悊閿洏鍒犻櫎浜嬩欢锛圖elete 鍜?Backspace锛?
  const handleNodesDelete = useCallback((nodesToDelete: Node[]) => {
    // 鑺傜偣鍒犻櫎鐢?onNodesChange 鑷姩澶勭悊
    console.log("Deleted nodes:", nodesToDelete.map(n => n.id));
  }, []);

  const handleEdgesDelete = useCallback((edgesToDelete: Edge[]) => {
    // 杈瑰垹闄ょ敱 onEdgesChange 鑷姩澶勭悊
    console.log("Deleted edges:", edgesToDelete.map(e => e.id));
  }, []);

  // 澶勭悊杈圭殑鐐瑰嚮浜嬩欢 - 鎻愪緵棰濆鐨勪氦浜掑弽棣?
  const handleEdgeClick = useCallback((event: React.MouseEvent, edge: Edge) => {
    console.log("Edge clicked:", edge.id);
    // 杈逛細鑷姩琚€変腑,鐢ㄦ埛鍙互鎸?Delete 鍒犻櫎
  }, []);

  // 馃敟 蹇嵎閿敮鎸?
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Cmd/Ctrl + A: 鍏ㄩ€夋墍鏈夎妭鐐?
      if ((event.metaKey || event.ctrlKey) && event.key === "a") {
        event.preventDefault();
        console.log("Select all nodes");
        // React Flow 宸叉湁鍐呯疆鍏ㄩ€夋敮鎸?
      }

      // Cmd/Ctrl + L: 鑷姩甯冨眬
      if ((event.metaKey || event.ctrlKey) && event.key === "l") {
        event.preventDefault();
        handleAutoLayout();
        toast.success("宸插簲鐢ㄨ嚜鍔ㄥ竷灞€", { duration: 1500 });
      }

      // Cmd/Ctrl + F: Fit View
      if ((event.metaKey || event.ctrlKey) && event.key === "f") {
        event.preventDefault();
        fitView({ padding: 0.2, duration: 400 });
        toast.success("宸查€傞厤瑙嗗浘", { duration: 1500 });
      }

      // Cmd/Ctrl + Shift + C: 娓呯┖鐢诲竷
      if ((event.metaKey || event.ctrlKey) && event.shiftKey && event.key === "C") {
        event.preventDefault();
        if (confirm("Clear the entire canvas?")) {
          setNodes([]);
          setEdges([]);
          // 馃啎 娓呯┖鐢诲竷鏃跺垹闄や細璇?
          deleteCanvasSession();
          setIncrementalMode(false);
          toast.info("Canvas cleared", { duration: 1500 });
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [handleAutoLayout, fitView, setNodes, setEdges, deleteCanvasSession, setIncrementalMode]);

  return (
    <div className="relative h-full w-full">
      <ReactFlow
        data-testid="reactflow-canvas"
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodesDelete={handleNodesDelete}
        onEdgesDelete={handleEdgesDelete}
        onEdgeClick={handleEdgeClick}
        nodeTypes={ARCHITECT_NODE_TYPES}
        edgeTypes={ARCHITECT_EDGE_TYPES}
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

        {/* 绌虹姸鎬佹杩庣晫闈?*/}
        {nodes.length === 0 && <EmptyCanvasState />}

        {/* 宸ュ叿鏍?*/}
        <Panel position="top-right" className="flex gap-2">
          <button
            onClick={() => {
              setNodes([]);
              setEdges([]);
              // 馃啎 娓呯┖鐢诲竷鏃跺垹闄や細璇?
              deleteCanvasSession();
              setIncrementalMode(false);
            }}
            data-testid="btn-clear-canvas"
            className="flex items-center gap-2 rounded-lg border border-red-200 bg-white px-3 py-2 text-xs font-semibold text-red-600 shadow-sm hover:border-red-300 hover:bg-red-50 dark:border-red-500/50 dark:bg-slate-800 dark:text-red-300 dark:hover:border-red-400 dark:hover:bg-red-500/10"
            title="娓呴櫎鐢诲竷涓婄殑鎵€鏈夎妭鐐瑰拰杩炵嚎"
          >
            <Trash2 className="h-4 w-4" />
            娓呯┖鐢诲竷
          </button>

          <button
            onClick={() => setStyleDockOpen((v) => !v)}
            data-testid="btn-toggle-style-dock"
            className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:border-indigo-300 hover:text-indigo-700 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200 dark:hover:border-indigo-400"
            title="鍒囨崲娴佺▼鍥炬牱寮?/ 瀛椾綋"
          >
            <Palette className="h-4 w-4 text-indigo-500" />
            鐢诲竷椋庢牸
          </button>

          {/* Style switcher dock */}
          <div className="relative">
            {styleDockOpen && (
              <div className="absolute right-0 mt-2 w-72 rounded-xl border border-slate-200 bg-white/95 p-3 text-xs shadow-2xl dark:border-slate-700 dark:bg-slate-900/95">
                <div className="mb-2 flex items-center justify-between text-[11px] font-semibold text-slate-700 dark:text-slate-200">
                  <span>Flowchart Style</span>
                  <button
                    onClick={() => setStyleDockOpen(false)}
                    className="rounded-full px-2 py-0.5 text-[10px] text-slate-500 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  >
                    鏀惰捣
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
                    <div className="text-[11px] font-semibold text-slate-700 dark:text-slate-200">瀛椾綋鏍峰紡</div>
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

          {/* 甯冨眬鏂瑰悜閫夋嫨鍣?- 鍙湪 flow 妯″紡鏄剧ず */}
          <div className="flex items-center gap-1 rounded-lg bg-white px-2 py-1 shadow-md dark:bg-slate-800">
                <button
                  onClick={() => setLayoutDirection("LR")}
                  className={`p-2 rounded transition-colors ${
                    layoutDirection === "LR"
                      ? "bg-indigo-100 text-indigo-600 dark:bg-indigo-900 dark:text-indigo-400"
                      : "hover:bg-slate-100 dark:hover:bg-slate-700"
                  }`}
                  title="Left to Right"
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
                  title="Top to Bottom"
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
                  title="Right to Left"
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
                  title="Bottom to Top"
                >
                  <ArrowUp className="h-4 w-4" />
                </button>
              </div>

              {/* Auto Layout 鎸夐挳 */}
              <button
                onClick={handleAutoLayout}
                data-testid="btn-auto-layout"
                className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white shadow-md hover:bg-indigo-700 dark:bg-indigo-500 dark:hover:bg-indigo-600 transition-colors"
              >
                <Network className="h-4 w-4" />
                <span>甯冨眬 {getLayoutLabel()}</span>
              </button>

          <ExportMenu />
        </Panel>
      </ReactFlow>
    </div>
  );
}

// 瀵煎嚭鍖呰鍚庣殑缁勪欢
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

// 淇濇寔鍚戝悗鍏煎
export const ArchitectCanvasWrapper = ArchitectCanvas;

