# SmartArchitect AI - 快速开始指南

## 环境要求

- Node.js 18+ (推荐 20+)
- Python 3.10+
- npm/yarn/pnpm

## 完整安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd SmartArchitect
```

### 2. 安装前端依赖

```bash
cd frontend
npm install
```

### 3. 安装后端依赖

```bash
cd ../backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install -r requirements.txt
```

### 4. 配置环境变量（可选）

```bash
# 后端配置
cd backend
cp .env.example .env
# 编辑 .env 文件，根据需要添加配置
```

### 5. 启动服务

#### 方式一：分别启动（推荐用于开发）

终端 1 - 启动后端：
```bash
cd backend
# 确保虚拟环境已激活
python -m app.main
```

终端 2 - 启动前端：
```bash
cd frontend
npm run dev
```

#### 方式二：使用启动脚本（即将提供）

```bash
# Windows
.\start.bat

# Linux/Mac
./start.sh
```

### 6. 访问应用

- 前端应用: http://localhost:3000
- 后端 API: http://localhost:8000
- API 文档: http://localhost:8000/docs

## 基本使用

### 添加节点

1. 点击左侧工具栏的图标（API、服务、数据库）
2. 节点会自动添加到画布上
3. 拖拽节点到合适的位置

### 连接节点

1. 从一个节点的连接点拖拽到另一个节点
2. 连接会自动创建
3. 右侧代码编辑器会自动更新

### 编辑代码

1. 在右侧 Monaco Editor 中编辑 Mermaid 代码
2. 点击 "Apply" 按钮
3. 画布会根据代码更新

### 配置 AI 模型（Phase 2 功能）

1. 点击左侧底部的设置图标
2. 选择模型提供商（Gemini、OpenAI、Claude 等）
3. 输入 API Key 和模型名称
4. 保存配置

## 下一步

- 查看 [架构文档](./architecture.md) 了解技术细节
- 查看 [API 文档](http://localhost:8000/docs) 了解后端接口
- 参考 README 中的路线图了解未来功能

## 常见问题

### 前端无法连接后端

确保：
1. 后端服务已启动（http://localhost:8000）
2. CORS 配置正确
3. 检查 `frontend/next.config.js` 中的代理配置

### 依赖安装失败

- Node.js: 确保版本 >= 18
- Python: 确保版本 >= 3.10
- 清理缓存后重试：`npm cache clean --force` 或 `pip cache purge`
