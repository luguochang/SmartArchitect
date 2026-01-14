# SmartArchitect 项目进度记录

> 最后更新：2026-01-08 17:30
> 当前版本：v0.5.0-dev（Phase 5 部分完成）

---

## 📊 当前完成状态

### 📅 2026-01-?? 最新更新
- ✨ BPMN 节点视觉对齐架构节点：事件/任务玻璃风格、图标居中、缺省 iconType 回退到 iconLabel/首字母。
- ✨ AI Actions (Prompter) 执行在无 API Key 时走本地 mock，不再请求后端。
- ✨ Chat Generator mock 数据已切换 BPMN 形状：start-event/end-event/task 及 iconType/color。
- ✨ 画布/边样式优化：glow edges、箭头、柔和网格、玻璃节点。


### ✅ 已完成功能（Phase 1-4）

#### Phase 1: 核心画布与 Mermaid 转换
- [x] React Flow 交互式画布
- [x] 双向 Mermaid 代码同步
- [x] 自定义节点类型（API, Service, Database）
- [x] 节点拖拽和连接

#### Phase 2: AI 视觉分析
- [x] 多 AI 提供商集成（Gemini, OpenAI, Claude, Custom）
- [x] 图片上传 → 架构图转换
- [x] 架构组件识别

#### Phase 3: Prompter + 主题系统
- [x] 3 种场景化重构提示（+ 自定义）
- [x] 12+ 专业主题
- [x] 动态 CSS 变量样式系统

#### Phase 4: RAG + 导出功能
- [x] ChromaDB 向量数据库集成
- [x] 文档上传（PDF, Markdown, DOCX）
- [x] 语义搜索
- [x] PowerPoint 导出
- [x] Slidev 导出
- [x] 演讲稿生成

---

### 🚧 Phase 5: BPMN 节点系统（进行中）

#### 已完成部分

##### 1. Sidebar 重构（✅ 完成）
**文件**：`frontend/components/Sidebar.tsx`
- [x] 宽度扩展：64px → 288px
- [x] 搜索功能：实时过滤节点
- [x] 分类折叠：架构节点、BPMN 节点
- [x] 3 列网格布局
- [x] 节点计数显示

##### 2. BPMN 2.0 标准形状实现（✅ 刚完成）
**文件**：
- `frontend/lib/utils/nodeShapes.ts`（新建）
- `frontend/components/nodes/DefaultNode.tsx`（重构）
- `frontend/components/nodes/GatewayNode.tsx`（优化）
- `backend/app/models/schemas.py`（扩展）

**实现的 BPMN 节点**：

1. **Start Event（开始事件）**
   - 形状：细边框圆形（2px，50x50px）
   - 颜色：绿色 #16a34a
   - 图标：PlayCircle
   - shape: `"start-event"`

2. **End Event（结束事件）**
   - 形状：粗边框圆形（4px，50x50px）
   - 颜色：红色 #dc2626
   - 图标：StopCircle
   - shape: `"end-event"`

3. **Intermediate Event（中间事件）**
   - 形状：双层圆形边框（50x50px）
   - 颜色：黄色 #ca8a04
   - 图标：AlertCircle
   - shape: `"intermediate-event"`

4. **Task（任务）**
   - 形状：大圆角矩形（140x80px）
   - 颜色：蓝色 #2563eb
   - 图标：Box
   - shape: `"task"`

5. **Gateway（异或网关）**
   - 形状：菱形（80x80px）+ 内部 X 符号
   - 颜色：橙色 #ea580c
   - 图标：Shield（仅 Sidebar 显示）
   - shape: `"diamond"`

**技术细节**：
- 图标映射系统：Sidebar 图标 → Canvas 渲染
- 颜色传递：Tailwind 类 → CSS hex 值
- SVG 渲染：Gateway 菱形 + X 符号
- 双层边框：Intermediate Event 实现

##### 3. Chat Generator（✅ Phase 4 完成）
**文件**：
- `backend/app/services/chat_generator.py`
- `backend/app/data/flow_templates.json`
- `frontend/components/ChatGeneratorModal.tsx`

