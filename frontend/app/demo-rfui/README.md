# React Flow UI 对比 Demo 使用指南

## 概述

这个demo页面用于对比**当前自定义节点**和**React Flow UI风格**的差异，帮助决策是否值得迁移。

## 访问Demo

### 启动前端服务

```bash
cd frontend
npm run dev
```

### 访问地址

```
http://localhost:3000/demo-rfui
```

## Demo内容

### 1. 并排对比画布

- **左侧：** 当前自定义节点（玻璃态风格）
  - ApiNode, ServiceNode, DatabaseNode, CacheNode
  - 渐变背景 + 阴影效果
  - Lucide图标 + 双击编辑

- **右侧：** React Flow UI风格（简化版演示）
  - 基于shadcn/ui设计理念
  - 简洁的卡片风格
  - 注意：这是**概念演示**，不是真正的React Flow UI组件

### 2. 对比指标面板

详细对比两种方案的优缺点：

| 维度 | 当前自定义节点 | React Flow UI |
|------|---------------|--------------|
| **视觉效果** | ✅ 玻璃态 + 渐变 | ⚠️ 简洁风格 |
| **代码复用** | ❌ 11个组件重复代码 | ✅ BaseNodeHeader等构建块 |
| **维护成本** | ⚠️ 修改需改多个文件 | ✅ 统一管理 |
| **技术栈** | React 18 + Tailwind 3 | React 19 + Tailwind 4 |
| **迁移成本** | - | ⚠️ 2-3天重构 |

### 3. 决策建议

根据项目实际情况给出建议：
- ✅ **建议迁移** - 如果代码维护困难 + 愿意升级依赖
- ❌ **保持现状** - 如果视觉是核心卖点 + 不想冒风险
- 🔧 **折中方案** - 提取公共组件但不用库

## 真正的React Flow UI需要的步骤

如果决定尝试真正的React Flow UI（当前demo只是简化演示）：

### Step 1: 升级依赖

```bash
# 升级到React 19
npm install react@^19 react-dom@^19

# 升级到Tailwind 4
npm install tailwindcss@^4 autoprefixer@^11 postcss@^9

# 更新types
npm install -D @types/react@^19 @types/react-dom@^19
```

### Step 2: 安装shadcn/ui

```bash
npx shadcn@latest init
```

配置选项：
- TypeScript: Yes
- Style: Default
- Base color: Slate
- CSS variables: Yes

### Step 3: 添加React Flow UI组件

```bash
npx shadcn@latest add react-flow-ui
```

这会安装：
- `@xyflow/react-flow-ui` 包
- 相关的shadcn/ui组件依赖

### Step 4: 重构节点组件

示例（ApiNode重构）：

**之前（~115行）：**
```typescript
export const ApiNode = memo(({ id, data }: NodeProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [label, setLabel] = useState(data.label);
  // ... 大量状态和逻辑

  return (
    <div className="glass-node ...">
      {/* 手动实现编辑、样式等 */}
    </div>
  );
});
```

**之后（~40行，使用React Flow UI）：**
```typescript
import { BaseNodeHeader } from '@xyflow/react-flow-ui';

export const ApiNode = memo(({ id, data }: NodeProps) => {
  const updateNodeLabel = useArchitectStore((s) => s.updateNodeLabel);

  return (
    <div className="glass-node custom-rfui-style">
      <BaseNodeHeader
        icon={<Globe />}
        title={data.label}
        subtitle="API"
        onEdit={(newLabel) => updateNodeLabel(id, newLabel)}
        className="rfui-header-glass"
      />
      <Handle type="target" position={Position.Left} />
      <Handle type="source" position={Position.Right} />
    </div>
  );
});
```

**保留玻璃态风格的CSS：**
```css
/* global.css */
.glass-node.custom-rfui-style {
  background: linear-gradient(135deg, var(--api-background) 0%, rgba(255,255,255,0.9) 100%);
  box-shadow: var(--api-shadow);
  /* 覆盖shadcn默认样式 */
}

.rfui-header-glass {
  /* 自定义BaseNodeHeader的样式 */
}
```

## 风险评估

### 升级依赖的风险

| 依赖 | 当前版本 | 目标版本 | 风险 |
|------|---------|---------|------|
| React | 18.3.1 | 19.x | 🟡 中等（可能有breaking changes） |
| Tailwind | 3.4.17 | 4.x | 🔴 高（配置文件格式变化） |
| Next.js | 14.2.18 | 14.x | 🟢 低（兼容React 19） |
| @excalidraw | 0.18.0 | ? | 🟡 中等（需验证React 19兼容性） |

### 建议的测试策略

如果决定升级：

1. **创建新分支**
   ```bash
   git checkout -b feature/react-flow-ui-migration
   ```

2. **逐步升级**
   - 先升级React 19，测试现有功能
   - 再升级Tailwind 4，测试样式
   - 最后引入React Flow UI

3. **全面测试**
   - Phase 1-5所有功能
   - Excalidraw集成
   - 主题切换
   - 导出功能

4. **性能对比**
   - 50个节点渲染速度
   - 内存占用
   - 打包体积

## 文件清单

```
frontend/
├── app/
│   └── demo-rfui/
│       ├── page.tsx          # Demo页面（本文件）
│       └── README.md         # 本说明文档
├── components/
│   └── nodes/
│       ├── ApiNode.tsx       # 当前自定义节点（参考）
│       ├── DatabaseNode.tsx
│       └── ...
└── DISCUSSION_PHASE6.md      # 讨论记录
```

## 参考资料

- [React Flow UI 官方文档](https://reactflow.dev/ui)
- [shadcn/ui 官方文档](https://ui.shadcn.com/)
- [React 19 升级指南](https://react.dev/blog/2024/12/05/react-19)
- [Tailwind CSS 4 Beta](https://tailwindcss.com/blog/tailwindcss-v4-beta)

## 常见问题

**Q: 为什么demo中的React Flow UI节点这么简单？**
A: 这只是**概念演示**，真正的React Flow UI需要安装依赖后才能使用完整功能。当前demo用简化版本展示设计理念。

**Q: 升级到React 19会破坏现有功能吗？**
A: 可能会。React 19有一些breaking changes，需要仔细测试，特别是Excalidraw的兼容性。

**Q: 可以只用React Flow UI的部分组件吗？**
A: 可以。shadcn/ui的理念就是"copy-paste"，你可以只复制需要的组件代码，不用全量引入。

**Q: 如果不迁移，有没有办法减少代码重复？**
A: 有。可以提取公共组件（如EditableLabel、NodeWrapper），参考React Flow UI的设计模式但不引入库。

## 下一步

根据demo效果和讨论，决定：

1. ✅ **迁移到React Flow UI** → 执行上述升级步骤
2. ❌ **保持当前方案** → 关闭此分支，优化现有代码
3. 🔧 **折中方案** → 提取公共组件，参考但不直接使用

---

**创建日期：** 2026-01-20
**状态：** 评估中
**相关讨论：** DISCUSSION_PHASE6.md, PHASE6_PROPOSAL.md
