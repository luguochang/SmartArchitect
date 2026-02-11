# 快速实现检查清单

## 后端实现（2天）

### Day 1: 核心服务

- [ ] **文件：** `backend/app/services/ai_vision.py`
  - [ ] 复制 `_build_flowchart_prompt()` 方法（从实现文档）
  - [ ] 复制 `analyze_flowchart()` 方法
  - [ ] 测试运行：`python -m app.main`

- [ ] **文件：** `backend/app/models/schemas.py`
  - [ ] 在 `ImageAnalysisResponse` 添加字段：
    ```python
    warnings: Optional[List[dict]] = None
    flowchart_analysis: Optional[dict] = None
    ```

- [ ] **文件：** `backend/app/api/vision.py`
  - [ ] 复制 `analyze_flowchart_screenshot()` 端点（从实现文档）
  - [ ] 访问：http://localhost:8000/docs 验证API出现

### Day 2: 测试验证

- [ ] **测试 API（用 Postman 或 curl）**
  ```bash
  curl -X POST "http://localhost:8000/api/vision/analyze-flowchart" \
    -F "file=@test_flowchart.png" \
    -F "provider=gemini" \
    -F "api_key=YOUR_KEY"
  ```

- [ ] **验证响应格式**
  - [ ] nodes 数组有数据
  - [ ] edges 数组有数据
  - [ ] warnings 字段存在
  - [ ] flowchart_analysis 字段存在

## 前端实现（1天）

### Day 3: 上传组件

- [ ] **文件：** `frontend/components/FlowchartUploader.tsx`（新建）
  - [ ] 复制完整代码（从实现文档）

- [ ] **文件：** `frontend/components/AiControlPanel.tsx`
  - [ ] 导入：`import { FlowchartUploader } from "./FlowchartUploader";`
  - [ ] 添加Tab：`<Tab value="upload"><Upload />截图识别</Tab>`
  - [ ] 添加内容：
    ```tsx
    {activeTab === "upload" && (
      <div className="p-4">
        <FlowchartUploader />
      </div>
    )}
    ```

- [ ] **测试前端**
  - [ ] 访问：http://localhost:3000
  - [ ] 打开 AI 控制面板
  - [ ] 看到"截图识别"Tab
  - [ ] 上传测试图片
  - [ ] 检查画布是否出现节点

## 测试用例

### 准备测试图片

- [ ] **简单流程图**（3-5节点）
  - 开始 → 处理 → 判断 → 结束
  - 预期识别率：>95%

- [ ] **中等流程图**（10-15节点）
  - 多分支、循环
  - 预期识别率：>90%

- [ ] **复杂流程图**（20+节点）
  - BPMN、泳道
  - 预期识别率：>80%

### 验证清单

- [ ] **节点识别**
  - [ ] 开始节点（圆形）→ start-event
  - [ ] 结束节点（圆形）→ end-event
  - [ ] 处理节点（矩形）→ task
  - [ ] 判断节点（菱形）→ decision

- [ ] **连线识别**
  - [ ] 箭头方向正确
  - [ ] 分支标签正确（是/否）
  - [ ] 连线ID唯一

- [ ] **布局**
  - [ ] preserve_layout=true：位置接近原图
  - [ ] preserve_layout=false：自动优化布局

- [ ] **警告信息**
  - [ ] 未知形状有警告
  - [ ] 警告信息清晰

## 常见问题排查

### API返回422错误

**原因：** AI响应JSON格式不对

**解决：**
- [ ] 检查 prompt 是否包含"不要用markdown代码块"
- [ ] 查看日志：`backend/app/services/ai_vision.py` 的 logger 输出
- [ ] 尝试降低温度：`temperature=0.1`

### 识别结果不准确

**原因：** 图片质量差或prompt不够清晰

**解决：**
- [ ] 使用清晰的截图（不要拍照）
- [ ] 尝试不同的provider（Gemini → Claude）
- [ ] 调整prompt的形状描述

### 前端上传后无反应

**原因：** CORS或网络错误

**解决：**
- [ ] 检查浏览器控制台的Network标签
- [ ] 验证后端CORS配置
- [ ] 确认API地址正确（http://localhost:8000）

### 节点位置重叠

**原因：** 布局算法问题

**解决：**
- [ ] 在prompt中调整间距参数
- [ ] 前端使用 `fitView()` 自动调整
- [ ] 或者用 `preserve_layout=false` 自动布局

## 性能优化（可选）

- [ ] **图片压缩**
  ```python
  # 如果图片>2MB，压缩到1MB
  if len(image_data) > 2 * 1024 * 1024:
      image_data = compress_image(image_data)
  ```

- [ ] **结果缓存**
  ```python
  # 使用Redis缓存识别结果（避免重复识别）
  cache_key = f"flowchart:{md5(image_data)}"
  ```

- [ ] **并发限制**
  ```python
  # 限制同时识别的请求数
  semaphore = asyncio.Semaphore(3)
  ```

## 完成标志

- [ ] ✅ 后端API能正常识别流程图
- [ ] ✅ 前端能上传并显示结果
- [ ] ✅ 识别准确率达到80%以上
- [ ] ✅ warnings正确显示
- [ ] ✅ 布局基本合理

---

**完成后：**
- 提交代码：`git add . && git commit -m "feat: add flowchart screenshot recognition"`
- 更新文档：PHASE6_PROPOSAL.md 标记为已完成
- 收集用户反馈：识别准确率、使用体验
