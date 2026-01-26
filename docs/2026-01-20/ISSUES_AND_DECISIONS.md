# Phase 6 开发问题记录

**日期：** 2026-01-20
**阶段：** Phase 6 规划与技术选型

---

## 核心问题汇总

### 问题1：ReactFlow vs Excalidraw 功能割裂

**问题描述：**
- 两个画布通过 `canvasMode` 状态切换，但数据完全隔离
- 用户在ReactFlow创建的图，切换到Excalidraw后丢失
- 无法利用两种画布的各自优势（ReactFlow严谨 vs Excalidraw灵活）

**现状：**
```typescript
// ArchitectCanvas.tsx:152-160
if (canvasMode === "excalidraw") {
  return <ExcalidrawBoard />;  // 完全独立
}
return <ArchitectCanvasInner />;  // ReactFlow
```

**影响：**
- 用户体验割裂
- 无法自由切换风格
- 限制使用场景

**建议方案：**
- ✅ 优先实现截图识别（Phase 6 MVP）
- ⏸️ 延后 ReactFlow ↔ Excalidraw 双向转换（用户需求待验证）

---

### 问题2：缺少流程图截图识别功能

**问题描述：**
- 现有 `/api/vision/analyze` 专注架构图（API、Service、Database）
- 无法识别流程图元素（开始/结束/判断/处理节点）
- 用户想从 Visio/ProcessOn 迁移数据困难

**用户需求场景：**
1. 产品经理截图 Visio 流程图 → 导入系统编辑
2. 拍摄白板手绘流程图 → 数字化存档
3. 复刻竞品流程图 → 微调优化

**解决方案：**
- ✅ 新增 `/api/vision/analyze-flowchart` API
- ✅ 使用 Qwen2.5-VL / Gemini 2.5 Flash
- ✅ 专门优化的 Prompt（流程图元素识别）
- ✅ 输出 ReactFlow 格式（匹配现有17种SVG形状）

**预期效果：**
- Visio标准流程图：>95% 识别率
- ProcessOn截图：>90% 识别率
- 手绘流程图：>80% 识别率

---

### 问题3：React Flow UI 误解

**问题描述：**
- 误以为 React Flow UI 提供丰富的节点库
- 实际上只提供5个组件（其中4个是通用构建块）
- 即使升级也需要自己写所有业务节点

**React Flow UI 实际提供：**
```
节点组件（5个）：
✅ Base Node - 基础包装器
✅ Database Schema - 数据库表节点
✅ Placeholder - 占位符
✅ Labeled Group - 分组
✅ Status Indicator - 状态指示

辅助组件（9个）：
✅ Handles, Edges, Controls 等工具组件
```

**没有提供：**
- ❌ 流程图专用节点
- ❌ 架构图专用节点
- ❌ BPMN标准节点
- ❌ 任何特定业务场景的节点

**结论：**
- React Flow UI 是设计系统，不是节点库
- 升级到 React 19 + Tailwind 4 风险高
- 对当前项目价值有限（玻璃态风格可能失去）

**决策：**
- ❌ 不升级到 React Flow UI
- ✅ 提取公共组件优化现有代码（可选）
- ✅ 保持 React 18 + Tailwind 3

---

### 问题4：当前自定义节点维护成本

**现状：**
- 11个自定义节点组件
- 每个组件 ~115 行代码
- 代码重复（编辑逻辑、样式处理）

**痛点：**
- 样式调整需要修改11个文件
- 新增节点类型工作量大
- 代码维护困难

**优化方案（不升级RFUI）：**
```typescript
// 提取公共组件
components/nodes/common/
├── EditableLabel.tsx    // 复用编辑逻辑
├── NodeWrapper.tsx      // 统一样式包装
└── NodeIcon.tsx         // 图标处理

// 节点简化后
ApiNode.tsx: 115行 → 40行
DatabaseNode.tsx: 115行 → 40行
```

**预期收益：**
- 代码量减少 60%
- 维护成本降低
- 保留玻璃态视觉风格

---

### 问题5：模型 API Key 管理体验极差

**问题描述：**
- 每次只能设置一个提供商的 API Key
- 切换不同 AI 模型需要频繁重新输入 Key
- 无法保存多个配置（如"个人账号" vs "公司账号"）
- 无法对比不同模型效果（需要反复切换配置）

**现状：**
```python
# backend/app/api/models.py
@router.post("/models/config")
async def set_model_config(config: ModelConfig):
    # 只能存储单个配置
    settings.set_model_config(config.provider, config.api_key, config.model_name)
```

**用户场景痛点：**
```
用户想用 Gemini 生成架构图 → 输入 Gemini API Key
用户想用 OpenAI 分析截图 → 删除 Gemini Key，输入 OpenAI Key
用户想回到 Gemini → 又要重新输入 Gemini Key ❌
```

**用户反馈（2026-01-20）：**
> "还有目前的模型apikey管理也有很大问题，应该支持设置多种类型，然后用户选择自己预设需要的模型要传参c实现功能，不然用户频繁替换体验感太差了"

**影响：**
- 严重影响用户体验
- 降低工作效率
- 无法快速测试不同模型
- 阻碍高级用户使用多账号

**建议方案：**
- ✅ 实现多配置管理系统（支持同时保存多个提供商配置）
- ✅ 每个配置可命名（如"我的 Gemini"、"公司 OpenAI"）
- ✅ 前端下拉选择预设配置，无需重复输入 Key
- ✅ 配置持久化到文件（JSON）

**技术方案文档：** `doc/2026-01-20/MODEL_CONFIG_REDESIGN.md`

**优先级：** 🔴 紧急（⭐⭐⭐⭐⭐）
**工作量：** 2-3天

