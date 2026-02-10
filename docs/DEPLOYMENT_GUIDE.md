# SmartArchitect AI 免费平台部署指南

> **版本**: v1.0
> **最后更新**: 2026-02-10
> **部署方案**: Vercel (前端) + Render (后端)

---

## 📋 目录

- [部署概览](#部署概览)
- [前置准备](#前置准备)
- [Phase 1: 准备代码](#phase-1-准备代码)
- [Phase 2: 部署后端到 Render](#phase-2-部署后端到-render)
- [Phase 3: 部署前端到 Vercel](#phase-3-部署前端到-vercel)
- [Phase 4: 配置跨域和环境变量](#phase-4-配置跨域和环境变量)
- [Phase 5: 功能测试](#phase-5-功能测试)
- [常见问题](#常见问题)
- [性能优化建议](#性能优化建议)
- [备选方案](#备选方案)

---

## 部署概览

### 🎯 部署目标

将 SmartArchitect AI 部署到免费的云平台，为用户提供在线 Demo 体验，无需本地安装即可使用。

### 🏗️ 架构方案

```
┌─────────────────┐         ┌─────────────────┐
│   Vercel        │         │   Render        │
│  (前端托管)      │────────▶│  (后端 API)      │
│  Next.js 14     │  HTTPS  │  FastAPI        │
│  全球 CDN       │         │  Python 3.12    │
└─────────────────┘         └─────────────────┘
      ↓                              ↓
   用户浏览器                    AI 服务调用
```

### 📊 成本与限制

| 项目 | 服务 | 免费额度 | 限制 |
|------|------|---------|------|
| **前端** | Vercel | 无限制 | 100GB 带宽/月 |
| **后端** | Render Free | 750 小时/月 | 512MB RAM<br>闲置 15 分钟休眠 |
| **总成本** | - | **$0/月** | - |

### ⚠️ 已知限制

1. **冷启动延迟**: 后端闲置 15 分钟后休眠，首次访问需 30-60 秒唤醒
2. **数据不持久化**: Canvas 会话和导出文件在服务重启后丢失（影响有限，TTL 60 分钟）
3. **RAG 功能不可用**: ChromaDB 依赖未安装（`requirements.txt` 中已注释），文档上传功能禁用
4. **内存限制**: 512MB RAM，大量并发请求可能 OOM

---

## 前置准备

### 1. GitHub 账号

- 已有账号：https://github.com/luguochang/SmartArchitect
- 分支：`dev20260129`
- 权限：Owner（可推送代码）

### 2. 注册云服务账号

#### Render 账号
- 网址：https://render.com
- 注册方式：使用 GitHub 账号一键登录
- 费用：完全免费（Free Plan）

#### Vercel 账号
- 网址：https://vercel.com
- 注册方式：使用 GitHub 账号一键登录
- 费用：完全免费（Hobby Plan）

### 3. AI API Keys（可选）

根据需要申请以下 API Keys（至少一个）：

| Provider | 用途 | 申请地址 | 免费额度 |
|----------|------|---------|---------|
| **SiliconFlow** | Excalidraw 生成 | https://siliconflow.cn | 免费试用 |
| **Google Gemini** | Vision 分析、Chat 生成 | https://makersuite.google.com/app/apikey | 免费 60 请求/分钟 |
| **OpenAI** | Vision 分析 | https://platform.openai.com/api-keys | 需付费 |
| **Anthropic** | Vision 分析 | https://console.anthropic.com | 需付费 |

### 4. 开发工具（本地测试用）

- Git 客户端
- 文本编辑器（VS Code 推荐）

---

## Phase 1: 准备代码

### 1.1 验证代码更改

确认以下文件已更新（本次部署已自动修改）：

#### ✅ `backend/app/core/config.py`

```python
# 已移除硬编码的 API Key，改为从环境变量读取
SILICONFLOW_API_KEY: str = os.getenv("SILICONFLOW_API_KEY", "")
```

#### ✅ `backend/render.yaml`

```yaml
# 已添加完整的环境变量配置和部署说明
envVars:
  - key: CORS_ORIGINS
    value: http://localhost:3000  # 部署后更新
  - key: SILICONFLOW_API_KEY
    sync: false  # 在 Render Dashboard 中配置
```

#### ✅ `frontend/.env.production`

```bash
# 已创建生产环境配置模板
BACKEND_ORIGIN=https://your-backend.onrender.com
```

### 1.2 提交更改到 GitHub

```bash
# 1. 切换到开发分支
git checkout dev20260129

# 2. 查看更改
git status

# 3. 添加所有修改的文件
git add backend/app/core/config.py backend/render.yaml backend/.env.example frontend/.env.production docs/DEPLOYMENT_GUIDE.md

# 4. 提交更改
git commit -m "chore: prepare for production deployment

- Remove hardcoded SiliconFlow API key for security
- Update Render config with full environment variables
- Add frontend production environment template
- Update backend .env.example with deployment instructions
- Add comprehensive deployment guide"

# 5. 推送到 GitHub
git push origin dev20260129
```

### 1.3 验证 GitHub 推送

1. 访问 https://github.com/luguochang/SmartArchitect/tree/dev20260129
2. 确认最新提交存在
3. 检查以下文件是否更新：
   - `backend/app/core/config.py`
   - `backend/render.yaml`
   - `frontend/.env.production`
   - `docs/DEPLOYMENT_GUIDE.md`

---

## Phase 2: 部署后端到 Render

### 2.1 创建 Web Service

1. **登录 Render Dashboard**
   - 访问：https://dashboard.render.com
   - 使用 GitHub 账号登录

2. **创建新服务**
   - 点击右上角 **New +** 按钮
   - 选择 **Web Service**

3. **连接 GitHub 仓库**
   - 选择 **Connect a repository**
   - 如果首次使用，点击 **Configure account** 授权 Render 访问 GitHub
   - 搜索并选择：`luguochang/SmartArchitect`

4. **配置部署参数**

   | 配置项 | 值 | 说明 |
   |--------|---|------|
   | **Name** | `smartarchitect-backend` | 服务名称（影响 URL） |
   | **Region** | `Singapore` 或 `Oregon` | 选择离用户最近的区域 |
   | **Branch** | `dev20260129` | 部署分支 |
   | **Root Directory** | `backend` | 后端代码目录 |
   | **Runtime** | `Python 3` | 自动检测 |
   | **Build Command** | `pip install -r requirements.txt` | 自动检测 |
   | **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | 自动检测 |
   | **Instance Type** | **Free** | 选择免费计划 |

5. **点击 Create Web Service**

### 2.2 配置环境变量

部署创建后，点击左侧菜单 **Environment** 标签页。

#### 必需的环境变量

| Key | Value | Type | 说明 |
|-----|-------|------|------|
| `PYTHON_VERSION` | `3.12.0` | Plain Text | Python 版本 |
| `ENVIRONMENT` | `production` | Plain Text | 环境模式 |
| `LOG_LEVEL` | `INFO` | Plain Text | 日志级别 |
| `CORS_ORIGINS` | `http://localhost:3000` | Plain Text | 稍后更新为 Vercel URL |

#### 可选的 API Keys（至少配置一个）

| Key | Value | Type | 说明 |
|-----|-------|------|------|
| `SILICONFLOW_API_KEY` | `sk-your-key` | **Secret** | Excalidraw 生成 |
| `GEMINI_API_KEY` | `your-key` | **Secret** | Vision + Chat |
| `OPENAI_API_KEY` | `sk-your-key` | **Secret** | Vision 分析 |
| `ANTHROPIC_API_KEY` | `sk-ant-your-key` | **Secret** | Vision 分析 |

**添加步骤**：
1. 点击 **Add Environment Variable**
2. 输入 Key 和 Value
3. 如果是 API Key，勾选 **Secret** 类型
4. 点击 **Save Changes**

### 2.3 等待部署完成

1. **查看构建日志**
   - 点击左侧菜单 **Logs** 标签页
   - 观察构建过程

2. **预期日志输出**
   ```
   ==> Cloning from https://github.com/luguochang/SmartArchitect...
   ==> Checking out commit 62d328f in branch dev20260129
   ==> Running build command 'pip install -r requirements.txt'...
   ==> Build completed successfully
   ==> Starting service with 'uvicorn app.main:app --host 0.0.0.0 --port 10000'
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   ```

3. **构建时间**: 约 3-5 分钟

### 2.4 验证后端部署

1. **获取后端 URL**
   - 部署成功后，页面顶部会显示 URL
   - 格式：`https://smartarchitect-backend.onrender.com`
   - **复制并保存此 URL**（后续配置需要）

2. **测试健康检查**
   - 访问：`https://smartarchitect-backend.onrender.com/api/health`
   - 预期响应：
     ```json
     {
       "status": "healthy",
       "timestamp": "2026-02-10T12:34:56.789Z",
       "version": "0.5.0"
     }
     ```

3. **测试 API 文档**
   - 访问：`https://smartarchitect-backend.onrender.com/docs`
   - 应显示 Swagger UI 交互式文档

4. **测试 Mermaid 解析**
   - 在 Swagger UI 中展开 `POST /api/mermaid/parse`
   - 点击 **Try it out**
   - 输入测试数据：
     ```json
     {
       "code": "graph TD\nA-->B"
     }
     ```
   - 点击 **Execute**
   - 预期返回解析后的节点和边

**如果遇到错误，请查看 [常见问题](#常见问题) 章节。**

---

## Phase 3: 部署前端到 Vercel

### 3.1 导入项目

1. **登录 Vercel Dashboard**
   - 访问：https://vercel.com/dashboard
   - 使用 GitHub 账号登录

2. **创建新项目**
   - 点击右上角 **Add New...** → **Project**
   - 或点击 **Import Project**

3. **导入 GitHub 仓库**
   - 在仓库列表中找到 `luguochang/SmartArchitect`
   - 如果没有看到，点击 **Adjust GitHub App Permissions** 授权访问
   - 点击仓库右侧的 **Import** 按钮

### 3.2 配置部署参数

在 **Configure Project** 页面设置：

#### 基础配置

| 配置项 | 值 | 说明 |
|--------|---|------|
| **Project Name** | `smartarchitect` | 项目名称（影响默认 URL） |
| **Framework Preset** | `Next.js` | 自动检测 |
| **Root Directory** | `frontend` | 前端代码目录 |
| **Build and Output Settings** | - | 使用默认值 |
| - Build Command | `npm run build` | 自动检测 |
| - Output Directory | `.next` | 自动检测 |
| - Install Command | `npm install` | 自动检测 |

#### 环境变量配置

点击 **Environment Variables** 展开，添加：

| Name | Value | Environment |
|------|-------|-------------|
| `BACKEND_ORIGIN` | `https://smartarchitect-backend.onrender.com` | Production |

**注意**：将 `https://smartarchitect-backend.onrender.com` 替换为您在 Phase 2.4 中获取的实际后端 URL。

### 3.3 部署项目

1. 点击 **Deploy** 按钮
2. 等待部署完成（约 2-3 分钟）

### 3.4 验证前端部署

1. **获取前端 URL**
   - 部署成功后会显示祝贺页面
   - URL 格式：`https://smartarchitect-xxx.vercel.app`
   - 或自定义域名：`https://smartarchitect.vercel.app`
   - **复制并保存此 URL**（后续配置需要）

2. **访问网站**
   - 点击 **Visit** 按钮或直接访问 URL
   - 应该看到 SmartArchitect AI 的主界面

3. **初步测试**
   - 尝试在 Canvas 上拖拽添加节点
   - 观察是否有 CORS 错误（控制台 F12）

**预期情况**：前端可以加载，但 API 调用会失败（因为还没配置 CORS）。

---

## Phase 4: 配置跨域和环境变量

### 4.1 更新后端 CORS 配置

1. **返回 Render Dashboard**
   - 访问：https://dashboard.render.com
   - 点击进入 `smartarchitect-backend` 服务

2. **更新 CORS_ORIGINS 环境变量**
   - 点击左侧菜单 **Environment**
   - 找到 `CORS_ORIGINS` 变量
   - 点击右侧 **Edit** 按钮
   - 更新 Value 为：
     ```
     https://smartarchitect-xxx.vercel.app,https://smartarchitect.vercel.app,http://localhost:3000
     ```
     **注意**：
     - 将 `smartarchitect-xxx.vercel.app` 替换为您的实际 Vercel URL
     - 多个域名用逗号分隔，**不要有空格**
     - 保留 `http://localhost:3000` 用于本地开发

3. **保存并重启**
   - 点击 **Save Changes**
   - Render 会自动重启服务（约 30 秒）

### 4.2 验证跨域配置

1. **清除浏览器缓存**
   - 按 Ctrl+Shift+Delete（Windows）或 Cmd+Shift+Delete（Mac）
   - 选择清除缓存和 Cookie

2. **重新访问前端**
   - 打开 `https://smartarchitect-xxx.vercel.app`
   - 按 F12 打开开发者工具
   - 切换到 **Console** 标签页

3. **测试功能**
   - 添加一个节点到 Canvas
   - 观察是否有 CORS 错误
   - **预期**：无错误，节点成功添加

4. **如果仍有错误**
   - 检查后端日志（Render Dashboard → Logs）
   - 确认 CORS_ORIGINS 配置正确
   - 等待 1-2 分钟让配置生效

### 4.3（可选）配置自定义域名

#### Vercel 自定义域名

1. Vercel Dashboard → 选择项目 → **Settings** → **Domains**
2. 点击 **Add** 输入域名（如 `smartarchitect.yourdomain.com`）
3. 按照提示在域名服务商处添加 DNS 记录：
   - 类型：`CNAME`
   - 名称：`smartarchitect`
   - 值：`cname.vercel-dns.com`
4. 等待 DNS 生效（通常 5-30 分钟）
5. **重要**：配置后需要回到 Phase 4.1 更新后端 CORS_ORIGINS

#### Render 自定义域名（可选）

1. Render Dashboard → 选择服务 → **Settings** → **Custom Domain**
2. 点击 **Add Custom Domain**
3. 输入域名（如 `api.yourdomain.com`）
4. 按照提示添加 DNS 记录（A 或 CNAME）

---

## Phase 5: 功能测试

### 5.1 基础功能测试

访问您的前端 URL：`https://smartarchitect-xxx.vercel.app`

#### ✅ Canvas 交互测试

1. **添加节点**
   - 从左侧工具栏拖拽节点到画布
   - 预期：节点成功添加并显示

2. **连接节点**
   - 从一个节点拖拽到另一个节点创建连线
   - 预期：连线成功创建

3. **编辑节点**
   - 双击节点或点击选中后在右侧编辑
   - 修改节点标签
   - 预期：标签实时更新

4. **Mermaid 代码同步**
   - 点击右上角 **Code Editor** 按钮
   - 观察 Mermaid 代码
   - 修改代码，点击 **Apply**
   - 预期：Canvas 自动更新

#### ✅ AI 功能测试

**前置条件**：确保已配置至少一个 AI API Key（在 Phase 2.2 中配置）

1. **Vision 分析**
   - 点击工具栏 **AI Vision** 按钮
   - 上传一张架构图（PNG/JPG）
   - 选择 AI Provider（如 Gemini）
   - 点击 **Analyze**
   - 预期：3-8 秒后生成架构图
   - **如果失败**：检查 API Key 是否正确配置

2. **Chat Generator**
   - 点击工具栏 **Chat Generator** 按钮
   - 输入自然语言描述（如："生成一个用户登录流程图"）
   - 选择模板或自定义
   - 点击 **Generate**
   - 预期：5-15 秒后生成流程图
   - **冷启动提示**：首次使用可能需要 30-60 秒唤醒后端服务

3. **Excalidraw 生成**
   - 点击工具栏 **Excalidraw** 按钮
   - 输入场景描述（如："设计一个移动应用界面"）
   - 点击 **Generate**
   - 预期：8-20 秒后生成手绘风格图
   - **注意**：如果 AI 生成失败，会自动使用 Mock 数据作为后备

#### ✅ 导出功能测试

1. **PowerPoint 导出**
   - 创建至少 3 个节点
   - 点击工具栏 **Export** → **PowerPoint**
   - 预期：下载 `.pptx` 文件（4 页）
   - 用 PowerPoint/WPS/LibreOffice 打开验证

2. **Slidev 导出**
   - 点击 **Export** → **Slidev**
   - 预期：下载 `.md` 文件
   - 用文本编辑器打开查看 Markdown 格式

3. **演讲稿生成**
   - 点击 **Export** → **Speech Script**
   - 选择时长（30 秒 / 2 分钟 / 5 分钟）
   - 预期：下载 `.json` 文件，包含演讲稿内容

### 5.2 性能测试

#### 冷启动测试（重要）

1. **触发冷启动**
   - 等待 15 分钟不访问网站（Render 服务休眠）
   - 或在 Render Dashboard 手动重启服务

2. **测量启动时间**
   - 清除浏览器缓存
   - 访问前端 URL
   - 打开开发者工具 Network 标签
   - 尝试调用任何 API（如添加节点）
   - **预期响应时间**：
     - 冷启动：30-60 秒（首次请求）
     - 后续请求：< 3 秒

3. **优化建议**
   - 在前端添加"服务唤醒中"的友好提示
   - 使用 UptimeRobot（免费）每 14 分钟 ping 一次后端保持活跃

#### 并发测试

1. **多标签页测试**
   - 打开 3-5 个浏览器标签页同时访问
   - 预期：正常响应（512MB RAM 足够）

2. **大图测试**
   - 添加 20+ 个节点和 30+ 条边
   - 观察渲染性能
   - 预期：略有延迟但可用

### 5.3 已知不可用功能

#### ❌ RAG 文档上传

**原因**：`requirements.txt` 中 ChromaDB 依赖被注释（避免 Windows 构建问题）

**影响**：
- 无法上传 PDF/Markdown/DOCX 文档
- 无法使用语义搜索功能

**解决方案**：
- 方案 1：在前端隐藏文档上传按钮（推荐）
- 方案 2：迁移到 Hugging Face Spaces 启用 ChromaDB（见备选方案）

**验证方式**：
- 访问 `/api/rag/upload` 端点
- 预期：返回 500 错误（ChromaDB 未安装）

### 5.4 功能测试清单

| 功能模块 | 测试项 | 预期结果 | 状态 |
|---------|--------|---------|-----|
| **基础功能** | 页面加载 | < 3 秒 | ☐ |
| | 添加节点 | 实时响应 | ☐ |
| | 连接节点 | 实时响应 | ☐ |
| | Mermaid 同步 | 双向同步正常 | ☐ |
| **AI 功能** | Vision 分析 | 3-8 秒生成 | ☐ |
| | Chat Generator | 5-15 秒生成 | ☐ |
| | Excalidraw | 8-20 秒生成 | ☐ |
| **导出功能** | PPT 导出 | 成功下载 | ☐ |
| | Slidev 导出 | 成功下载 | ☐ |
| | 脚本生成 | 成功下载 | ☐ |
| **性能** | 冷启动时间 | 30-60 秒 | ☐ |
| | 热启动时间 | < 3 秒 | ☐ |
| **已知限制** | RAG 文档上传 | ⚠️ 不可用 | ☐ |

---

## 常见问题

### Q1: 后端部署失败，显示 "Build failed"

**可能原因**：
1. Python 版本不匹配
2. 依赖安装失败
3. 代码语法错误

**解决方案**：
1. 检查 Render Logs 标签页的详细错误信息
2. 确认环境变量 `PYTHON_VERSION=3.12.0`
3. 检查 `requirements.txt` 文件格式是否正确
4. 在本地运行 `pip install -r requirements.txt` 测试依赖

### Q2: 前端可以访问，但 API 调用返回 CORS 错误

**错误信息**：
```
Access to fetch at 'https://...onrender.com/api/...' from origin 'https://...vercel.app'
has been blocked by CORS policy
```

**解决方案**：
1. 确认后端 `CORS_ORIGINS` 环境变量包含前端完整 URL
2. 确认没有多余的空格或换行符
3. 等待 1-2 分钟让配置生效
4. 清除浏览器缓存后重试
5. 检查后端日志确认 CORS 配置已加载

### Q3: 首次访问非常慢（超过 60 秒）

**原因**：Render 免费层冷启动限制

**解决方案**：
1. **短期**：在前端添加加载提示和重试逻辑
2. **长期**：使用 UptimeRobot 定期 ping 后端
   - 注册：https://uptimerobot.com
   - 添加监控：HTTP(s) 类型
   - URL：`https://your-backend.onrender.com/api/health`
   - 监控间隔：14 分钟
3. **付费方案**：升级到 Render Starter Plan ($7/月) 避免休眠

### Q4: AI 功能返回 "API key not found" 错误

**解决方案**：
1. 确认在 Render Dashboard → Environment 中已配置对应的 API Key
2. 确认 API Key 设置为 **Secret** 类型
3. 确认 API Key 格式正确：
   - Gemini: 无固定前缀
   - OpenAI: `sk-...`
   - Anthropic: `sk-ant-...`
   - SiliconFlow: `sk-...`
4. 保存后手动重启服务（Render Dashboard → Manual Deploy → Deploy latest commit）

### Q5: Vercel 部署成功但显示 "Application error"

**可能原因**：
1. `BACKEND_ORIGIN` 环境变量配置错误
2. 前端构建失败

**解决方案**：
1. 检查 Vercel Dashboard → Project → Deployments → 最新部署 → Build Logs
2. 确认 `BACKEND_ORIGIN` 变量值是完整的 HTTPS URL（不要以 `/` 结尾）
3. 确认 `next.config.js` 中的 rewrites 配置正确
4. 在 Vercel 中触发 Redeploy

### Q6: Canvas 会话数据丢失

**原因**：Render 免费层服务重启后内存数据清空

**影响范围**：
- Canvas 会话（TTL 60 分钟，影响有限）
- 导出的临时文件

**解决方案**：
1. **接受现状**：大部分用户会话不会超过 60 分钟，影响可控
2. **迁移到 HF Spaces**：支持持久化存储（见备选方案）
3. **集成云存储**：使用 AWS S3 / Cloudflare R2 免费层

### Q7: 如何查看后端日志？

**实时日志**：
1. Render Dashboard → 选择服务 → **Logs** 标签页
2. 点击右上角 **Live** 切换到实时模式

**历史日志**：
- Render 免费层保留最近 7 天日志
- 可以按关键词搜索

### Q8: 部署后如何更新代码？

**自动部署**（推荐）：
1. 本地修改代码
2. 提交到 GitHub：
   ```bash
   git add .
   git commit -m "feat: add new feature"
   git push origin dev20260129
   ```
3. Render 和 Vercel 会自动检测并重新部署（约 3-5 分钟）

**手动部署**：
- Render: Dashboard → Manual Deploy → Deploy latest commit
- Vercel: Deployments → ... → Redeploy

---

## 性能优化建议

### 1. 避免冷启动

#### 方案 A: UptimeRobot 定期 Ping（推荐）

**优势**：完全免费，简单易用

**步骤**：
1. 注册 UptimeRobot：https://uptimerobot.com
2. 添加新监控：
   - Monitor Type: `HTTP(s)`
   - URL: `https://your-backend.onrender.com/api/health`
   - Monitoring Interval: `Every 14 minutes`（保持在 15 分钟内）
   - Alert Contacts: 可选

#### 方案 B: GitHub Actions 定时任务

**优势**：完全控制，可自定义逻辑

**步骤**：
创建 `.github/workflows/keep-alive.yml`：

```yaml
name: Keep Backend Alive

on:
  schedule:
    - cron: '*/14 * * * *'  # 每 14 分钟运行一次

jobs:
  ping:
    runs-on: ubuntu-latest
    steps:
      - name: Ping backend
        run: curl -f https://your-backend.onrender.com/api/health || exit 0
```

### 2. 前端加载优化

#### 添加重试逻辑

创建 `frontend/lib/api-client.ts`：

```typescript
export async function fetchWithRetry(
  url: string,
  options: RequestInit = {},
  maxRetries: number = 3
): Promise<Response> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetch(url, options);
      if (response.ok) return response;

      // 非 5xx 错误直接返回
      if (response.status < 500) return response;

      // 5xx 错误重试
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, 2000 * (i + 1)));
      }
    } catch (error) {
      // 网络错误重试
      if (i === maxRetries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 2000 * (i + 1)));
    }
  }
  throw new Error('Max retries reached');
}
```

#### 添加冷启动提示

在 API 调用前显示加载提示：

```typescript
"后端服务正在唤醒，首次访问可能需要 30-60 秒，请稍候..."
```

### 3. 缓存优化

#### Vercel 静态资源缓存

在 `vercel.json` 中添加：

```json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        {
          "key": "Cache-Control",
          "value": "public, max-age=31536000, immutable"
        }
      ]
    }
  ]
}
```

#### 后端响应缓存

在高频 API（如 `/api/health`）中添加缓存头：

```python
@router.get("/health")
async def health_check(response: Response):
    response.headers["Cache-Control"] = "public, max-age=60"
    return {"status": "healthy", ...}
```

### 4. 监控和分析

#### Vercel Analytics（免费）

1. Vercel Dashboard → Project → Analytics
2. 点击 **Enable** 启用
3. 可查看：页面访问量、性能指标、地理分布

#### Render 监控

- Dashboard → Service → Metrics
- 可查看：CPU 使用率、内存使用率、请求数

---

## 备选方案

### 方案二：Vercel + Hugging Face Spaces

**适用场景**：需要持久化存储、启用 RAG 功能

**优势**：
- ✅ 完全免费，无休眠
- ✅ 16GB RAM，2 vCPU
- ✅ 支持持久化存储
- ✅ 适合 AI 应用展示

**劣势**：
- ⚠️ 需要创建 Dockerfile
- ⚠️ 社区资源，可能排队启动

**实施步骤**：

#### 1. 创建 Dockerfile

`backend/Dockerfile`：

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 复制并修改依赖文件
COPY requirements.txt .
RUN sed -i 's/# chromadb/chromadb/g' requirements.txt && \
    sed -i 's/# sentence-transformers/sentence-transformers/g' requirements.txt && \
    sed -i 's/# pypdf2/pypdf2/g' requirements.txt && \
    sed -i 's/# python-docx/python-docx/g' requirements.txt && \
    sed -i 's/# markdown/markdown/g' requirements.txt

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data/chromadb /app/data/canvas_sessions /app/data/scripts

# 暴露端口（HF Spaces 使用 7860）
EXPOSE 7860

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
```

#### 2. 创建 HF Spaces README

`backend/README.md`（注意：这是 HF Spaces 的配置文件）：

```yaml
---
title: SmartArchitect AI Backend
emoji: 🏗️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 7860
---

# SmartArchitect AI Backend

AI-powered architecture design platform backend.

- **Frontend**: [Vercel](https://smartarchitect.vercel.app)
- **GitHub**: [luguochang/SmartArchitect](https://github.com/luguochang/SmartArchitect)
- **License**: MIT
```

#### 3. 部署到 HF Spaces

```bash
# 1. 创建 HF Spaces（网页操作）
# 访问 https://huggingface.co/spaces
# 点击 New Space
# Space name: smartarchitect-backend
# SDK: Docker
# Visibility: Public

# 2. 克隆 HF Spaces 仓库
git clone https://huggingface.co/spaces/YOUR_USERNAME/smartarchitect-backend
cd smartarchitect-backend

# 3. 复制后端代码
cp -r /path/to/SmartArchitect/backend/* .

# 4. 提交并推送
git add .
git commit -m "Initial deployment"
git push
```

#### 4. 配置 Secrets

HF Spaces Settings → Repository secrets：
- `SILICONFLOW_API_KEY`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `CORS_ORIGINS`

#### 5. 更新 Vercel 前端

Vercel Environment Variables：
```
BACKEND_ORIGIN=https://YOUR_USERNAME-smartarchitect-backend.hf.space
```

**详细教程**：见 Hugging Face Spaces 官方文档
- https://huggingface.co/docs/hub/spaces-sdks-docker

---

## 总结

### ✅ 完成清单

- [x] 准备代码（移除硬编码 API Key）
- [x] 部署后端到 Render
- [x] 部署前端到 Vercel
- [x] 配置 CORS 和环境变量
- [x] 功能测试
- [x] 创建部署文档

### 🎉 成果

您的 SmartArchitect AI 现在已经：

1. **可在线访问**：`https://smartarchitect-xxx.vercel.app`
2. **完全免费**：无需服务器费用
3. **自动更新**：推送代码到 GitHub 自动部署
4. **全球加速**：Vercel CDN + Render 全球节点

### 📊 关键 URL

| 类型 | URL | 说明 |
|------|-----|------|
| **前端** | `https://smartarchitect-xxx.vercel.app` | 用户访问地址 |
| **后端** | `https://smartarchitect-backend.onrender.com` | API 服务地址 |
| **API 文档** | `https://smartarchitect-backend.onrender.com/docs` | Swagger UI |
| **GitHub** | `https://github.com/luguochang/SmartArchitect` | 源代码仓库 |

### 🔗 分享给用户

将前端 URL 分享给用户：

```markdown
🎉 SmartArchitect AI 在线体验：https://smartarchitect-xxx.vercel.app

特点：
- 🚀 无需安装，打开即用
- 🎨 可视化架构设计
- 🤖 AI 智能生成
- 📥 多格式导出

注意：首次访问可能需要 30-60 秒加载（服务唤醒）
```

### 📚 下一步

1. **监控部署状态**：定期检查 Render 和 Vercel Dashboard
2. **收集用户反馈**：观察实际使用情况
3. **优化性能**：根据 [性能优化建议](#性能优化建议) 章节实施
4. **考虑升级**：如需要更好的性能，可考虑：
   - Render Starter Plan ($7/月) - 无休眠
   - Vercel Pro Plan ($20/月) - 更高带宽
   - 迁移到 HF Spaces - 持久化存储

---

**部署文档版本**: v1.0
**最后更新**: 2026-02-10
**维护者**: SmartArchitect AI Team
**反馈**: https://github.com/luguochang/SmartArchitect/issues
