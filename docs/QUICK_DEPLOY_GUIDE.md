# SmartArchitect AI 快速部署指南

> **重要**: 这是简化版部署指南，只需 15-20 分钟即可完成！
> 完整文档见 `DEPLOYMENT_GUIDE.md`

---

## ✅ 准备工作（已完成）

- [x] 代码已更新并推送到 GitHub
- [x] Custom API Key 已配置为默认值
- [x] API Provider: Claude Sonnet 4.5 (via linkflow.run)
- [x] 余额限制保护已启用

---

## 📋 部署清单

### 第一步：部署后端到 Render（10 分钟）

#### 1.1 创建 Render 账号并登录

**操作步骤**：

1. 打开浏览器访问：https://render.com
2. 点击右上角 **Sign Up** 或 **Get Started**
3. 选择 **Sign up with GitHub**（推荐）
4. 授权 Render 访问您的 GitHub 账号
5. 登录成功后进入 Dashboard

#### 1.2 创建 Web Service

**操作步骤**：

1. 在 Render Dashboard 点击右上角 **New +** 按钮
2. 选择 **Web Service**
3. 在页面中找到 **Public Git repository** 输入框
4. 粘贴仓库地址：`https://github.com/luguochang/SmartArchitect`
5. 点击 **Connect**

#### 1.3 配置服务参数

在配置页面填写以下信息：

| 配置项 | 填写内容 | 说明 |
|--------|---------|------|
| **Name** | `smartarchitect-backend` | 服务名称（可自定义） |
| **Region** | `Singapore` 或 `Oregon` | 选择离您最近的区域 |
| **Branch** | `dev20260129` | 部署分支 |
| **Root Directory** | `backend` | ⚠️ 必填 |
| **Runtime** | `Python 3` | 自动检测 |
| **Build Command** | `pip install -r requirements.txt` | 自动检测 |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | 自动检测 |
| **Instance Type** | **Free** | 选择免费计划 |

#### 1.4 配置环境变量（关键步骤）

向下滚动到 **Environment Variables** 部分，点击 **Add Environment Variable**。

**必需配置**（按顺序添加）：

1. **PYTHON_VERSION**
   - Key: `PYTHON_VERSION`
   - Value: `3.12.0`

2. **ENVIRONMENT**
   - Key: `ENVIRONMENT`
   - Value: `production`

3. **LOG_LEVEL**
   - Key: `LOG_LEVEL`
   - Value: `INFO`

4. **CORS_ORIGINS**（稍后更新）
   - Key: `CORS_ORIGINS`
   - Value: `http://localhost:3000`
   - 注意：部署前端后需要更新此值

5. **CUSTOM_API_KEY**（已配置默认值）
   - Key: `CUSTOM_API_KEY`
   - Value: `sk-7Vm4JJgG9J7ghGWdtxH4vOqyVgpMcPs9zgeBLj9RqHhCswlh`
   - ⚠️ 点击右侧 **Secret** 切换按钮（建议）

6. **CUSTOM_BASE_URL**
   - Key: `CUSTOM_BASE_URL`
   - Value: `https://www.linkflow.run`

7. **CUSTOM_MODEL_NAME**
   - Key: `CUSTOM_MODEL_NAME`
   - Value: `claude-sonnet-4-5-20250929`

**配置完成效果**：

```
✓ PYTHON_VERSION = 3.12.0
✓ ENVIRONMENT = production
✓ LOG_LEVEL = INFO
✓ CORS_ORIGINS = http://localhost:3000
✓ CUSTOM_API_KEY = sk-7Vm4... (Secret)
✓ CUSTOM_BASE_URL = https://www.linkflow.run
✓ CUSTOM_MODEL_NAME = claude-sonnet-4-5-20250929
```

#### 1.5 开始部署

1. 滚动到页面底部
2. 点击蓝色按钮 **Create Web Service**
3. 等待部署（约 3-5 分钟）

#### 1.6 验证后端部署

**等待部署成功**：

观察页面顶部的状态：
- `Building...` → `Deploying...` → `Live` ✅

**获取后端 URL**：

部署成功后，页面顶部会显示 URL，格式类似：
```
https://smartarchitect-backend.onrender.com
```

**📋 复制并保存此 URL**（稍后配置前端需要）

**测试后端**：