---

## 技术选型决策

### 决策1：流程图识别方案

**选择：VLM端到端识别（Qwen2.5-VL / Gemini）**

**理由：**
- 开发速度快（2-3天）
- 维护成本低
- 准确率高（90-95%）
- 已有技术栈支持

**替代方案（延后）：**
- OCR + OpenCV Pipeline（7-10天，准确率80-90%）

### 决策2：画布闭环优先级

**选择：延后 ReactFlow ↔ Excalidraw 双向转换**

**理由：**
- 技术复杂度高（4-5天）
- 用户需求不明确（需验证）
- 优先实现高价值功能（截图识别）

**用户场景分析：**
- ReactFlow → Excalidraw：手绘风格演示（需求中等）
- Excalidraw → ReactFlow：手绘转结构化（需求低？）

### 决策3：React Flow UI 迁移

**选择：不迁移，优化现有代码**

**理由：**
- 成本 > 收益
- 玻璃态是产品特色
- React 19 升级风险高
- React Flow UI 不提供业务节点

**替代方案：**
- 参考 React Flow UI 设计模式
- 提取公共组件
- 保持 React 18 + Tailwind 3

---

## 优先级排序（最终决定）

### Week 1-2: 流程图截图识别（⭐⭐⭐⭐⭐）

**目标：**
- 用户上传截图 → AI识别 → ReactFlow可编辑图

**工作量：** 2-3天

**关键任务：**
1. 扩展 `ai_vision.py`：新增 `analyze_flowchart()` 方法
2. 新增 API：`POST /api/vision/analyze-flowchart`
3. 前端上传组件：`FlowchartUploader.tsx`
4. 集成到 `AiControlPanel.tsx`

**验收标准：**
- Visio流程图识别率 >95%
- ProcessOn截图识别率 >90%
- 手绘流程图识别率 >80%

### Week 3: 代码优化（⭐⭐⭐）

**目标：**
- 减少节点组件代码重复

**工作量：** 1-2天

**关键任务：**
1. 提取 `EditableLabel` 组件
2. 提取 `NodeWrapper` 组件
3. 重构11个节点组件

**验收标准：**
- 代码量减少 60%
- 功能无损
- 视觉风格保持

### 延后：Excalidraw 闭环（⏸️）

**等待：**
- 截图识别上线后收集用户反馈
- 验证用户是否真的需要画布互转

---

## 技术债务

### 已识别问题

1. **自动布局缺失**
   - 现状：只有简单的 `fitView()`
   - 计划：集成 dagre/elk 算法（Phase 7?）

2. **节点代码重复**
   - 现状：11个组件，每个 ~115行
   - 计划：Week 3 优化

3. **画布数据隔离**
   - 现状：ReactFlow 和 Excalidraw 无法互通
   - 计划：用户需求验证后决定

4. **错误处理不统一**
   - 现状：各模块错误处理方式不同
   - 计划：Phase 7 统一重构

---

## 用户反馈待收集

### 关键问题

1. **截图识别的主要场景？**
   - [ ] A. 标准流程图（Visio/ProcessOn/Draw.io）
   - [ ] B. 手绘草图照片（白板拍照）
   - [ ] C. 混合场景

2. **画布切换需求？**
   - [ ] 高：强烈需要手绘 ↔ 结构化转换
   - [ ] 中：有需求但不紧急
   - [ ] 低：先做截图识别，闭环可以延后

3. **当前节点满意度？**
   - [ ] 视觉风格满意
   - [ ] 功能齐全
   - [ ] 性能良好
   - [ ] 维护可接受

---

## 参考文档

**技术方案：**
- `doc/2026-01-20/PHASE6_PROPOSAL.md` - 原始技术方案
- `doc/2026-01-20/FLOWCHART_RECOGNITION_IMPLEMENTATION.md` - 实现细节
- `doc/2026-01-20/IMPLEMENTATION_CHECKLIST.md` - 实现检查清单

**讨论记录：**
- `doc/2026-01-20/DISCUSSION_PHASE6.md` - 完整讨论过程
- `doc/2026-01-20/REACT_FLOW_UI_TRUTH.md` - React Flow UI 真相澄清

**现有文档：**
- `CLAUDE.md` - 项目总体说明（保留在根目录）
- `README.md` - 项目介绍（保留在根目录）

---

## 风险评估

### 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| VLM识别准确率不足 | 中 | 高 | 准备OCR Pipeline备选方案 |
| 大图性能问题（50+节点） | 低 | 中 | 限制节点数 + 前端虚拟化 |
| 用户不理解两种画布区别 | 中 | 低 | 引导提示 + 示例 |

### 业务风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| 用户不需要截图识别 | 低 | 高 | 先MVP验证需求 |
| Excalidraw闭环是刚需 | 中 | 中 | 收集反馈后快速迭代 |
| 节点视觉风格不满意 | 低 | 中 | 提供主题定制 |

---

## 下一步行动

### 立即执行

1. ✅ 创建文档目录结构（`doc/2026-01-20/`）
2. ✅ 移动MD文件到对应目录
3. ✅ 记录问题和决策（本文档）

### 等待用户决策

4. ⏸️ 确认是否开始实现截图识别
5. ⏸️ 确认代码优化的优先级
6. ⏸️ 确认 Excalidraw 闭环的必要性

### 实现阶段（如果启动）

7. ⏸️ Day 1-2: 后端 API 实现
8. ⏸️ Day 3: 前端上传组件
9. ⏸️ 测试验证和调优

---

**文档创建时间：** 2026-01-20 23:45
**状态：** 问题已识别，方案已确定，等待实施
**负责人：** Claude + 用户
