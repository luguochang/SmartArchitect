import { create } from "zustand";
import { Node, Edge, NodeChange, EdgeChange, applyNodeChanges, applyEdgeChanges } from "reactflow";
import { PROVIDER_DEFAULTS } from "@/lib/config/providerDefaults";
import { getLayoutedElements, estimateNodeSize } from "@/lib/utils/autoLayout";

export interface PromptScenario {
  id: string;
  name: string;
  description: string;
  category: "refactoring" | "security" | "beautification" | "custom";
  style_hint?: string;
  impact?: string;
  recommended_theme?: string;
}

export interface FlowTemplate {
  id: string;
  name: string;
  description: string;
  example_input: string;
  category?: string;
}

export type DiagramType = "flow" | "architecture";
export type CanvasMode = "reactflow" | "excalidraw";

export interface ExcalidrawScene {
  elements: any[];
  appState: Record<string, any>;
  files?: Record<string, any>;
}

interface ArchitectState {
  nodes: Node[];
  edges: Edge[];
  mermaidCode: string;
  generationLogs: string[];
  chatHistory: { role: "user" | "assistant"; content: string }[];
  diagramType: DiagramType;
  uploadedImage: File | null;
  imagePreviewUrl: string | null;
  isAnalyzing: boolean;
  analysisError?: string;

  // Canvas mode
  canvasMode: CanvasMode;
  setCanvasMode: (mode: CanvasMode) => void;

  // Excalidraw scene
  excalidrawScene: ExcalidrawScene | null;
  setExcalidrawScene: (scene: ExcalidrawScene | null) => void;

  // 🎬 流式渲染状态
  _preparedNodes: Node[]; // 准备好的节点（已布局但未显示）
  _preparedEdges: Edge[]; // 准备好的边（未显示）

  // 节点和边操作
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  updateNodeData: (id: string, data: Partial<Node["data"]>) => void;
  updateNodeLabel: (id: string, label: string) => void;
  uploadImage: (file: File) => void;
  clearImage: () => void;
  analyzeImage: () => Promise<void>;

  // Mermaid 代码操作
  setMermaidCode: (code: string) => void;
  updateFromMermaid: (code: string) => void;
  updateFromCanvas: () => void;

  // AI 模型配置
  modelConfig: {
    provider: "gemini" | "openai" | "claude" | "siliconflow" | "custom";
    apiKey: string;
    modelName: string;
    baseUrl?: string;
  };
  setModelConfig: (config: Partial<ArchitectState["modelConfig"]>) => void;

  // 流程生成（Phase 5 mock）
  flowTemplates: FlowTemplate[];
  isGeneratingFlowchart: boolean;
  loadFlowTemplates: () => Promise<void>;
  generateFlowchart: (input: string, templateId?: string, diagramType?: DiagramType) => Promise<void>;
  generateExcalidrawScene: (prompt: string) => Promise<void>;
  generateExcalidrawSceneStream: (prompt: string) => Promise<void>;

  // Prompter mock actions
  promptScenarios: PromptScenario[];
  isExecutingPrompt: boolean;
  promptError?: string;
  loadPromptScenarios: () => Promise<void>;
  executePromptScenario: (scenarioId: string, userInput?: string) => Promise<void>;
  applyMockScenario: (scenarioId: string) => void;
}

const DEFAULT_FLOW_TEMPLATES: FlowTemplate[] = [
  {
    id: "microservice-architecture",
    name: "微服务架构流程",
    description: "API 网关 → 认证服务 → 缓存 → 订单服务 → 消息队列 → 库存服务",
    example_input: "生成电商请求处理路径，含认证、缓存、订单、队列、库存、存储。",
    category: "architecture",
  },
  {
    id: "high-concurrency-system",
    name: "高并发秒杀系统",
    description: "限流 + 预扣库存 + 消息削峰 + 冗余存储链路",
    example_input: "秒杀系统架构，限流、缓存命中、Kafka 削峰、订单/存储节点。",
    category: "architecture",
  },
  {
    id: "incident-response",
    name: "故障响应流程",
    description: "检测 → 分流 → 回滚 → RCA → 复盘",
    example_input: "生成一次故障响应流程，包含检测、告警、人工确认、回滚与复盘。",
    category: "troubleshooting",
  },
];

const DEFAULT_PROMPT_SCENARIOS: PromptScenario[] = [
  {
    id: "beautify-bpmn",
    name: "Beautify BPMN",
    description: "Align gateways, label edges, clean crossings, swimlane feel.",
    category: "beautification",
    style_hint: "Grid + labeled edges",
    impact: "medium",
  },
  {
    id: "cyberpunk-visual",
    name: "Cyberpunk Visual",
    description: "Neon gradients, glow edges, futuristic palette.",
    category: "beautification",
    style_hint: "Neon + glow",
    impact: "medium",
  },
  {
    id: "handdrawn-sketch",
    name: "Hand-drawn Sketch",
    description: "Comic/hand-drawn vibe with curved edges, pastel fills.",
    category: "beautification",
    style_hint: "Sketch/pastel",
    impact: "low",
  },
  {
    id: "swimlane-layout",
    name: "Swimlane Layout",
    description: "Organize nodes by lanes (client/edge/services/data) with vertical connectors.",
    category: "refactoring",
    style_hint: "Lanes + grid",
    impact: "high",
  },
];

