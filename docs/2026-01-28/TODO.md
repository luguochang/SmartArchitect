# 待办事项 - 图片转流程图功能

## 📅 日期
2026-01-28

## ✅ 已完成

### 后端实现
- [x] Vision API endpoints实现 (`/api/vision/generate-excalidraw`, `/api/vision/generate-reactflow`)
- [x] 多Provider支持 (Gemini, OpenAI, Claude, SiliconFlow, Custom)
- [x] Claude API格式自动检测 (linkflow/anthropic)
- [x] 路径重复问题修复 (`/v1/v1` → `/v1`)
- [x] 真实图片测试通过 (131KB架构图 → 51个元素)
- [x] 单元测试编写 (`tests/test_vision_to_diagram.py`, `tests/test_real_image.py`)

### 前端实现
- [x] 工具函数库 (`frontend/lib/utils/imageConversion.ts`)
- [x] 可复用Modal组件 (`frontend/components/ImageConversionModal.tsx`)
- [x] Excalidraw集成 (`frontend/components/ExcalidrawBoard.tsx`)
- [x] React Flow集成 (`frontend/components/ArchitectCanvas.tsx`)

### 文档
- [x] FlowPilot分析文档 (`IMAGE_TO_DIAGRAM_REPLICATION_ANALYSIS.md`)
- [x] Vision模型技术说明 (`VISION_MODEL_EXPLANATION.md`)
- [x] 后端实现总结 (`IMPLEMENTATION_SUMMARY.md`)
- [x] 真实图片测试报告 (`REAL_IMAGE_TEST_REPORT.md`)
- [x] 前端集成总结 (`FRONTEND_INTEGRATION_SUMMARY.md`)

---

## 🔴 待处理（高优先级）

### 1. 环境准备
- [ ] **升级Node.js版本**
  - 当前: v16.20.0
  - 需要: v18.17.0 或更高
  - 下载地址: https://nodejs.org/en/download/
  - 验证命令: `node --version`

### 2. 前端手动测试

#### 2.1 启动服务
```bash
# 终端1: 启动后端
cd backend
venv\Scripts\activate  # Windows
python -m app.main

# 终端2: 启动前端
cd frontend
npm install  # 如果是首次运行
npm run dev
```

#### 2.2 Excalidraw测试清单
- [ ] 访问 http://localhost:3000
- [ ] 切换到Excalidraw模式（如果有模式切换）
- [ ] 点击右上角蓝色"Import from Image"按钮
- [ ] 验证Modal弹出
- [ ] 拖拽图片到上传区域
- [ ] 验证图片预览显示
- [ ] 点击"Convert with AI"按钮
- [ ] 观察进度提示：
  - "Uploading image..."
  - "AI is analyzing the diagram..."
  - "Generating Excalidraw scene..."
  - "Done!"
- [ ] 验证元素自动导入到画布
- [ ] 验证Toast通知显示元素数量
- [ ] 验证Modal自动关闭
- [ ] 测试生成的元素可编辑（移动、调整大小、修改文本）
- [ ] 刷新页面，验证场景是否保持

#### 2.3 React Flow测试清单
- [ ] 切换到React Flow模式
- [ ] 点击工具栏"Import from Image"按钮
- [ ] 上传架构图图片
- [ ] 验证转换过程
- [ ] 验证节点和边正确导入
- [ ] 验证自动fitView()居中显示
- [ ] 验证节点样式正确（根据type字段）
- [ ] 测试节点可拖拽、可选中
- [ ] 测试边的连接关系正确
- [ ] 点击"Auto Layout"按钮验证布局功能

#### 2.4 错误场景测试
- [ ] 上传非图片文件（.txt, .pdf），验证错误提示
- [ ] 上传超大图片（>10MB），验证错误提示
- [ ] 断开网络连接，验证网络错误提示
- [ ] 使用错误的API Key，验证API错误提示

#### 2.5 UI/UX测试
- [ ] 切换到Dark Mode，验证所有元素正常显示
- [ ] 调整窗口大小，验证响应式布局
- [ ] 测试键盘导航（Tab、Enter、Esc）
- [ ] 验证按钮hover效果
- [ ] 验证进度动画流畅