- [x] 8 个模板预设
- [x] 模板分类：architecture, troubleshooting, business, algorithm, devops
- [x] Mock 数据支持
- [x] 模板 ID 条件渲染

---

## 📋 待办事项（TODO）

### 🔴 高优先级

#### 1. Mock 数据更新
**问题**：Chat Generator 的 mock 数据仍使用旧的 shape 值
**文件**：`backend/app/services/chat_generator.py`
**需要修改**：
```python
# 旧值（需要更新）
{"data": {"label": "开始", "shape": "circle"}}  # ❌
{"data": {"label": "网关", "shape": "diamond"}}  # ❌

# 新值（BPMN 标准）
{"data": {"label": "开始", "shape": "start-event", "iconType": "play-circle", "color": "#16a34a"}}  # ✅
{"data": {"label": "网关", "shape": "diamond"}}  # ✅ Gateway 保持不变
{"data": {"label": "任务", "shape": "task", "iconType": "box", "color": "#2563eb"}}  # ✅
```

#### 2. 测试 BPMN 节点
- [ ] 浏览器刷新测试 Sidebar BPMN 分类
- [ ] 添加各类型节点到画布
- [ ] 验证形状渲染正确
- [ ] 验证颜色一致性
- [ ] 测试主题切换（12 个主题）
- [ ] 测试节点编辑（双击）
- [ ] 测试节点连接

#### 3. AI 生成流程图测试
- [ ] 选择模板生成流程图
- [ ] 验证 BPMN 节点正确应用
- [ ] 检查 shape 属性传递

---

### 🟡 中优先级

#### 4. Phase 5 剩余任务（原计划）

##### 4.1 Group B 节点重构（部分完成）
**状态**：Gateway 已优化，其他 4 个节点待重构
**待重构节点**：
- [ ] `CacheNode.tsx` - 使用 CSS 变量
- [ ] `QueueNode.tsx` - 使用 CSS 变量
- [ ] `StorageNode.tsx` - 使用 CSS 变量
- [ ] `ClientNode.tsx` - 使用 CSS 变量

**重构模式**：参考 `ApiNode.tsx`
- 移除硬编码 Tailwind 颜色类
- 使用 `var(--cache-border)` 等 CSS 变量
- 统一内边距 `px-4 py-3`
- 添加副标题标签

##### 4.2 主题系统扩展
**文件**：
- `frontend/lib/themes/types.ts`
- `frontend/lib/themes/presets.ts`
- `frontend/lib/themes/ThemeContext.tsx`

- [ ] 添加 4 个节点类型到 ThemeColors 接口
  - `cacheNode: NodeColors`
  - `queueNode: NodeColors`
  - `storageNode: NodeColors`
  - `clientNode: NodeColors`
- [ ] 为 12 个主题添加这 4 个节点的颜色
- [ ] 应用 CSS 变量到 DOM

---

### 🟢 低优先级

#### 5. 视觉增强
- [ ] 悬停效果优化（`globals.css`）
- [ ] 图标微动画
- [ ] 细微渐变背景（可选）

#### 6. Phase 6: 条件边样式（可选）
- [ ] 创建 `ConditionalEdge.tsx`
- [ ] 绿色/红色条件分支
- [ ] 更新 AI Prompt 生成条件边

#### 7. 更多 BPMN 节点（未来）
- [ ] Parallel Gateway（并行网关）- 菱形 + 内部 ＋ 符号
- [ ] Inclusive Gateway（包容网关）- 菱形 + 内部 ○ 符号
- [ ] Event Gateway（事件网关）- 菱形 + 内部五边形
- [ ] Subprocess（子流程）- 矩形 + 底部 ＋ 符号
- [ ] Timer Event（定时事件）- 圆形 + 内部时钟图标
- [ ] Message Event（消息事件）- 圆形 + 内部信封图标

---

## 🐛 已知问题

