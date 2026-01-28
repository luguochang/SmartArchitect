# 🚀 部署配置完成清单

## ✅ 已完成的配置

### 1. 前端配置
- [x] 创建 API 配置文件 `frontend/lib/api-config.ts`
- [x] 创建环境变量示例 `frontend/.env.example`
- [x] 创建 Vercel 配置 `frontend/vercel.json`

### 2. 后端配置
- [x] 更新 `backend/app/core/config.py` 支持 PORT 环境变量
- [x] 更新 CORS 配置支持多域名
- [x] 创建 Railway 配置 `backend/railway.toml`
- [x] 创建 Render 配置 `backend/render.yaml`

### 3. CI/CD 配置
- [x] 创建 GitHub Actions CI `.github/workflows/ci.yml`
- [x] 创建后端自动部署 `.github/workflows/deploy-backend.yml`

### 4. 文档
- [x] 创建完整部署指南 `DEPLOYMENT.md`
- [x] 创建一键部署说明 `DEPLOY_BUTTONS.md`

## 📝 下一步操作

### 1. 更新前端代码使用新的 API 配置

需要替换所有硬编码的 `http://localhost:8000` 为使用 `api-config.ts`

**需要修改的文件：**
```
frontend/components/ModelPresetsManager.tsx
frontend/components/FlowchartUploader.tsx
frontend/components/AiControlPanel.tsx
frontend/components/ScriptGenerator.tsx
... 以及其他调用后端 API 的组件
```

**修改示例：**

```typescript
// 旧代码
const response = await fetch("http://localhost:8000/api/models/presets");

// 新代码
import { API_ENDPOINTS } from '@/lib/api-config';
const response = await fetch(API_ENDPOINTS.modelPresets);
```

### 2. 创建 .env.local 文件

```bash
cd frontend
cp .env.example .env.local
```

### 3. 提交代码

```bash
git add .
git commit -m "feat: add deployment configuration"
git push origin main
```

### 4. 部署后端

选择一个平台：
- **Railway**（推荐）: https://railway.app
- **Render**: https://render.com

跟随 `DEPLOYMENT.md` 的步骤。

### 5. 部署前端

访问 https://vercel.com 部署前端。

### 6. 配置环境变量

在 Vercel 设置：
```
NEXT_PUBLIC_API_URL=https://your-backend-url.railway.app
```

### 7. 更新 README.md

添加部署链接和徽章：

```markdown
## 🌐 在线演示

- **前端**: https://your-project.vercel.app
- **后端 API**: https://your-backend.railway.app
- **API 文档**: https://your-backend.railway.app/docs

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=...)
[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/...)
```

## 🎯 测试清单

部署完成后测试：

### 后端测试
```bash
# 健康检查
curl https://your-backend.railway.app/api/health

# 应该返回
{"status":"healthy"}
```

### 前端测试
- [ ] 页面能正常加载
- [ ] 能添加节点
- [ ] 能连接节点
- [ ] AI 生成功能正常
- [ ] 主题切换正常
- [ ] Excalidraw 正常

## ⚠️ 注意事项

1. **SiliconFlow API Key**
   - 配置文件中有一个硬编码的 SiliconFlow API Key
   - 建议移除或改为环境变量

2. **CORS 配置**
   - 部署后记得在后端添加前端 URL 到 CORS_ORIGINS

3. **API 调用**
   - 所有前端组件都需要更新使用新的 API 配置

## 📚 相关文档

- [完整部署指南](DEPLOYMENT.md)
- [一键部署](DEPLOY_BUTTONS.md)
- [API 配置说明](frontend/lib/api-config.ts)
