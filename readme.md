# SmartArchitect AI: 开发者驱动的 AI 架构设计平台

## 1. 项目概览 (Project Overview)

### 1.1 背景

开发者在进行架构设计时，往往在“白板/截图”与“代码/文档”之间存在断层。SmartArchitect 旨在通过 AI 实现从“视觉输入”到“可编辑架构代码”的无缝转换，并提供架构级的优化建议。

### 1.2 核心愿景

* **不仅仅是复刻，更是重构**：AI 识别现有的系统瓶颈并提供优化版本。

* **代码即架构 (Architecture as Code)**：实时生成 Mermaid.js、D2 或 Terraform 代码。

* **对话式绘图**：通过自然语言直接控制 React Flow 画布。

## 2. 技术架构 (Technical Architecture)

### 2.1 整体拓扑

* **前端 (Frontend)**: Next.js 14 (App Router) + React Flow + Tailwind CSS + Shadcn UI.

* **后端 (Backend)**: Python FastAPI + Pydantic + Google Generative AI (Gemini).

* **通信 (Communication)**:

  * REST API (常规请求)

  * SSE (Server-Sent Events) (AI 流式对话)

  * WebSocket (实时协作预览 - 选配)

### 2.2 前后端分工

* **Next.js**: 处理复杂的节点状态（Zustand）、Mermaid 代码同步渲染、以及极致的响应式 UI。

* **FastAPI**: 负责多模态 AI 处理（图片解析）、架构逻辑验证、以及生成复杂的基础设施代码（Terraform/K8s）。

## 3. 核心功能设计 (Feature Specification)

### 3.1 AI Vision-to-Graph (图片转图表)

* **流程**：用户上传图片 -> FastAPI 预处理 -> Gemini 2.5 Flash 多模态解析 -> 返回符合 React Flow 规范的 JSON 节点和连线。

* **重构逻辑**：AI 在解析过程中会自动标记潜在的“单点故障”或“性能瓶颈”，并在 UI 中以热点形式展示。

### 3.2 代码同步引擎 (Code Sync Engine)

* **双向绑定**：

  1. **Canvas -> Code**: 拖拽节点时，自动更新 Monaco Editor 里的 Mermaid 代码。

  2. **Code -> Canvas**: 修改代码，画布实时重绘。

* **导出模块**：Python 后端支持将架构逻辑转换为 Terraform (HCL) 或 Docker Compose 文件。

### 3.3 交互式对话 UI (Conversational UI)

* **Command Center**: 画布底部的 Command Bar 支持自然语言指令。

* **示例指令**：

  * "在 API Gateway 后面增加一个消息队列和两个消费者。"

  * "优化现有的数据库结构，增加读写分离。"

## 4. 技术规格 (Technical Specs)

### 4.1 前端：React Flow 深度集成

* **自定义节点 (Custom Nodes)**：为数据库、网关、微服务等设计专属的开发者图标（使用 Lucide-React）。

* **自动布局 (Auto Layout)**：集成 `dagre` 或 `elkjs` 算法，实现一键整理凌乱的节点。

### 4.2 后端：AI 处理流

* **Prompt Engineering**：针对架构设计优化的 System Prompt，确保 AI 输出的 JSON 结构严谨。

* **安全性**：使用 Python 校验生成的代码片段，防止恶意指令注入。

## 5. UI/UX 规范 (Design Guidelines)

* **审美风格**：参考 Vercel (Geist) 与 Linear。

* **色彩方案**：

  * 背景: `#F8FAFC` (Slate 50) / `#020617` (Slate 950)。

  * 品牌色: Indigo 600 (`#4F46E5`)。

* **交互细节**：

  * 所有 AI 建议的操作均带有 `Sparkles` 图标提示。

  * 节点拖拽带有磁吸感（Snap to Grid）。

## 6. API 设计预览

### `POST /api/v1/architect/analyze` (图片分析)

* **Request**: `multipart/form-data` { `file`: Image }

* **Response**:

  ```json
  {
    "nodes": [...],
    "edges": [...],
    "mermaid_code": "graph TD...",
    "ai_analysis": {
      "bottlenecks": ["Single point of failure at Node A"],
      "optimized_version": "..."
    }
  }
  ```

## 7. 项目路线图 (Roadmap)

* [x] **Phase 1**: 基础画布预览与 Mermaid 代码双向编辑 (MVP) - ✅ 已完成

* [ ] **Phase 2**: 接入多模型 AI 接口（Gemini/OpenAI/Claude），实现图片一键转画布。

* [ ] **Phase 3**: 增加对话式修改与 AI 架构重构建议。

* [ ] **Phase 4**: 导出 Terraform 与 CloudFormation 配置。

## 8. 快速开始 (Quick Start)

### 8.1 环境要求

- Node.js 18+ (推荐 20+)
- Python 3.10+
- npm/yarn/pnpm

### 8.2 安装步骤

#### 前端安装

```bash
cd frontend
npm install
```

#### 后端安装

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 8.3 启动服务

#### 方式一：使用启动脚本（推荐）

```bash
# Windows
start-dev.bat

# Linux/Mac
./start-dev.sh
```

#### 方式二：分别启动

**终端 1 - 启动后端：**
```bash
cd backend
# 确保虚拟环境已激活
python -m app.main
```

**终端 2 - 启动前端：**
```bash
cd frontend
npm run dev
```

### 8.4 访问应用

- **前端应用**: http://localhost:3000
- **后端 API**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

### 8.5 Phase 1 MVP 功能

✅ **已实现的功能**：
- React Flow 可视化画布
- 自定义节点类型（API、Service、Database）
- 节点拖拽、连接
- Monaco Editor 代码编辑器
- Mermaid 代码双向同步（Canvas ↔ Code）
- AI 模型配置界面（支持 Gemini、OpenAI、Claude、自定义模型）
- 响应式 UI 设计（参考 Vercel/Linear 风格）

🚧 **下一步计划**（Phase 2）：
- 图片上传与 AI 解析
- 架构优化建议
- 自动布局算法（dagre/elkjs）

### 8.6 项目结构

```
SmartArchitect/
├── frontend/          # Next.js 14 前端应用
│   ├── app/          # App Router 页面
│   ├── components/   # React 组件
│   ├── lib/          # 工具函数和状态管理
│   └── public/       # 静态资源
│
├── backend/          # FastAPI 后端服务
│   ├── app/          # 应用主目录
│   │   ├── api/      # API 路由
│   │   ├── core/     # 核心配置
│   │   ├── models/   # 数据模型
│   │   └── main.py   # 应用入口
│   └── tests/        # 测试文件
│
└── docs/            # 项目文档
    ├── architecture.md
    └── getting-started.md
```

### 8.7 了解更多

- 📖 [详细安装指南](docs/getting-started.md)
- 🏗️ [技术架构文档](docs/architecture.md)
- 🔌 [API 文档](http://localhost:8000/docs)（需先启动后端）