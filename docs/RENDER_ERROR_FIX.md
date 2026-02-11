# Render 部署错误修复指南

## 🚨 错误信息

```
ERROR: Could not open requirements file: [Errno 2] No such file or directory: 'requirements.txt'
```

## 🔍 问题原因

**Root Directory 未设置或设置错误**，导致 Render 在项目根目录查找 `requirements.txt`，但实际文件在 `backend/requirements.txt`。

---

## ✅ 解决方案一：修改现有服务配置（推荐）

### 步骤 1：进入服务设置

1. 在 Render Dashboard 找到 `smartarchitect-backend` 服务
2. 点击进入服务详情页
3. 点击左侧菜单栏的 **Settings** 标签

### 步骤 2：修改 Root Directory

1. 在 Settings 页面向下滚动，找到 **Build & Deploy** 部分
2. 找到 **Root Directory** 配置项
3. 点击右侧的 **Edit** 或直接在输入框中修改
4. 填写：`backend`
5. 点击 **Save Changes** 按钮

### 步骤 3：手动触发重新部署

1. 部署会自动触发，或者手动触发：
2. 返回服务主页（点击左侧 **Dashboard** 或服务名称）
3. 点击右上角 **Manual Deploy** 下拉按钮
4. 选择 **Deploy latest commit**
5. 等待构建完成（约 3-5 分钟）

### 步骤 4：验证部署

观察日志输出，应该看到：

```
==> Cloning from https://github.com/luguochang/SmartArchitect
==> Checking out commit ... in branch dev20260129
==> Running build command 'pip install -r requirements.txt'...
Collecting fastapi==0.115.6
Collecting uvicorn[standard]==0.34.0
...
==> Build succeeded 🎉
```

---

## ✅ 解决方案二：删除并重新创建服务

### 适用场景

如果方法一找不到 Root Directory 设置，或修改后仍然失败。

### 步骤 1：删除现有服务

1. 在服务页面，点击左侧 **Settings** 标签
2. 滚动到页面最底部
3. 找到 **Danger Zone** 部分
4. 点击红色按钮 **Delete Web Service**
5. 在确认对话框中输入服务名称（如 `smartarchitect-backend`）
6. 点击 **Delete** 确认

### 步骤 2：重新创建服务（完整步骤）

#### 2.1 开始创建

1. 返回 Render Dashboard 主页
2. 点击右上角 **New +** 按钮
3. 选择 **Web Service**

#### 2.2 连接 Git 仓库

**选项 A：使用 Public Repository**（推荐）

1. 向下滚动找到 **Public Git repository** 输入框
2. 粘贴仓库地址：
   ```
   https://github.com/luguochang/SmartArchitect
   ```
3. 点击 **Connect** 按钮

**选项 B：从已连接的仓库选择**

1. 如果之前已授权，可以直接在列表中找到 `luguochang/SmartArchitect`
2. 点击右侧的 **Connect** 按钮

#### 2.3 配置服务参数（关键步骤）

**⚠️ 重要：请严格按照以下配置填写**

| 配置项 | 填写内容 | 说明 |
|--------|---------|------|
| **Name** | `smartarchitect-backend` | 服务名称 |
| **Region** | `Singapore` 或 `Oregon` | 选择区域 |
| **Branch** | `dev20260129` | ⚠️ 必须选择此分支 |
| **Root Directory** | `backend` | ⚠️⚠️⚠️ **最关键的配置** |
| **Runtime** | `Python 3` | 自动检测 |
| **Build Command** | `pip install -r requirements.txt` | 自动检测 |
| **Start Command** | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` | 自动检测 |
| **Instance Type** | **Free** | 选择免费计划 |

**如何设置 Root Directory**：

1. 找到 **Root Directory** 配置项
2. **注意**：默认可能是空的或显示 `.`
3. 在输入框中清除默认值
4. 输入：`backend`（全小写，无斜杠）
5. 确认输入正确

#### 2.4 配置环境变量

向下滚动到 **Environment Variables** 部分，点击 **Add Environment Variable** 逐个添加：

**必需的环境变量**（按顺序添加）：

1. **PYTHON_VERSION**
   ```
   Key: PYTHON_VERSION
   Value: 3.12.0
   ```

2. **ENVIRONMENT**
   ```
   Key: ENVIRONMENT
   Value: production
   ```

3. **LOG_LEVEL**
   ```
   Key: LOG_LEVEL
   Value: INFO
   ```

4. **CORS_ORIGINS**（稍后更新）
   ```
   Key: CORS_ORIGINS
   Value: http://localhost:3000
   ```

5. **CUSTOM_API_KEY**（⚠️ 点击 Secret 开关）
   ```
   Key: CUSTOM_API_KEY
   Value: sk-7Vm4JJgG9J7ghGWdtxH4vOqyVgpMcPs9zgeBLj9RqHhCswlh
   Type: Secret（点击右侧开关）
   ```

6. **CUSTOM_BASE_URL**
   ```
   Key: CUSTOM_BASE_URL
   Value: https://www.linkflow.run
   ```

7. **CUSTOM_MODEL_NAME**
   ```
   Key: CUSTOM_MODEL_NAME
   Value: claude-sonnet-4-5-20250929
   ```

**配置完成后确认**：
```
✓ 7 个环境变量已添加
✓ CUSTOM_API_KEY 设置为 Secret 类型
```

#### 2.5 创建服务

1. 检查所有配置项是否正确
2. **特别确认**：Root Directory = `backend`
3. 滚动到页面底部
4. 点击蓝色按钮 **Create Web Service**

#### 2.6 观察部署日志

部署开始后，自动跳转到日志页面。观察输出：

**✅ 正确的日志输出**：

```
==> Cloning from https://github.com/luguochang/SmartArchitect
==> Checking out commit ... in branch dev20260129
==> Installing Python version 3.12.0...
==> Using Python version 3.12.0
==> Running build command 'pip install -r requirements.txt'...
Collecting fastapi==0.115.6
  Downloading fastapi-0.115.6-py3-none-any.whl
