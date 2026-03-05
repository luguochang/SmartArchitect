"use client";

import { useEffect, useMemo, useState, useRef } from "react";
import {
  MessageSquare,
  Send,
  Wand2,
  Sparkles,
  Shield,
  Brush,
  Loader2,
  Sparkles as SparklesIcon,
  AlertCircle,
  Palette,
  Grid3x3,
  Upload,
  FileText,
  ChevronDown,
  ArrowLeft,
} from "lucide-react";
import { useArchitectStore, PromptScenario, DiagramType, ArchitectureType } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";
import { SelectedDetailsPanel } from "./SelectedDetailsPanel";
import { FlowchartUploader } from "./FlowchartUploader";
import { ExcalidrawUploader } from "./ExcalidrawUploader";

const CATEGORY_ICONS = {
  refactoring: Sparkles,
  security: Shield,
  beautification: Brush,
  custom: Wand2,
};

const CATEGORY_COLORS = {
  refactoring: "text-purple-500 bg-purple-50 dark:bg-purple-500/10",
  security: "text-red-500 bg-red-50 dark:bg-red-500/10",
  beautification: "text-blue-500 bg-blue-50 dark:bg-blue-500/10",
  custom: "text-gray-500 bg-gray-100 dark:bg-gray-500/10",
};

// Excalidraw 预设提示词 - 适合手绘风格的具体界面和图表
const EXCALIDRAW_PROMPTS = [
  {
    id: "github-heatmap",
    name: "GitHub贡献图",
    prompt: "手绘风格的GitHub贡献热力图：12-15列（周）× 7行（周一-周日）小方块，浅→深绿色渐变表示活跃度，格子之间留出微小间距，整体整齐对齐，背景留白"
  },
  {
    id: "kanban-board",
    name: "看板布局",
    prompt: "手绘看板：4列（To Do / In Progress / Testing / Done），列头有标题；每列3-4张统一尺寸的圆角卡片，卡片带细分栏位和简笔图标；保持网格对齐和均匀留白"
  },
  {
    id: "dashboard-layout",
    name: "数据面板",
    prompt: "仪表盘线框：左侧窄导航栏（5-6个菜单 + 小图标），右侧主区域为2×2卡片网格：折线图、环形进度条、柱状图、饼图。用简笔线条表现图表，强调卡片边框和分栏对齐"
  },
  {
    id: "calendar-month",
    name: "月历视图",
    prompt: "月历线框：顶部月份标题，下方7列×5~6行网格，左上角标日期数字；随机格子加小圆点或浅色高亮表示事件；线条轻、间距均匀、整体居中"
  },
  {
    id: "flowchart-boxes",
    name: "流程图结构",
    prompt: "手绘流程图：开始椭圆 → 3-4个矩形步骤 → 1个菱形判断分成2条路径 → 结束椭圆。所有节点用箭头连接，分支箭头标注“是/否”，留出均匀间距，线条略有手绘抖动感"
  },
  {
    id: "sitemap-tree",
    name: "网站地图树",
    prompt: "Sitemap树：顶层首页矩形，下方3个主分支（用户中心、产品列表、帮助文档），每个主分支带2-3个子页面节点。保持分支对齐和层级缩进，连接线清晰，手绘风格"
  },
  {
    id: "gantt-chart",
    name: "甘特图",
    prompt: "甘特图线框：左侧任务列表5-6行，右侧是横向时间轴网格（约12列）；每个任务用彩色横条表示跨度，条宽不一且与时间轴对齐；保持行列对齐和简洁描边"
  },
  {
    id: "mobile-wireframe",
    name: "手机界面原型",
    prompt: "手机首页线框（竖屏）：顶部状态栏 + 搜索框；中上部2×2圆角卡片入口；中间列表区3-4个卡片（左图占位、右侧标题/描述线条）；底部Tab栏4个图标。保持留白与对齐，简笔线框"
  },
  {
    id: "er-diagram",
    name: "数据库ER图",
    prompt: "简洁ER图：3个表（Users / Orders / Products），表内分栏列出3-4个字段；用连接线标注基数（1 / N），表格对齐，线条清晰，保持手绘感"
  },
  {
    id: "timeline-horizontal",
    name: "水平时间轴",
    prompt: "水平时间轴：中央水平线 + 5-6个里程碑圆点，节点间等距；每个节点附带上下交错的圆角卡片描述；使用单一主色+浅色填充，保持对齐和留白"
  }
];

