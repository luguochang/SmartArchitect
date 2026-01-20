# 📚 文档索引

**最后更新：** 2026-01-20

本文件是 SmartArchitect AI 项目所有文档的索引导航。

---

## 🗂️ 文档目录结构

```
SmartArchitect/
├── README.md                    # 项目介绍（中文）
├── CLAUDE.md                    # 开发者指南（给 Claude Code 的说明）
├── QUICKSTART.md                # 快速开始指南
│
├── doc/                         # 文档目录
│   ├── TODO.md                  # ⭐ 功能实现状态总览（最重要）
│   │
│   ├── 2026-01-20/              # 今日文档（Phase 6）
│   │   ├── ISSUES_AND_DECISIONS.md                    # 问题记录与决策
│   │   ├── PHASE6_PROPOSAL.md                         # Phase 6 技术方案
│   │   ├── FLOWCHART_RECOGNITION_IMPLEMENTATION.md    # 截图识别实现细节
│   │   ├── IMPLEMENTATION_CHECKLIST.md                # 实现检查清单
│   │   ├── DISCUSSION_PHASE6.md                       # 讨论记录
│   │   ├── REACT_FLOW_UI_TRUTH.md                     # React Flow UI 真相澄清
│   │   ├── RAG_AND_PROMPT_DESIGN.md                   # RAG 与 Prompt 管理系统设计
│   │   └── MODEL_CONFIG_REDESIGN.md                   # 模型配置管理重构方案
│   │
│   └── archive/                 # 历史文档归档
│       ├── fixes/               # 修复日志（13个文件）
│       ├── progress/            # 进度文档（3个文件）
│       ├── test/                # 测试文档（2个文件）
│       ├── review/              # 系统评审（2个文件）
│       ├── TODO.md              # 旧版TODO（已废弃）
│       └── AGENTS.md            # Agent配置（已废弃）
│
├── frontend/                    # 前端代码
└── backend/                     # 后端代码
```

---

## 📖 核心文档说明

### 1. **README.md**（根目录）

**内容：** 项目介绍、功能概览、技术栈、快速开始
**语言：** 中文
**受众：** 新用户、开发者
**查看：** 项目首页

---

### 2. **CLAUDE.md**（根目录）⭐

**内容：**
- 项目架构深度解析
- 开发命令和脚本
- API端点文档（30+）
- 数据模型和Schema
- 配置说明
- 已知问题和限制

**语言：** 英文
**受众：** 开发者、Claude Code
**更新频率：** 每次重大功能完成后更新

**重要章节：**
- Architecture Deep Dive
- Backend API Architecture
- Frontend Architecture
- Data Flow & Schemas
- Phase History & Features

---

### 3. **QUICKSTART.md**（根目录）

**内容：** 环境搭建、快速启动、常见问题
**语言：** 英文
**受众：** 新开发者
**查看：** 初次使用时

---

### 4. **doc/TODO.md** ⭐⭐⭐

**内容：**
- **功能实现状态总览**（最重要！）
- Phase 1-6 完成情况
- 未实现功能清单
- 问题记录
- 优先级排序

**语言：** 中文
**受众：** 所有人
**更新频率：** 每次完成功能后立即更新

**使用说明：**
- 完成功能后在对应项前打勾 `[x]`
- 添加新功能时标注优先级和工作量
- CLAUDE.md 中的状态可能过时，以此文档为准！

**关键章节：**
- 功能实现状态概览
- 关键未实现功能汇总
- Phase 详细清单

---

## 📅 2026-01-20 文档（Phase 6）

### 核心问题与决策

#### **ISSUES_AND_DECISIONS.md**

**内容：**
- Phase 6 核心问题汇总
- 技术选型决策
- 优先级排序
- 风险评估

**关键问题：**
1. ReactFlow vs Excalidraw 功能割裂
2. 缺少流程图截图识别功能
3. React Flow UI 误解澄清
4. 节点代码维护成本

**决策：**
- ✅ 优先实现截图识别（2-3天）
- ✅ 延后画布闭环（用户需求待验证）
- ❌ 不升级 React Flow UI

---

### 技术方案文档

#### **PHASE6_PROPOSAL.md**

**内容：** Phase 6 完整技术方案（原始版本）
**包括：**
- 双向画布转换桥设计
- 流程图截图识别方案
- 完整闭环架构
- 技术选型对比

**状态：** 方案已调整，部分延后

---

#### **FLOWCHART_RECOGNITION_IMPLEMENTATION.md** ⭐

**内容：** 流程图截图识别功能完整实现方案
**包括：**
- 5个实现步骤（后端扩展、API、前端组件、测试）
- 完整代码示例
- Prompt 设计
- 测试策略

**工作量：** 2-3天
**优先级：** ⭐⭐⭐⭐⭐ 最高

**关键文件：**
- `backend/app/services/ai_vision.py` - 添加 `analyze_flowchart()`
- `backend/app/api/vision.py` - 新增 `/api/vision/analyze-flowchart`
- `frontend/components/FlowchartUploader.tsx` - 新建上传组件

---

#### **IMPLEMENTATION_CHECKLIST.md**

**内容：** 3天实现检查清单
**包括：**
- Day 1-2: 后端核心服务
- Day 3: 前端上传组件
- 测试用例准备
- 常见问题排查

**使用方式：** 逐项打勾完成

---

### 讨论记录

#### **DISCUSSION_PHASE6.md**

**内容：** 完整讨论过程记录
**包括：**
- 核心疑问与解答
- 技术方案修正
- 待确认问题列表

