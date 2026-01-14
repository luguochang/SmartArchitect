"use client";

import { useState, useMemo } from "react";
import {
  Database,
  Globe,
  Box,
  Settings,
  Image as ImageIcon,
  Wand2,
  FileText,
  Shield,
  Zap,
  Layers,
  HardDrive,
  Monitor,
  MessageSquare,
  Search,
  ChevronDown,
  ChevronRight,
  PlayCircle,
  StopCircle,
  AlertCircle,
  CheckCircle,
  Circle,
  Square,
  Diamond,
  Hexagon,
  Triangle,
  Star,
  Cloud,
  FileCode,
  Octagon,
  Pentagon,
  User,
  Users,
  Smartphone,
  Server,
  Network,
  Container,
  Folder,
  FolderOpen,
  Package,
  Cpu,
  Activity,
  Wifi,
  Lock,
} from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { ModelConfigModal } from "./ModelConfigModal";
import { ImageUploadModal } from "./ImageUploadModal";
import PrompterModal from "./PrompterModal";
import DocumentUploadModal from "./DocumentUploadModal";
import ChatGeneratorModal from "./ChatGeneratorModal";

// 节点类型定义
interface NodeType {
  type: string;
  icon: any;
  iconType?: string;  // Icon identifier for canvas rendering
  label: string;
  color: string;
  shape?: string;
  description?: string;
}

interface NodeCategory {
  id: string;
  name: string;
  nodes: NodeType[];
  defaultExpanded: boolean;
}