// Flow Diagram 预设提示词（补充现有模板）
const FLOW_PROMPTS = [
  {
    id: "date-day",
    name: "约会日流程",
    prompt: "生成“和异性约会的一天”流程图：从早晨准备→路上见面→午餐/下午活动→晚餐/散步→送别，考虑迟到/堵车/临时改地点/冷场/过敏等突发情况，并标注应对策略（如备用话题、应急药物、备选餐厅）"
  },
  {
    id: "incident-response",
    name: "故障应急",
    prompt: "生成技术故障应急流程：监控告警→初步分级→值班响应→定位（日志/指标/链路追踪）→缓解措施（回滚/降级/扩容）→验证恢复→事后复盘。包含严重级别分支、升级路径、通信同步节点"
  },
  {
    id: "onboarding",
    name: "新人入职",
    prompt: "生成新人入职全流程：预入职邮件/账号申请→报到→设备/权限开通→导师分配→首日引导→一周/一月检查点→转正评估。考虑异常如设备缺货、权限审批延迟、导师缺席"
  },
  {
    id: "ml-deployment",
    name: "模型上线",
    prompt: "生成机器学习模型上线流程：数据准备→特征校验→训练/评估→模型注册→A/B或灰度发布→实时/批量推理→监控（漂移/延迟/成本）→回滚策略。突出安全网：模型回滚、阈值降级、熔断"
  },
  {
    id: "release-train",
    name: "发布列车",
    prompt: "生成跨团队发布列车流程：需求冻结→分支策略→CI流水线→自动化测试（单测/集成/端到端）→安全扫描→预发布验证→分批放量→观测与回滚。加入失败分支和审批/沟通节点"
  }
];

// Architecture 预设提示词（补充现有模板）
const ARCHITECTURE_PROMPTS = [
  {
    id: "frontend-backend",
    name: "前后端分离",
    prompt: "生成前后端分离架构：React前端（部署在Nginx）→ API Gateway（Kong网关，限流鉴权）→ Spring Cloud微服务（订单服务、用户服务、商品服务）→ MySQL主从数据库 + Redis缓存 → Elasticsearch全文搜索"
  },
  {
    id: "realtime-data",
    name: "实时数据处理",
    prompt: "生成实时数据处理架构：数据源（App、Web、IoT设备）→ Kafka消息队列（分区存储）→ Flink流式计算（实时聚合）→ ClickHouse列式数据库 → Grafana可视化大屏 + 实时告警"
  },
  {
    id: "k8s-deployment",
    name: "容器化部署",
    prompt: "生成K8s容器化部署架构：代码提交GitHub → Jenkins CI/CD流水线 → 构建Docker镜像推送Harbor → K8s集群部署（Deployment、Service、Ingress）→ Prometheus监控 + ELK日志 → 钉钉告警"
  },
  {
    id: "bigdata-platform",
    name: "大数据平台",
    prompt: "生成大数据架构：数据采集层（Flume、Logstash）→ 消息队列（Kafka）→ 离线计算（Spark批处理）→ 数据仓库（Hive）→ OLAP引擎（Kylin）→ BI报表（Superset）"
  },
  {
    id: "mobile-architecture",
    name: "移动端架构",
    prompt: "生成移动App架构：iOS/Android客户端 → CDN静态资源加速 → API网关（灰度发布、AB测试）→ 后端微服务集群 → 消息推送服务（极光/个推）→ 埋点数据采集 → 用户行为分析"
  },
  {
    id: "serverless",
    name: "Serverless架构",
    prompt: "生成Serverless无服务器架构：用户请求 → API Gateway（AWS）→ Lambda函数（按需执行、自动扩缩容）→ DynamoDB NoSQL数据库 → S3对象存储（图片、文件）→ CloudWatch监控日志"
  }
];

