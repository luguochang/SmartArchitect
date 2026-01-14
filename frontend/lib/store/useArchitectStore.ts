import { create } from "zustand";
import { Node, Edge, NodeChange, EdgeChange, applyNodeChanges, applyEdgeChanges } from "reactflow";

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

  // Canvas mode
  canvasMode: CanvasMode;
  setCanvasMode: (mode: CanvasMode) => void;

  // Excalidraw scene
  excalidrawScene: ExcalidrawScene | null;
  setExcalidrawScene: (scene: ExcalidrawScene | null) => void;

  // 节点和边操作
  setNodes: (nodes: Node[]) => void;
  setEdges: (edges: Edge[]) => void;
  onNodesChange: (changes: NodeChange[]) => void;
  onEdgesChange: (changes: EdgeChange[]) => void;
  updateNodeLabel: (id: string, label: string) => void;

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
  mermaidCode: `graph TD
    1["API Gateway"]
    2[["Auth Service"]]
    3[("PostgreSQL")]
    1 -->|auth| 2
    2 -->|query| 3`,

  canvasMode: "reactflow",
  excalidrawScene: null,
  flowTemplates: DEFAULT_FLOW_TEMPLATES,
  isGeneratingFlowchart: false,
  generationLogs: [],
  chatHistory: [],

  promptScenarios: DEFAULT_PROMPT_SCENARIOS,
  isExecutingPrompt: false,
  promptError: undefined,

  modelConfig: {
    provider: "siliconflow",
    apiKey: "sk-labtoeibcevkdzanpprwezzivdokslxnspigjnapxyogvpgp",
    modelName: "Pro/Qwen/Qwen2.5-7B-Instruct",
  },

  setCanvasMode: (mode) => set({ canvasMode: mode }),
  setExcalidrawScene: (scene) => set({ excalidrawScene: scene }),

  setNodes: (nodes) => set({ nodes }),
  setEdges: (edges) => set({ edges }),

  updateNodeLabel: (id, label) =>
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === id ? { ...node, data: { ...(node.data as any), label } } : node
      ),
    })),

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
    set({ isGeneratingFlowchart: true });
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
          // Final payload is a JSON-like string; attempt to parse
          if (content.startsWith("{")) {
            try {
              const data = JSON.parse(content);
              if (data?.nodes && data?.edges) {
                const nodes = data.nodes as Node[];
                const edges = data.edges as Edge[];
                const mermaidCode = data.mermaid_code || get().mermaidCode;
                // 立即添加所有节点和边，不使用动画避免阻塞流读取
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
          set({ nodes: data.nodes as Node[], edges: data.edges as Edge[], mermaidCode: data.mermaid_code });
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
        style: "neon cyber cat with glowing eyes, bold strokes, 8-color palette",
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
    set({ isGeneratingFlowchart: true, generationLogs: ["🎨 Starting generation..."], excalidrawScene: null });
    try {
      const { modelConfig } = get();

      const body = {
        prompt,
        style: "neon cyber cat with glowing eyes, bold strokes, 8-color palette",
        width: 1200,
        height: 800,
        provider: modelConfig.provider,
        api_key: modelConfig.apiKey?.trim() || undefined,
        base_url: modelConfig.baseUrl?.trim() || undefined,
        model_name: modelConfig.modelName,
      };

      const response = await fetch("/api/excalidraw/generate-stream", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Excalidraw streaming failed");
      }

      const reader = response.body!.getReader();
      const decoder = new TextDecoder();
      let buffered = "";
      let accumulatedJson = "";  // Accumulated JSON text for typewriter effect

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffered += decoder.decode(value, { stream: true });
        const parts = buffered.split("\n\n");
        buffered = parts.pop() || "";

        for (const part of parts) {
          const content = part.trim().replace(/^data:\s?/, "");

          if (!content) continue;

          if (content.startsWith("[TOKEN]")) {
            const token = content.replace("[TOKEN]", "").trimStart();
            accumulatedJson += token;

            // Update the LAST log entry with accumulated JSON (typewriter effect)
            set(state => {
              const logs = [...state.generationLogs];
              if (logs.length > 0 && logs[logs.length - 1].startsWith("🤖")) {
                // Update existing JSON display
                logs[logs.length - 1] = `🤖 Generating JSON...\n${accumulatedJson}`;
              } else {
                // Start new JSON display
                logs.push(`🤖 Generating JSON...\n${accumulatedJson}`);
              }
              return { generationLogs: logs };
            });
          } else if (content.startsWith("[RESULT]")) {
            const resultContent = content.replace("[RESULT]", "").trim();
            const result = JSON.parse(resultContent);

            if (result.scene) {
              set({ excalidrawScene: result.scene });
              console.log("Excalidraw scene saved to store (streaming):", result.scene.elements?.length, "elements");

              // Add completion message
              set(state => ({
                generationLogs: [...state.generationLogs, `✅ Scene generated: ${result.scene.elements?.length || 0} elements`]
              }));
            }
          } else if (content.startsWith("[START]")) {
            const message = content.replace("[START]", "").trim();
            set(state => ({
              generationLogs: [...state.generationLogs, `🎬 ${message}`]
            }));
          } else if (content.startsWith("[CALL]")) {
            const message = content.replace("[CALL]", "").trim();
            set(state => ({
              generationLogs: [...state.generationLogs, `🔮 ${message}`]
            }));
          } else if (content.startsWith("[ERROR]")) {
            const errorMsg = content.replace("[ERROR]", "").trim();
            console.error("Excalidraw streaming error:", errorMsg);
            throw new Error(errorMsg);
          }
        }
      }

      console.log("Excalidraw streaming completed successfully");
    } catch (error: any) {
      console.error("Excalidraw streaming error:", error);
      // Don't throw - the mock scene should have been sent by the backend
      set(state => ({
        generationLogs: [...state.generationLogs, `❌ Error: ${error.message}`]
      }));
    } finally {
      set({ isGeneratingFlowchart: false });
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

      const updatedNodes = data.nodes as Node[];
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