### 3. 修复发现的问题
记录测试中发现的问题：

**问题模板**:
```
问题描述:
复现步骤:
期望行为:
实际行为:
错误信息:
解决方案:
```

---

## 🟡 待处理（中优先级）

### 1. 补充自动化测试

#### 前端单元测试
创建 `frontend/__tests__/imageConversion.test.ts`:
```typescript
describe('imageConversion utils', () => {
  test('fileToBase64 converts File to base64', async () => {
    // TODO
  });

  test('validateImageFile rejects invalid files', () => {
    // TODO
  });

  test('formatFileSize formats bytes correctly', () => {
    // TODO
  });
});
```

创建 `frontend/__tests__/ImageConversionModal.test.tsx`:
```typescript
describe('ImageConversionModal', () => {
  test('renders when isOpen is true', () => {
    // TODO
  });

  test('calls onSuccess after conversion', async () => {
    // TODO
  });

  test('shows error on conversion failure', async () => {
    // TODO
  });
});
```

#### E2E测试
安装并配置Playwright或Cypress:
```bash
cd frontend
npm install -D @playwright/test
npx playwright install
```

创建 `frontend/e2e/image-import.spec.ts`:
```typescript
test('Excalidraw image import flow', async ({ page }) => {
  // TODO
});

test('React Flow image import flow', async ({ page }) => {
  // TODO
});
```

### 2. 性能优化

#### 前端图片压缩
```typescript
// 在 imageConversion.ts 中添加
export async function compressImage(file: File, maxSizeMB: number = 2): Promise<File> {
  // TODO: 实现图片压缩
  // 可以使用 browser-image-compression 库
}
```

#### 实现请求缓存
```typescript
// 避免重复转换相同图片
const cache = new Map<string, ExcalidrawScene | ReactFlowDiagram>();

export async function convertImageToExcalidrawWithCache(file: File) {
  const hash = await getFileHash(file);
  if (cache.has(hash)) return cache.get(hash);

  const result = await convertImageToExcalidraw(file);
  cache.set(hash, result);
  return result;
}
```

### 3. 用户体验优化

#### 添加取消按钮
在Modal中添加取消正在进行的转换：
```typescript
const abortController = new AbortController();

// 在fetch中使用
fetch(url, { signal: abortController.signal });

// 取消按钮
<button onClick={() => abortController.abort()}>Cancel</button>
```

#### 添加历史记录
```typescript
// 保存最近的转换记录
interface ConversionHistory {
  id: string;
  fileName: string;
  timestamp: number;
  result: ExcalidrawScene | ReactFlowDiagram;
}

// 从localStorage读取
const history = JSON.parse(localStorage.getItem('conversionHistory') || '[]');
```

---

## 🟢 待处理（低优先级）

### 1. 功能增强

#### 批量导入
```typescript
interface BatchImportProps {
  files: File[];
  onProgress: (current: number, total: number) => void;
  onComplete: (results: Array<ExcalidrawScene | ReactFlowDiagram>) => void;
}
```

#### 预览对比
添加一个对比视图，显示原图和生成结果：
```tsx
<div className="grid grid-cols-2 gap-4">
  <div>
    <h3>Original Image</h3>
    <img src={originalImage} />
  </div>
  <div>
    <h3>Generated Result</h3>
    <ExcalidrawPreview scene={result} />
  </div>
</div>
```

#### 自定义Prompt
允许用户编辑转换提示词：
```tsx
<textarea
  value={customPrompt}
  onChange={(e) => setCustomPrompt(e.target.value)}
  placeholder="Enter custom conversion prompt..."
/>
```

### 2. 文档完善

#### 用户使用手册
创建 `docs/USER_GUIDE.md`:
- 功能介绍
- 使用步骤（带截图）
- 常见问题解答
- 最佳实践建议

#### API文档
创建 `docs/API_REFERENCE.md`:
- Vision API endpoints详细说明
- 请求/响应格式
- 错误码说明
- 使用示例

#### 视频教程
录制演示视频：
1. 图片上传流程
2. Excalidraw导入演示
3. React Flow导入演示
4. 常见问题排查

---

## 🐛 已知问题