Collecting uvicorn[standard]==0.34.0
  Downloading uvicorn-0.34.0-py3-none-any.whl
...
Successfully installed fastapi-0.115.6 uvicorn-0.34.0 ...
==> Build succeeded 🎉
==> Deploying...
==> Starting service...
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
==> Your service is live 🎉
```

**❌ 错误的日志输出**：

```
==> Installing Python version 3.13.4...  ← 版本错误
==> Using Python version 3.13.4 (default)
ERROR: Could not open requirements file  ← Root Directory 错误
```

如果看到错误日志，说明配置未生效，请返回 Settings 重新检查。

#### 2.7 获取后端 URL

部署成功后：

1. 页面顶部会显示绿色的 **Live** 状态
2. URL 格式：`https://smartarchitect-backend.onrender.com`
3. **复制并保存此 URL**（部署前端时需要）

#### 2.8 验证部署

**测试健康检查**：

1. 访问：`https://your-backend.onrender.com/api/health`
2. 预期响应：
   ```json
   {
     "status": "healthy",
     "timestamp": "2026-02-10T...",
     "version": "0.5.0"
   }
   ```

**测试 API 文档**：

1. 访问：`https://your-backend.onrender.com/docs`
2. 应显示 Swagger UI 界面

---

## 📋 配置检查清单

在点击 Create Web Service 之前，请确认：

- [ ] **Branch** = `dev20260129`
- [ ] **Root Directory** = `backend`（⚠️ 最关键）
- [ ] **Instance Type** = **Free**
- [ ] **环境变量已添加 7 个**
- [ ] **PYTHON_VERSION** = `3.12.0`
- [ ] **CUSTOM_API_KEY** 设置为 **Secret** 类型

---

## 🆘 如果仍然失败

### 检查项 1：确认 Root Directory

1. 进入服务 Settings
2. 查看 **Build & Deploy** 部分
3. 确认 Root Directory = `backend`

### 检查项 2：查看详细日志

1. 点击左侧 **Logs** 标签
2. 查看完整错误信息
3. 搜索关键词：`requirements.txt`

### 检查项 3：确认 GitHub 分支

1. 访问：https://github.com/luguochang/SmartArchitect/tree/dev20260129
2. 确认 `backend/requirements.txt` 文件存在
3. 确认最新提交已推送

### 检查项 4：Python 版本

如果日志显示使用 Python 3.13.4：

1. 进入 Settings → Environment Variables
2. 确认 `PYTHON_VERSION` = `3.12.0`
3. 删除并重新添加此环境变量
4. 手动触发重新部署

---

## 📞 仍然有问题？

提供以下信息以便排查：

1. **完整的错误日志**（复制 Render Logs 标签页的内容）
2. **Root Directory 截图**（Settings 页面的配置）
3. **环境变量列表截图**

---

## ✅ 部署成功后

继续执行 `docs/QUICK_DEPLOY_GUIDE.md` 的：
- **第二步**：部署前端到 Vercel
- **第三步**：配置 CORS
- **第四步**：功能测试

---

**修复指南版本**: v1.0
**最后更新**: 2026-02-10
**问题**: Root Directory 配置错误
**解决方案**: 设置 Root Directory = `backend`
