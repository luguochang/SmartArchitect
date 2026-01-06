# SmartArchitect AI - Backend

FastAPI 后端服务，提供架构图解析、AI 模型配置等功能。

## 安装

1. 创建虚拟环境：
```bash
python -m venv venv
```

2. 激活虚拟环境：
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量（可选）：
```bash
cp .env.example .env
# 编辑 .env 文件，添加必要的配置
```

## 运行

```bash
python -m app.main
```

或使用 uvicorn：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API 文档将在以下地址可用：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### Phase 1 MVP
- `GET /api/health` - 健康检查
- `POST /api/mermaid/parse` - 解析 Mermaid 代码为图数据
- `POST /api/graph/to-mermaid` - 将图数据转换为 Mermaid 代码
- `POST /api/models/config` - 配置 AI 模型
- `GET /api/models/config/{provider}` - 获取模型配置

## 项目结构

```
backend/
├── app/
│   ├── api/          # API 路由
│   ├── core/         # 核心配置
│   ├── models/       # 数据模型
│   ├── services/     # 业务逻辑（未来扩展）
│   └── main.py       # 应用入口
├── tests/            # 测试文件
└── requirements.txt  # 依赖列表
```