### 1. Node.js版本要求
**问题**: 前端需要Node.js >= v18.17.0
**当前**: v16.20.0
**解决**: 升级Node.js

### 2. 大图片处理
**问题**: 10MB限制可能不够
**影响**: 高分辨率图片无法上传
**建议解决方案**:
- 前端实现图片压缩
- 或提高限制到20MB
- 显示压缩进度

### 3. 转换超时
**问题**: AI生成可能需要30-90秒
**影响**: 用户体验较差
**建议解决方案**:
- 实现WebSocket实时更新
- 显示更详细的进度信息
- 提供取消按钮

### 4. API URL硬编码
**问题**: 开发环境URL硬编码
**影响**: 生产环境部署需要修改
**当前解决**: 使用环境变量 `NEXT_PUBLIC_API_URL`
**建议**: 在部署时设置环境变量

---

## 📚 参考文档

### 项目文档
- `docs/2026-01-28/IMAGE_TO_DIAGRAM_REPLICATION_ANALYSIS.md` - FlowPilot实现分析
- `docs/2026-01-28/VISION_MODEL_EXPLANATION.md` - Vision模型技术说明
- `docs/2026-01-28/IMPLEMENTATION_SUMMARY.md` - 后端实现总结
- `docs/2026-01-28/REAL_IMAGE_TEST_REPORT.md` - 真实图片测试报告
- `docs/2026-01-28/FRONTEND_INTEGRATION_SUMMARY.md` - 前端集成总结

### 测试图片
- `backend/tests/8d8c58ed11c145efbd76c954b4fe6233.png` - 测试用架构图（131KB）

### 后端输出
- `backend/excalidraw_output.json` - AI生成的Excalidraw场景示例

---

## 🚀 长期规划

### Phase 1: 稳定性（1-2周）
- [ ] 完成所有手动测试
- [ ] 补充自动化测试
- [ ] 修复发现的bug
- [ ] 性能优化（压缩、缓存）

### Phase 2: 功能增强（1-2月）
- [ ] 批量导入
- [ ] 历史记录
- [ ] 预览对比
- [ ] 自定义Prompt
- [ ] 导出功能增强

### Phase 3: 高级功能（3-6月）
- [ ] 实时协作（WebSocket）
- [ ] 版本控制
- [ ] AI微调迭代
- [ ] 模板系统
- [ ] 插件系统

---

## 💡 技术债务

### 代码质量
- [ ] 添加ESLint规则
- [ ] 添加Prettier格式化
- [ ] 添加Husky pre-commit hooks
- [ ] 增加代码注释

### 性能监控
- [ ] 添加性能指标收集
- [ ] 监控API响应时间
- [ ] 监控转换成功率
- [ ] 用户行为分析

### 安全性
- [ ] 文件上传安全检查
- [ ] API rate limiting
- [ ] CORS配置优化
- [ ] 敏感信息加密

---

## 📞 联系方式

如有问题，请参考：
- 项目文档: `docs/2026-01-28/`
- 测试代码: `backend/tests/test_vision_to_diagram.py`
- GitHub Issues: （如果有的话）

---

## 📝 备注

### 测试用配置
如果需要测试，可以使用以下配置（从localStorage读取）：
```javascript
// 在浏览器Console中设置
localStorage.setItem('selectedProvider', 'custom');
localStorage.setItem('modelConfig', JSON.stringify({
  provider: 'custom',
  apiKey: 'your-api-key',
  baseUrl: 'https://www.linkflow.run',
  modelName: 'claude-sonnet-4-5-20250929'
}));
```

### 快速启动脚本
Windows:
```batch
@echo off
start cmd /k "cd backend && venv\Scripts\activate && python -m app.main"
timeout /t 5
start cmd /k "cd frontend && npm run dev"
start http://localhost:3000
```

Linux/Mac:
```bash
#!/bin/bash
cd backend && source venv/bin/activate && python -m app.main &
sleep 5
cd frontend && npm run dev &
sleep 10
open http://localhost:3000
```

---

**创建时间**: 2026-01-28 16:55
**创建者**: Claude Code
**状态**: 待验证
**优先级**: 🔴 高优先级 - 需要手动测试验证