### 1. 首次 RAG 查询延迟
**现象**：首次语义搜索约 26 秒
**原因**：sentence-transformers 模型初始化
**状态**：已知行为，后续查询正常（100-200ms）

### 2. 测试超时
**测试**：`test_export_script_no_api_key`
**现象**：无效 API key 时挂起
**状态**：预期行为（错误路径测试）

### 3. 认证和限流缺失
**影响**：生产环境不可用
**文档**：参见 `SYSTEM_REVIEW.md`
**计划**：Phase 7（生产部署）

---

## 📂 关键文件清单

### 最近修改的文件（2026-01-08）

#### Frontend
```
frontend/
├── components/
│   ├── Sidebar.tsx                          # ✅ 重构完成
│   ├── nodes/
│   │   ├── DefaultNode.tsx                  # ✅ BPMN 支持完成
│   │   ├── GatewayNode.tsx                  # ✅ 优化完成（X 符号）
│   │   ├── CacheNode.tsx                    # 🚧 待重构
│   │   ├── QueueNode.tsx                    # 🚧 待重构
│   │   ├── StorageNode.tsx                  # 🚧 待重构
│   │   └── ClientNode.tsx                   # 🚧 待重构
│   └── ChatGeneratorModal.tsx               # ✅ Phase 4 完成
├── lib/
│   ├── utils/
│   │   └── nodeShapes.ts                    # ✅ 新建（BPMN 配置）
│   └── themes/
│       ├── types.ts                         # 🚧 待扩展
│       ├── presets.ts                       # 🚧 待扩展
│       └── ThemeContext.tsx                 # 🚧 待扩展
└── app/
    └── globals.css                           # 🟡 待增强
```

#### Backend
```
backend/
├── app/
│   ├── models/
│   │   └── schemas.py                       # ✅ 新增 shape 类型
│   ├── services/
│   │   └── chat_generator.py                # 🚧 Mock 数据待更新
│   └── data/
│       └── flow_templates.json              # ✅ Phase 4 完成
└── tests/
    ├── test_api.py                           # ✅ 97% 通过
    └── test_services.py                      # ✅ 100% 通过
```

---

## 🔧 运行环境

### 后端
- **端口**：8002（当前运行中，PID: 3852）
- **Python**：3.12.5
- **虚拟环境**：`backend/venv`
- **启动命令**：
  ```bash
  cd backend
  venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8002
  ```

### 前端
- **端口**：3000
- **Node.js**：建议 18+
- **包管理器**：npm
- **启动命令**：
  ```bash
  cd frontend
  npm run dev
  ```

### 代理配置
- **文件**：`frontend/next.config.js`
- **当前配置**：`/api/:path*` → `http://localhost:8002/api/:path*`

---

## 🎯 下一步行动计划

### 立即执行（切换环境前）
1. ✅ 创建此进度文档
2. 🔄 提交当前代码到 Git
   ```bash
   git add .
   git commit -m "feat: implement BPMN 2.0 standard shapes with proper styling

   - Add 5 BPMN standard node shapes (start-event, end-event, intermediate-event, task, gateway)
   - Refactor DefaultNode to support multiple shape types
   - Update GatewayNode with X symbol and proper 80px size
   - Refactor Sidebar to 288px width with search and categories
   - Add icon and color mapping system for node customization
   - Update backend schemas to support new shape types

   Breaking changes:
   - shape: 'circle' → 'start-event'/'end-event'/'intermediate-event'
   - Gateway size: 120px → 80px

   Known issues:
   - Mock data in chat_generator.py needs updating to new shape types
   - 4 architecture nodes (Cache, Queue, Storage, Client) need CSS variable refactor"
   ```

### 切换环境后
1. 启动后端：`cd backend && venv\Scripts\activate && python -m app.main`
2. 启动前端：`cd frontend && npm run dev`
3. 测试 BPMN 节点：
   - 展开 Sidebar "BPMN 节点" 分类
   - 添加 5 种节点到画布
   - 验证形状和颜色
