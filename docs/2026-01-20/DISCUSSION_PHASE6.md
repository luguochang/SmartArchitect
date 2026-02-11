# Phase 6 讨论记录

**日期：** 2026-01-20
**参与者：** 用户 + Claude
**主题：** 画布闭环、截图识别、React Flow组件库选型

---

## 核心疑问与解答

### 疑问1：上传图片后，ReactFlow能画出来吗？Excalidraw能吗？

**现状分析：**

| 能力维度 | ReactFlow（当前系统） | Excalidraw |
|---------|---------------------|------------|
| **已有形状** | 17种SVG形状（SvgShapes.tsx）<br>+ 11种自定义节点组件 | 无限制（自由绘制） |
| **标准流程图** | ✅ 可以（矩形、菱形、圆形等） | ✅ 可以（但需复杂转换逻辑） |
| **BPMN流程图** | ✅ 可以（除泳道外） | ⚠️ 理论可以但失去结构化 |
| **架构图** | ✅ 可以（API/DB等专用节点） | ❌ 不适合（无语义信息） |
| **手绘草图** | ❌ 不行（形状库有限） | ✅ 最佳选择 |
| **不规则图形** | ❌ SVG形状固定 | ✅ 自由曲线 |

**结论：**
- **截图识别优先支持ReactFlow输出**（覆盖90%标准流程图场景）
- 现有17种SVG形状 + 11种节点足够应对大部分需求
- Excalidraw作为补充（手绘风格识别时提示用户切换）

---

### 疑问2：React Flow组件库真相 + 为什么建议自定义

**React Flow UI（官方）实际提供内容：**

✅ **有的组件：**
- Database Schema Node（数据库表关系可视化）
- Zoom Slider（缩放滑块）
- Debugging Components（调试工具）
- BaseNodeHeader, LabeledHandle（构建块）
- DataEdge（自定义连线）

❌ **没有的组件：**
- 流程图专用节点（开始/结束/判断）
- BPMN标准节点
- 架构图专用节点（API/Service/Cache）
- 图标库或视觉样式预设

**技术栈：**
- 基于 shadcn/ui + Tailwind CSS
- React 19 + Tailwind 4（2025年10月更新）
- 通过 shadcn CLI 安装：`npx shadcn@latest add react-flow-ui`

**为什么之前建议自定义：**
1. 架构图节点没有现成库（API Gateway、Redis等是业务特定需求）
2. 视觉风格定制化（玻璃态+渐变是产品特色）
3. 灵活性考虑（完全掌控交互逻辑）

**现在的建议：**
- React Flow UI的 `BaseNodeHeader` 可作为**构建块**减少重复代码
- 如果当前自定义节点维护困难，可以**迁移到React Flow UI基础上再定制**
- 保留视觉风格的同时提升代码质量

---

### 疑问3：当前自定义节点效果不好？

**当前实现回顾：**
```typescript
// frontend/components/nodes/ApiNode.tsx
- ✅ 支持双击编辑标签
- ✅ 玻璃态视觉效果（glass-node + 渐变背景）
- ✅ CSS变量主题支持（12+主题）
- ✅ Lucide图标集成
- ✅ 响应式交互
```

**可能的"效果不好"原因（待用户确认）：**

| 问题类型 | 具体表现 |
|---------|---------|
| **视觉问题** | 渐变太重？阴影太深？图标不清晰？对比度不够？ |
| **功能问题** | 节点类型不够？缺BPMN形状？编辑交互不流畅？ |
| **性能问题** | 大量节点卡顿？玻璃态效果影响性能？ |
| **维护问题** | 11个组件代码重复？样式调整工作量大？ |

**如果是代码重复问题，可优化为：**
```typescript
// 使用React Flow UI的BaseNodeHeader重构
import { BaseNodeHeader } from '@xyflow/react-flow-ui';

export const ApiNode = ({ id, data }) => {
  return (
    <div className="glass-node ...">
      <BaseNodeHeader
        icon={<Globe />}
        title={data.label}
        subtitle="API"
        onEdit={(newLabel) => updateNodeLabel(id, newLabel)}
      />
      <Handle ... />
    </div>
  );
};
```

