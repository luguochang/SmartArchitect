# 2026-01-29 工作日志

## 主要完成工作

### 1. 实现流式图片上传功能
**需求背景**: 用户上传流程图时，需要看到 AI 处理的实时进度，不能被上传组件遮挡。

#### Backend 改动
- **新增流式 endpoint**: `/api/vision/analyze-flowchart-stream-v2`
  - 文件: `backend/app/api/vision.py` (第345行起)
  - 使用 Server-Sent Events (SSE) 实现流式响应
  - 改用 JSON body + base64 编码图片（与 Excalidraw 相同方式，避免文件关闭问题）

- **Pydantic Schema 更新**: `backend/app/models/schemas.py`
  - `VisionToReactFlowRequest` 添加 `preserve_layout` 和 `fast_mode` 字段
  - 支持 base64 格式的 `image_data` 字段

- **进度消息节点**:
  ```
  ✅ 开始分析流程图...
  ✅ 正在配置 AI 模型...
  ✅ 🔍 正在分析图片结构...
  ✅ 📊 正在识别节点形状（开始/结束/任务/判断）...
  ✅ ✏️ 正在提取文本标签...
  ✅ 🔗 正在识别连线关系...
  ✅ ⚡ 正在生成 Mermaid 代码...
  ✅ ✅ 识别完成！
  ```

#### Frontend 改动
- **FlowchartUploader.tsx** (第82行)
  - 使用新的流式 endpoint v2
  - 集成 `fileToBase64` 工具函数
  - 添加 `addChatMessage` 辅助函数，将进度消息显示在聊天面板
  - 实现 SSE 流式响应解析

#### 技术细节
- **传输方式**: 从 FormData file upload 改为 JSON body + base64
  - 原因: FormData 方式会导致 FastAPI 关闭文件，async generator 无法读取
  - 用户指示: "不行就改成和excalidraw的方式传输，不要走那么弯路了"

- **测试结果**: ✅ 自测通过
  ```bash
  curl -N -X POST "http://localhost:8000/api/vision/analyze-flowchart-stream-v2" \
    -H "Content-Type: application/json" \
    -d '{"image_data": "data:image/png;base64,...", "provider": "gemini", ...}'
  ```

---

### 2. 修复 Claude 模型 API 调用重大 Bug

**问题描述**:
```
AttributeError: 'Anthropic' object has no attribute 'chat'
```

#### Root Cause
当使用 custom provider (Claude 模型) 时:
1. 初始化时创建了 `Anthropic` 客户端
2. 但调用时使用了 OpenAI 风格的 API: `self.client.chat.completions.create`
3. Anthropic SDK 的正确 API 是: `self.client.messages.create`

#### 修复内容

##### ai_vision.py (第782行)
**Before**:
```python
response = await asyncio.to_thread(
    self.client.chat.completions.create,  # ❌ OpenAI API
    model=model,
    messages=[...],
    max_tokens=max_tokens,
    temperature=0.2
)
```

**After**:
```python
response = await asyncio.to_thread(
    self.client.messages.create,  # ✅ Anthropic API
    model=model,
    messages=[...],
    max_tokens=max_tokens,
    temperature=0.2
)
```

**额外改进**:
- 添加 Anthropic 响应格式的专门处理逻辑 (第852行)
```python
# Anthropic SDK 标准格式：response.content[0].text
if is_claude_model and hasattr(response, 'content') and response.content:
    logger.info("[CUSTOM] Using Anthropic 'content' format")
    for content_block in response.content:
        if hasattr(content_block, 'text'):
            content = content_block.text
            break
```

##### chat_generator.py (第122行)
**Before**:
```python
stream = vision_service.client.chat.completions.create(  # ❌ OpenAI API
    model=vision_service.model_name,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4096,
    temperature=0.2,
    stream=True,
)
```

**After**:
```python
# 检测是否是 Claude 模型
is_claude_model = selected_provider == "custom" and vision_service.model_name and "claude" in vision_service.model_name.lower()

if is_claude_model:
    # 使用 Anthropic streaming API
    logger.info("[STREAM] Using Anthropic streaming API")
    stream = vision_service.client.messages.stream(  # ✅ Anthropic Streaming
        model=vision_service.model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0.2,
    )
else:
    # 使用 OpenAI streaming API
    stream = vision_service.client.chat.completions.create(
        model=vision_service.model_name,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=4096,
        temperature=0.2,
        stream=True,
    )
```

**流式响应处理** (第149行):
```python
if is_claude_model:
    # Anthropic streaming API使用context manager
    with stream as s:
        for text in s.text_stream:
            accumulated += text
            yield f"data: [TOKEN] {text}\n\n"
else:
    # OpenAI streaming API
    for chunk in stream:
        if not getattr(chunk, "choices", None):
            continue
        delta = chunk.choices[0].delta.content if chunk.choices[0].delta else None
        if not delta:
            continue
        text = "".join(delta)
        accumulated += text
        yield f"data: [TOKEN] {text}\n\n"
```

