# 🚀 部署指南

完整的前后端部署教程，10 分钟部署到线上！

## 📋 目录

- [架构概览](#架构概览)
- [后端部署（Railway/Render）](#后端部署)
- [前端部署（Vercel）](#前端部署)
- [环境变量配置](#环境变量配置)
- [域名配置](#域名配置可选)
- [故障排查](#故障排查)

---

## 🏗️ 架构概览

```
前端 (Vercel)               后端 (Railway/Render)
┌─────────────┐            ┌──────────────────┐
│  Next.js 14 │  REST API  │  FastAPI + Python│
│  Port: 3000 │ ◄────────► │  Port: 8000      │
│  Static     │   HTTPS    │  Dynamic         │
└─────────────┘            └──────────────────┘
```

---

## 🚂 后端部署

### 方案 A: Railway（推荐，更简单）

#### 1. 注册 Railway

访问 [railway.app](https://railway.app)，用 GitHub 账号登录

#### 2. 创建新项目

```bash
# 点击 "New Project"
# → 选择 "Deploy from GitHub repo"
# → 选择你的仓库
# → 选择 backend 目录
```

#### 3. 配置环境变量

在 Railway Dashboard → Variables 添加：

```bash
# Python 版本
PYTHON_VERSION=3.12.0

# 端口（Railway 自动提供 $PORT 变量）
# 无需手动设置

# AI API Keys（可选，可以在前端配置）
GEMINI_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
SILICONFLOW_API_KEY=your-siliconflow-key
```

#### 4. 部署命令

Railway 会自动检测到 `railway.toml`，使用以下命令：

```bash
# 启动命令（已在 railway.toml 配置）
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

#### 5. 获取后端 URL

部署成功后，Railway 会生成一个 URL，例如：
```
https://archboard-backend-production.up.railway.app
```

**保存这个 URL，前端需要用！**

---

### 方案 B: Render（备选，免费层限制更多）

#### 1. 注册 Render

访问 [render.com](https://render.com)，用 GitHub 登录

#### 2. 创建 Web Service

```bash
# 点击 "New +" → "Web Service"
# → 选择你的 GitHub 仓库
# → Root Directory: backend
```

#### 3. 配置

```yaml
Name: archboard-backend
Environment: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Instance Type: Free
```

#### 4. 环境变量

在 Render Dashboard → Environment 添加：

```bash
PYTHON_VERSION=3.12.0
GEMINI_API_KEY=xxx
OPENAI_API_KEY=xxx
ANTHROPIC_API_KEY=xxx
```

#### 5. 获取 URL

例如：
```
https://archboard-backend.onrender.com
```

**注意**：Render 免费层会在 15 分钟无活动后休眠，首次访问需要等待 30 秒启动。

---

## 🌐 前端部署

### Vercel 部署（5 分钟搞定）

#### 1. 安装 Vercel CLI（可选）

```bash
npm install -g vercel
```

#### 2. 方式 A：通过 Vercel Dashboard

访问 [vercel.com](https://vercel.com)

```bash
# 1. 点击 "Add New" → "Project"
# 2. 选择你的 GitHub 仓库
# 3. 配置：
#    - Framework Preset: Next.js
#    - Root Directory: frontend
#    - Build Command: npm run build
#    - Output Directory: .next
```

#### 3. 配置环境变量

**重要！** 在 Vercel → Settings → Environment Variables 添加：

```bash
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
```

**替换为你的后端 URL！**

#### 4. 重新部署

```bash
# 在 Vercel Dashboard → Deployments
# 点击右上角的 "Redeploy"
```

#### 5. 方式 B：通过 CLI 部署

```bash
cd frontend
vercel

# 按提示操作：
# ? Set up and deploy "~/frontend"? Y
# ? Which scope? (选择你的账号)
# ? Link to existing project? N
# ? What's your project's name? archboard
# ? In which directory is your code located? ./
# ? Want to modify these settings? N

# 部署完成后会给你一个 URL
```

#### 6. 添加环境变量（CLI）

```bash
vercel env add NEXT_PUBLIC_API_URL

# 粘贴你的后端 URL，例如：
# https://archboard-backend-production.up.railway.app
```

#### 7. 重新部署使环境变量生效

```bash
vercel --prod
```

---

## 🔑 环境变量配置

### 前端环境变量

```bash
# 必须以 NEXT_PUBLIC_ 开头才能在浏览器中访问
NEXT_PUBLIC_API_URL=https://your-backend-url.com
```

### 后端环境变量

```bash
# Python 版本
PYTHON_VERSION=3.12.0

# AI API Keys（可选，可以在前端界面配置）
GEMINI_API_KEY=AIza...
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
SILICONFLOW_API_KEY=sk-...

# CORS（Railway/Render 会自动设置）
CORS_ORIGINS=https://your-frontend-url.vercel.app
```

---

## 🌍 域名配置（可选）

### 配置自定义域名

#### 前端（Vercel）

```bash
# 1. 在 Vercel Dashboard → Settings → Domains
# 2. 添加你的域名：archboard.yourdomain.com
# 3. 按提示在你的 DNS 服务商添加 CNAME 记录：
#    CNAME archboard -> cname.vercel-dns.com
```

#### 后端（Railway）

```bash
# 1. 在 Railway Dashboard → Settings → Domains
# 2. 点击 "Generate Domain" 或 "Custom Domain"
# 3. 添加自定义域名：api.archboard.com
# 4. 添加 DNS 记录：
#    CNAME api -> your-service.railway.app
```

---

## 🐛 故障排查

### 前端连接不上后端

**检查清单：**

1. ✅ 后端是否成功部署？
   ```bash
   # 访问后端健康检查
   curl https://your-backend-url.com/api/health

   # 应该返回：
   {"status": "healthy"}
   ```

2. ✅ 前端环境变量是否正确？
   ```bash
   # 在 Vercel Dashboard 检查
   NEXT_PUBLIC_API_URL=https://...
   ```

3. ✅ CORS 是否配置正确？
   ```python
   # backend/app/core/config.py
   CORS_ORIGINS = [
       "https://your-frontend.vercel.app",
       "http://localhost:3000",  # 开发环境
   ]
   ```

### 后端部署失败

**常见问题：**

1. **Python 版本不匹配**
   ```bash
   # 确保 runtime.txt 或环境变量设置了正确版本
   python-3.12.0
   ```

2. **依赖安装失败**
   ```bash
   # 检查 requirements.txt 是否有问题
   # 移除 ChromaDB 相关依赖（如果不需要）
   ```

3. **端口配置错误**
   ```python
   # Railway/Render 使用 $PORT 环境变量
   # main.py 应该使用：
   port = int(os.getenv("PORT", 8000))
   ```

### Vercel 构建失败

**常见原因：**

1. **Node 版本不对**
   ```json
   // package.json
   "engines": {
     "node": ">=18.0.0"
   }
   ```

2. **构建命令错误**
   ```bash
   # 确保 package.json 有：
   "scripts": {
     "build": "next build"
   }
   ```

---

## 📊 部署后测试

### 1. 测试后端

```bash
# 健康检查
curl https://your-backend-url.com/api/health

# 测试 AI 模型列表
curl https://your-backend-url.com/api/models/presets
```

### 2. 测试前端

访问 `https://your-frontend.vercel.app`

- ✅ 页面能正常加载
- ✅ 能添加节点
- ✅ 能调用 AI 生成
- ✅ 主题切换正常

---

## 🎉 部署完成！

现在你有了：
- ✅ 前端：`https://your-project.vercel.app`
- ✅ 后端：`https://your-backend.railway.app`
- ✅ CI/CD：每次 push 自动部署
- ✅ HTTPS：自动配置 SSL 证书

### 更新 README

把你的部署 URL 添加到 README：

```markdown
## 🌐 在线演示

- **前端**: https://archboard.vercel.app
- **后端 API**: https://archboard-backend.railway.app
- **API 文档**: https://archboard-backend.railway.app/docs

[![Deploy](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/archboard)
```

---

## 💰 费用说明

### 完全免费的配置

- **Vercel**:
  - ✅ 免费 100GB 带宽/月
  - ✅ 无限部署次数
  - ✅ 自动 HTTPS

- **Railway**:
  - ✅ $5 免费额度/月
  - ✅ 够用于小型项目
  - ✅ 休眠策略（30分钟无请求）

- **Render**（备选）:
  - ✅ 750 小时/月免费
  - ⚠️ 15分钟无活动会休眠
  - ⚠️ 冷启动较慢（30秒）

### 升级方案

如果项目火了，用户多了：

- **Vercel Pro**: $20/月，无限带宽
- **Railway Pro**: $20/月，更多资源
- **自建服务器**: 阿里云/腾讯云 ¥50-200/月

---

## 📞 需要帮助？

- [GitHub Issues](https://github.com/yourusername/archboard/issues)
- [Vercel 文档](https://vercel.com/docs)
- [Railway 文档](https://docs.railway.app)
- [Render 文档](https://render.com/docs)
