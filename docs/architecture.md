# SmartArchitect 技术架构文档

## 项目结构

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
│   │   └── services/ # 业务逻辑
│   └── tests/        # 测试文件
│
└── docs/            # 项目文档
```

## 技术栈

### 前端
- **框架**: Next.js 14 (App Router)
- **UI 库**: React Flow (画布), Shadcn UI (组件), Tailwind CSS (样式)
- **代码编辑器**: Monaco Editor
- **状态管理**: Zustand
- **图标**: Lucide React

### 后端
- **框架**: FastAPI
- **AI 集成**: 支持多模型配置（Gemini, OpenAI, Claude 等）
- **数据验证**: Pydantic
- **CORS**: 支持跨域请求

## Phase 1 MVP 功能

1. **基础画布**
   - React Flow 节点和边的创建、拖拽、删除
   - 自定义节点类型（数据库、API、服务等）
   - 自动布局功能

2. **代码编辑器**
   - Monaco Editor 集成
   - Mermaid 语法高亮
   - 实时代码验证

3. **双向同步**
   - 画布变化 → 自动更新 Mermaid 代码
   - 代码修改 → 实时重绘画布

4. **AI 模型配置**
   - 可配置的模型提供商
   - 灵活的 API Key 管理
   - 支持多种 AI 模型（预留接口）

## API 端点设计

### Phase 1
- `GET /api/health` - 健康检查
- `POST /api/models/config` - 配置 AI 模型
- `POST /api/mermaid/parse` - 解析 Mermaid 代码为 React Flow 格式
- `POST /api/graph/to-mermaid` - 将 React Flow 图转换为 Mermaid 代码

### Phase 2+（未来扩展）
- `POST /api/architect/analyze` - 图片分析
- `POST /api/architect/optimize` - AI 架构优化建议
- `POST /api/export/terraform` - 导出 Terraform 配置