#### 影响范围
此 bug 影响以下功能：
- ❌ Flow canvas 调用 Claude 模型（AI 生成流程图）
- ❌ Excalidraw 调用 Claude 模型（AI 生成图表）
- ❌ 流程图图片识别调用 Claude 模型
- ✅ 修复后全部恢复正常

---

## 其他改动

### config.py 端口更新
- 默认端口从 8000 改为 8003
- 文件: `backend/app/core/config.py` (第10行)
```python
API_PORT: int = int(os.getenv("PORT", 8003))
```

---

## 文件变更清单

### Backend
1. `backend/app/api/vision.py`
   - 新增 `/api/vision/analyze-flowchart-stream-v2` endpoint (L345-494)
   - 修复 Claude API 调用 (L782)
   - 添加 Anthropic 响应格式处理 (L852-862)

2. `backend/app/api/chat_generator.py`
   - 修复 Claude streaming API 调用 (L122-142)
   - 添加 Anthropic streaming 响应处理 (L149-166)

3. `backend/app/models/schemas.py`
   - `VisionToReactFlowRequest` 添加字段 (L447-455)

4. `backend/app/core/config.py`
   - 默认端口改为 8003 (L10)

### Frontend
1. `frontend/components/FlowchartUploader.tsx`
   - 使用新的流式 endpoint v2 (L82)
   - 添加 `addChatMessage` 辅助函数 (L36-40)
   - 重写 `handleFile` 使用 JSON body (L42-192)

---

## 调试过程记录

### 问题1: Backend 模块缓存
**现象**: 修改代码后，运行的 server 仍使用旧代码
**尝试**:
- 多次重启 backend
- 清除 `__pycache__`
- Kill 所有 Python 进程
**解决**: 创建新的 endpoint name (`-v2`) 绕过缓存问题

### 问题2: Port 配置混乱
**现象**:
- Backend 默认在 8000
- Frontend 期望在 8001
- 用户自己改成了 8003
**解决**: 用户统一改为 8003

---

## 测试验证

### 流式上传测试
```bash
# 测试命令
curl -N -X POST "http://localhost:8000/api/vision/analyze-flowchart-stream-v2" \
  -H "Content-Type: application/json" \
  -d '{"image_data": "data:image/png;base64,iVBORw0KGg...", "provider": "gemini", "preserve_layout": true, "fast_mode": true}'

# 返回结果
data: {"type": "init", "message": "开始分析流程图..."}
data: {"type": "progress", "message": "正在配置 AI 模型..."}
data: {"type": "progress", "message": "🔍 正在分析图片结构..."}
data: {"type": "progress", "message": "📊 正在识别节点形状（开始/结束/任务/判断）..."}
data: {"type": "progress", "message": "✏️ 正在提取文本标签..."}
data: {"type": "progress", "message": "🔗 正在识别连线关系..."}
data: {"type": "progress", "message": "⚡ 正在生成 Mermaid 代码..."}
data: {"type": "complete", "message": "✅ 识别完成！", "result": {...}}
```

### Claude API 修复验证
**修复前**:
```
ERROR: 'Anthropic' object has no attribute 'chat'
```

**修复后**:
- Flow canvas ✅
- Excalidraw ✅
- 流程图识别 ✅

---

## 待处理事项

1. ⏸️ 端口配置标准化
   - Frontend 和 Backend 保持一致
   - 建议统一使用 8003

2. ⏸️ 测试覆盖
   - 添加 Claude streaming API 的单元测试
   - 添加流式上传的集成测试

3. ⏸️ 文档更新
   - 更新 API 文档说明新的流式 endpoint
   - 更新架构文档说明 Anthropic SDK 集成

---

## 用户反馈

> "我自己把前后端都改成了8003端口自测了下，不知道你改了什么，现在flow canvas和excalidraw调用模型的接口都报错了"

**问题**: 修复流式上传时引入的 Claude API 调用 bug
**状态**: ✅ 已修复
**解决方案**:
- 正确使用 Anthropic SDK API (`messages.create` 而非 `chat.completions.create`)
- 添加 Claude 模型检测和专门的响应处理逻辑

---

## 技术笔记

### Anthropic SDK vs OpenAI SDK

| Feature | OpenAI SDK | Anthropic SDK |
|---------|------------|---------------|
| 普通调用 | `client.chat.completions.create()` | `client.messages.create()` |
| 流式调用 | `client.chat.completions.create(stream=True)` | `client.messages.stream()` |
| 响应格式 | `response.choices[0].message.content` | `response.content[0].text` |
| 流式处理 | `for chunk in stream:` | `with stream as s: for text in s.text_stream:` |

### SSE (Server-Sent Events) 格式
```
data: {"type": "init", "message": "开始处理..."}\n\n
data: {"type": "progress", "message": "步骤1完成"}\n\n
data: {"type": "complete", "message": "处理完成", "result": {...}}\n\n
data: {"type": "error", "message": "错误信息"}\n\n
```

---

**日志创建时间**: 2026-01-29
**工作时长**: 约 3 小时
**主要成果**: 流式上传功能 + Claude API bug 修复
