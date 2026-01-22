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
import { DocumentUploader } from "./DocumentUploader";
import { ImageUploader } from "./ImageUploader";

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

// Excalidraw 预设提示词
const EXCALIDRAW_PROMPTS = [
  {
    id: "mindmap",
    name: "思维导图",
    prompt: "画一个思维导图：中心主题是'产品规划'，主要分支包括：用户研究（用户画像、需求调研）、需求分析（功能优先级、技术可行性）、设计原型（UI设计、交互流程）、开发测试（迭代计划、质量保证）"
  },
  {
    id: "architecture-sketch",
    name: "架构草图",
    label: "手绘架构",
    prompt: "手绘风格的Web系统架构草图：用户通过浏览器访问，经过Nginx负载均衡，到达Spring Boot后端服务集群，后端连接MySQL主从数据库和Redis缓存，使用Kafka消息队列处理异步任务"
  },
  {
    id: "user-journey",
    name: "用户旅程图",
    prompt: "绘制一个电商APP用户购物旅程地图：浏览商品（兴奋）→ 加入购物车（犹豫）→ 支付（焦虑）→ 等待配送（期待）→ 收货（满意）。标注每个阶段的情绪曲线和关键痛点"
  },
  {
    id: "project-timeline",
    name: "项目时间线",
    prompt: "绘制一个项目时间线图，横轴是时间（Q1-Q4），纵轴标注关键里程碑：需求评审（1月）、技术选型（2月）、开发阶段（3-6月）、测试上线（7月）、运营推广（8-12月）"
  },
  {
    id: "team-workflow",
    name: "团队协作",
    prompt: "画一个敏捷团队协作流程图：产品经理提出需求 → UI设计师设计原型 → 前端开发实现界面 → 后端开发提供API → 测试工程师验收 → DevOps部署上线。用不同颜色区分角色"
  },
  {
    id: "concept-diagram",
    name: "概念图",
    prompt: "绘制微服务概念图：展示服务注册发现（Eureka）、API网关（Gateway）、配置中心（Config）、链路追踪（Zipkin）、熔断降级（Hystrix）之间的关系，用箭头表示调用方向"
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
  const [showDocUploader, setShowDocUploader] = useState(false);
  const [showImageUploader, setShowImageUploader] = useState(false);
  const [showTemplates, setShowTemplates] = useState(false); // Templates 默认折叠
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
          {(showUploader || showImageUploader || showDocUploader) && (
            <button
              onClick={() => {
                setShowUploader(false);
                setShowImageUploader(false);
                setShowDocUploader(false);
              }}
              className="flex-shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-medium shadow-sm transition bg-gradient-to-r from-emerald-500 to-teal-500 text-white hover:from-emerald-600 hover:to-teal-600"
              title="返回聊天界面"
            >
              <ArrowLeft className="mr-1 inline-block h-3.5 w-3.5" />
              Back to Chat
            </button>
          )}
          <button
            onClick={() => {
              // Toggle off if already active, otherwise activate and deactivate others
              if (showUploader) {
                setShowUploader(false);
              } else {
                setShowUploader(true);
                setShowDocUploader(false);
                setShowImageUploader(false);
              }
            }}
            className={`flex-shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-medium shadow-sm transition ${
              showUploader
                ? "bg-indigo-500 text-white hover:bg-indigo-600"
                : "bg-white text-slate-700 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            <Upload className="mr-1 inline-block h-3.5 w-3.5" />
            Flowchart
          </button>
          <button
            onClick={() => {
              // Toggle off if already active, otherwise activate and deactivate others
              if (showImageUploader) {
                setShowImageUploader(false);
              } else {
                setShowImageUploader(true);
                setShowUploader(false);
                setShowDocUploader(false);
              }
            }}
            className={`flex-shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-medium shadow-sm transition ${
              showImageUploader
                ? "bg-indigo-500 text-white hover:bg-indigo-600"
                : "bg-white text-slate-700 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            <Grid3x3 className="mr-1 inline-block h-3.5 w-3.5" />
            Architecture
          </button>
          <button
            onClick={() => {
              // Toggle off if already active, otherwise activate and deactivate others
              if (showDocUploader) {
                setShowDocUploader(false);
              } else {
                setShowDocUploader(true);
                setShowUploader(false);
                setShowImageUploader(false);
              }
            }}
            className={`flex-shrink-0 rounded-lg px-2.5 py-1.5 text-xs font-medium shadow-sm transition ${
              showDocUploader
                ? "bg-indigo-500 text-white hover:bg-indigo-600"
                : "bg-white text-slate-700 hover:bg-slate-50 dark:bg-slate-800 dark:text-slate-200 dark:hover:bg-slate-700"
            }`}
          >
            <FileText className="mr-1 inline-block h-3.5 w-3.5" />
            Docs
          </button>
        </div>
        </div>
      </div>

      <SelectedDetailsPanel />

      {/* Main Content - Full Height */}
      <div className="flex min-h-0 flex-1 flex-col gap-4">
        {/* Flowchart Uploader Section */}
        {showUploader ? (
          <section className="flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 p-4 overflow-y-auto">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                📸 流程图截图识别
              </h3>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                上传流程图截图，AI 将自动识别并转换为可编辑的节点结构。支持手绘图、Visio、ProcessOn 等各类流程图。
              </p>
            </div>
            <FlowchartUploader />
          </section>
        ) : showImageUploader ? (
          <section className="flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 p-4 overflow-y-auto">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                🏗️ 架构图 AI 分析
              </h3>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                上传系统架构图，AI 将分析组件、服务、数据流等架构要素。支持微服务架构、系统拓扑、部署架构等。
              </p>
            </div>
            <ImageUploader />
          </section>
        ) : showDocUploader ? (
          <section className="flex min-h-0 flex-1 flex-col rounded-xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900 p-4 overflow-y-auto">
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
                📚 RAG 知识库文档
              </h3>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                上传技术文档、API 手册、设计规范等，构建知识库以增强 AI 生成效果。支持 PDF、Markdown、Word 格式。
              </p>
            </div>
            <DocumentUploader />
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