---

## 技术方案修正

### 原方案（PHASE6_PROPOSAL.md）

**优先级：**
1. ⭐⭐⭐⭐⭐ 流程图截图识别（2-3天）
2. ⭐⭐⭐⭐ ReactFlow → Excalidraw 转换（3-4天）
3. ⭐⭐⭐ Excalidraw → ReactFlow 转换（4-5天）

### 修正方案（基于讨论）

**Phase 6 MVP（优先级重排）：**

| 阶段 | 功能 | 工作量 | 理由 |
|------|------|--------|------|
| **Step 1** | 流程图截图识别 → ReactFlow | 2-3天 | 核心痛点，现有17种形状足够 |
| **Step 2** | 评估React Flow UI引入价值 | 1天 | 做对比demo，验证是否改善体验 |
| **Step 3** | 优化现有节点视觉/代码（按需） | 2-3天 | 根据用户反馈决定 |
| **延后** | Excalidraw双向转换 | - | 技术复杂度高，用户需求待验证 |

**核心策略调整：**
- ✅ 聚焦截图识别（解决"从其他工具迁移"的痛点）
- ✅ 用现有能力（17种SVG形状）而非盲目扩展
- ⚠️ 暂缓Excalidraw闭环（先验证需求）
- 🔍 评估React Flow UI（提升代码质量）

---

## 截图识别技术方案细化

### VLM模型选择

| 模型 | 优势 | 缺点 | 推荐度 |
|------|------|------|--------|
| **Qwen2.5-VL** | 文档理解强、已集成SiliconFlow、性价比高 | - | ⭐⭐⭐⭐⭐ |
| **Gemini 2.5 Flash** | 速度最快（2-3s）、已集成 | 图表识别中等 | ⭐⭐⭐⭐ |
| **Claude 3.5 Sonnet** | 图表理解最强 | 慢（5-8s）、贵 | ⭐⭐⭐ |

**推荐策略：**
- 默认用 **Qwen2.5-VL**（性价比最佳）
- 提供选项让用户选择模型

### 识别能力边界

**现有17种SVG形状可覆盖：**
```
✅ 矩形 → task节点
✅ 菱形 → decision节点
✅ 圆形 → start-event/end-event
✅ 平行四边形 → data节点
✅ 六边形 → preparation节点
✅ 梯形 → manual-operation节点
✅ 圆柱体 → database节点（BPMN）
✅ 文档形状 → document节点
✅ 云形状 → cloud节点
✅ 其他特殊形状：星形、三角形、文件夹等
```

**识别失败时的降级策略：**
```python
# 如果AI识别出未知形状
if shape_type not in SUPPORTED_SHAPES:
    # 退化到default节点
    node = Node(
        type="default",
        data={
            "label": extracted_text,
            "original_shape": shape_type,  # 记录原始形状
            "suggestion": "请手动调整节点类型"
        }
    )
```

### API设计

```python
# backend/app/api/vision.py (新增)

@router.post("/vision/analyze-flowchart")
async def analyze_flowchart_screenshot(
    file: UploadFile,
    provider: str = Query("qwen", description="AI provider"),
    preserve_layout: bool = Query(True),
    target_canvas: Literal["reactflow", "excalidraw"] = Query("reactflow"),
):
    """
    识别流程图截图

    - provider: qwen（推荐）| gemini | claude
    - preserve_layout: 保留原始布局 vs AI重排
    - target_canvas: reactflow（结构化）| excalidraw（手绘，暂不支持）

    返回：
    - nodes: ReactFlow节点数组（匹配现有17种形状）
    - edges: 连线数组
    - warnings: 未识别形状的警告列表
    """
```

