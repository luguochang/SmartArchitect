# ArchBoard - One-Click Deploy

## 🚀 快速部署

### 部署前端到 Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fluguochang%2FSmartArchitect&project-name=archboard&repository-name=archboard&root-directory=frontend&env=NEXT_PUBLIC_API_URL&envDescription=Backend%20API%20URL&envLink=https%3A%2F%2Fgithub.com%2Fluguochang%2FSmartArchitect%2Fblob%2Fmain%2FDEPLOYMENT.md)

点击上面的按钮，Vercel 会：
1. Fork 你的仓库
2. 自动部署前端
3. 提示你输入后端 URL

### 部署后端到 Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/smartarchitect?referralCode=xxx)

点击上面的按钮，Railway 会：
1. 自动部署后端
2. 生成公开 URL
3. 自动配置 HTTPS

## ⚙️ 环境变量

### 前端（Vercel）

| 变量名 | 说明 | 示例 |
|-------|------|------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | `https://your-backend.railway.app` |

### 后端（Railway/Render）

| 变量名 | 是否必需 | 说明 |
|-------|---------|------|
| `GEMINI_API_KEY` | 可选 | Google Gemini API Key |
| `OPENAI_API_KEY` | 可选 | OpenAI API Key |
| `ANTHROPIC_API_KEY` | 可选 | Anthropic Claude API Key |
| `SILICONFLOW_API_KEY` | 可选 | SiliconFlow API Key |

**注意**：AI API Keys 可以在部署后通过前端界面配置，不一定要设置环境变量。

## 📝 手动部署

详细步骤请查看 [DEPLOYMENT.md](./DEPLOYMENT.md)