**关键章节：**
- 疑问1：上传图片后能画出来吗？
- 疑问2：React Flow UI 真相
- 疑问3：当前节点效果不好？

---

#### **REACT_FLOW_UI_TRUTH.md**

**内容：** React Flow UI 真相澄清与建议修正
**关键发现：**
- React Flow UI 不是节点库，是设计系统
- 只提供5个组件（1个构建块 + 1个数据库节点 + 3个辅助）
- 升级成本 > 收益

**决策：** 不升级，优化现有代码

---

#### **RAG_AND_PROMPT_DESIGN.md** ⭐

**内容：** RAG 知识库与 Prompt 提示词管理系统设计方案
**包括：**
- 无用户认证的 RAG 存储策略（全局共享 vs Session vs 混合）
- Prompt 预设快速选择系统
- 自定义 Prompt 管理
- 前端组件设计（DocumentUploadModal、PromptQuickSelect）

**工作量：** 2-3天（RAG前端集成 + Prompt管理）
**优先级：** ⭐⭐⭐⭐

**关键设计决策：**
- RAG 采用全局共享知识库方案（简单、适合团队）
- Prompt 采用预设（后端）+ 自定义（LocalStorage）混合方案

---

#### **MODEL_CONFIG_REDESIGN.md** ⭐⭐⭐⭐⭐

**内容：** 模型 API Key 管理系统重构方案
**核心问题：** 频繁替换 API Key 体验极差

**包括：**
- 多配置管理系统设计（支持同时保存多个提供商配置）
- 配置持久化（JSON 文件存储）
- 前端管理界面（ModelPresetsManager、ModelPresetSelector）
- 向后兼容策略（渐进式迁移）

**工作量：** 2-3天
**优先级：** 🔴 紧急（⭐⭐⭐⭐⭐）

**用户反馈：** "用户频繁替换体验感太差了"

**关键功能：**
- 每个配置可命名（如"我的 Gemini"、"公司 OpenAI"）
- 下拉选择预设，无需重复输入 Key
- 支持设为默认配置
- 记录最后使用时间

---

## 📦 历史文档归档

### doc/archive/fixes/ （修复日志）

13个修复日志文件，记录了各种问题的修复过程：
- Excalidraw 相关修复（5个）
- 流式传输相关修复（3个）
- 节点样式修复（3个）
- 其他修复（2个）

**查看场景：** 遇到类似问题时参考

---

### doc/archive/progress/ （进度文档）

3个进度跟踪文档：
- DEV_LOG.md - 开发日志
- PROGRESS.md - 详细进度
- QUICK_STATUS.md - 快速状态

**状态：** 已由 `doc/TODO.md` 替代

---

### doc/archive/review/ （系统评审）

2个系统评审文档：
- SYSTEM_REVIEW.md - 生产就绪评估
- TEST_COVERAGE_REPORT.md - 测试覆盖率报告

**重要性：** 生产部署前必读

---

### doc/archive/test/ （测试文档）

2个测试相关文档

---

### doc/archive/ （其他废弃文档）

- TODO.md - 旧版TODO（2026-01-08版本）
- AGENTS.md - Agent配置

---

## 🔍 快速查找指南

### 想了解项目概况？
→ `README.md`

### 想知道某个功能是否实现？
→ `doc/TODO.md` ⭐

### 想了解 API 如何使用？
→ `CLAUDE.md` → Backend API Architecture

### 想快速启动项目？
→ `QUICKSTART.md`

### 想实现流程图截图识别？
→ `doc/2026-01-20/FLOWCHART_RECOGNITION_IMPLEMENTATION.md`

### 想了解 Phase 6 的决策过程？
→ `doc/2026-01-20/ISSUES_AND_DECISIONS.md`

### 想知道为什么不升级 React Flow UI？
→ `doc/2026-01-20/REACT_FLOW_UI_TRUTH.md`

### 遇到之前修复过的问题？
→ `doc/archive/fixes/` 目录

---

## 📝 文档维护规范

### 新增文档时

1. **确定文档类型**
   - 技术方案 → `doc/YYYY-MM-DD/`
   - 问题记录 → `doc/TODO.md` 或 `doc/YYYY-MM-DD/ISSUES_*.md`
   - 实现指南 → `doc/YYYY-MM-DD/*_IMPLEMENTATION.md`

2. **命名规范**
   - 使用大写字母和下划线
   - 描述性文件名（如：FLOWCHART_RECOGNITION_IMPLEMENTATION.md）
   - 避免缩写

3. **添加到索引**
   - 更新本文件（INDEX.md）
   - 在对应章节添加说明

### 文档废弃时

1. **移动到归档**
   ```bash
   mv OLD_DOC.md doc/archive/
   ```

2. **更新索引**
   - 从活跃文档列表移除
   - 添加到归档章节

3. **保留原因说明**
   - 为什么废弃
   - 被什么替代

---

## 🔗 外部资源

**React Flow 官方文档：**
- https://reactflow.dev

**Excalidraw 官方文档：**
- https://docs.excalidraw.com

**AI 模型文档：**
- Gemini: https://ai.google.dev/gemini-api/docs
- Claude: https://docs.anthropic.com/claude/docs
- OpenAI: https://platform.openai.com/docs

---

## 📧 维护者

**文档负责人：** 开发团队
**更新频率：**
- `doc/TODO.md` - 每次完成功能后
- 其他文档 - 根据需要

**上次审查：** 2026-01-20
**下次审查：** 2026-01-27

---

**提示：** 本索引是查找所有项目文档的起点。建议将本文件收藏或固定在浏览器标签页！