1. 点击后端 URL 右侧的 **Open** 按钮（或直接访问）
2. 在浏览器中访问：`https://your-backend-url.onrender.com/docs`
3. 应该看到 Swagger UI 文档页面 ✅
4. 访问健康检查：`https://your-backend-url.onrender.com/api/health`
5. 应该返回 JSON：
   ```json
   {
     "status": "healthy",
     "timestamp": "...",
     "version": "0.5.0"
   }
   ```

**如果出现错误**，点击左侧菜单 **Logs** 查看详细日志。

---

### 第二步：部署前端到 Vercel（5 分钟）

#### 2.1 创建 Vercel 账号并登录

**操作步骤**：

1. 打开浏览器访问：https://vercel.com
2. 点击右上角 **Sign Up**
3. 选择 **Continue with GitHub**
4. 授权 Vercel 访问您的 GitHub 账号
5. 登录成功后进入 Dashboard

#### 2.2 导入项目

**操作步骤**：

1. 在 Vercel Dashboard 点击 **Add New...** → **Project**
2. 在 **Import Git Repository** 部分找到 `luguochang/SmartArchitect`
   - 如果没有看到，点击 **Adjust GitHub App Permissions** 授权
3. 点击仓库右侧的 **Import** 按钮

#### 2.3 配置项目

在 **Configure Project** 页面填写：

| 配置项 | 填写内容 | 说明 |
|--------|---------|------|
| **Project Name** | `smartarchitect` | 项目名称（可自定义） |
| **Framework Preset** | `Next.js` | 自动检测 |
| **Root Directory** | `frontend` | ⚠️ 点击 Edit 修改 |
| **Build Command** | `npm run build` | 自动检测 |
| **Output Directory** | `.next` | 自动检测 |
| **Install Command** | `npm install` | 自动检测 |

**配置 Root Directory**：
1. 点击 **Root Directory** 右侧的 **Edit** 按钮
2. 选择 `frontend` 文件夹
3. 点击 **Continue**

#### 2.4 配置环境变量

展开 **Environment Variables** 部分：

**添加环境变量**：

1. **Name**: `BACKEND_ORIGIN`
2. **Value**: `https://your-backend-url.onrender.com`
   - ⚠️ 替换为您在步骤 1.6 中获取的后端 URL
   - ⚠️ 不要以 `/` 结尾
3. **Environment**: 勾选所有选项（Production, Preview, Development）

**示例**：
```
Name: BACKEND_ORIGIN
Value: https://smartarchitect-backend.onrender.com
```

#### 2.5 开始部署

1. 点击页面底部的 **Deploy** 按钮
2. 等待部署（约 2-3 分钟）

#### 2.6 验证前端部署

**等待部署成功**：

观察部署进度：
- `Building...` → `Deploying...` → 🎉 祝贺页面

**获取前端 URL**：

部署成功后会显示祝贺页面，URL 格式类似：
```
https://smartarchitect-xxx.vercel.app
```

**📋 复制并保存此 URL**（稍后配置 CORS 需要）

**测试前端**：

1. 点击 **Visit** 按钮访问网站
2. 应该看到 SmartArchitect AI 主界面 ✅
3. 按 F12 打开开发者工具（Console 标签页）
4. **预期**：可能有 CORS 错误（下一步修复）

---

### 第三步：配置 CORS（5 分钟）

#### 3.1 更新后端 CORS 配置

**操作步骤**：

1. 返回 Render Dashboard：https://dashboard.render.com
2. 点击进入 `smartarchitect-backend` 服务
3. 点击左侧菜单 **Environment** 标签页
4. 找到 `CORS_ORIGINS` 变量，点击右侧 **Edit** 按钮
5. 更新 Value 为：
   ```
   https://your-vercel-url.vercel.app,http://localhost:3000
   ```
   - ⚠️ 替换 `your-vercel-url.vercel.app` 为您的实际 Vercel URL
   - 多个域名用逗号分隔，**不要有空格**

6. 点击 **Save Changes**
7. 等待服务自动重启（约 30 秒）

**示例**：
```
CORS_ORIGINS = https://smartarchitect-abc123.vercel.app,http://localhost:3000
```

#### 3.2 验证 CORS 配置

**操作步骤**：

1. 清除浏览器缓存：
   - Windows: `Ctrl + Shift + Delete`
   - Mac: `Cmd + Shift + Delete`
   - 勾选"缓存"和"Cookie"

2. 重新访问前端 URL：`https://your-vercel-url.vercel.app`

3. 按 F12 打开开发者工具 → Console 标签页

4. 尝试添加一个节点到 Canvas

5. **预期结果**：
   - ✅ 无 CORS 错误
   - ✅ 节点成功添加

