# 故障排除指南 (Troubleshooting Guide)

## 常见问题 (Common Issues)

### 1. 模块未找到错误：`Can't resolve '@/lib/utils/autoLayout'`

#### 问题描述
每次在新环境中拉取代码或切换分支后，前端启动时报错：
```
Module not found: Can't resolve '@/lib/utils/autoLayout'
Module not found: Can't resolve '@/lib/utils/imageConversion'
```

#### 根本原因
`.gitignore` 文件中的 `lib/` 规则原本是为了忽略 Python 的构建目录，但意外地也忽略了 `frontend/lib/` 目录，导致这些重要的工具文件没有被提交到代码仓库。

#### 解决方案

**已修复** (Commit: 2da4684)
- `.gitignore` 已更新，现在只忽略 Python 相关的 `lib/` 目录
- 所有 `frontend/lib/` 文件已添加到仓库

**如果你仍然遇到此问题**，请执行以下步骤：

```bash
# 1. 拉取最新代码
git pull origin dev

# 2. 确认 frontend/lib 目录存在且包含文件
ls frontend/lib/utils/

# 3. 如果文件仍然缺失，手动检出
git checkout origin/dev -- frontend/lib/

# 4. 重新安装依赖
cd frontend
npm install

# 5. 重启开发服务器
npm run dev
```

#### 预防措施

1. **提交前检查**: 在提交代码前，确保所有必要的文件都已被跟踪
   ```bash
   git status
   git ls-files frontend/lib/
   ```

2. **验证 .gitignore**: 定期检查 `.gitignore` 规则，确保不会意外忽略重要目录
   ```bash
   # 测试文件是否被忽略
   git check-ignore -v frontend/lib/utils/autoLayout.ts
   ```

3. **克隆后验证**: 在新环境克隆代码后，立即验证关键文件
   ```bash
   # 检查关键工具文件
   test -f frontend/lib/utils/autoLayout.ts && echo "✓ autoLayout.ts exists" || echo "✗ autoLayout.ts missing"
   test -f frontend/lib/utils/imageConversion.ts && echo "✓ imageConversion.ts exists" || echo "✗ imageConversion.ts missing"
   test -f frontend/lib/utils/nodeShapes.ts && echo "✓ nodeShapes.ts exists" || echo "✗ nodeShapes.ts missing"
   ```

---

### 2. 流式转换函数缺失

#### 问题描述
前端启动后，使用 Excalidraw Uploader 或 Image Conversion Modal 时报错：
```
TypeError: convertImageToExcalidrawStreaming(...) is not a function or its return value is not async iterable
```

#### 根本原因
`ExcalidrawUploader.tsx` 和 `ImageConversionModal.tsx` 导入了 `convertImageToExcalidrawStreaming` 函数，但该函数在 `lib/utils/imageConversion.ts` 中不存在。

#### 解决方案

**已修复** (Commit: 67785d0)
- 添加了 `convertImageToExcalidrawStreaming` 异步生成器函数
- 实现了 SSE (Server-Sent Events) 流式解析
- 支持实时接收和渲染 Excalidraw 元素

**函数签名**:
```typescript
async function* convertImageToExcalidrawStreaming(
  file: File,
  onProgress?: (message: string) => void
): AsyncGenerator<{
  type: "start_streaming" | "element" | "complete";
  total?: number;
  appState?: any;
  element?: ExcalidrawElement;
  message?: string;
}>
```

---

### 3. CORS 错误（端口 3001）

#### 问题描述
前端在端口 3001 运行时，调用后端 API 被 CORS 策略阻止：
```
Access to fetch at 'http://localhost:8000/api/excalidraw/generate-stream'
from origin 'http://localhost:3001' has been blocked by CORS policy
```

#### 根本原因
后端 CORS 配置 (`backend/app/core/config.py`) 只允许端口 3000，不包含 3001。

#### 解决方案

**已修复** (Commit: 67785d0)
- 更新 CORS 配置，添加 `http://localhost:3001` 和 `http://127.0.0.1:3001`

**配置位置**: `backend/app/core/config.py:17-18`
```python
CORS_ORIGINS: List[str] = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",  # 新增
    "http://127.0.0.1:3001"   # 新增
]
```

**注意**: 修改 CORS 配置后需要重启后端服务器：
```bash
# 杀掉旧进程
taskkill //F //PID <backend_pid>

# 重启后端
cd backend
venv/Scripts/python.exe -m app.main
```

---

### 2. 其他常见启动问题

#### 端口占用
**错误**: `Error: listen EADDRINUSE: address already in use :::3000`

**解决方案**:
```bash
# Windows
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:3000 | xargs kill -9
```

#### 依赖安装失败
**错误**: `npm ERR! code ERESOLVE`

**解决方案**:
```bash
# 清理并重新安装
rm -rf node_modules package-lock.json
npm install

# 或使用 --legacy-peer-deps
npm install --legacy-peer-deps
```

#### Python 虚拟环境问题
**错误**: `ModuleNotFoundError: No module named 'fastapi'`

**解决方案**:
```bash
cd backend

# 激活虚拟环境
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

---

## 开发环境设置检查清单

新环境设置时，请按顺序检查：

- [ ] Git 仓库已克隆
- [ ] Node.js (v18+) 已安装
- [ ] Python (3.12+) 已安装
- [ ] 前端依赖已安装 (`cd frontend && npm install`)
- [ ] 后端虚拟环境已创建 (`cd backend && python -m venv venv`)
- [ ] 后端依赖已安装 (`pip install -r requirements.txt`)
- [ ] 关键文件存在验证 (见上文)
- [ ] 环境变量配置 (`.env` 文件，如需要)
- [ ] 端口 3000 和 8000 未被占用

---

## 需要帮助？

如果问题仍未解决：

1. 检查 [GitHub Issues](https://github.com/your-repo/issues)
2. 查看 `CLAUDE.md` 了解项目架构
3. 查看 `README.md` 了解快速启动指南
4. 运行测试验证后端: `cd backend && pytest tests/ -v`
