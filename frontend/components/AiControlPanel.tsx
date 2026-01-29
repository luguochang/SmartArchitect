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
import { useArchitectStore, PromptScenario, DiagramType } from "@/lib/store/useArchitectStore";
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
    prompt: "画一个类似GitHub贡献热力图的表格，横向12-15列（代表周），纵向7行（代表周一到周日）。每个格子是小方块，用不同深浅的绿色填充表示活跃度：深绿色（高活跃）、浅绿色（中等）、灰色（无活跃）。尽可能复刻真实的GitHub样式，方块之间有小间隙，整体排列整齐"
  },
  {
    id: "kanban-board",
    name: "看板布局",
    prompt: "绘制一个Trello/Jira风格的看板，包含4列：待办(To Do)、进行中(In Progress)、测试中(Testing)、已完成(Done)。每列内有3-4张卡片，卡片是圆角矩形，包含标题栏和简单的图标（如小旗帜、打钩符号）。尽可能复刻真实看板的布局和样式"
  },
  {
    id: "dashboard-layout",
    name: "数据面板",
    prompt: "画一个Dashboard仪表盘布局，左侧是垂直导航栏（5-6个菜单项，用简单图标表示），右侧主区域分成4个卡片：左上是折线图（用曲线和坐标轴）、右上是环形进度条、左下是柱状图（5根柱子）、右下是饼图（分3-4块）。尽可能复刻真实数据看板的网格布局和卡片样式"
  },
  {
    id: "calendar-month",
    name: "月历视图",
    prompt: "绘制一个月历（日历）视图，顶部是月份标题，下方是7x5或7x6的网格（周一到周日，4-5周）。某些日期格子内有小圆点标记（表示有事件），某些格子被高亮（不同颜色）。尽可能复刻常见日历应用的样式，网格线清晰，日期数字在格子左上角"
  },
  {
    id: "flowchart-boxes",
    name: "流程图结构",
    prompt: "画一个标准的流程图结构，包含：1个起始椭圆（开始）→ 2-3个处理矩形（步骤）→ 1个菱形判断节点（是/否分支）→ 2个不同路径的矩形 → 1个结束椭圆。用箭头连接各个节点，箭头标注简单的文字（是/否）。尽可能复刻经典流程图的样式"
  },
  {
    id: "sitemap-tree",
    name: "网站地图树",
    prompt: "绘制一个网站Sitemap树状结构图，顶部是首页（根节点，用矩形表示），下方分3个主分支（用户中心、产品列表、帮助文档），每个分支下有2-3个子页面。用树状连接线连接各个节点，尽可能复刻真实sitemap的层级结构和对齐方式"
  },
  {
    id: "gantt-chart",
    name: "甘特图",
    prompt: "画一个项目甘特图，左侧列出5-6个任务名称（需求分析、设计、开发、测试、上线），右侧是时间轴网格（横向12列代表月份），每个任务用不同颜色的横条表示时间跨度，横条长度不同表示任务耗时。尽可能复刻真实甘特图的网格和横条样式"
  },
  {
    id: "mobile-wireframe",
    name: "手机界面原型",
    prompt: "绘制一个手机APP首页的线框图原型（竖屏），包含：顶部状态栏（信号、电量图标）、搜索框、4个圆角方块分类入口（2x2网格）、中间是列表区域（3-4个卡片，每个卡片左侧是正方形图片占位符、右侧是标题和描述线条）、底部Tab栏（4个图标）。尽可能复刻真实APP线框图的布局和元素样式"
  },
  {
    id: "er-diagram",
    name: "数据库ER图",
    prompt: "画一个简单的数据库ER图（实体关系图），包含3个实体表：用户(Users)、订单(Orders)、商品(Products)。每个表是矩形，内部列出3-4个字段（用横线分隔），表之间用连线表示关系（1对多、多对多），连线上标注基数（1、N）。尽可能复刻真实ER图的符号和布局"
  },
  {
    id: "timeline-horizontal",
    name: "水平时间轴",
    prompt: "绘制一条水平时间轴，从左到右有5-6个里程碑节点（用圆点标记），每个节点上方或下方有一个圆角矩形卡片（里程碑描述），节点之间用实线连接。尽可能复刻产品Roadmap的样式，节点对齐在中心线，卡片交错排列（上下交替）"
  }
];

// Flow Diagram 预设提示词（补充现有模板）
const FLOW_PROMPTS = [
  {
    id: "api-request",
    name: "API请求流程",
    prompt: "生成API请求处理完整流程：客户端发起请求 → 网关验证Token → 参数校验 → 业务逻辑处理 → 查询数据库 → 封装响应数据 → 返回JSON结果。包含异常处理分支"
  },
  {
    id: "email-verify",
    name: "邮箱验证",
    prompt: "生成用户邮箱验证流程：用户注册填写邮箱 → 系统生成验证码（6位数字）→ 发送邮件（异步）→ 用户点击链接 → 验证码校验（是否过期？是否正确？）→ 激活账号 → 跳转登录页"
  },
  {
    id: "order-refund",
    name: "订单退款",
    prompt: "生成电商订单退款流程：用户申请退款 → 填写退款原因 → 客服审核（通过/驳回）→ 调用支付接口退款 → 更新订单状态 → 发送退款通知（短信+站内信）→ 完成"
  },
  {
    id: "cache-penetration",
    name: "缓存穿透方案",
    prompt: "生成缓存穿透解决方案流程图：请求到达 → 先查布隆过滤器（Key存在？）→ 不存在直接返回空 → 存在则查Redis缓存 → 缓存命中返回 → 未命中查数据库 → 数据存在写入缓存 → 数据不存在缓存空值（5分钟TTL）"
  },
  {
    id: "login-sso",
    name: "单点登录SSO",
    prompt: "生成单点登录SSO流程：用户访问应用A → 未登录重定向到SSO中心 → 输入账号密码 → SSO验证成功生成Token → 重定向回应用A并携带Token → 应用A验证Token → 建立Session → 访问应用B时自动登录"
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

        {/* 图片上传按钮卡片 - 只在未激活上传界面时显示 */}
        {!showUploader && !showExcalidrawUploader && (
          <button
            onClick={() => {
              if (canvasMode === "excalidraw") {
                setShowExcalidrawUploader(true);
              } else {
                setShowUploader(true);
              }
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
                  {canvasMode === "reactflow"
                    ? "上传流程图/架构图截图，AI自动识别转为可编辑节点"
                    : "上传任意图片，AI实时流式转换为Excalidraw手绘风格"
                  }
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
                      {msg.content}
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
