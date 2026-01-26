"use client";

import { useCallback } from "react";
import ReactFlow, {
  Background,
  Controls,
  Panel,
  Node,
  Edge,
  ReactFlowProvider,
} from "reactflow";
import "reactflow/dist/style.css";

// 导入当前自定义节点
import { ApiNode } from "@/components/nodes/ApiNode";
import { DatabaseNode } from "@/components/nodes/DatabaseNode";
import { ServiceNode } from "@/components/nodes/ServiceNode";
import { CacheNode } from "@/components/nodes/CacheNode";
import { DefaultNode } from "@/components/nodes/DefaultNode";

// 准备对比的节点数据
const currentStyleNodes: Node[] = [
  {
    id: "1",
    type: "api",
    position: { x: 100, y: 100 },
    data: { label: "API Gateway" },
  },
  {
    id: "2",
    type: "service",
    position: { x: 100, y: 220 },
    data: { label: "Auth Service" },
  },
  {
    id: "3",
    type: "database",
    position: { x: 350, y: 100 },
    data: { label: "PostgreSQL" },
  },
  {
    id: "4",
    type: "cache",
    position: { x: 350, y: 220 },
    data: { label: "Redis Cache" },
  },
  {
    id: "5",
    type: "default",
    position: { x: 225, y: 340 },
    data: { label: "Processing" },
  },
];

const currentStyleEdges: Edge[] = [
  { id: "e1-2", source: "1", target: "2", animated: true },
  { id: "e1-3", source: "1", target: "3" },
  { id: "e2-4", source: "2", target: "4" },
  { id: "e2-5", source: "2", target: "5" },
];

// 自定义节点类型映射
const currentNodeTypes = {
  api: ApiNode,
  service: ServiceNode,
  database: DatabaseNode,
  cache: CacheNode,
  default: DefaultNode,
};