export function AiControlPanel() {
  const {
    modelConfig,
    setModelConfig,
    // Flowchat generator
    flowTemplates,
    isGeneratingFlowchart,
    generationLogs,
    chatHistory,
    loadFlowTemplates,
    generateFlowchart,
    generateExcalidrawScene,
    generateExcalidrawSceneStream,
    canvasMode,
    architectureType,
    setArchitectureType,
    // 🆕 增量生成
    incrementalMode,
    setIncrementalMode,
    currentSessionId,
    nodes,
    // Prompter
    promptScenarios,
    isExecutingPrompt,
    promptError,
    loadPromptScenarios,
    executePromptScenario,
    applyMockScenario,
  } = useArchitectStore();

  const [flowInput, setFlowInput] = useState("");
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [selectedScenario, setSelectedScenario] = useState<string | null>(null);
  const [scenarioInput, setScenarioInput] = useState("");
  const [showUploader, setShowUploader] = useState(false);
  const [showExcalidrawUploader, setShowExcalidrawUploader] = useState(false);
  const [showTemplates, setShowTemplates] = useState(true); // Templates 默认展开
  const [diagramType, setDiagramType] = useState<DiagramType>("flow");
  const [templateFilter, setTemplateFilter] = useState<"flow" | "architecture">("flow");

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (flowTemplates.length === 0) {
      loadFlowTemplates();
    }
    if (promptScenarios.length === 0) {
      loadPromptScenarios();
    }
  }, [flowTemplates.length, promptScenarios.length, loadFlowTemplates, loadPromptScenarios]);

  // Keep uploader panels aligned with the active canvas mode.
  useEffect(() => {
    if (canvasMode === "reactflow") {
      setShowExcalidrawUploader(false);
      return;
    }
    if (canvasMode === "excalidraw") {
      setShowUploader(false);
    }
  }, [canvasMode]);

  // Auto-scroll to bottom when messages update (throttled)
  useEffect(() => {
    if (generationLogs.length === 0 && chatHistory.length === 0) {
      return;
    }

    // Use requestAnimationFrame to batch scroll updates
    const scrollTimeout = setTimeout(() => {
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
      });
    }, 100);

    return () => clearTimeout(scrollTimeout);
  }, [generationLogs, chatHistory]);

  const apiReady = useMemo(() => Boolean(modelConfig.apiKey && modelConfig.apiKey.trim()), [modelConfig.apiKey]);

  const handleTemplatePick = (templateId: string, example: string) => {
    const tpl = flowTemplates.find((t) => t.id === templateId);
    if (tpl?.category === "architecture") {
      setDiagramType("architecture");
    } else {
      setDiagramType("flow");
    }
    setSelectedTemplate(templateId);
    setFlowInput(example);
  };

  const handleGenerateFlow = async () => {
    if (!flowInput.trim()) {
      toast.error("Please enter a description");
      return;
    }
    if (!apiReady) {
      toast.error("API key not configured. Please set it first.");
      return;
    }
    try {
      if (canvasMode === "excalidraw") {
        await generateExcalidrawSceneStream(flowInput);
        toast.success("Excalidraw scene generated");
      } else {
        await generateFlowchart(flowInput, selectedTemplate || undefined, diagramType);
        toast.success("Flowchart generated");
      }
    } catch (error) {
        toast.error("Generation failed");
    }
  };

  const handleExecutePrompt = async () => {
    if (!selectedScenario) {
      toast.error("Please select a scenario");
      return;
    }
    // Mock path if no API key: apply local changes only
    if (!apiReady) {
      applyMockScenario(selectedScenario);
      toast.success("Mock prompt applied locally");
      return;
    }
    try {
      await executePromptScenario(selectedScenario, scenarioInput || undefined);
      toast.success("Prompt executed successfully");
    } catch (error) {
      toast.error(promptError || "Failed to execute prompt");
    }
  };

  return (
    <aside className="flex h-full w-96 flex-col gap-3 border-l border-slate-200 bg-gradient-to-br from-slate-50 to-slate-100/50 p-4 dark:border-slate-800 dark:from-slate-900 dark:to-slate-900/50">
      {/* Header */}
      <div className="space-y-3">
        {/* Title */}
        <div className="flex items-center gap-2">
          <div className="rounded-lg bg-gradient-to-br from-emerald-500 to-teal-600 p-2 shadow-sm">
            {canvasMode === "excalidraw" ? (
              <Palette className="h-5 w-5 text-white" />
            ) : (
              <MessageSquare className="h-5 w-5 text-white" />
            )}
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-sm font-bold text-slate-900 dark:text-white">
              {canvasMode === "excalidraw" ? "AI Drawing" : "AI Generator"}
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400 truncate">
              {canvasMode === "excalidraw" ? "Generate hand-drawn diagrams" : "Generate flowcharts & architectures"}
            </p>
          </div>
        </div>

        {/* Action Buttons - Two Rows */}
        <div className="space-y-2">
          {/* Row 1: Config + Main Actions */}
          <div className="flex items-center gap-1.5 flex-wrap">
          {/* Back to Chat Button - Only show when any uploader is active */}
          {(showUploader || showExcalidrawUploader) && (
            <button
              onClick={() => {
                setShowUploader(false);
                setShowExcalidrawUploader(false);
              }}
              className="flex-shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-medium shadow-sm transition bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:from-emerald-600 hover:to-teal-600"
              title="返回聊天界面"
            >
              <ArrowLeft className="mr-1 inline-block h-3.5 w-3.5" />
              Back to Chat
            </button>
          )}
        </div>

        {/* 图片上传按钮卡片 - 只在 Excalidraw 模式下显示，ReactFlow 模式禁用（效果不好） */}
        {!showUploader && !showExcalidrawUploader && canvasMode === "excalidraw" && (
          <button
            onClick={() => {
              setShowExcalidrawUploader(true);
            }}
            className="w-full rounded-lg bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/30 dark:to-indigo-950/30 p-3 border border-blue-100 dark:border-blue-900/50 hover:from-blue-100 hover:to-indigo-100 dark:hover:from-blue-950/50 dark:hover:to-indigo-950/50 transition-all text-left"
          >
            <div className="flex items-start gap-2">
              <Upload className="h-4 w-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <p className="text-xs font-semibold text-blue-900 dark:text-blue-100">
                    💡 图片上传
                  </p>
                  <span className="px-1.5 py-0.5 text-[10px] font-bold rounded bg-gradient-to-r from-purple-500 to-pink-500 text-white">
                    ⭐ 特色
                  </span>
                </div>
                <p className="text-xs text-blue-700 dark:text-blue-300 leading-relaxed">
                  上传任意图片，AI实时流式转换为Excalidraw手绘风格
                </p>
              </div>
            </div>
          </button>
        )}
        </div>
      </div>

      <SelectedDetailsPanel />

      {/* Main Content - Full Height */}
      <div className="flex min-h-0 flex-1 flex-col gap-4">
        {/* Excalidraw Uploader Section */}
        {showExcalidrawUploader ? (
          <section className="flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 p-4 overflow-y-auto">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                🎨 图片转 Excalidraw
              </h3>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                上传架构图或流程图图片，AI 将实时流式转换为 Excalidraw 手绘风格，元素逐个显示。
              </p>
            </div>
            <ExcalidrawUploader />
          </section>
        ) : showUploader ? (
          <section className="flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 p-4 overflow-y-auto">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                📸 图片识别
              </h3>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                上传流程图或架构图截图，AI 自动识别转换为可编辑的节点结构。支持手绘图、Visio、ProcessOn、Draw.io 等各类图表。
              </p>
            </div>
            <FlowchartUploader />
          </section>
        ) : (
          <>
            {/* Generator Section */}
            <section className="flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
          {/* Quick Prompts - Always show, different content for each mode */}
          <div className="border-b border-slate-200 dark:border-slate-800">
            <button
              onClick={() => setShowTemplates(!showTemplates)}
              className="w-full px-4 py-3 flex items-center justify-between hover:bg-slate-50 dark:hover:bg-slate-800/50 transition"
            >
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                {canvasMode === "excalidraw"
                  ? `✨ Quick Prompts ${showTemplates ? '' : `(${EXCALIDRAW_PROMPTS.length})`}`
                  : `💡 Quick Prompts ${showTemplates ? '' : `(${templateFilter === "flow" ? FLOW_PROMPTS.length : ARCHITECTURE_PROMPTS.length})`}`
                }
              </h3>
              <ChevronDown className={`h-4 w-4 text-slate-500 transition-transform ${showTemplates ? '' : '-rotate-90'}`} />
            </button>

            {showTemplates && (
              <div className="px-4 pb-4 space-y-3">
                {/* Excalidraw Mode: Show Excalidraw Prompts */}
                {canvasMode === "excalidraw" ? (
                  <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-1">
                    {EXCALIDRAW_PROMPTS.map((prompt) => (
                      <button
                        key={prompt.id}
                        onClick={() => {
                          setFlowInput(prompt.prompt);
                        }}
                        disabled={isGeneratingFlowchart}
                        className={`rounded-lg border px-3 py-2.5 text-left text-xs transition-all border-purple-200 bg-purple-50/80 hover:border-purple-400 hover:bg-purple-100 hover:shadow-sm dark:border-purple-700 dark:bg-purple-900/30 dark:hover:border-purple-500 dark:hover:bg-purple-900/50 ${
                          isGeneratingFlowchart ? "opacity-50 cursor-not-allowed" : ""
                        }`}
                      >
                        <p className="font-semibold text-purple-900 dark:text-purple-100">{prompt.name}</p>
                      </button>
                    ))}
                  </div>
                ) : (
                  <>
                    {/* ReactFlow Mode: Enhanced Flow/Architecture Toggle */}
                    <div className="flex items-center justify-center">
                      <div className="inline-flex rounded-xl border-2 border-slate-200 bg-white p-1 shadow-sm dark:border-slate-700 dark:bg-slate-800">
                        <button
                          onClick={() => {
                            setTemplateFilter("flow");
                            setDiagramType("flow");
                          }}
                          className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 ${
                            templateFilter === "flow"
                              ? "bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-md scale-105"
                              : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-700/50"
                          }`}
                        >
                          📊 Flow Diagram
                        </button>
                        <button
                          onClick={() => {
                            setTemplateFilter("architecture");
                            setDiagramType("architecture");
                          }}
                          className={`px-4 py-2 rounded-lg text-xs font-semibold transition-all duration-200 ${
                            templateFilter === "architecture"
                              ? "bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-md scale-105"
                              : "text-slate-600 hover:text-slate-900 hover:bg-slate-50 dark:text-slate-300 dark:hover:text-white dark:hover:bg-slate-700/50"
                          }`}
                        >
                          🏗️ Architecture
                        </button>
                      </div>
                    </div>

                    {/* Architecture Type Selector - Only show when Architecture is selected */}
                    {templateFilter === "architecture" && (
                      <div className="space-y-2">
                        <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300">
                          📐 Architecture Type
                        </label>
                        <div className="grid grid-cols-2 gap-2">
                          <button
                            onClick={() => setArchitectureType("layered")}
                            className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                              architectureType === "layered"
                                ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-md"
                                : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                            }`}
                          >
                            🏢 Layered
                          </button>
                          <button
                            onClick={() => setArchitectureType("business")}
                            className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                              architectureType === "business"
                                ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-md"
                                : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                            }`}
                          >
                            💼 Business
                          </button>
                          <button
                            onClick={() => setArchitectureType("technical")}
                            className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                              architectureType === "technical"
                                ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-md"
                                : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                            }`}
                          >
                            ⚙️ Technical
                          </button>
                          <button
                            onClick={() => setArchitectureType("deployment")}
                            className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                              architectureType === "deployment"
                                ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-md"
                                : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                            }`}
                          >
                            🚀 Deployment
                          </button>
                          <button
                            onClick={() => setArchitectureType("domain")}
                            className={`px-3 py-2 rounded-lg text-xs font-medium transition-all col-span-2 ${
                              architectureType === "domain"
                                ? "bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-md"
                                : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700"
                            }`}
                          >
                            🎯 Domain-Driven
                          </button>
                        </div>
                      </div>
                    )}

                    {/* ReactFlow Mode: Show Quick Prompts */}
                    <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto pr-1">
                      {(templateFilter === "flow" ? FLOW_PROMPTS : ARCHITECTURE_PROMPTS).map((prompt) => (
                        <button
                          key={prompt.id}
                          onClick={() => {
                            setFlowInput(prompt.prompt);
                            setSelectedTemplate(null);
                          }}
                          disabled={isGeneratingFlowchart}
                          className={`rounded-lg border px-3 py-2.5 text-left text-xs transition-all border-emerald-200 bg-emerald-50/80 hover:border-emerald-400 hover:bg-emerald-100 hover:shadow-sm dark:border-emerald-700 dark:bg-emerald-900/30 dark:hover:border-emerald-500 dark:hover:bg-emerald-900/50 ${
                            isGeneratingFlowchart ? "opacity-50 cursor-not-allowed" : ""
                          }`}
                        >
                          <p className="font-semibold text-emerald-900 dark:text-emerald-100">{prompt.name}</p>
                        </button>
                      ))}
                    </div>
                  </>
                )}
              </div>
            )}
          </div>

          {/* Messages Area - Unified */}
          <div className="flex-1 min-h-0 overflow-y-auto p-4 space-y-3">
            {/* Chat History */}
            {chatHistory.length > 0 && (
              <>
                {chatHistory.map((msg, idx) => (
                  <div
                    key={`chat-${idx}`}
                    className={`flex ${msg.role === "assistant" ? "justify-start" : "justify-end"}`}
                  >
                    <div
                      className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
                        msg.role === "assistant"
                          ? "bg-gradient-to-br from-emerald-50 to-teal-50 text-emerald-900 dark:from-emerald-900/30 dark:to-teal-900/30 dark:text-emerald-50"
                          : "bg-slate-200 text-slate-900 dark:bg-slate-700 dark:text-white"
                      }`}
                    >
                      {/* Show loading animation for generating messages */}
                      {msg.role === "assistant" && msg.content.includes("正在生成") && (
                        <div className="flex items-center gap-2 mb-1">
                          <Loader2 className="h-3 w-3 animate-spin" />
                          <span className="text-xs opacity-75">AI 正在工作中...</span>
                        </div>
                      )}
                      <div className="whitespace-pre-wrap">{msg.content}</div>
                    </div>
                  </div>
                ))}
              </>
            )}

            {/* Generation Logs */}
            {generationLogs.length > 0 && (
              <div className="space-y-2">
                {generationLogs.map((log, idx) => (
                  <div
                    key={`log-${idx}`}
                    className={`rounded-lg bg-gradient-to-br from-emerald-50 to-teal-50 px-3 py-2 text-xs font-mono text-emerald-900 dark:from-emerald-900/30 dark:to-teal-900/30 dark:text-emerald-50 ${
                      log.startsWith("[生成中]")
                        ? "overflow-x-auto whitespace-nowrap max-w-full"
                        : "whitespace-pre-wrap break-words"
                    }`}
                  >
                    {/* Show animated dots for generating logs */}
                    {log.startsWith("[生成中]") && (
                      <div className="flex items-center gap-2 mb-1">
                        <div className="flex gap-1">
                          <div className="w-1.5 h-1.5 bg-emerald-600 dark:bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }}></div>
                          <div className="w-1.5 h-1.5 bg-emerald-600 dark:bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }}></div>
                          <div className="w-1.5 h-1.5 bg-emerald-600 dark:bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }}></div>
                        </div>
                        <span className="text-xs opacity-75">流式生成中...</span>
                      </div>
                    )}
                    {log}
                  </div>
                ))}
              </div>
            )}

            {/* Empty State - Compact */}
            {chatHistory.length === 0 && generationLogs.length === 0 && (
              <div className="flex items-center justify-center py-8 text-center">
                <div className="max-w-xs space-y-2">
                  <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-gradient-to-br from-emerald-100 to-teal-100 dark:from-emerald-900/30 dark:to-teal-900/30">
                    <SparklesIcon className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
                  </div>
                  <p className="text-sm font-semibold text-slate-900 dark:text-white">
                    {canvasMode === "excalidraw" ? "Ready to draw!" : "AI Flowchart Generator"}
                  </p>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    {canvasMode === "excalidraw"
                      ? "Describe what you want to draw below"
                      : "Describe your process in the input box below"}
                  </p>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area - Fixed at Bottom */}
          <div className="border-t border-slate-200 p-4 bg-gradient-to-br from-white to-slate-50/50 dark:border-slate-800 dark:from-slate-900 dark:to-slate-800/50">
            <div className="space-y-3">
              <div>
                <div className="mb-2 flex items-center gap-2">
                  <label className="text-sm font-bold text-slate-900 dark:text-white">
                    {canvasMode === "excalidraw" ? "💬 Describe your drawing" : "💬 Describe your flowchart"}
                  </label>
                  {!apiReady && (
                    <span className="text-xs text-amber-600 dark:text-amber-400">
                      ⚠️ Configure AI first
                    </span>
                  )}
                </div>
                <textarea
                  value={flowInput}
                  onChange={(e) => setFlowInput(e.target.value)}
                  placeholder={
                    canvasMode === "excalidraw"
                      ? "e.g. A colorful robot with glowing eyes..."
                      : "e.g. User authentication flow with login, verification, and error handling..."
                  }
                  rows={3}
                  className="w-full rounded-lg border-2 border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 outline-none transition focus:border-emerald-500 focus:ring-4 focus:ring-emerald-100 dark:border-slate-700 dark:bg-slate-800 dark:text-white dark:focus:border-emerald-400 dark:focus:ring-emerald-500/20"
                  disabled={isGeneratingFlowchart}
                />
              </div>

              {/* 🆕 增量生成模式切换 - 暂时隐藏 */}
              {/* <div className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  id="incremental-mode"
                  checked={incrementalMode}
                  onChange={(e) => setIncrementalMode(e.target.checked)}
                  disabled={nodes.length === 0}
                  className="w-4 h-4 rounded border-slate-300 text-emerald-600 focus:ring-emerald-500 disabled:opacity-50 disabled:cursor-not-allowed"
                />
                <label
                  htmlFor="incremental-mode"
                  className={`cursor-pointer select-none ${
                    nodes.length === 0
                      ? "text-slate-400 dark:text-slate-600"
                      : "text-slate-700 dark:text-slate-300"
                  }`}
                >
                  增量模式（在现有架构上追加）
                </label>
                {currentSessionId && (
                  <span
                    className="text-xs text-emerald-600 dark:text-emerald-400"
                    title={`会话 ID: ${currentSessionId}`}
                  >
                    ✓ 会话已保存
                  </span>
                )}
              </div>

              {incrementalMode && nodes.length > 0 && (
                <div className="text-xs text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-500/10 rounded-lg px-3 py-2">
                  💡 将在现有 {nodes.length} 个节点基础上追加
                </div>
              )} */}

              <button
                onClick={handleGenerateFlow}
                disabled={isGeneratingFlowchart || !apiReady}
                className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-600 to-teal-600 px-4 py-3 text-sm font-bold text-white shadow-md transition hover:from-emerald-700 hover:to-teal-700 hover:shadow-lg disabled:cursor-not-allowed disabled:opacity-60 disabled:shadow-sm"
              >
                {isGeneratingFlowchart ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    <Send className="h-4 w-4" />
                    Generate Flowchart
                  </>
                )}
              </button>
            </div>
          </div>
        </section>
          </>
        )}
      </div>
    </aside>
  );
}