4. 更新 Mock 数据（如需要）
5. 继续 Phase 5 剩余任务

---

## 📚 参考文档

### 项目文档
- `README.md` - 项目概述（中文）
- `CLAUDE.md` - Claude Code 指导文档
- `SYSTEM_REVIEW.md` - 生产就绪评估
- `TEST_COVERAGE_REPORT.md` - 测试覆盖报告

### BPMN 2.0 标准参考
- **开始事件**：细边框圆形（1-2px）
- **结束事件**：粗边框圆形（3-4px）
- **中间事件**：双层圆形
- **任务**：圆角矩形（radius: 10-15px）
- **异或网关**：菱形 + X 符号
- **并行网关**：菱形 + ＋ 符号
- **包容网关**：菱形 + ○ 符号

### API 文档
- **Swagger UI**：http://localhost:8002/docs（后端运行时可访问）

---

## 💡 技术债务

### 代码质量
- [ ] Group B 节点硬编码颜色类（技术债）
- [ ] Mock 数据 shape 值过时
- [ ] 缺少 BPMN 节点单元测试

### 架构改进
- [ ] 节点注册系统可改为动态加载
- [ ] 主题系统配置可抽离为 JSON
- [ ] 图标映射可使用枚举类型

### 性能优化
- [ ] RAG 首次查询延迟（模型预加载）
- [ ] 大型流程图渲染（虚拟化）
- [ ] Bundle 大小优化（代码分割）

---

## ✅ 验收标准

### BPMN 节点系统验收
- [ ] 所有 5 种 BPMN 节点可从 Sidebar 添加
- [ ] 形状符合 BPMN 2.0 标准
- [ ] 颜色与 Sidebar 图标一致
- [ ] 12 个主题切换正常
- [ ] 节点可编辑、连接、拖拽
- [ ] 导出为 Mermaid 代码正确
- [ ] AI 生成的流程图使用正确的 shape 值

---

**最后提交者**：Claude Sonnet 4.5
**下次继续点**：测试 BPMN 节点 → 更新 Mock 数据 → Group B 节点重构
---



## 当前可继续的计划（已写入“下一步计划”）：

  1. 主题系统扩展：为 cache/queue/storage/client 在 frontend/lib/themes/types.ts / frontend/lib/themes/presets.ts / frontend/lib/themes/
     ThemeContext.tsx 补充色板和 CSS 变量。
  2. BPMN 节点验证：Sidebar 添加、形状/颜色/主题切换、编辑/连线等手动检查或测试。
  3. 可选：条件边（Phase 6 草案）与更多 BPMN 节点（并行/包容网关等）
# 最新进展快照（2026-01-14 17:00）

- 新增 Excalidraw 生成接口 `/api/excalidraw/generate`，前端支持 Flow / Excalidraw 切换，Excalidraw 模式隐藏 Sidebar。
- 新增 Frame/Layer 框节点，可双击改名，用于分层包裹。
- 问题：SiliconFlow 默认 `Qwen3-VL` 返回非标准 JSON（缺逗号/冒号）导致 500 并回落 mock；尝试自动退回 `Qwen2.5-14B` 更稳定但尚未完整验证。
- 问题：流式体验未打通，React Flow / Excalidraw 的 SSE 状态与聊天框未统一，Excalidraw 模式切换时 UI 有错位/丢失。
- 已提高后端超时至 180s，并对 SiliconFlow 使用 `response_format=json_object`，但仍需更强 JSON 清洗/兜底。

### 下次优先事项
1) 先用 `Qwen/Qwen2.5-14B-Instruct` 自测 `/api/excalidraw/generate` 确保不回落 mock，并记录日志。
2) 前端明确传递 canvasMode/model，后端识别模式；补充 loading/error 提示，修复 Excalidraw 模式布局/聊天框缺失。
3) 对 SiliconFlow 响应增加健壮清洗（去尾逗号、补键）或加强提示词，必要时后处理修复 JSON。
4) 补最小化集成测试（脚本或单测）覆盖 Excalidraw 生成成功路径。