function CurrentStyleCanvas() {
  return (
    <div className="h-[600px] w-full rounded-xl border-2 border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
      <ReactFlow
        nodes={currentStyleNodes}
        edges={currentStyleEdges}
        nodeTypes={currentNodeTypes}
        fitView
        style={{
          background: "radial-gradient(circle at 20% 20%, rgba(99,102,241,0.08), transparent 35%), var(--canvas-background)",
        }}
      >
        <Background color="var(--canvas-grid)" gap={18} size={0.75} />
        <Controls className="!bg-white/90 !rounded-lg !shadow-md dark:!bg-slate-900/90" />
        <Panel position="top-left">
          <div className="rounded-lg bg-indigo-600 px-4 py-2 text-sm text-white shadow-lg">
            当前风格（自定义节点）
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

// React Flow UI风格的简化版本（基于shadcn思路）
// 注意：这里先用简化版演示概念，真正的React Flow UI需要安装依赖
function SimplifiedRFUINode({ data }: any) {
  return (
    <div className="rounded-lg border border-slate-300 bg-white px-4 py-3 shadow-sm dark:border-slate-600 dark:bg-slate-800">
      <div className="mb-1 text-xs font-medium text-slate-500 dark:text-slate-400">
        {data.type?.toUpperCase() || "NODE"}
      </div>
      <div className="text-sm font-semibold text-slate-900 dark:text-white">
        {data.label}
      </div>
    </div>
  );
}

const rfuiStyleNodes: Node[] = currentStyleNodes.map(node => ({
  ...node,
  id: `rfui-${node.id}`,
  type: "rfui",
  data: { ...node.data, type: node.type },
}));

const rfuiStyleEdges: Edge[] = currentStyleEdges.map(edge => ({
  ...edge,
  id: `rfui-${edge.id}`,
  source: `rfui-${edge.source}`,
  target: `rfui-${edge.target}`,
}));

const rfuiNodeTypes = {
  rfui: SimplifiedRFUINode,
};

function RFUIStyleCanvas() {
  return (
    <div className="h-[600px] w-full rounded-xl border-2 border-slate-200 bg-white dark:border-slate-700 dark:bg-slate-900">
      <ReactFlow
        nodes={rfuiStyleNodes}
        edges={rfuiStyleEdges}
        nodeTypes={rfuiNodeTypes}
        fitView
      >
        <Background color="#e5e7eb" gap={16} size={1} />
        <Controls className="!bg-white/90 !rounded-lg !shadow-md dark:!bg-slate-900/90" />
        <Panel position="top-left">
          <div className="rounded-lg bg-emerald-600 px-4 py-2 text-sm text-white shadow-lg">
            React Flow UI风格（简化版）
          </div>
        </Panel>
      </ReactFlow>
    </div>
  );
}

// 对比指标组件
function ComparisonMetrics() {
  return (
    <div className="mt-8 grid grid-cols-1 gap-6 md:grid-cols-2">
      <div className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
        <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-white">
          当前自定义节点
        </h3>

        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-green-100 p-1 dark:bg-green-900">
              <svg className="h-4 w-4 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-white">玻璃态视觉效果</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">渐变背景、阴影、现代设计</div>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="rounded-full bg-green-100 p-1 dark:bg-green-900">
              <svg className="h-4 w-4 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-white">完整功能</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">双击编辑、图标、主题支持</div>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="rounded-full bg-yellow-100 p-1 dark:bg-yellow-900">
              <svg className="h-4 w-4 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-white">代码重复</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">11个组件，每个~115行代码</div>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="rounded-full bg-yellow-100 p-1 dark:bg-yellow-900">
              <svg className="h-4 w-4 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-white">维护成本</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">样式调整需修改多个文件</div>
            </div>
          </div>
        </div>

        <div className="mt-4 rounded-lg bg-slate-50 p-3 dark:bg-slate-900">
          <div className="text-xs text-slate-600 dark:text-slate-300">
            <strong>代码示例：</strong>
            <pre className="mt-2 overflow-x-auto text-[10px]">
{`// ApiNode.tsx (~115行)
export const ApiNode = ({ id, data }) => {
  const [isEditing, setIsEditing] = useState(false);
  // ... 状态管理

  return (
    <div className="glass-node ...">
      {/* 手动实现所有交互 */}
    </div>
  );
};`}
            </pre>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
        <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-white">
          React Flow UI风格
        </h3>

        <div className="space-y-3">
          <div className="flex items-start gap-3">
            <div className="rounded-full bg-green-100 p-1 dark:bg-green-900">
              <svg className="h-4 w-4 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-white">代码复用</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">BaseNodeHeader等构建块</div>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="rounded-full bg-green-100 p-1 dark:bg-green-900">
              <svg className="h-4 w-4 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-white">易于维护</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">shadcn CLI管理，统一更新</div>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="rounded-full bg-green-100 p-1 dark:bg-green-900">
              <svg className="h-4 w-4 text-green-600 dark:text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-white">现代技术栈</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">React 19 + Tailwind 4</div>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="rounded-full bg-red-100 p-1 dark:bg-red-900">
              <svg className="h-4 w-4 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-white">需要迁移工作</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">升级React 19 + 重构节点</div>
            </div>
          </div>

          <div className="flex items-start gap-3">
            <div className="rounded-full bg-yellow-100 p-1 dark:bg-yellow-900">
              <svg className="h-4 w-4 text-yellow-600 dark:text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="flex-1">
              <div className="text-sm font-medium text-slate-900 dark:text-white">视觉风格调整</div>
              <div className="text-xs text-slate-500 dark:text-slate-400">可能失去玻璃态特色</div>
            </div>
          </div>
        </div>

        <div className="mt-4 rounded-lg bg-slate-50 p-3 dark:bg-slate-900">
          <div className="text-xs text-slate-600 dark:text-slate-300">
            <strong>代码示例：</strong>
            <pre className="mt-2 overflow-x-auto text-[10px]">
{`// 使用BaseNodeHeader (~30行)
import { BaseNodeHeader } from '@xyflow/react-flow-ui';

export const ApiNode = ({ id, data }) => (
  <div className="custom-glass-style">
    <BaseNodeHeader
      icon={<Globe />}
      title={data.label}
      onEdit={(newLabel) => update(id, newLabel)}
    />
  </div>
);`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ReactFlowUIDemo() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-8 dark:from-slate-900 dark:to-slate-800">
      <div className="mx-auto max-w-7xl">
        {/* 标题 */}
        <div className="mb-8 text-center">
          <h1 className="mb-2 text-4xl font-bold text-slate-900 dark:text-white">
            React Flow UI 对比 Demo
          </h1>
          <p className="text-lg text-slate-600 dark:text-slate-300">
            评估是否值得从自定义节点迁移到 React Flow UI
          </p>
        </div>

        {/* 对比画布 */}
        <div className="mb-8 grid grid-cols-1 gap-8 lg:grid-cols-2">
          <div>
            <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-white">
              🎨 当前风格（Phase 1-5）
            </h2>
            <ReactFlowProvider>
              <CurrentStyleCanvas />
            </ReactFlowProvider>
          </div>

          <div>
            <h2 className="mb-4 text-xl font-semibold text-slate-900 dark:text-white">
              ✨ React Flow UI风格（概念演示）
            </h2>
            <ReactFlowProvider>
              <RFUIStyleCanvas />
            </ReactFlowProvider>
          </div>
        </div>

        {/* 对比指标 */}
        <ComparisonMetrics />

        {/* 说明 */}
        <div className="mt-8 rounded-xl border border-amber-200 bg-amber-50 p-6 dark:border-amber-900 dark:bg-amber-950">
          <h3 className="mb-3 flex items-center gap-2 text-lg font-semibold text-amber-900 dark:text-amber-100">
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            重要说明
          </h3>
          <div className="space-y-2 text-sm text-amber-900 dark:text-amber-100">
            <p>
              <strong>1. 右侧是简化演示版本：</strong>
              真正的React Flow UI需要安装 <code className="rounded bg-amber-100 px-1 dark:bg-amber-900">@xyflow/react-flow-ui</code> 和 shadcn/ui。
            </p>
            <p>
              <strong>2. 依赖升级要求：</strong>
              React Flow UI最新版本要求 React 19 + Tailwind 4，当前项目使用 React 18 + Tailwind 3。
            </p>
            <p>
              <strong>3. 可以保留视觉风格：</strong>
              即使使用React Flow UI的构建块，也可以覆盖CSS保留玻璃态效果。
            </p>
            <p>
              <strong>4. 迁移成本：</strong>
              需要重构11个节点组件 + 升级依赖，预计2-3天工作量。
            </p>
          </div>
        </div>

        {/* 安装指南 */}
        <div className="mt-8 rounded-xl border border-slate-200 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
          <h3 className="mb-4 text-lg font-semibold text-slate-900 dark:text-white">
            📦 如果要尝试React Flow UI，需要执行：
          </h3>
          <div className="space-y-3">
            <div className="rounded-lg bg-slate-900 p-4 text-sm text-green-400 dark:bg-slate-950">
              <div className="mb-2 text-slate-400"># 1. 升级到React 19</div>
              <code>npm install react@^19 react-dom@^19</code>
            </div>
            <div className="rounded-lg bg-slate-900 p-4 text-sm text-green-400 dark:bg-slate-950">
              <div className="mb-2 text-slate-400"># 2. 升级到Tailwind 4</div>
              <code>npm install tailwindcss@^4 autoprefixer@^11 postcss@^9</code>
            </div>
            <div className="rounded-lg bg-slate-900 p-4 text-sm text-green-400 dark:bg-slate-950">
              <div className="mb-2 text-slate-400"># 3. 安装shadcn/ui</div>
              <code>npx shadcn@latest init</code>
            </div>
            <div className="rounded-lg bg-slate-900 p-4 text-sm text-green-400 dark:bg-slate-950">
              <div className="mb-2 text-slate-400"># 4. 添加React Flow UI组件</div>
              <code>npx shadcn@latest add react-flow-ui</code>
            </div>
          </div>
        </div>

        {/* 决策建议 */}
        <div className="mt-8 rounded-xl border border-blue-200 bg-blue-50 p-6 dark:border-blue-900 dark:bg-blue-950">
          <h3 className="mb-3 text-lg font-semibold text-blue-900 dark:text-blue-100">
            💡 决策建议
          </h3>
          <div className="space-y-3 text-sm text-blue-900 dark:text-blue-100">
            <div className="flex items-start gap-2">
              <span className="font-bold">✅ 建议迁移，如果：</span>
              <ul className="list-inside list-disc space-y-1">
                <li>代码维护成本高（11个组件改起来麻烦）</li>
                <li>愿意升级到React 19 + Tailwind 4</li>
                <li>可以接受视觉风格微调</li>
              </ul>
            </div>
            <div className="flex items-start gap-2">
              <span className="font-bold">❌ 建议保持现状，如果：</span>
              <ul className="list-inside list-disc space-y-1">
                <li>玻璃态视觉是核心卖点，不能妥协</li>
                <li>不想承担升级依赖的风险</li>
                <li>当前代码维护尚可接受</li>
              </ul>
            </div>
            <div className="flex items-start gap-2">
              <span className="font-bold">🔧 折中方案：</span>
              <ul className="list-inside list-disc space-y-1">
                <li>保留当前节点，但提取公共组件（如EditableLabel）</li>
                <li>只参考React Flow UI的设计模式，不直接使用库</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