**如果仍有错误**：
- 等待 1-2 分钟让配置生效
- 确认 CORS_ORIGINS 格式正确（无空格）
- 检查后端日志：Render Dashboard → Logs

---

### 第四步：功能测试（5 分钟）

#### 4.1 基础功能测试

访问您的前端 URL，测试以下功能：

**✅ Canvas 交互**：
1. 从左侧拖拽节点到画布
2. 连接两个节点
3. 双击节点编辑标签
4. 观察右侧代码编辑器的 Mermaid 代码

**✅ AI 功能测试**：

1. **Chat Generator**（推荐测试）：
   - 点击工具栏 **Chat Generator** 按钮
   - 输入："生成一个用户登录流程图"
   - 选择 Provider: **custom**
   - 点击 **Generate**
   - ⚠️ **首次访问**: 如果后端休眠，需要等待 30-60 秒唤醒
   - 预期：5-15 秒后生成流程图

2. **Vision 分析**：
   - 点击工具栏 **AI Vision** 按钮
   - 上传一张架构图
   - 选择 Provider: **custom**
   - 点击 **Analyze**
   - 预期：3-8 秒后生成架构图

**✅ 导出功能测试**：

1. **PowerPoint 导出**：
   - 创建 3-5 个节点
   - 点击 **Export** → **PowerPoint**
   - 预期：下载 `.pptx` 文件

2. **Slidev 导出**：
   - 点击 **Export** → **Slidev**
   - 预期：下载 `.md` 文件

#### 4.2 功能测试清单

| 功能 | 测试项 | 状态 |
|------|--------|-----|
| **Canvas** | 添加节点 | ☐ |
| | 连接节点 | ☐ |
| | 编辑标签 | ☐ |
| | Mermaid 同步 | ☐ |
| **AI** | Chat Generator | ☐ |
| | Vision 分析 | ☐ |
| **导出** | PPT 导出 | ☐ |
| | Slidev 导出 | ☐ |

---

## 🎉 部署完成！

### 📊 部署结果

**前端地址**：`https://your-vercel-url.vercel.app`

**后端地址**：`https://your-backend-url.onrender.com`

**API 文档**：`https://your-backend-url.onrender.com/docs`

**AI Provider**：Custom (Claude Sonnet 4.5 via linkflow.run)

### 📝 部署总结

- ✅ 后端部署到 Render（免费）
- ✅ 前端部署到 Vercel（免费）
- ✅ CORS 配置完成
- ✅ Custom API Key 已配置
- ✅ 所有功能可用（除 RAG）

### ⚠️ 已知限制

1. **冷启动延迟**：后端闲置 15 分钟后休眠，首次访问需 30-60 秒
2. **RAG 功能不可用**：文档上传功能禁用（依赖未安装）
3. **内存限制**：512MB RAM（日常使用足够）

### 🔧 后续优化（可选）

#### 避免冷启动

使用 UptimeRobot 定期 ping 后端：

1. 注册：https://uptimerobot.com
2. 添加监控：
   - Type: `HTTP(s)`
   - URL: `https://your-backend-url.onrender.com/api/health`
   - Interval: `Every 14 minutes`

#### 自定义域名

**Vercel**：
- Dashboard → Project → Settings → Domains
- 添加自定义域名（如 `smartarchitect.yourdomain.com`）

**Render**：
- Dashboard → Service → Settings → Custom Domain
- 添加自定义域名（如 `api.yourdomain.com`）

---

## 🆘 遇到问题？

### 常见问题

**Q: 后端构建失败**
- 检查 Render Logs 查看详细错误
- 确认 `PYTHON_VERSION=3.12.0`

**Q: CORS 错误**
- 确认 `CORS_ORIGINS` 包含前端完整 URL
- 等待 1-2 分钟让配置生效
- 清除浏览器缓存

**Q: 首次访问很慢**
- 正常现象（冷启动），等待 30-60 秒
- 后续访问会很快（< 3 秒）

**Q: AI 功能报错**
- 检查 Custom API Key 是否配置正确
- 查看后端日志：Render Dashboard → Logs

### 📚 完整文档

详细说明请查看：`docs/DEPLOYMENT_GUIDE.md`

### 📞 获取帮助

- GitHub Issues: https://github.com/luguochang/SmartArchitect/issues
- 完整部署文档: `docs/DEPLOYMENT_GUIDE.md`

---

**部署指南版本**: v1.1
**最后更新**: 2026-02-10
**配置**: Vercel + Render + Custom AI Provider