// Auto-wrap architecture nodes into layer frames when model output lacks them
const LAYER_BUCKETS: { name: string; types: Set<string>; color: string }[] = [
  { name: "Client Layer", types: new Set(["client", "user", "users", "mobile", "desktop", "tablet"]), color: "#06b6d4" },
  { name: "Edge Layer", types: new Set(["gateway", "load-balancer", "firewall", "cdn", "api"]), color: "#f97316" },
  { name: "Service Layer", types: new Set(["service", "cache", "queue"]), color: "#6366f1" },
  { name: "Data Layer", types: new Set(["database", "storage"]), color: "#22c55e" },
];

function addLayerFrames(nodes: Node[], diagramType?: DiagramType): Node[] {
  if (diagramType !== "architecture") return nodes;
  if (nodes.some((n) => n.type === "layerFrame")) return nodes;

  const padding = 60;
  const frames: Node[] = [];

  const getSize = (node: Node) => {
    const data = (node.data || {}) as any;
    return { width: data.width ?? 180, height: data.height ?? 90 };
  };

  for (const bucket of LAYER_BUCKETS) {
    const bucketNodes = nodes.filter((n) => bucket.types.has(n.type || ""));
    if (bucketNodes.length === 0) continue;

    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
    bucketNodes.forEach((node) => {
      const { width, height } = getSize(node);
      minX = Math.min(minX, node.position.x);
      minY = Math.min(minY, node.position.y);
      maxX = Math.max(maxX, node.position.x + width);
      maxY = Math.max(maxY, node.position.y + height);
    });

    const frameWidth = Math.max(300, maxX - minX + padding * 2);
    const frameHeight = Math.max(180, maxY - minY + padding * 2);

    frames.push({
      id: `layer-${bucket.name.toLowerCase().replace(/\s+/g, "-")}-${Math.random().toString(36).slice(2, 7)}`,
      type: "layerFrame",
      position: { x: minX - padding, y: minY - padding },
      data: {
        label: bucket.name,
        color: bucket.color,
        width: frameWidth,
        height: frameHeight,
      },
    });
  }

  if (frames.length === 0) return nodes;
  return [...frames, ...nodes];
}

// 将 React Flow 节点和边转换为 Mermaid 代码
function canvasToMermaid(nodes: Node[], edges: Edge[]): string {
  let mermaidCode = "graph TD\n";

  // 添加节点
  nodes.forEach((node) => {
    const nodeId = node.id;
    const label = (node.data as any)?.label || nodeId;
    const nodeType = node.type || "default";

    // 根据节点类型选择不同的 Mermaid 符号
    let nodeDefinition = "";
    switch (nodeType) {
      case "database":
        nodeDefinition = `    ${nodeId}[("${label}")]`;
        break;
      case "api":
        nodeDefinition = `    ${nodeId}["${label}"]`;
        break;
      case "service":
        nodeDefinition = `    ${nodeId}[["${label}"]]`;
        break;
      default:
        nodeDefinition = `    ${nodeId}["${label}"]`;
    }
    mermaidCode += nodeDefinition + "\n";
  });

  // 添加连接
  edges.forEach((edge) => {
    const label = edge.label ? `|${edge.label}|` : "";
    mermaidCode += `    ${edge.source} -->${label} ${edge.target}\n`;
  });

  return mermaidCode;
}

// 将 Mermaid 代码解析为 React Flow 节点和边（简化版）
function mermaidToCanvas(code: string): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const lines = code.split("\n");
  let yOffset = 0;

  lines.forEach((line, index) => {
    line = line.trim();

    // 跳过空行和 graph 声明
    if (!line || line.startsWith("graph")) return;

    // 简单的节点定义解析: nodeId["label"] 或 nodeId[("label")]
    const nodeMatch = line.match(/(\w+)\[([^\]]+)\]/);
    if (nodeMatch) {
      const [, nodeId, labelPart] = nodeMatch;
      const label = labelPart.replace(/["\(\)]/g, "").trim();

      // 确定节点类型
      let nodeType = "default";
      if (labelPart.includes("(")) nodeType = "database";
      if (labelPart.includes("[[")) nodeType = "service";

      nodes.push({
        id: nodeId,
        type: nodeType,
        position: { x: 100 + (index % 3) * 250, y: yOffset },
        data: { label },
      });

      yOffset += 100;
    }

    // 简单的边定义解析: source --> target 或 source -->|label| target
    const edgeMatch = line.match(/(\w+)\s*-->\s*(?:\|([^|]+)\|)?\s*(\w+)/);
    if (edgeMatch) {
      const [, source, label, target] = edgeMatch;
      edges.push({
        id: `${source}-${target}`,
        source,
        target,
        label: label?.trim(),
      });
    }
  });

  return { nodes, edges };
}