export function Sidebar() {
  const [isConfigOpen, setIsConfigOpen] = useState(false);
  const [isImageUploadOpen, setIsImageUploadOpen] = useState(false);
  const [isPrompterOpen, setIsPrompterOpen] = useState(false);
  const [isDocumentUploadOpen, setIsDocumentUploadOpen] = useState(false);
  const [isChatGeneratorOpen, setIsChatGeneratorOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(["basic", "flowchart"])
  );

  const { nodes, setNodes } = useArchitectStore();

  // 节点分类配置 - 参考 draw.io 的节点库
  const nodeCategories: NodeCategory[] = [
    {
      id: "basic",
      name: "基础图形",
      defaultExpanded: true,
      nodes: [
        { type: "rectangle", icon: Square, label: "矩形", color: "text-blue-600", shape: "rectangle", description: "基础矩形" },
        { type: "rounded-rectangle", icon: Box, label: "圆角矩形", color: "text-blue-500", shape: "rounded-rectangle", description: "圆角矩形" },
        { type: "circle", icon: Circle, label: "圆形", color: "text-green-600", shape: "circle", description: "圆形/椭圆" },
        { type: "diamond", icon: Diamond, label: "菱形", color: "text-yellow-600", shape: "diamond", description: "决策/判断" },
        { type: "hexagon", icon: Hexagon, label: "六边形", color: "text-purple-600", shape: "hexagon", description: "六边形" },
        { type: "triangle", icon: Triangle, label: "三角形", color: "text-orange-600", shape: "triangle", description: "三角形" },
        { type: "parallelogram", icon: Square, label: "平行四边形", color: "text-cyan-600", shape: "parallelogram", description: "数据/输入输出" },
        { type: "trapezoid", icon: Square, label: "梯形", color: "text-indigo-600", shape: "trapezoid", description: "手动操作" },
        { type: "star", icon: Star, label: "星形", color: "text-yellow-500", shape: "star", description: "星形" },
        { type: "cloud", icon: Cloud, label: "云形", color: "text-sky-600", shape: "cloud", description: "云/注释" },
        { type: "cylinder", icon: Database, label: "圆柱", color: "text-teal-600", shape: "cylinder", description: "数据库/存储" },
        { type: "document", icon: FileText, label: "文档", color: "text-slate-600", shape: "document", description: "文档/报告" },
      ],
    },
    {
      id: "flowchart",
      name: "流程图",
      defaultExpanded: true,
      nodes: [
        { type: "start", icon: PlayCircle, label: "开始", color: "text-green-600", shape: "start", description: "流程开始" },
        { type: "end", icon: StopCircle, label: "结束", color: "text-red-600", shape: "end", description: "流程结束" },
        { type: "process", icon: Box, label: "过程", color: "text-blue-600", shape: "process", description: "处理步骤" },
        { type: "decision", icon: Diamond, label: "判断", color: "text-yellow-600", shape: "decision", description: "条件判断" },
        { type: "data", icon: Square, label: "数据", color: "text-cyan-600", shape: "data", description: "数据/IO" },
        { type: "subprocess", icon: Box, label: "子流程", color: "text-purple-600", shape: "subprocess", description: "预定义过程" },
        { type: "delay", icon: AlertCircle, label: "延迟", color: "text-orange-600", shape: "delay", description: "延迟/等待" },
        { type: "merge", icon: Layers, label: "合并", color: "text-indigo-600", shape: "merge", description: "合并" },
        { type: "manual-input", icon: Square, label: "手动输入", color: "text-slate-600", shape: "manual-input", description: "手动输入" },
        { type: "manual-operation", icon: Square, label: "手动操作", color: "text-slate-700", shape: "manual-operation", description: "手动操作" },
        { type: "preparation", icon: Hexagon, label: "准备", color: "text-teal-600", shape: "preparation", description: "准备/初始化" },
        { type: "or-gate", icon: Octagon, label: "或", color: "text-amber-600", shape: "or", description: "逻辑或" },
      ],
    },
    {
      id: "container",
      name: "容器/分组",
      defaultExpanded: false,
      nodes: [
        { type: "container", icon: Container, label: "容器", color: "text-slate-600", shape: "container", description: "容器/组" },
        { type: "frame", icon: Square, label: "框架", color: "text-gray-600", shape: "frame", description: "分组框架" },
        { type: "swimlane-h", icon: Layers, label: "泳道(横)", color: "text-blue-500", shape: "swimlane-horizontal", description: "水平泳道" },
        { type: "swimlane-v", icon: Layers, label: "泳道(竖)", color: "text-blue-600", shape: "swimlane-vertical", description: "垂直泳道" },
        { type: "note", icon: FileText, label: "注释", color: "text-yellow-500", shape: "note", description: "注释框" },
        { type: "folder", icon: Folder, label: "文件夹", color: "text-amber-600", shape: "folder", description: "文件夹" },
        { type: "package", icon: Package, label: "包", color: "text-purple-500", shape: "package", description: "包/模块" },
      ],
    },
    {
      id: "architecture",
      name: "架构组件",
      defaultExpanded: false,
      nodes: [
        { type: "client", icon: Monitor, label: "客户端", color: "text-cyan-600", description: "客户端" },
        { type: "server", icon: Server, label: "服务器", color: "text-indigo-600", description: "服务器" },
        { type: "gateway", icon: Shield, label: "网关", color: "text-orange-600", description: "API网关" },
        { type: "api", icon: Globe, label: "API", color: "text-blue-600", description: "API服务" },
        { type: "service", icon: Box, label: "服务", color: "text-purple-600", description: "微服务" },
        { type: "database", icon: Database, label: "数据库", color: "text-green-600", description: "数据库" },
        { type: "cache", icon: Zap, label: "缓存", color: "text-yellow-600", description: "缓存" },
        { type: "queue", icon: Layers, label: "队列", color: "text-indigo-600", description: "消息队列" },
        { type: "storage", icon: HardDrive, label: "存储", color: "text-gray-600", description: "文件存储" },
        { type: "load-balancer", icon: Activity, label: "负载均衡", color: "text-emerald-600", description: "负载均衡器" },
        { type: "firewall", icon: Lock, label: "防火墙", color: "text-red-600", description: "防火墙" },
        { type: "cdn", icon: Network, label: "CDN", color: "text-sky-600", description: "CDN" },
      ],
    },
    {
      id: "user-device",
      name: "用户/设备",
      defaultExpanded: false,
      nodes: [
        { type: "user", icon: User, label: "用户", color: "text-blue-600", shape: "user", description: "单个用户" },
        { type: "users", icon: Users, label: "用户组", color: "text-blue-700", shape: "users", description: "用户组" },
        { type: "mobile", icon: Smartphone, label: "手机", color: "text-purple-600", shape: "mobile", description: "移动设备" },
        { type: "desktop", icon: Monitor, label: "桌面", color: "text-slate-600", shape: "desktop", description: "桌面设备" },
        { type: "tablet", icon: Monitor, label: "平板", color: "text-indigo-600", shape: "tablet", description: "平板设备" },
        { type: "iot", icon: Cpu, label: "IoT", color: "text-green-600", shape: "iot", description: "物联网设备" },
        { type: "network-device", icon: Wifi, label: "网络设备", color: "text-cyan-600", shape: "network", description: "网络设备" },
      ],
    },
    {
      id: "bpmn",
      name: "BPMN",
      defaultExpanded: false,
      nodes: [
        { type: "bpmn-start", icon: PlayCircle, label: "开始事件", color: "text-green-600", shape: "bpmn-start-event", description: "BPMN开始" },
        { type: "bpmn-end", icon: StopCircle, label: "结束事件", color: "text-red-600", shape: "bpmn-end-event", description: "BPMN结束" },
        { type: "bpmn-task", icon: Box, label: "任务", color: "text-blue-600", shape: "bpmn-task", description: "BPMN任务" },
        { type: "bpmn-gateway", icon: Diamond, label: "网关", color: "text-orange-600", shape: "bpmn-gateway", description: "BPMN网关" },
        { type: "bpmn-event", icon: AlertCircle, label: "中间事件", color: "text-yellow-600", shape: "bpmn-intermediate-event", description: "BPMN中间事件" },
        { type: "bpmn-subprocess", icon: Box, label: "子流程", color: "text-purple-600", shape: "bpmn-subprocess", description: "BPMN子流程" },
      ],
    },
  ];

  // 过滤节点
  const filteredCategories = useMemo(() => {
    if (!searchQuery.trim()) {
      return nodeCategories;
    }

    const query = searchQuery.toLowerCase();
    return nodeCategories
      .map((category) => ({
        ...category,
        nodes: category.nodes.filter((node) =>
          node.label.toLowerCase().includes(query)
        ),
      }))
      .filter((category) => category.nodes.length > 0);
  }, [searchQuery]);

  const handleAddNode = (
    type: string,
    shape?: string,
    iconType?: string,
    color?: string
  ) => {
    // Convert Tailwind color classes to CSS values
    const colorMap: Record<string, string> = {
      "text-green-600": "#16a34a",
      "text-red-600": "#dc2626",
      "text-orange-600": "#ea580c",
      "text-blue-600": "#2563eb",
      "text-blue-500": "#3b82f6",
      "text-blue-700": "#1d4ed8",
      "text-yellow-600": "#ca8a04",
      "text-yellow-500": "#eab308",
      "text-cyan-600": "#0891b2",
      "text-purple-600": "#9333ea",
      "text-purple-500": "#a855f7",
      "text-indigo-600": "#4f46e5",
      "text-gray-600": "#4b5563",
      "text-slate-600": "#475569",
      "text-slate-700": "#334155",
      "text-teal-600": "#0d9488",
      "text-sky-600": "#0284c7",
      "text-amber-600": "#d97706",
      "text-emerald-600": "#059669",
    };

    const newNode = {
      id: `node-${Date.now()}`,
      type: type === "default" ? "default" : type,
      position: { x: Math.random() * 400 + 100, y: Math.random() * 400 + 100 },
      data: {
        label: `New ${type}`,
        ...(shape && { shape }),
        ...(iconType && { iconType }),
        ...(color && { color: colorMap[color] || color }),
      },
    };
    setNodes([...nodes, newNode]);
  };

  const toggleCategory = (categoryId: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(categoryId)) {
      newExpanded.delete(categoryId);
    } else {
      newExpanded.add(categoryId);
    }
    setExpandedCategories(newExpanded);
  };

  return (
    <>
      {/* 侧边面板 */}
      <aside className="flex w-72 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
        {/* 标题 */}
        <div className="border-b border-slate-200 px-4 py-4 dark:border-slate-800">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-white">
            节点库
          </h2>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-1">
            拖拽或点击添加节点到画布
          </p>
        </div>

        {/* 搜索框 */}
        <div className="px-4 py-3 border-b border-slate-200 dark:border-slate-800">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="搜索节点..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white pl-9 pr-3 py-2 text-sm
                       placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1
                       focus:ring-blue-500 dark:border-slate-600 dark:bg-slate-800 dark:text-white"
            />
          </div>
        </div>

        {/* 节点分类列表 */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
          {filteredCategories.map((category) => {
            const isExpanded = expandedCategories.has(category.id);
            const isEmpty = category.nodes.length === 0;

            return (
              <div key={category.id}>
                {/* 分类标题 */}
                <button
                  onClick={() => !isEmpty && toggleCategory(category.id)}
                  disabled={isEmpty}
                  className="flex w-full items-center justify-between rounded-lg px-2 py-2
                           text-sm font-medium text-slate-700 hover:bg-slate-100
                           dark:text-slate-300 dark:hover:bg-slate-800
                           disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="flex items-center gap-2">
                    {isExpanded ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                    {category.name}
                    <span className="text-xs text-slate-400">
                      ({category.nodes.length})
                    </span>
                  </span>
                </button>

                {/* 节点网格 */}
                {isExpanded && !isEmpty && (
                  <div className="mt-2 grid grid-cols-3 gap-2">
                    {category.nodes.map(({ type, icon: Icon, iconType, label, color, shape, description }) => (
                      <button
                        key={`${type}-${shape || 'default'}-${label}`}
                        onClick={() => handleAddNode(type, shape, iconType, color)}
                        className="group flex flex-col items-center justify-center rounded-lg
                                 border-2 border-slate-200 bg-white p-3 transition-all
                                 hover:border-blue-400 hover:shadow-md
                                 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-blue-500"
                        title={description || `添加 ${label}`}
                      >
                        <Icon className={`h-6 w-6 ${color} mb-1`} />
                        <span className="text-xs font-medium text-slate-700 dark:text-slate-300 text-center">
                          {label}
                        </span>
                      </button>
                    ))}
                  </div>
                )}

                {/* 空状态提示 */}
                {isExpanded && isEmpty && (
                  <div className="mt-2 rounded-lg border-2 border-dashed border-slate-200
                                bg-slate-50 px-4 py-8 text-center dark:border-slate-700 dark:bg-slate-800/50">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      即将推出
                    </p>
                  </div>
                )}
              </div>
            );
          })}

          {/* 无搜索结果 */}
          {searchQuery && filteredCategories.length === 0 && (
            <div className="rounded-lg border-2 border-dashed border-slate-200 bg-slate-50
                          px-4 py-8 text-center dark:border-slate-700 dark:bg-slate-800/50">
              <Search className="mx-auto h-8 w-8 text-slate-400 mb-2" />
              <p className="text-sm text-slate-500 dark:text-slate-400">
                未找到匹配的节点
              </p>
              <p className="text-xs text-slate-400 mt-1">
                尝试其他关键词
              </p>
            </div>
          )}
        </div>

        {/* 功能按钮区域 */}
        <div className="border-t border-slate-200 px-4 py-3 space-y-2 dark:border-slate-800">
          <button
            onClick={() => setIsImageUploadOpen(true)}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm
                     text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            <ImageIcon className="h-5 w-5 text-indigo-600" />
            <span>上传架构图</span>
          </button>

          <button
            onClick={() => setIsPrompterOpen(true)}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm
                     text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            <Wand2 className="h-5 w-5 text-purple-600" />
            <span>AI Prompter</span>
          </button>

          <button
            onClick={() => setIsChatGeneratorOpen(true)}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm
                     text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            <MessageSquare className="h-5 w-5 text-green-600" />
            <span>Chat Generator</span>
          </button>

          <button
            onClick={() => setIsDocumentUploadOpen(true)}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm
                     text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            <FileText className="h-5 w-5 text-green-600" />
            <span>上传文档 (RAG)</span>
          </button>

          <div className="h-px bg-slate-200 dark:bg-slate-700 my-2" />

          <button
            onClick={() => setIsConfigOpen(true)}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm
                     text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
          >
            <Settings className="h-5 w-5 text-slate-600 dark:text-slate-400" />
            <span>设置</span>
          </button>
        </div>
      </aside>

      {/* 模型配置弹窗 */}
      <ModelConfigModal
        isOpen={isConfigOpen}
        onClose={() => setIsConfigOpen(false)}
      />

      {/* 图片上传弹窗 */}
      <ImageUploadModal
        isOpen={isImageUploadOpen}
        onClose={() => setIsImageUploadOpen(false)}
      />

      {/* AI Prompter 弹窗 */}
      <PrompterModal
        isOpen={isPrompterOpen}
        onClose={() => setIsPrompterOpen(false)}
      />

      {/* 文档上传弹窗（Phase 4 RAG） */}
      <DocumentUploadModal
        isOpen={isDocumentUploadOpen}
        onClose={() => setIsDocumentUploadOpen(false)}
      />

      {/* Chat Flowchart Generator 弹窗（Phase 5） */}
      <ChatGeneratorModal
        isOpen={isChatGeneratorOpen}
        onClose={() => setIsChatGeneratorOpen(false)}
      />
    </>
  );
}
