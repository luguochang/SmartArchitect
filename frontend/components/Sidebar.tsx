"use client";

import { useState, useMemo, useCallback } from "react";
import { Search, ChevronDown, ChevronRight } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { ShapeRenderer } from "./nodes/ShapeRenderer";
import { NodeShape } from "@/lib/utils/nodeShapes";

// 节点配置接口
interface ShapeLibraryItem {
  id: string;
  label: string;
  shape: NodeShape;
  iconType?: string;
  color: string;
  description?: string;
  // 节点配置
  nodeConfig: {
    type: string;
    shape?: NodeShape;
    iconType?: string;
  };
}

interface NodeCategory {
  id: string;
  name: string;
  items: ShapeLibraryItem[];
  defaultExpanded: boolean;
}

export function Sidebar() {
  const [searchQuery, setSearchQuery] = useState("");
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(
    new Set(["basic", "flowchart", "architecture"])
  );

  const { nodes, setNodes } = useArchitectStore();

  // 颜色映射表（Tailwind色值转CSS）
  const colorMap: Record<string, string> = {
    "text-green-600": "#16a34a",
    "text-red-600": "#dc2626",
    "text-orange-600": "#ea580c",
    "text-blue-600": "#2563eb",
    "text-blue-500": "#3b82f6",
    "text-yellow-600": "#ca8a04",
    "text-cyan-600": "#0891b2",
    "text-purple-600": "#9333ea",
    "text-indigo-600": "#4f46e5",
    "text-gray-600": "#4b5563",
    "text-slate-600": "#475569",
    "text-teal-600": "#0d9488",
    "text-sky-600": "#0284c7",
    "text-amber-600": "#d97706",
    "text-emerald-600": "#059669",
  };

  // 节点库配置 - 参考 draw.io 设计
  const nodeCategories: NodeCategory[] = [
    {
      id: "basic",
      name: "基础图形",
      defaultExpanded: true,
      items: [
        {
          id: "rectangle",
          label: "矩形",
          shape: "rectangle",
          iconType: "square",
          color: colorMap["text-blue-600"],
          description: "基础矩形",
          nodeConfig: { type: "default", shape: "rectangle", iconType: "rectangle" },
        },
        {
          id: "rounded-rectangle",
          label: "圆角矩形",
          shape: "rounded-rectangle",
          iconType: "rounded-rectangle",
          color: colorMap["text-blue-500"],
          description: "圆角矩形",
          nodeConfig: { type: "default", shape: "rounded-rectangle", iconType: "rounded-rectangle" },
        },
        {
          id: "circle",
          label: "圆形",
          shape: "circle",
          iconType: "circle",
          color: colorMap["text-green-600"],
          description: "圆形",
          nodeConfig: { type: "default", shape: "circle", iconType: "circle" },
        },
        {
          id: "diamond",
          label: "菱形",
          shape: "diamond",
          iconType: "diamond",
          color: colorMap["text-yellow-600"],
          description: "决策/判断",
          nodeConfig: { type: "default", shape: "diamond", iconType: "diamond" },
        },
        {
          id: "hexagon",
          label: "六边形",
          shape: "hexagon",
          iconType: "hexagon",
          color: colorMap["text-purple-600"],
          description: "六边形",
          nodeConfig: { type: "default", shape: "hexagon", iconType: "hexagon" },
        },
        {
          id: "triangle",
          label: "三角形",
          shape: "triangle",
          iconType: "triangle",
          color: colorMap["text-orange-600"],
          description: "三角形",
          nodeConfig: { type: "default", shape: "triangle", iconType: "triangle" },
        },
        {
          id: "parallelogram",
          label: "平行四边形",
          shape: "parallelogram",
          iconType: "data",
          color: colorMap["text-cyan-600"],
          description: "数据/输入输出",
          nodeConfig: { type: "default", shape: "parallelogram", iconType: "data" },
        },
        {
          id: "trapezoid",
          label: "梯形",
          shape: "trapezoid",
          iconType: "manual-operation",
          color: colorMap["text-indigo-600"],
          description: "手动操作",
          nodeConfig: { type: "default", shape: "trapezoid", iconType: "manual-operation" },
        },
        {
          id: "star",
          label: "星形",
          shape: "star",
          iconType: "star",
          color: colorMap["text-yellow-600"],
          description: "星形",
          nodeConfig: { type: "default", shape: "star", iconType: "star" },
        },
        {
          id: "cloud",
          label: "云形",
          shape: "cloud",
          iconType: "cloud",
          color: colorMap["text-sky-600"],
          description: "云/注释",
          nodeConfig: { type: "default", shape: "cloud", iconType: "cloud" },
        },
        {
          id: "cylinder",
          label: "圆柱",
          shape: "cylinder",
          iconType: "database",
          color: colorMap["text-teal-600"],
          description: "数据库/存储",
          nodeConfig: { type: "default", shape: "cylinder", iconType: "database" },
        },
        {
          id: "document",
          label: "文档",
          shape: "document",
          iconType: "file-text",
          color: colorMap["text-slate-600"],
          description: "文档/报告",
          nodeConfig: { type: "default", shape: "document", iconType: "file-text" },
        },
      ],
    },
    {
      id: "flowchart",
      name: "流程图",
      defaultExpanded: true,
      items: [
        {
          id: "start",
          label: "开始",
          shape: "start",
          iconType: "play-circle",
          color: colorMap["text-green-600"],
          description: "流程开始",
          nodeConfig: { type: "default", shape: "start", iconType: "play-circle" },
        },
        {
          id: "end",
          label: "结束",
          shape: "end",
          iconType: "stop-circle",
          color: colorMap["text-red-600"],
          description: "流程结束",
          nodeConfig: { type: "default", shape: "end", iconType: "stop-circle" },
        },
        {
          id: "process",
          label: "过程",
          shape: "process",
          iconType: "process",
          color: colorMap["text-blue-600"],
          description: "处理步骤",
          nodeConfig: { type: "default", shape: "process", iconType: "process" },
        },
        {
          id: "decision",
          label: "判断",
          shape: "decision",
          iconType: "decision",
          color: colorMap["text-yellow-600"],
          description: "条件判断",
          nodeConfig: { type: "default", shape: "decision", iconType: "decision" },
        },
        {
          id: "data",
          label: "数据",
          shape: "data",
          iconType: "data",
          color: colorMap["text-cyan-600"],
          description: "数据/IO",
          nodeConfig: { type: "default", shape: "data", iconType: "data" },
        },
        {
          id: "subprocess",
          label: "子流程",
          shape: "subprocess",
          iconType: "subprocess",
          color: colorMap["text-purple-600"],
          description: "预定义过程",
          nodeConfig: { type: "default", shape: "subprocess", iconType: "subprocess" },
        },
        {
          id: "delay",
          label: "延迟",
          shape: "delay",
          iconType: "alert-circle",
          color: colorMap["text-orange-600"],
          description: "延迟/等待",
          nodeConfig: { type: "default", shape: "delay", iconType: "alert-circle" },
        },
        {
          id: "merge",
          label: "合并",
          shape: "merge",
          iconType: "layers",
          color: colorMap["text-indigo-600"],
          description: "合并",
          nodeConfig: { type: "default", shape: "merge", iconType: "layers" },
        },
        {
          id: "manual-input",
          label: "手动输入",
          shape: "manual-input",
          iconType: "manual-input",
          color: colorMap["text-slate-600"],
          description: "手动输入",
          nodeConfig: { type: "default", shape: "manual-input", iconType: "manual-input" },
        },
        {
          id: "preparation",
          label: "准备",
          shape: "preparation",
          iconType: "preparation",
          color: colorMap["text-teal-600"],
          description: "准备/初始化",
          nodeConfig: { type: "default", shape: "preparation", iconType: "preparation" },
        },
      ],
    },
    {
      id: "bpmn",
      name: "BPMN",
      defaultExpanded: false,
      items: [
        {
          id: "bpmn-start",
          label: "开始事件",
          shape: "bpmn-start-event",
          iconType: "play-circle",
          color: colorMap["text-green-600"],
          description: "BPMN开始",
          nodeConfig: { type: "default", shape: "bpmn-start-event", iconType: "play-circle" },
        },
        {
          id: "bpmn-end",
          label: "结束事件",
          shape: "bpmn-end-event",
          iconType: "stop-circle",
          color: colorMap["text-red-600"],
          description: "BPMN结束",
          nodeConfig: { type: "default", shape: "bpmn-end-event", iconType: "stop-circle" },
        },
        {
          id: "bpmn-intermediate",
          label: "中间事件",
          shape: "bpmn-intermediate-event",
          iconType: "alert-circle",
          color: colorMap["text-yellow-600"],
          description: "BPMN中间事件",
          nodeConfig: { type: "default", shape: "bpmn-intermediate-event", iconType: "alert-circle" },
        },
        {
          id: "bpmn-task",
          label: "任务",
          shape: "bpmn-task",
          iconType: "process",
          color: colorMap["text-blue-600"],
          description: "BPMN任务",
          nodeConfig: { type: "default", shape: "bpmn-task", iconType: "process" },
        },
        {
          id: "bpmn-gateway",
          label: "网关",
          shape: "bpmn-gateway",
          iconType: "decision",
          color: colorMap["text-orange-600"],
          description: "BPMN网关",
          nodeConfig: { type: "default", shape: "bpmn-gateway", iconType: "decision" },
        },
        {
          id: "bpmn-subprocess",
          label: "子流程",
          shape: "bpmn-subprocess",
          iconType: "subprocess",
          color: colorMap["text-purple-600"],
          description: "BPMN子流程",
          nodeConfig: { type: "default", shape: "bpmn-subprocess", iconType: "subprocess" },
        },
      ],
    },
    {
      id: "architecture",
      name: "架构组件",
      defaultExpanded: false,
      items: [
        {
          id: "api",
          label: "API",
          shape: "rounded-rectangle",
          iconType: "api",
          color: colorMap["text-blue-600"],
          description: "API服务",
          nodeConfig: { type: "api", iconType: "api" },
        },
        {
          id: "service",
          label: "服务",
          shape: "rounded-rectangle",
          iconType: "service",
          color: colorMap["text-purple-600"],
          description: "微服务",
          nodeConfig: { type: "service", iconType: "service" },
        },
        {
          id: "database",
          label: "数据库",
          shape: "cylinder",
          iconType: "database",
          color: colorMap["text-green-600"],
          description: "数据库",
          nodeConfig: { type: "database", iconType: "database" },
        },
        {
          id: "cache",
          label: "缓存",
          shape: "rounded-rectangle",
          iconType: "cache",
          color: colorMap["text-yellow-600"],
          description: "缓存",
          nodeConfig: { type: "cache", iconType: "cache" },
        },
        {
          id: "queue",
          label: "队列",
          shape: "rounded-rectangle",
          iconType: "queue",
          color: colorMap["text-indigo-600"],
          description: "消息队列",
          nodeConfig: { type: "queue", iconType: "queue" },
        },
        {
          id: "storage",
          label: "存储",
          shape: "cylinder",
          iconType: "storage",
          color: colorMap["text-gray-600"],
          description: "文件存储",
          nodeConfig: { type: "storage", iconType: "storage" },
        },
        {
          id: "gateway",
          label: "网关",
          shape: "rounded-rectangle",
          iconType: "gateway",
          color: colorMap["text-orange-600"],
          description: "API网关",
          nodeConfig: { type: "gateway", iconType: "gateway" },
        },
        {
          id: "client",
          label: "客户端",
          shape: "rounded-rectangle",
          iconType: "client",
          color: colorMap["text-cyan-600"],
          description: "客户端",
          nodeConfig: { type: "client", iconType: "client" },
        },
        {
          id: "layerFrame",
          label: "Layer Frame",
          shape: "frame",
          iconType: "layerFrame",
          color: colorMap["text-emerald-600"],
          description: "层容器",
          nodeConfig: { type: "layerFrame", iconType: "layerFrame" },
        },
      ],
    },
  ];

  // 搜索过滤
  const filteredCategories = useMemo(() => {
    if (!searchQuery.trim()) {
      return nodeCategories;
    }

    const query = searchQuery.toLowerCase();
    return nodeCategories
      .map((category) => ({
        ...category,
        items: category.items.filter((item) => item.label.toLowerCase().includes(query)),
      }))
      .filter((category) => category.items.length > 0);
  }, [searchQuery]);

  // 添加节点到画布
  const handleAddNode = useCallback(
    (item: ShapeLibraryItem) => {
      const newNode = {
        id: `node-${Date.now()}`,
        type: item.nodeConfig.type,
        position: {
          x: Math.random() * 400 + 100,
          y: Math.random() * 400 + 100,
        },
        data: {
          label: `${item.label}`,
          ...(item.nodeConfig.shape && { shape: item.nodeConfig.shape }),
          ...(item.color && { color: item.color }),
          ...(item.nodeConfig.iconType && { iconType: item.nodeConfig.iconType }),
        },
      };
      setNodes([...nodes, newNode]);
    },
    [nodes, setNodes]
  );

  // 拖拽开始
  const handleDragStart = useCallback(
    (event: React.DragEvent, item: ShapeLibraryItem) => {
      const payload = {
        type: item.nodeConfig.type,
        shape: item.nodeConfig.shape,
        color: item.color,
        label: item.label,
        iconType: item.nodeConfig.iconType,
      };
      event.dataTransfer.setData("application/reactflow", JSON.stringify(payload));
      event.dataTransfer.effectAllowed = "move";

      // 设置拖拽图像（ghost image）
      const dragImage = document.createElement("div");
      dragImage.style.position = "absolute";
      dragImage.style.top = "-1000px";
      dragImage.style.padding = "8px";
      dragImage.style.background = "white";
      dragImage.style.borderRadius = "8px";
      dragImage.style.boxShadow = "0 4px 12px rgba(0,0,0,0.15)";
      dragImage.innerHTML = `<div style="display: flex; align-items: center; gap: 8px;">
        <span style="font-size: 12px; color: #64748b;">拖拽添加</span>
        <strong style="color: ${item.color};">${item.label}</strong>
      </div>`;
      document.body.appendChild(dragImage);
      event.dataTransfer.setDragImage(dragImage, 20, 20);
      setTimeout(() => document.body.removeChild(dragImage), 0);
    },
    []
  );

  // 切换分类展开/折叠
  const toggleCategory = useCallback(
    (categoryId: string) => {
      const newExpanded = new Set(expandedCategories);
      if (newExpanded.has(categoryId)) {
        newExpanded.delete(categoryId);
      } else {
        newExpanded.add(categoryId);
      }
      setExpandedCategories(newExpanded);
    },
    [expandedCategories]
  );

  return (
    <aside className="flex w-72 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      {/* 标题 */}
      <div className="border-b border-slate-200 px-4 py-4 dark:border-slate-800">
        <h2 className="text-lg font-semibold text-slate-900 dark:text-white">节点库</h2>
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
          const isEmpty = category.items.length === 0;

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
                  <span className="text-xs text-slate-400">({category.items.length})</span>
                </span>
              </button>

              {/* 节点网格 */}
              {isExpanded && !isEmpty && (
                <div className="mt-2 grid grid-cols-3 gap-2">
                  {category.items.map((item) => (
                    <button
                      key={item.id}
                      onClick={() => handleAddNode(item)}
                      draggable
                      onDragStart={(event) => handleDragStart(event, item)}
                      className="group flex flex-col items-center justify-center rounded-lg
                               border-2 border-slate-200 bg-white p-3 transition-all
                               hover:border-blue-400 hover:shadow-md active:scale-95
                               dark:border-slate-700 dark:bg-slate-800 dark:hover:border-blue-500"
                      title={item.description || `添加 ${item.label}`}
                    >
                      {/* 使用 ShapeRenderer 渲染预览 */}
                      <div className="mb-1">
                        <ShapeRenderer
                          shape={item.shape}
                          iconType={item.iconType}
                          color={item.color}
                          size="small"
                          showLabel={false}
                          showIcon={true}
                        />
                      </div>
                      <span className="text-xs font-medium text-slate-700 dark:text-slate-300 text-center">
                        {item.label}
                      </span>
                    </button>
                  ))}
                </div>
              )}

              {/* 空状态提示 */}
              {isExpanded && isEmpty && (
                <div
                  className="mt-2 rounded-lg border-2 border-dashed border-slate-200
                            bg-slate-50 px-4 py-8 text-center dark:border-slate-700 dark:bg-slate-800/50"
                >
                  <p className="text-sm text-slate-500 dark:text-slate-400">即将推出</p>
                </div>
              )}
            </div>
          );
        })}

        {/* 无搜索结果 */}
        {searchQuery && filteredCategories.length === 0 && (
          <div
            className="rounded-lg border-2 border-dashed border-slate-200 bg-slate-50
                      px-4 py-8 text-center dark:border-slate-700 dark:bg-slate-800/50"
          >
            <Search className="mx-auto h-8 w-8 text-slate-400 mb-2" />
            <p className="text-sm text-slate-500 dark:text-slate-400">未找到匹配的节点</p>
            <p className="text-xs text-slate-400 mt-1">尝试其他关键词</p>
          </div>
        )}
      </div>
    </aside>
  );
}
