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
  shape?: "rectangle" | "circle" | "diamond" | "start-event" | "end-event" | "intermediate-event" | "task";
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
    new Set(["architecture"])
  );

  const { nodes, setNodes } = useArchitectStore();

  // 节点分类配置
  const nodeCategories: NodeCategory[] = [
    {
      id: "architecture",
      name: "架构节点",
      defaultExpanded: true,
      nodes: [
        { type: "client", icon: Monitor, label: "Client", color: "text-cyan-600" },
        { type: "gateway", icon: Shield, label: "Gateway", color: "text-orange-600" },
        { type: "api", icon: Globe, label: "API", color: "text-blue-600" },
        { type: "service", icon: Box, label: "Service", color: "text-purple-600" },
        { type: "cache", icon: Zap, label: "Cache", color: "text-yellow-600" },
        { type: "queue", icon: Layers, label: "Queue", color: "text-indigo-600" },
        { type: "database", icon: Database, label: "Database", color: "text-green-600" },
        { type: "storage", icon: HardDrive, label: "Storage", color: "text-gray-600" },
      ],
    },
    {
      id: "bpmn",
      name: "BPMN 节点",
      defaultExpanded: false,
      nodes: [
        { type: "default", icon: PlayCircle, iconType: "play-circle", label: "Start", color: "text-green-600", shape: "start-event" },
        { type: "default", icon: StopCircle, iconType: "stop-circle", label: "End", color: "text-red-600", shape: "end-event" },
        { type: "default", icon: Box, iconType: "box", label: "Task", color: "text-blue-600", shape: "task" },
        { type: "gateway", icon: Shield, label: "Gateway", color: "text-orange-600", shape: "diamond" },
        { type: "default", icon: AlertCircle, iconType: "alert-circle", label: "Event", color: "text-yellow-600", shape: "intermediate-event" },
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
    shape?: "rectangle" | "circle" | "diamond" | "start-event" | "end-event" | "intermediate-event" | "task",
    iconType?: string,
    color?: string
  ) => {
    // Convert Tailwind color classes to CSS values
    const colorMap: Record<string, string> = {
      "text-green-600": "#16a34a",
      "text-red-600": "#dc2626",
      "text-orange-600": "#ea580c",
      "text-blue-600": "#2563eb",
      "text-yellow-600": "#ca8a04",
      "text-cyan-600": "#0891b2",
      "text-purple-600": "#9333ea",
      "text-indigo-600": "#4f46e5",
      "text-gray-600": "#4b5563",
    };

    const newNode = {
      id: `node-${Date.now()}`,
      type,
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
                    {category.nodes.map(({ type, icon: Icon, iconType, label, color, shape }) => (
                      <button
                        key={`${type}-${shape || 'default'}-${label}`}
                        onClick={() => handleAddNode(type, shape, iconType, color)}
                        className="group flex flex-col items-center justify-center rounded-lg
                                 border-2 border-slate-200 bg-white p-3 transition-all
                                 hover:border-blue-400 hover:shadow-md
                                 dark:border-slate-700 dark:bg-slate-800 dark:hover:border-blue-500"
                        title={`Add ${label}`}
                      >
                        <Icon className={`h-6 w-6 ${color} mb-1`} />
                        <span className="text-xs font-medium text-slate-700 dark:text-slate-300">
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