**Prompt优化方向：**
```python
FLOWCHART_PROMPT = f"""
识别这张流程图，提取节点和连线。

支持的形状类型：
{', '.join(SUPPORTED_SHAPES)}  # 从SvgShapes.tsx动态生成

规则：
1. 圆形/圆角矩形 → start-event或end-event（根据文本判断）
2. 矩形 → task
3. 菱形 → decision
4. 平行四边形 → data
5. 如果形状不在支持列表，使用最接近的形状 + 在warnings中说明

输出JSON格式：
{{
  "nodes": [...],
  "edges": [...],
  "warnings": [
    {{"node_id": "n3", "message": "原图为八边形，已转为六边形"}}
  ]
}}
"""
```

---

## React Flow UI 评估计划

### 对比Demo需求

创建两个版本对比：

**版本A：当前自定义节点**
```typescript
// 玻璃态 + 渐变 + Lucide图标
<ApiNode data={{ label: "API Gateway" }} />
<DatabaseNode data={{ label: "PostgreSQL" }} />
```

**版本B：React Flow UI基础上定制**
```typescript
// shadcn + BaseNodeHeader + 保留视觉风格
<RFUIApiNode data={{ label: "API Gateway" }} />
<RFUIDatabaseNode data={{ label: "PostgreSQL" }} />
```

**对比维度：**
1. 视觉效果（截图对比）
2. 代码复杂度（行数、可维护性）
3. 性能（渲染50个节点的FPS）
4. 扩展性（新增节点类型的工作量）

### Demo页面结构

```
/demo-react-flow-ui
├── 左侧：当前自定义节点画布
├── 右侧：React Flow UI版本画布
└── 底部：对比指标面板
```

---

## 待确认问题（需用户反馈）

### 问题1：当前节点具体哪里不满意？

- [ ] 视觉风格（渐变、阴影、颜色等）
- [ ] 功能缺失（缺少哪些节点类型？）
- [ ] 交互体验（编辑、拖拽等）
- [ ] 代码维护（重复代码、调整困难）
- [ ] 性能问题（卡顿、渲染慢）

### 问题2：截图识别的主要场景？

- [ ] A. 标准流程图（Visio/ProcessOn/Draw.io导出）
- [ ] B. 手绘草图照片（白板拍照）
- [ ] C. 混合场景（两者都有）

### 问题3：Excalidraw闭环优先级？

- [ ] 高（用户强烈需要手绘 ↔ 结构化转换）
- [ ] 中（有需求但不紧急）
- [ ] 低（先做截图识别，闭环可以延后）

### 问题4：是否尝试React Flow UI？

- [ ] 是（做demo对比后再决定）
- [ ] 否（继续优化当前自定义节点）
- [ ] 待定（先看demo效果）

---

## 下一步行动

### 立即执行（本次会话）

1. ✅ 记录讨论要点（本文档）
2. 🔄 创建React Flow UI对比demo
3. 📦 安装shadcn/ui + React Flow UI依赖
4. 🎨 实现两种节点的并排对比

### 等待用户反馈后

5. ⏸️ 根据demo效果决定是否迁移到React Flow UI
6. ⏸️ 确认截图识别的优先级和功能范围
7. ⏸️ 评估Excalidraw闭环的必要性

---

## 参考资源

**官方文档：**
- [React Flow UI](https://reactflow.dev/ui)
- [Getting Started with React Flow UI](https://reactflow.dev/learn/tutorials/getting-started-with-react-flow-components)
- [shadcn/ui](https://ui.shadcn.com/)

**已有实现：**
- `frontend/components/nodes/` - 11个自定义节点
- `frontend/components/nodes/SvgShapes.tsx` - 17种SVG形状
- `backend/app/services/ai_vision.py` - Vision服务（需扩展）

**对比参考：**
- [Comparing React-Based Flowchart Tools](https://patrickkarsh.medium.com/comparing-tools-for-creating-react-based-flowcharts-36203531dfd7)
- [Top JavaScript Diagramming Libraries 2026](https://www.jointjs.com/blog/javascript-diagramming-libraries)

---

**文档版本：** v1.0
**状态：** 讨论中，待用户反馈
**关联文档：** PHASE6_PROPOSAL.md
