# SmartArchitect AI - Frontend

Next.js 14 前端应用，提供可视化架构设计画布和代码编辑器。

## 安装

```bash
npm install
# 或
yarn install
# 或
pnpm install
```

## 运行

开发模式：
```bash
npm run dev
# 或
yarn dev
# 或
pnpm dev
```

访问 http://localhost:3000 查看应用。

## 构建

```bash
npm run build
npm start
```

## 功能特性

### Phase 1 MVP
- ✅ React Flow 画布 - 拖拽式架构设计
- ✅ 自定义节点类型（API、服务、数据库）
- ✅ Monaco Editor - Mermaid 代码编辑
- ✅ 画布 ↔ 代码双向同步
- ✅ AI 模型配置界面（支持 Gemini、OpenAI、Claude）

## 项目结构

```
frontend/
├── app/              # Next.js App Router
│   ├── globals.css   # 全局样式
│   ├── layout.tsx    # 根布局
│   └── page.tsx      # 首页
├── components/       # React 组件
│   ├── nodes/        # 自定义节点
│   ├── ArchitectCanvas.tsx
│   ├── CodeEditor.tsx
│   ├── Sidebar.tsx
│   └── ModelConfigModal.tsx
├── lib/              # 工具库
│   └── store/        # Zustand 状态管理
└── public/           # 静态资源
```

## 技术栈

- **框架**: Next.js 14 (App Router)
- **UI 库**: React Flow, Tailwind CSS, Lucide Icons
- **编辑器**: Monaco Editor
- **状态管理**: Zustand