export const useArchitectStore = create<ArchitectState>((set, get) => ({
  nodes: [
    {
      id: "1",
      type: "api",
      position: { x: 100, y: 100 },
      data: { label: "API Gateway" },
    },
    {
      id: "2",
      type: "service",
      position: { x: 400, y: 100 },
      data: { label: "Auth Service" },
    },
    {
      id: "3",
      type: "database",
      position: { x: 400, y: 250 },
      data: { label: "PostgreSQL" },
    },
  ],
  edges: [
    { id: "e1-2", source: "1", target: "2", label: "auth" },
    { id: "e2-3", source: "2", target: "3", label: "query" },
  ],
  diagramType: "flow",
  mermaidCode: `graph TD
    1["API Gateway"]
    2[["Auth Service"]]
    3[("PostgreSQL")]
    1 -->|auth| 2
    2 -->|query| 3`,
  uploadedImage: null,
  imagePreviewUrl: null,
  isAnalyzing: false,
  analysisError: undefined,

  canvasMode: "reactflow",
  excalidrawScene: null,
  flowTemplates: DEFAULT_FLOW_TEMPLATES,
  isGeneratingFlowchart: false,
  generationLogs: [],
  chatHistory: [],

  // 🎬 流式渲染状态初始化
  _preparedNodes: [],
  _preparedEdges: [],

  promptScenarios: DEFAULT_PROMPT_SCENARIOS,
  isExecutingPrompt: false,
  promptError: undefined,

  modelConfig: {
    provider: PROVIDER_DEFAULTS.custom.provider,
    apiKey: PROVIDER_DEFAULTS.custom.apiKey,
    modelName: PROVIDER_DEFAULTS.custom.modelName,
    baseUrl: PROVIDER_DEFAULTS.custom.baseUrl,
  },

  setCanvasMode: (mode) => set({ canvasMode: mode }),
  setExcalidrawScene: (scene) => set({ excalidrawScene: scene }),

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  updateNodeData: (id, data) => {
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === id ? { ...node, data: { ...(node.data as any), ...data } } : node
      ),
    }));
    get().updateFromCanvas();
  },

  updateNodeLabel: (id, label) => {
    get().updateNodeData(id, { label });
  },

  uploadImage: (file: File) => {
    const previewUrl = URL.createObjectURL(file);
    set({ uploadedImage: file, imagePreviewUrl: previewUrl, analysisError: undefined });
  },

  clearImage: () => {
    set((state) => {
      if (state.imagePreviewUrl) {
        URL.revokeObjectURL(state.imagePreviewUrl);
      }
      return { uploadedImage: null, imagePreviewUrl: null, analysisError: undefined };
    });
  },

  analyzeImage: async () => {
    set({ isAnalyzing: true, analysisError: undefined });
    try {
      // TODO: implement real vision analysis; placeholder resolves immediately
      await Promise.resolve();
    } catch (error: any) {
      set({ analysisError: error?.message || "Analyze failed" });
      throw error;
    } finally {
      set({ isAnalyzing: false });
    }
  },

  onNodesChange: (changes) => {
    set({
      nodes: applyNodeChanges(changes, get().nodes),
    });
    // 节点变化后自动更新 Mermaid 代码
    get().updateFromCanvas();
  },

  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
    // 边变化后自动更新 Mermaid 代码
    get().updateFromCanvas();
  },

  setMermaidCode: (code) => set({ mermaidCode: code }),

  updateFromMermaid: (code) => {
    const { nodes, edges } = mermaidToCanvas(code);
    set({ nodes, edges, mermaidCode: code });
  },

  updateFromCanvas: () => {
    const { nodes, edges } = get();
    const mermaidCode = canvasToMermaid(nodes, edges);
    set({ mermaidCode });
  },

  setModelConfig: (config) =>
    set((state) => ({
      modelConfig: { ...state.modelConfig, ...config },
    })),

  loadFlowTemplates: async () => {
    try {
      const res = await fetch("/api/chat-generator/templates");
      if (!res.ok) {
        throw new Error(`Failed to load templates: ${res.status}`);
      }
      const data = await res.json();
      if (data?.templates?.length) {
        set({ flowTemplates: data.templates });
        return;
      }
    } catch (error) {
      console.warn("Load flow templates failed, fallback to defaults", error);
    }
    set({ flowTemplates: DEFAULT_FLOW_TEMPLATES });
  },

  generateFlowchart: async (input, templateId, diagramType) => {
    set({ isGeneratingFlowchart: true, diagramType: diagramType || "flow" });
    try {
      const { modelConfig } = get();
      set((state) => ({
        generationLogs: [],
        chatHistory: [
          ...state.chatHistory,
          { role: "user", content: input },
        ],
      }));
      const body = {
        user_input: input,
        template_id: templateId,
        diagram_type: diagramType,
        provider: modelConfig.provider,
        api_key: modelConfig.apiKey?.trim() || undefined,
        base_url: modelConfig.baseUrl?.trim() || undefined,
        model_name: modelConfig.modelName,
      };

      // Stream events to show progress and avoid spinner-only UX
      const response = await fetch("/api/chat-generator/generate-stream", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify(body),
      });

      if (!response.ok || !response.body) {
        const detail = await response.text();
        throw new Error(detail || "Backend generation failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffered = "";

      const logs: string[] = [];
      const pushLog = (line: string) => {
        logs.push(line);
        console.log(`[STREAM LOG] ${line.substring(0, 50)}`);
        set({ generationLogs: [...logs] });
      };

      // Track generation status in chat history
      let statusMessage = "🔄 正在生成流程图...";
      const updateChatStatus = (message: string) => {
        statusMessage = message;
        set((state) => {
          const newHistory = [...state.chatHistory];
          const last = newHistory[newHistory.length - 1];
          if (last && last.role === "assistant") {
            newHistory[newHistory.length - 1] = { role: "assistant", content: statusMessage };
          } else {
            newHistory.push({ role: "assistant", content: statusMessage });
          }
          return { chatHistory: newHistory };
        });
      };

      // Accumulate JSON tokens for display in logs
      let jsonBuffer = "";
      let isGenerating = false;
      const updateJsonLog = (token: string) => {
        jsonBuffer += token;
        // Find the index of the "[生成中]" log entry
        const generatingIndex = logs.findIndex(log => log.startsWith("[生成中]"));
        if (generatingIndex !== -1) {
          logs[generatingIndex] = `[生成中] ${jsonBuffer}`;
        } else {
          logs.push(`[生成中] ${jsonBuffer}`);
        }
        set({ generationLogs: [...logs] });
      };

      // Initialize status message
      updateChatStatus(statusMessage);

      console.log("[STREAM] 开始读取流...");
      let chunkCount = 0;
      while (true) {
        console.log(`[STREAM] 等待读取chunk ${chunkCount + 1}...`);
        const { value, done } = await reader.read();
        chunkCount++;
        console.log(`[STREAM] 收到chunk ${chunkCount}, size: ${value?.length || 0}, done: ${done}`);
        if (done) break;
        buffered += decoder.decode(value, { stream: true });

        const parts = buffered.split("\n\n");
        buffered = parts.pop() || "";

        for (const part of parts) {
          const cleaned = part.trim();
          if (!cleaned.startsWith("data:")) continue;
          const content = cleaned.replace(/^data:\s?/, "");

          // Only log key events, not every token
          if (content.startsWith("[START]")) {
            pushLog(content);
            updateChatStatus("📝 正在构建提示词...");
          } else if (content.startsWith("[CALL]")) {
            pushLog(content);
            updateChatStatus("🤖 AI 正在思考...");
            isGenerating = true;
          } else if (content.startsWith("[RESULT]")) {
            // Remove the "[生成中]" entry
            const generatingIndex = logs.findIndex(log => log.startsWith("[生成中]"));
            if (generatingIndex !== -1) {
              logs.splice(generatingIndex, 1);
            }
            pushLog(content);
            const match = content.match(/nodes=(\d+), edges=(\d+)/);
            if (match) {
              const [_, nodeCount, edgeCount] = match;
              updateChatStatus(`✅ 流程图生成完成\n- 节点数: ${nodeCount}\n- 连线数: ${edgeCount}`);
            }
          } else if (content.startsWith("[END]")) {
            pushLog(content);
          } else if (content.startsWith("[ERROR]")) {
            pushLog(content);
            updateChatStatus(`❌ 生成失败: ${content.replace("[ERROR]", "").trim()}`);
          }

          // Accumulate tokens and display in logs area with typewriter effect
          if (content.startsWith("[TOKEN]")) {
            const token = content.replace("[TOKEN]", "").trimStart();
            updateJsonLog(token);
            continue;
          }

          // 🎬 流式渲染：布局数据
          if (content.startsWith("[LAYOUT_DATA]")) {
            try {
              const layoutData = JSON.parse(content.replace("[LAYOUT_DATA]", "").trim());
              let rawNodes = layoutData.nodes as Node[];
              const edges = layoutData.edges as Edge[];
              const diagramType = layoutData.diagram_type;
              const mermaidCode = layoutData.mermaid_code;

              let preparedNodes: Node[];

              // 只对 flow 类型应用自动布局
              if (diagramType === "flow") {
                const nodesWithSize = rawNodes.map((node) => {
                  const size = estimateNodeSize(node);
                  return { ...node, width: size.width, height: size.height };
                });

                const layoutedNodes = getLayoutedElements(nodesWithSize, edges, {
                  direction: "LR",
                  ranksep: 150,
                  nodesep: 100,
                });

                preparedNodes = addLayerFrames(layoutedNodes, diagramType);
              } else {
                // architecture 模式：使用原始坐标
                preparedNodes = addLayerFrames(rawNodes, diagramType);
              }

              // 存储准备好的数据，但先清空显示
              set({
                _preparedNodes: preparedNodes,
                _preparedEdges: edges,
                nodes: [],
                edges: [],
                mermaidCode,
              });

              console.log(`[LAYOUT_DATA] Prepared ${preparedNodes.length} nodes, ${edges.length} edges`);
            } catch (err) {
              console.error("[LAYOUT_DATA] Parse failed:", err);
            }
            continue;
          }

          // 🎬 流式渲染：显示节点
          if (content.startsWith("[NODE_SHOW]")) {
            const nodeId = content.replace("[NODE_SHOW]", "").trim();
            const preparedNodes = get()._preparedNodes;
            const node = preparedNodes.find((n) => n.id === nodeId);

            if (node) {
              const currentNodes = get().nodes;
              set({ nodes: [...currentNodes, node] });
              console.log(`[NODE_SHOW] Displayed node ${nodeId}`);
            }
            continue;
          }

          // 🎬 流式渲染：显示边
          if (content.startsWith("[EDGE_SHOW]")) {
            const edgeId = content.replace("[EDGE_SHOW]", "").trim();
            const preparedEdges = get()._preparedEdges;
            const edge = preparedEdges.find((e) => e.id === edgeId);

            if (edge) {
              const currentEdges = get().edges;
              set({ edges: [...currentEdges, edge] });
              console.log(`[EDGE_SHOW] Displayed edge ${edgeId}`);
            }
            continue;
          }

          // Fallback: 完整JSON payload（兼容旧版本）
          if (content.startsWith("{")) {
            try {
              const data = JSON.parse(content);
              if (data?.nodes && data?.edges) {
                let rawNodes = data.nodes as Node[];
                const edges = data.edges as Edge[];

                let nodes: Node[];

                // 只对 flow 类型应用自动布局，architecture 保持原始位置
                if (get().diagramType === "flow") {
                  // 🔥 应用智能布局算法
                  const nodesWithSize = rawNodes.map((node) => {
                    const size = estimateNodeSize(node);
                    return { ...node, width: size.width, height: size.height };
                  });

                  const layoutedNodes = getLayoutedElements(nodesWithSize, edges, {
                    direction: "LR",  // 默认左到右，更符合阅读习惯
                    ranksep: 150,
                    nodesep: 100,
                  });

                  // 添加分层框架（如果是架构图）
                  nodes = addLayerFrames(layoutedNodes, get().diagramType);
                } else {
                  // architecture 模式：使用后端返回的原始坐标
                  nodes = addLayerFrames(rawNodes, get().diagramType);
                }

                const mermaidCode = data.mermaid_code || get().mermaidCode;

                // 直接设置（fallback兼容）
                set({ nodes, edges, mermaidCode });
              }
            } catch {
              // ignore parse errors for non-JSON events
            }
          }
        }
      }

      // Stream ended, logs are already updated
      set({ generationLogs: [...logs] });

      // Fallback: if streaming didn't deliver nodes, retry non-stream
      if (get().nodes.length === 0) {
        const retry = await fetch("/api/chat-generator/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const data = await retry.json();
        if (data?.nodes && data?.edges) {
          let rawNodes = data.nodes as Node[];
          const edges = data.edges as Edge[];

          let nodes: Node[];

          // 只对 flow 类型应用自动布局，architecture 保持原始位置
          if (get().diagramType === "flow") {
            // 🔥 应用智能布局算法
            const nodesWithSize = rawNodes.map((node) => {
              const size = estimateNodeSize(node);
              return { ...node, width: size.width, height: size.height };
            });

            const layoutedNodes = getLayoutedElements(nodesWithSize, edges, {
              direction: "LR",  // 默认左到右
              ranksep: 150,
              nodesep: 100,
            });

            nodes = addLayerFrames(layoutedNodes, get().diagramType);
          } else {
            // architecture 模式：使用后端返回的原始坐标
            nodes = addLayerFrames(rawNodes, get().diagramType);
          }

          const mermaidCode = data.mermaid_code;

          // 直接设置（非stream fallback）
          set({ nodes, edges, mermaidCode });
        } else {
          throw new Error(data?.message || "Generation failed");
        }
      }
    } finally {
      set({ isGeneratingFlowchart: false });
    }
  },

  generateExcalidrawScene: async (prompt) => {
    set({ isGeneratingFlowchart: true });
    try {
      const { modelConfig } = get();

      const body = {
        prompt,
        style: "balanced",  // Use FlowPilot-compatible style system
        width: 1200,
        height: 800,
        provider: modelConfig.provider,
        api_key: modelConfig.apiKey?.trim() || undefined,
        base_url: modelConfig.baseUrl?.trim() || undefined,
        model_name: modelConfig.modelName,
      };

      const response = await fetch("/api/excalidraw/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Excalidraw generation failed");
      }

      const data = await response.json();

      if (!data.success) {
        throw new Error(data.message || "Generation failed");
      }

      // Store scene data to render in Excalidraw component
      if (data.scene) {
        set({ excalidrawScene: data.scene });
        console.log("Excalidraw scene saved to store:", data.scene.elements?.length, "elements");
      } else {
        throw new Error("No scene data in response");
      }

    } catch (error: any) {
      console.error("Excalidraw generation error:", error);
      throw error;
    } finally {
      set({ isGeneratingFlowchart: false });
    }
  },

  generateExcalidrawSceneStream: async (prompt) => {
    console.log("[Excalidraw] Starting generation for:", prompt.substring(0, 50));
    set({ isGeneratingFlowchart: true, generationLogs: [], excalidrawScene: null });

    try {
      const { modelConfig } = get();

      // 添加用户消息到聊天历史
      set((state) => ({
        chatHistory: [
          ...state.chatHistory,
          { role: "user", content: prompt },
        ],
      }));

      const body = {
        prompt,
        style: "balanced",
        width: 1200,
        height: 800,
        provider: modelConfig.provider,
        api_key: modelConfig.apiKey?.trim() || undefined,
        base_url: modelConfig.baseUrl?.trim() || undefined,
        model_name: modelConfig.modelName,
      };

      // IMPORTANT: Connect directly to backend to avoid Next.js proxy buffering
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
      const response = await fetch(`${backendUrl}/api/excalidraw/generate-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffered = "";
      let tokenCount = 0;

      const logs: string[] = [];
      const pushLog = (line: string) => {
        logs.push(line);
        // Throttle log updates to every 10 logs to reduce re-renders
        if (logs.length % 10 === 0) {
          setTimeout(() => set({ generationLogs: [...logs] }), 0);
        }
      };

      // Track generation status in chat history (打字机效果)
      let statusMessage = "🎨 正在生成 Excalidraw 场景...";
      let lastChatUpdate = Date.now();
      const updateChatStatus = (message: string, force = false) => {
        statusMessage = message;
        // Throttle chat updates to max once per 500ms unless forced
        const now = Date.now();
        if (!force && now - lastChatUpdate < 500) return;
        lastChatUpdate = now;

        setTimeout(() => {
          set((state) => {
            const newHistory = [...state.chatHistory];
            const last = newHistory[newHistory.length - 1];
            if (last && last.role === "assistant") {
              newHistory[newHistory.length - 1] = { role: "assistant", content: statusMessage };
            } else {
              newHistory.push({ role: "assistant", content: statusMessage });
            }
            return { chatHistory: newHistory };
          });
        }, 0);
      };

      // Accumulate JSON tokens for display in logs
      let jsonBuffer = "";
      let parsedElements: any[] = []; // Track already parsed elements for incremental rendering
      let hasReceivedFinalResult = false; // 🔥 Flag to prevent incremental updates after receiving final result
      const MAX_INCREMENTAL_ELEMENTS = 50; // ✅ Match backend's max_elems limit

      // Throttle scene updates using requestAnimationFrame
      let pendingSceneUpdate: any = null;
      let animationFrameId: number | null = null;

      const scheduleSceneUpdate = (elements: any[]) => {
        // 🔥 NEW: Don't schedule updates if we already have the final result
        if (hasReceivedFinalResult) {
          console.log(`⛔ [Excalidraw INCREMENTAL] Blocked incremental update (${elements.length} elements) - already have final result`);
          return;
        }

        console.log(`📊 [Excalidraw INCREMENTAL] Scheduling update with ${elements.length} elements`);
        pendingSceneUpdate = elements;

        if (animationFrameId === null) {
          animationFrameId = requestAnimationFrame(() => {
            // 🔥 NEW: Double-check flag before actually updating
            if (hasReceivedFinalResult) {
              console.log(`⛔ [Excalidraw INCREMENTAL] Cancelled scheduled update (had ${pendingSceneUpdate?.length} elements) - final result received`);
              animationFrameId = null;
              pendingSceneUpdate = null;
              return;
            }

            if (pendingSceneUpdate && pendingSceneUpdate.length > 0) {
              const partialScene = {
                elements: pendingSceneUpdate,
                appState: { viewBackgroundColor: "#ffffff" },
                files: {}
              };
              console.log(`✏️ [Excalidraw INCREMENTAL] Applying incremental update: ${pendingSceneUpdate.length} elements`);
              set({ excalidrawScene: partialScene });
            }
            animationFrameId = null;
            pendingSceneUpdate = null;
          });
        }
      };

      const updateJsonLog = (token: string) => {
        jsonBuffer += token;
        const generatingIndex = logs.findIndex(log => log.startsWith("[生成中]"));

        // Only update logs display every 50 tokens to reduce re-renders
        if (tokenCount % 50 === 0) {
          if (generatingIndex !== -1) {
            logs[generatingIndex] = `[生成中] ${jsonBuffer.substring(0, 200)}...`;
          } else {
            logs.push(`[生成中] ${jsonBuffer.substring(0, 200)}...`);
          }
          setTimeout(() => set({ generationLogs: [...logs] }), 0);
        }

        // Try to parse and render partial elements in real-time
        tryParseAndRenderPartialElements();
      };

      const tryParseAndRenderPartialElements = () => {
        try {
          // Strip markdown fences if present (AI sometimes returns ```json ... ```)
          let cleanBuffer = jsonBuffer.trim();
          if (cleanBuffer.startsWith('```json')) {
            cleanBuffer = cleanBuffer.substring('```json'.length).trim();
          } else if (cleanBuffer.startsWith('```')) {
            cleanBuffer = cleanBuffer.substring('```'.length).trim();
          }
          if (cleanBuffer.endsWith('```')) {
            cleanBuffer = cleanBuffer.substring(0, cleanBuffer.length - 3).trim();
          }

          // Try to extract completed elements from the JSON buffer
          // Look for pattern: "elements": [{ ... }, { ... },
          const elementsMatch = cleanBuffer.match(/"elements"\s*:\s*\[([\s\S]*)/);
          if (!elementsMatch) {
            return;
          }

          const elementsJson = elementsMatch[1];
          let depth = 0;
          let currentElement = "";
          let inString = false;
          let escape = false;
          let foundNewElement = false;
          let startedElement = false;

          for (let i = 0; i < elementsJson.length; i++) {
            const char = elementsJson[i];

            // Track string context to avoid false positives in strings
            if (char === '"' && !escape) {
              inString = !inString;
            }
            escape = char === '\\' && !escape;

            if (!inString) {
              if (char === '{') {
                depth++;
                if (depth === 1) {
                  // Start of a new element
                  startedElement = true;
                  currentElement = "";
                }
              }
              if (char === '}') {
                depth--;
              }
            }

            // Only accumulate if we're inside an element
            if (startedElement) {
              currentElement += char;
            }

            // Found a complete element (depth back to 0 after closing })
            if (startedElement && depth === 0 && char === '}') {
              try {
                const elementText = currentElement.trim();
                const element = JSON.parse(elementText);

                // ✅ Only add new elements (check if ID already exists) and respect max limit
                if (element.id &&
                    !parsedElements.some(e => e.id === element.id) &&
                    parsedElements.length < MAX_INCREMENTAL_ELEMENTS) {
                  parsedElements.push(element);
                  foundNewElement = true;

                  // Only log every 5th element to reduce console spam
                  if (parsedElements.length % 5 === 0 || parsedElements.length === 1) {
                    console.log(`[Excalidraw INCREMENTAL] ✅ Parsed ${parsedElements.length} elements`);
                  }
                } else if (parsedElements.length >= MAX_INCREMENTAL_ELEMENTS) {
                  // ⚠️ Stop parsing when we hit the limit (matches backend behavior)
                  console.warn(`[Excalidraw INCREMENTAL] ⚠️ Reached max limit of ${MAX_INCREMENTAL_ELEMENTS} elements`);
                }
              } catch (e) {
                // Element not yet complete or invalid JSON, continue silently
              }

              currentElement = "";
              startedElement = false;
            }
          }

          // Use throttled update if we found new elements
          // ✅ Batch updates: only update every 5 elements to reduce DOM updates
          if (foundNewElement && parsedElements.length > 0) {
            const shouldUpdate = (
              parsedElements.length === 1 ||        // First element
              parsedElements.length % 5 === 0 ||    // Every 5 elements
              parsedElements.length >= MAX_INCREMENTAL_ELEMENTS  // At limit
            );

            if (shouldUpdate) {
              scheduleSceneUpdate([...parsedElements]);
            }
          }
        } catch (e) {
          // Parsing failed, wait for more data (silent)
        }
      };

      // Initialize status message
      updateChatStatus(statusMessage, true);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        buffered += chunk;
        const parts = buffered.split("\n\n");
        buffered = parts.pop() || "";

        for (const part of parts) {
          const content = part.trim().replace(/^data:\s?/, "");
          if (!content) continue;

          if (content.startsWith("[START]")) {
            pushLog(content);
            updateChatStatus("📝 正在构建提示词...");
          } else if (content.startsWith("[CALL]")) {
            pushLog(content);
            updateChatStatus("🤖 AI 正在绘制场景...");
          } else if (content.startsWith("[TOKEN]")) {
            const token = content.replace("[TOKEN]", "").trimStart();
            tokenCount++;

            updateJsonLog(token);

            // 每 100 个 token 更新聊天状态
            if (tokenCount % 100 === 0) {
              updateChatStatus(`🤖 AI 正在绘制场景...\n已生成 ${tokenCount} tokens`);
            }
          } else if (content.startsWith("[RESULT]")) {
            // Remove "[生成中]" log
            const generatingIndex = logs.findIndex(log => log.startsWith("[生成中]"));
            if (generatingIndex !== -1) {
              logs.splice(generatingIndex, 1);
            }

            pushLog(content);
            const resultContent = content.replace("[RESULT]", "").trim();

            try {
              const result = JSON.parse(resultContent);
              console.log("🔍 [Excalidraw] Received [RESULT]:", {
                hasScene: !!result.scene,
                rawElementsCount: result.scene?.elements?.length || 0,
                incrementalParsedCount: parsedElements.length,
                success: result.success,
                message: result.message
              });

              if (result.scene?.elements) {
                // 🔥 CRITICAL FIX: Set flag FIRST to prevent race conditions
                hasReceivedFinalResult = true;
                console.log("🚫 [Excalidraw] hasReceivedFinalResult = true, blocking incremental updates");

                // Cancel any pending animation frame
                if (animationFrameId !== null) {
                  console.log("❌ [Excalidraw] Cancelling pending animation frame");
                  cancelAnimationFrame(animationFrameId);
                  animationFrameId = null;
                }

                // 🔍 DEBUG: Compare element IDs
                const incrementalIds = parsedElements.map((e: any) => e.id);
                const finalIds = result.scene.elements.map((e: any) => e.id);
                const missingIds = incrementalIds.filter((id: string) => !finalIds.includes(id));
                const newIds = finalIds.filter((id: string) => !incrementalIds.includes(id));

                if (missingIds.length > 0 || newIds.length > 0) {
                  console.warn("⚠️ [Excalidraw] Element ID mismatch detected:");
                  console.warn("  - Missing from final:", missingIds);
                  console.warn("  - New in final:", newIds);
                  console.warn("  - This causes the 'disappearing elements' bug!");
                }

                // ✅ SMART FIX: Only update if element IDs are different
                // If IDs match perfectly, keep the incremental version (has better properties)
                const shouldUpdate = (missingIds.length > 0 || newIds.length > 0);

                let finalElements;
                if (shouldUpdate) {
                  console.log("🔄 [Excalidraw] Using backend elements (IDs differ)");
                  finalElements = result.scene.elements;
                } else {
                  console.log("✅ [Excalidraw] Keeping incremental elements (IDs match perfectly)");
                  finalElements = parsedElements;
                }

                // CRITICAL FIX: Always use complete RESULT elements as the final data
                // Incremental parsing is only for intermediate display
                const finalScene = {
                  elements: finalElements,
                  appState: result.scene.appState || { viewBackgroundColor: "#ffffff" },
                  files: result.scene.files || {}
                };

                console.log("✅ [Excalidraw] Prepared final scene:", {
                  elementsCount: finalElements.length,
                  incrementalParsed: parsedElements.length,
                  source: shouldUpdate ? 'backend-validated' : 'incremental-kept',
                  firstElementIds: finalElements.slice(0, 5).map((e: any) => ({ id: e.id, type: e.type }))
                });

                // 🔥 NEW: Use setTimeout to ensure this update happens AFTER any pending animation frames
                setTimeout(() => {
                  console.log("📝 [Excalidraw] Setting final scene in store NOW");
                  set({ excalidrawScene: finalScene });
                  console.log("✅ [Excalidraw] Final scene set, incremental updates blocked");
                }, 0);

                const successMsg = result.success
                  ? `✅ Excalidraw 场景生成完成\n- 元素数量: ${result.scene.elements.length}\n- 增量解析: ${parsedElements.length} 个元素\n- 生成方式: ${parsedElements.length > 0 ? 'AI 实时流式生成' : 'AI 智能生成'}`
                  : `⚠️ 使用备用场景\n- 元素数量: ${result.scene.elements.length}\n- 原因: ${result.message || 'AI 生成失败'}`;

                updateChatStatus(successMsg, true);
              }
            } catch (e) {
              console.error("[Excalidraw] Failed to parse RESULT:", e);
            }
          } else if (content.startsWith("[END]")) {
            pushLog(content);
            // Final log update
            set({ generationLogs: [...logs] });
          } else if (content.startsWith("[ERROR]")) {
            pushLog(content);
            updateChatStatus(`❌ 生成失败: ${content.replace("[ERROR]", "").trim()}`, true);
            throw new Error(content.replace("[ERROR]", ""));
          }
        }
      }

      console.log("[Excalidraw] Stream completed");
    } catch (error: any) {
      console.error("[Excalidraw] Error:", error);
      set(state => ({
        generationLogs: [...state.generationLogs, `❌ Error: ${error.message}`],
        chatHistory: [
          ...state.chatHistory,
          { role: "assistant", content: `❌ 生成失败: ${error.message}` }
        ]
      }));
    } finally {
      console.log("[Excalidraw] Finally block: setting isGeneratingFlowchart = false");
      set({ isGeneratingFlowchart: false });
      console.log("[Excalidraw] Finally block: completed");
    }
  },

  loadPromptScenarios: async () => {
    try {
      const res = await fetch("/api/prompter/scenarios");
      if (!res.ok) {
        throw new Error(`Failed to load prompt scenarios: ${res.status}`);
      }
      const data = await res.json();
      if (data?.scenarios?.length) {
        set({ promptScenarios: data.scenarios });
        return;
      }
    } catch (error) {
      console.warn("Load prompt scenarios failed, fallback to defaults", error);
    }
    set({ promptScenarios: DEFAULT_PROMPT_SCENARIOS });
  },

  executePromptScenario: async (scenarioId, userInput) => {
    set({ isExecutingPrompt: true, promptError: undefined });
    try {
      const { modelConfig, nodes, edges } = get();
      const payload = {
        scenario_id: scenarioId,
        nodes,
        edges,
        user_input: userInput,
        mermaid_code: get().mermaidCode,
      };

      const params = new URLSearchParams();
      params.set("provider", modelConfig.provider);
      if (modelConfig.apiKey) params.set("api_key", modelConfig.apiKey);
      if (modelConfig.baseUrl) params.set("base_url", modelConfig.baseUrl);
      if (modelConfig.modelName) params.set("model_name", modelConfig.modelName);

      const res = await fetch(`/api/prompter/execute?${params.toString()}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const detail = await res.text();
        throw new Error(detail || "Prompter failed");
      }

      const data = await res.json();
      if (!data?.success) {
        throw new Error(data?.message || "Prompter failed");
      }

      const updatedNodes = addLayerFrames(data.nodes as Node[], get().diagramType);
      const updatedEdges = data.edges as Edge[];
      const updatedMermaid = data.mermaid_code || get().mermaidCode;

      set({ nodes: updatedNodes, edges: updatedEdges, mermaidCode: updatedMermaid });
      set((state) => ({
        chatHistory: [
          ...state.chatHistory,
          { role: "assistant", content: data.ai_explanation || "Architecture transformed." },
        ],
      }));
    } catch (e: any) {
      set({ promptError: e?.message || "Execution failed" });
      throw e;
    } finally {
      set({ isExecutingPrompt: false });
    }
  },

  applyMockScenario: (scenarioId) => {
    const nodes = get().nodes.map((node, idx) =>
      idx === 0 ? { ...node, data: { ...(node.data as any), label: `${(node.data as any).label} (${scenarioId})` } } : node
    );
    set({ nodes });
    get().updateFromCanvas();
  },
}));
