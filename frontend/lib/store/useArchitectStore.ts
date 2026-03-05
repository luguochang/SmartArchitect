import { create } from "zustand";
import { Node, Edge, NodeChange, EdgeChange, applyNodeChanges, applyEdgeChanges, MarkerType } from "reactflow";
import { PROVIDER_DEFAULTS } from "@/lib/config/providerDefaults";
import { getLayoutedElements, estimateNodeSize } from "@/lib/utils/autoLayout";
import { API_ENDPOINTS, API_BASE_URL } from "@/lib/api-config";
import { useFlowchartStyleStore } from "@/lib/stores/flowchartStyleStore";

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
export type ArchitectureType = "layered" | "business" | "technical" | "deployment" | "domain";

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
  architectureType: ArchitectureType;
  setArchitectureType: (type: ArchitectureType) => void;
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

  // 棣冨箑 濞翠礁绱″〒鍙夌厠閻樿埖鈧?
  _preparedNodes: Node[]; // 閸戝棗顦總鐣屾畱閼哄倻鍋ｉ敍鍫濆嚒鐢啫鐪担鍡樻弓閺勫墽銇氶敍?
  _preparedEdges: Edge[]; // 閸戝棗顦總鐣屾畱鏉堢櫢绱欓張顏呮▔缁€鐚寸礆

  // 閼哄倻鍋ｉ崪宀冪珶閹垮秳缍?
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  updateNodeData: (id: string, data: Partial<Node["data"]>) => void;
  updateNodeLabel: (id: string, label: string) => void;
  uploadImage: (file: File) => void;
  clearImage: () => void;
  analyzeImage: () => Promise<void>;

  // Mermaid 娴狅絿鐖滈幙宥勭稊
  setMermaidCode: (code: string) => void;
  updateFromMermaid: (code: string) => void;
  updateFromCanvas: () => void;

  // AI 濡€崇€烽柊宥囩枂
  modelConfig: {
    provider: "custom";
    apiKey: string;
    modelName: string;
    baseUrl: string;
  };
  setModelConfig: (config: Partial<ArchitectState["modelConfig"]>) => void;

  // 濞翠胶鈻奸悽鐔稿灇閿涘湧hase 5 mock閿?
  flowTemplates: FlowTemplate[];
  isGeneratingFlowchart: boolean;
  loadFlowTemplates: () => Promise<void>;
  generateFlowchart: (input: string, templateId?: string, diagramType?: DiagramType) => Promise<void>;
  generateExcalidrawScene: (prompt: string) => Promise<void>;
  generateExcalidrawSceneStream: (prompt: string) => Promise<void>;

  // 棣冨晭 婢х偤鍣洪悽鐔稿灇閻樿埖鈧?
  incrementalMode: boolean;
  currentSessionId: string | null;
  setIncrementalMode: (enabled: boolean) => void;
  saveCanvasSession: () => Promise<string | null>;
  loadCanvasSession: (sessionId: string) => Promise<void>;
  deleteCanvasSession: () => Promise<void>;

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
    name: "Microservice Fulfillment Flow",
    description: "API Gateway -> Auth -> Cache -> Order Service -> Queue -> Inventory Service",
    example_input: "Generate an e-commerce request flow with auth, cache, order, queue, inventory, and storage.",
    category: "architecture",
  },
  {
    id: "high-concurrency-system",
    name: "High Concurrency Path",
    description: "Rate limit + stock pre-deduction + queue decoupling + durable write path",
    example_input: "Design a flash-sale system flow with throttling, cache hit path, queue buffering, and order persistence.",
    category: "architecture",
  },
  {
    id: "incident-response",
    name: "Incident Response Workflow",
    description: "Detect -> triage -> rollback -> RCA -> postmortem",
    example_input: "Generate an incident response flow including detection, alerting, manual verification, rollback, and review.",
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

// 鐏?React Flow 閼哄倻鍋ｉ崪宀冪珶鏉烆剚宕叉稉?Mermaid 娴狅絿鐖?
function canvasToMermaid(nodes: Node[], edges: Edge[]): string {
  let mermaidCode = "graph TD\n";

  // 濞ｈ濮為懞鍌滃仯
  nodes.forEach((node) => {
    const nodeId = node.id;
    const label = (node.data as any)?.label || nodeId;
    const nodeType = node.type || "default";

    // 閺嶈宓侀懞鍌滃仯缁鐎烽柅澶嬪娑撳秴鎮撻惃?Mermaid 缁楋箑褰?
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

  // 濞ｈ濮炴潻鐐村复
  edges.forEach((edge) => {
    const label = edge.label ? `|${edge.label}|` : "";
    mermaidCode += `    ${edge.source} -->${label} ${edge.target}\n`;
  });

  return mermaidCode;
}

// 鐏?Mermaid 娴狅絿鐖滅憴锝嗙€芥稉?React Flow 閼哄倻鍋ｉ崪宀冪珶閿涘牏鐣濋崠鏍閿?
function mermaidToCanvas(code: string): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const lines = code.split("\n");
  let yOffset = 0;

  lines.forEach((line, index) => {
    line = line.trim();

    // 鐠哄疇绻冪粚楦款攽閸?graph 婢圭増妲?
    if (!line || line.startsWith("graph")) return;

    // 缁犫偓閸楁洜娈戦懞鍌滃仯鐎规矮绠熺憴锝嗙€? nodeId["label"] 閹?nodeId[("label")]
    const nodeMatch = line.match(/(\w+)\[([^\]]+)\]/);
    if (nodeMatch) {
      const [, nodeId, labelPart] = nodeMatch;
      const label = labelPart.replace(/["\(\)]/g, "").trim();

      // 绾喖鐣鹃懞鍌滃仯缁鐎?
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

    // 缁犫偓閸楁洜娈戞潏鐟扮暰娑斿袙閺? source --> target 閹?source -->|label| target
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

// 缂佹瑨绔熸惔鏃傛暏瑜版挸澧犻惃鍕壉瀵繘鍘ょ純?
function applyEdgeStyles(edges: Edge[]): Edge[] {
  const { currentPresentationStyle, edgeType } = useFlowchartStyleStore.getState();

  return edges.map((edge) => ({
    ...edge,
    type: edgeType,
    animated: false, // 棣冩暉 娣囶喖顦查敍姘暭娑撳搫鐤勭痪鍖＄礉娑撳秳濞囬悽銊ュЗ閻㈢粯鏅ラ弸?
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
      ...edge.data,
      showGlow: currentPresentationStyle.edge.showGlow,
    },
  }));
}

export const useArchitectStore = create<ArchitectState>((set, get) => ({
  nodes: [],
  edges: [],
  diagramType: "flow",
  architectureType: "layered",
  mermaidCode: "",
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

  // 棣冨箑 濞翠礁绱″〒鍙夌厠閻樿埖鈧礁鍨垫慨瀣
  _preparedNodes: [],
  _preparedEdges: [],

  // 棣冨晭 婢х偤鍣洪悽鐔稿灇閻樿埖鈧礁鍨垫慨瀣
  incrementalMode: false,
  currentSessionId: null,

  promptScenarios: DEFAULT_PROMPT_SCENARIOS,
  isExecutingPrompt: false,
  promptError: undefined,

  modelConfig: {
    provider: "custom",
    apiKey: "", // 棣冩暋 娴犲酣鍘ょ純顔绢吀閻炲棔鑵戦崝鐘烘祰閿涘奔绗夋担璺ㄦ暏绾剛绱惍?
    modelName: "",
    baseUrl: "",
  },

  setCanvasMode: (mode) => set({ canvasMode: mode }),
  setExcalidrawScene: (scene) => set({ excalidrawScene: scene }),
  setArchitectureType: (type) => set({ architectureType: type }),

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
    // 閼哄倻鍋ｉ崣妯哄閸氬氦鍤滈崝銊︽纯閺?Mermaid 娴狅絿鐖?
    get().updateFromCanvas();
  },

  onEdgesChange: (changes) => {
    set({
      edges: applyEdgeChanges(changes, get().edges),
    });
    // 鏉堢懓褰夐崠鏍ф倵閼奉亜濮╅弴瀛樻煀 Mermaid 娴狅絿鐖?
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
      const res = await fetch(API_ENDPOINTS.chatTemplates);
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

  // ============================================================
  // 棣冨晭 婢х偤鍣洪悽鐔稿灇娴兼俺鐦界粻锛勬倞閺傝纭?
  // ============================================================

  setIncrementalMode: (enabled) => {
    set({ incrementalMode: enabled });

    // 閸氼垳鏁ゆ晶鐐哄櫤濡€崇础閺冭绱濋懛顏勫З娣囨繂鐡ㄨぐ鎾冲閻㈣绔烽崚棰佺窗鐠?
    if (enabled && get().nodes.length > 0) {
      get().saveCanvasSession();
    }
  },

  saveCanvasSession: async () => {
    const { nodes, edges, currentSessionId } = get();

    if (nodes.length === 0) {
      return null;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/chat-generator/session/save`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionId,
          nodes,
          edges,
        }),
      });

      const data = await response.json();

      if (data.success) {
        set({ currentSessionId: data.session_id });
        console.log(`Canvas session saved: ${data.session_id}`);
        return data.session_id;
      }
    } catch (error) {
      console.error("Failed to save canvas session:", error);
    }

    return null;
  },

  loadCanvasSession: async (sessionId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/chat-generator/session/${sessionId}`);
      const data = await response.json();

      if (data.success && data.session) {
        set({
          nodes: data.session.nodes,
          edges: data.session.edges,
          currentSessionId: sessionId,
        });
        console.log(`Canvas session loaded: ${sessionId}`);
      }
    } catch (error) {
      console.error("Failed to load canvas session:", error);
    }
  },

  deleteCanvasSession: async () => {
    const { currentSessionId } = get();

    if (!currentSessionId) {
      return;
    }

    try {
      await fetch(`${API_BASE_URL}/api/chat-generator/session/${currentSessionId}`, {
        method: "DELETE",
      });

      set({ currentSessionId: null, incrementalMode: false });
      console.log(`Canvas session deleted: ${currentSessionId}`);
    } catch (error) {
      console.error("Failed to delete canvas session:", error);
    }
  },

  generateFlowchart: async (input, templateId, diagramType) => {
    set({ isGeneratingFlowchart: true, diagramType: diagramType || "flow" });
    try {
      const { modelConfig, architectureType, incrementalMode, currentSessionId, nodes, saveCanvasSession } = get();
      set((state) => ({
        generationLogs: [],
        chatHistory: [...state.chatHistory, { role: "user", content: input }],
      }));

      const shouldResetCanvas = !(incrementalMode && nodes.length > 0);
      if (shouldResetCanvas) {
        set({
          nodes: [],
          edges: [],
          _preparedNodes: [],
          _preparedEdges: [],
          mermaidCode: "",
        });
      }

      let sessionId = currentSessionId;
      if (incrementalMode && nodes.length > 0 && !sessionId) {
        sessionId = await saveCanvasSession();
      }

      const body = {
        user_input: input,
        template_id: templateId,
        diagram_type: diagramType,
        architecture_type: diagramType === "architecture" ? architectureType : undefined,
        provider: modelConfig.provider,
        api_key: modelConfig.apiKey?.trim() || undefined,
        base_url: modelConfig.baseUrl?.trim() || undefined,
        model_name: modelConfig.modelName,
        incremental_mode: incrementalMode && nodes.length > 0,
        session_id: sessionId,
      };

      const response = await fetch(API_ENDPOINTS.chatGeneratorStream, {
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
        if (
          logs.length % 8 === 0 ||
          line.startsWith("[ERROR]") ||
          line.startsWith("[RESULT]") ||
          line.startsWith("[WARN]") ||
          line.startsWith("[END]")
        ) {
          setTimeout(() => set({ generationLogs: [...logs] }), 0);
        }
      };

      let statusMessage = "馃 姝ｅ湪鐢熸垚娴佺▼鍥?..";
      let aiResponseBuffer = "";
      let jsonBuffer = "";
      let lastStatusUpdateAt = 0;
      let lastJsonLogAt = 0;
      let lastAiUpdateAt = 0;

      const updateChatStatus = (message: string, force = false) => {
        const now = Date.now();
        if (!force && now - lastStatusUpdateAt < 180 && message !== statusMessage) {
          statusMessage = message;
          return;
        }
        lastStatusUpdateAt = now;
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

      const updateAiResponse = (token: string) => {
        aiResponseBuffer += token;
        const now = Date.now();
        if (now - lastAiUpdateAt < 150) return;
        lastAiUpdateAt = now;

        const preview = aiResponseBuffer.length > 2400
          ? `...${aiResponseBuffer.slice(-2400)}`
          : aiResponseBuffer;
        set((state) => {
          const newHistory = [...state.chatHistory];
          const last = newHistory[newHistory.length - 1];
          const content = `馃 AI 姝ｅ湪鐢熸垚...\n\n${preview}`;
          if (last && last.role === "assistant") {
            newHistory[newHistory.length - 1] = { role: "assistant", content };
          } else {
            newHistory.push({ role: "assistant", content });
          }
          return { chatHistory: newHistory };
        });
      };

      const updateJsonLog = (token: string) => {
        jsonBuffer += token;
        const now = Date.now();
        if (now - lastJsonLogAt < 250) return;
        lastJsonLogAt = now;

        const preview = jsonBuffer.length > 3200
          ? `...${jsonBuffer.slice(-3200)}`
          : jsonBuffer;
        const generatingIndex = logs.findIndex((log) => log.startsWith("[鐢熸垚涓璢"));
        if (generatingIndex !== -1) {
          logs[generatingIndex] = `[鐢熸垚涓璢 ${preview}`;
        } else {
          logs.push(`[鐢熸垚涓璢 ${preview}`);
        }
        setTimeout(() => set({ generationLogs: [...logs] }), 0);
      };

      let hasLayoutData = false;
      let sawPartialGraphEvents = false;
      const partialNodeMap = new Map<string, Node>();
      const partialEdgeMap = new Map<string, Edge>();
      let partialFlushScheduled = false;

      const schedulePartialFlush = () => {
        if (partialFlushScheduled) return;
        partialFlushScheduled = true;

        const flush = () => {
          partialFlushScheduled = false;
          const visibleNodes = Array.from(partialNodeMap.values());
          const visibleNodeIds = new Set(visibleNodes.map((n) => n.id));
          const visibleEdges = Array.from(partialEdgeMap.values()).filter(
            (edge) => visibleNodeIds.has(edge.source) && visibleNodeIds.has(edge.target)
          );
          set({ nodes: visibleNodes, edges: visibleEdges });
        };

        if (typeof window !== "undefined" && typeof window.requestAnimationFrame === "function") {
          window.requestAnimationFrame(flush);
        } else {
          setTimeout(flush, 0);
        }
      };

      const normalizePartialNode = (payload: any): Node | null => {
        if (!payload || typeof payload !== "object") return null;

        const fallbackIndex = partialNodeMap.size;
        const id = (typeof payload.id === "string" && payload.id.trim())
          ? payload.id.trim()
          : `partial-node-${fallbackIndex + 1}`;

        const nodeType = (typeof payload.type === "string" && payload.type.trim())
          ? payload.type.trim()
          : "default";

        const rawPosition = payload.position && typeof payload.position === "object" ? payload.position : {};
        const x = Number.isFinite(rawPosition.x)
          ? Number(rawPosition.x)
          : 120 + (fallbackIndex % 4) * 260;
        const y = Number.isFinite(rawPosition.y)
          ? Number(rawPosition.y)
          : 120 + Math.floor(fallbackIndex / 4) * 180;

        const rawData = payload.data && typeof payload.data === "object" ? payload.data : {};
        const label = (typeof rawData.label === "string" && rawData.label.trim())
          ? rawData.label.trim()
          : id;

        return {
          id,
          type: nodeType,
          position: { x, y },
          data: { ...rawData, label },
        };
      };

      const normalizePartialEdge = (payload: any): Edge | null => {
        if (!payload || typeof payload !== "object") return null;

        const source = typeof payload.source === "string" ? payload.source.trim() : "";
        const target = typeof payload.target === "string" ? payload.target.trim() : "";
        if (!source || !target) return null;

        const fallbackIndex = partialEdgeMap.size;
        const id = (typeof payload.id === "string" && payload.id.trim())
          ? payload.id.trim()
          : `partial-edge-${fallbackIndex + 1}`;

        const edgePayload: Edge = {
          id,
          source,
          target,
          ...(typeof payload.label === "string" && payload.label.trim() ? { label: payload.label.trim() } : {}),
        };

        return applyEdgeStyles([edgePayload])[0];
      };

      updateChatStatus(statusMessage);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffered += decoder.decode(value, { stream: true });
        const parts = buffered.split("\n\n");
        buffered = parts.pop() || "";

        for (const part of parts) {
          const cleaned = part.trim();
          if (!cleaned.startsWith("data:")) continue;
          const content = cleaned.replace(/^data:\s?/, "");

          if (content.startsWith("[START]")) {
            pushLog(content);
            updateChatStatus("馃數 姝ｅ湪鏋勫缓鎻愮ず璇?..");
            continue;
          }

          if (content.startsWith("[CALL]")) {
            pushLog(content);
            updateChatStatus("馃 AI 姝ｅ湪鐢熸垚娴佺▼鍥?..");
            if (!logs.some((log) => log.startsWith("[鐢熸垚涓璢"))) {
              pushLog("[鐢熸垚涓璢 ");
            }
            continue;
          }

          if (content.startsWith("[PROGRESS]")) {
            pushLog(content);
            const progress = content.replace("[PROGRESS]", "").trim();
            updateChatStatus(`馃 AI 姝ｅ湪鐢熸垚娴佺▼鍥?..\n${progress}`);
            continue;
          }

          if (content.startsWith("[SESSION]")) {
            const streamedSessionId = content.replace("[SESSION]", "").trim();
            if (streamedSessionId) {
              set({ currentSessionId: streamedSessionId });
            }
            continue;
          }

          if (content.startsWith("[RESULT]")) {
            const generatingIndex = logs.findIndex((log) => log.startsWith("[鐢熸垚涓璢"));
            if (generatingIndex !== -1) {
              logs.splice(generatingIndex, 1);
            }
            pushLog(content);
            const match = content.match(/nodes=(\d+), edges=(\d+)/);
            if (match) {
              const [, nodeCount, edgeCount] = match;
              updateChatStatus(`鉁?娴佺▼鍥剧敓鎴愬畬鎴怽n- 鑺傜偣鏁? ${nodeCount}\n- 杩炵嚎鏁? ${edgeCount}`, true);
            }
            continue;
          }

          if (content.startsWith("[END]")) {
            pushLog(content);
            continue;
          }

          if (content.startsWith("[WARN]")) {
            pushLog(content);
            continue;
          }

          if (content.startsWith("[ERROR]")) {
            pushLog(content);
            updateChatStatus(`鉂?鐢熸垚澶辫触: ${content.replace("[ERROR]", "").trim()}`, true);
            continue;
          }

          if (content.startsWith("[TOKEN]")) {
            const token = content.replace("[TOKEN]", "").trimStart();
            updateJsonLog(token);
            updateAiResponse(token);
            continue;
          }

          if (content.startsWith("[PARTIAL_NODE]")) {
            try {
              const payload = JSON.parse(content.replace("[PARTIAL_NODE]", "").trim());
              const node = normalizePartialNode(payload);
              if (node) {
                sawPartialGraphEvents = true;
                partialNodeMap.set(node.id, node);
                schedulePartialFlush();
              }
            } catch (err) {
              console.warn("[PARTIAL_NODE] parse failed:", err);
            }
            continue;
          }

          if (content.startsWith("[PARTIAL_EDGE]")) {
            try {
              const payload = JSON.parse(content.replace("[PARTIAL_EDGE]", "").trim());
              const edge = normalizePartialEdge(payload);
              if (edge) {
                sawPartialGraphEvents = true;
                partialEdgeMap.set(edge.id, edge);
                schedulePartialFlush();
              }
            } catch (err) {
              console.warn("[PARTIAL_EDGE] parse failed:", err);
            }
            continue;
          }

          if (content.startsWith("[LAYOUT_DATA]")) {
            try {
              hasLayoutData = true;
              const layoutData = JSON.parse(content.replace("[LAYOUT_DATA]", "").trim());
              const rawNodes = layoutData.nodes as Node[];
              const rawEdges = layoutData.edges as Edge[];
              const finalDiagramType = layoutData.diagram_type;
              const mermaidCode = layoutData.mermaid_code;

              const edges = applyEdgeStyles(rawEdges);
              let preparedNodes: Node[];

              if (finalDiagramType === "flow") {
                const nodesWithSize = rawNodes.map((node) => {
                  const size = estimateNodeSize(node);
                  return { ...node, width: size.width, height: size.height };
                });

                const layoutedNodes = getLayoutedElements(nodesWithSize, edges, {
                  direction: "LR",
                  ranksep: 150,
                  nodesep: 100,
                });
                preparedNodes = addLayerFrames(layoutedNodes, finalDiagramType);
              } else {
                preparedNodes = addLayerFrames(rawNodes, finalDiagramType);
              }

              const shouldDirectFinalize = sawPartialGraphEvents || partialNodeMap.size > 0 || partialEdgeMap.size > 0;
              set({
                _preparedNodes: preparedNodes,
                _preparedEdges: edges,
                nodes: shouldDirectFinalize ? preparedNodes : [],
                edges: shouldDirectFinalize ? edges : [],
                mermaidCode,
              });
            } catch (err) {
              console.error("[LAYOUT_DATA] Parse failed:", err);
            }
            continue;
          }

          if (content.startsWith("[NODE_SHOW]")) {
            if (sawPartialGraphEvents) {
              continue;
            }
            const nodeId = content.replace("[NODE_SHOW]", "").trim();
            const preparedNodes = get()._preparedNodes;
            const node = preparedNodes.find((n) => n.id === nodeId);
            if (node) {
              const currentNodes = get().nodes;
              set({ nodes: [...currentNodes, node] });
            }
            continue;
          }

          if (content.startsWith("[EDGE_SHOW]")) {
            if (sawPartialGraphEvents) {
              continue;
            }
            const edgeId = content.replace("[EDGE_SHOW]", "").trim();
            const preparedEdges = get()._preparedEdges;
            const edge = preparedEdges.find((e) => e.id === edgeId);
            if (edge) {
              const currentEdges = get().edges;
              set({ edges: [...currentEdges, edge] });
            }
            continue;
          }

          if (content.startsWith("{")) {
            try {
              const data = JSON.parse(content);
              if (data?.nodes && data?.edges) {
                hasLayoutData = true;
                const rawNodes = data.nodes as Node[];
                const rawEdges = data.edges as Edge[];
                const edges = applyEdgeStyles(rawEdges);

                let finalNodes: Node[];
                if (get().diagramType === "flow") {
                  const nodesWithSize = rawNodes.map((node) => {
                    const size = estimateNodeSize(node);
                    return { ...node, width: size.width, height: size.height };
                  });
                  const layoutedNodes = getLayoutedElements(nodesWithSize, edges, {
                    direction: "LR",
                    ranksep: 150,
                    nodesep: 100,
                  });
                  finalNodes = addLayerFrames(layoutedNodes, get().diagramType);
                } else {
                  finalNodes = addLayerFrames(rawNodes, get().diagramType);
                }

                const mermaidCode = data.mermaid_code || get().mermaidCode;
                set({ nodes: finalNodes, edges, mermaidCode });
              }
            } catch {
              // ignore parse errors for non-JSON events
            }
          }
        }
      }

      set({ generationLogs: [...logs] });

      if (!hasLayoutData) {
        const retry = await fetch(API_ENDPOINTS.chatGenerator, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const data = await retry.json();

        if (data?.nodes && data?.edges) {
          const rawNodes = data.nodes as Node[];
          const rawEdges = data.edges as Edge[];
          const edges = applyEdgeStyles(rawEdges);

          let finalNodes: Node[];
          if (get().diagramType === "flow") {
            const nodesWithSize = rawNodes.map((node) => {
              const size = estimateNodeSize(node);
              return { ...node, width: size.width, height: size.height };
            });
            const layoutedNodes = getLayoutedElements(nodesWithSize, edges, {
              direction: "LR",
              ranksep: 150,
              nodesep: 100,
            });
            finalNodes = addLayerFrames(layoutedNodes, get().diagramType);
          } else {
            finalNodes = addLayerFrames(rawNodes, get().diagramType);
          }

          set({ nodes: finalNodes, edges, mermaidCode: data.mermaid_code });
          if (data.session_id) {
            set({ currentSessionId: data.session_id });
          }
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
        width: 1800,
        height: 1200,
        provider: modelConfig.provider,
        api_key: modelConfig.apiKey?.trim() || undefined,
        base_url: modelConfig.baseUrl?.trim() || undefined,
        model_name: modelConfig.modelName,
      };

      const response = await fetch(API_ENDPOINTS.excalidrawGenerate, {
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
    set({ isGeneratingFlowchart: true, generationLogs: [], excalidrawScene: null });

    try {
      const { modelConfig } = get();
      set((state) => ({
        chatHistory: [...state.chatHistory, { role: "user", content: prompt }],
      }));

      const body = {
        prompt,
        style: "balanced",
        width: 1800,
        height: 1200,
        provider: modelConfig.provider,
        api_key: modelConfig.apiKey?.trim() || undefined,
        base_url: modelConfig.baseUrl?.trim() || undefined,
        model_name: modelConfig.modelName,
      };

      const response = await fetch(`${API_BASE_URL}/api/excalidraw/generate-stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify(body),
      });

      if (!response.ok || !response.body) {
        const detail = await response.text();
        throw new Error(detail || `HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffered = "";

      const logs: string[] = [];
      const pushLog = (line: string) => {
        logs.push(line);
        if (logs.length % 6 === 0 || line.startsWith("[ERROR]") || line.startsWith("[RESULT]")) {
          setTimeout(() => set({ generationLogs: [...logs] }), 0);
        }
      };

      let aiResponseBuffer = "";
      let lastChatUpdate = 0;
      let currentStatus = "Starting Excalidraw generation...";
      let partialElementsCount = 0;
      let hasFinalResult = false;
      const partialElements = new Map<string, any>();
      let partialFlushScheduled = false;

      const updateChatStatus = (message: string, force = false) => {
        currentStatus = message;
        const now = Date.now();
        if (!force && now - lastChatUpdate < 250) return;
        lastChatUpdate = now;

        setTimeout(() => {
          set((state) => {
            const newHistory = [...state.chatHistory];
            const last = newHistory[newHistory.length - 1];
            if (last && last.role === "assistant") {
              newHistory[newHistory.length - 1] = { role: "assistant", content: currentStatus };
            } else {
              newHistory.push({ role: "assistant", content: currentStatus });
            }
            return { chatHistory: newHistory };
          });
        }, 0);
      };

      const updateAiResponse = (token: string) => {
        aiResponseBuffer += token;
        const now = Date.now();
        if (now - lastChatUpdate < 120) return;
        lastChatUpdate = now;

        setTimeout(() => {
          set((state) => {
            const newHistory = [...state.chatHistory];
            const last = newHistory[newHistory.length - 1];
            const content = `AI is generating Excalidraw JSON...\n\n${aiResponseBuffer}`;
            if (last && last.role === "assistant") {
              newHistory[newHistory.length - 1] = { role: "assistant", content };
            } else {
              newHistory.push({ role: "assistant", content });
            }
            return { chatHistory: newHistory };
          });
        }, 0);
      };

      const schedulePartialSceneFlush = () => {
        if (partialFlushScheduled || hasFinalResult) return;
        partialFlushScheduled = true;

        const flush = () => {
          partialFlushScheduled = false;
          if (hasFinalResult) return;

          const elements = Array.from(partialElements.values());
          if (!elements.length) return;

          set({
            excalidrawScene: {
              elements,
              appState: { viewBackgroundColor: "#ffffff", __streaming: true },
              files: {},
            },
          });
        };

        if (typeof window !== "undefined" && typeof window.requestAnimationFrame === "function") {
          window.requestAnimationFrame(flush);
        } else {
          setTimeout(flush, 0);
        }
      };

      updateChatStatus(currentStatus, true);

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffered += decoder.decode(value, { stream: true });
        const parts = buffered.split("\n\n");
        buffered = parts.pop() || "";

        for (const part of parts) {
          const cleaned = part.trim();
          if (!cleaned.startsWith("data:")) continue;
          const content = cleaned.replace(/^data:\s?/, "");
          if (!content) continue;

          if (content.startsWith("[START]")) {
            pushLog(content);
            updateChatStatus("Preparing Excalidraw prompt...");
            continue;
          }

          if (content.startsWith("[CALL]")) {
            pushLog(content);
            updateChatStatus("Calling model and streaming elements...");
            continue;
          }

          if (content.startsWith("[TOKEN]")) {
            const token = content.replace("[TOKEN]", "").trimStart();
            updateAiResponse(token);
            continue;
          }

          if (content.startsWith("[PARTIAL_ELEMENT]")) {
            try {
              const element = JSON.parse(content.replace("[PARTIAL_ELEMENT]", "").trim());
              if (element && typeof element.id === "string") {
                partialElements.set(element.id, element);
                partialElementsCount = partialElements.size;
                schedulePartialSceneFlush();
                if (partialElementsCount % 4 === 0 || partialElementsCount === 1) {
                  updateChatStatus(`Streaming diagram... ${partialElementsCount} elements drawn`);
                }
              }
            } catch (err) {
              console.warn("[Excalidraw] PARTIAL_ELEMENT parse failed:", err);
            }
            continue;
          }

          if (content.startsWith("[PROGRESS]")) {
            pushLog(content);
            const progress = content.replace("[PROGRESS]", "").trim();
            updateChatStatus(`Generating diagram... ${progress}`);
            continue;
          }

          if (content.startsWith("[WARN]")) {
            pushLog(content);
            updateChatStatus(content.replace("[WARN]", "").trim());
            continue;
          }

          if (content.startsWith("[RESULT]")) {
            pushLog(content);
            const payload = content.replace("[RESULT]", "").trim();
            try {
              const result = JSON.parse(payload);
              hasFinalResult = true;

              const scene = result?.scene;
              if (scene?.elements && Array.isArray(scene.elements)) {
                set({
                  excalidrawScene: {
                    elements: scene.elements,
                    appState: {
                      ...(scene.appState || {}),
                      viewBackgroundColor: "#ffffff",
                      __streaming: false,
                    },
                    files: scene.files || {},
                  },
                });
              }

              const finalElements = scene?.elements?.length || 0;
              const success = Boolean(result?.success);
              const statusText = success
                ? `Excalidraw generated successfully\n- Final elements: ${finalElements}\n- Streamed partial elements: ${partialElementsCount}`
                : `Excalidraw generation returned fallback\n- Elements: ${finalElements}\n- Message: ${result?.message || "Unknown"}`;
              updateChatStatus(statusText, true);
            } catch (err) {
              console.error("[Excalidraw] RESULT parse failed:", err);
              throw new Error("Invalid [RESULT] payload from stream");
            }
            continue;
          }

          if (content.startsWith("[ERROR]")) {
            pushLog(content);
            throw new Error(content.replace("[ERROR]", "").trim() || "Excalidraw generation failed");
          }

          if (content.startsWith("[END]")) {
            pushLog(content);
            continue;
          }
        }
      }

      set({ generationLogs: [...logs] });
    } catch (error: any) {
      set((state) => ({
        generationLogs: [...state.generationLogs, `Error: ${error?.message || "unknown error"}`],
        chatHistory: [
          ...state.chatHistory,
          { role: "assistant", content: `Generation failed: ${error?.message || "unknown error"}` },
        ],
      }));
      throw error;
    } finally {
      set({ isGeneratingFlowchart: false });
    }
  },
  loadPromptScenarios: async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/prompter/scenarios`);
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

      const res = await fetch(`${API_BASE_URL}/api/prompter/execute?${params.toString()}`, {
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
      const rawEdges = data.edges as Edge[];

      // 鎼存梻鏁よぐ鎾冲閺嶅嘲绱￠崚鎷岀珶
      const updatedEdges = applyEdgeStyles(rawEdges);

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



