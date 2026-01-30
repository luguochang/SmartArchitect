# 代码变更对照 - 2026-01-29

## 1. backend/app/api/vision.py

### 新增 Endpoint (L345-494)
```python
@router.post("/vision/analyze-flowchart-stream-v2")
async def analyze_flowchart_screenshot_stream_v2(request: VisionToReactFlowRequest):
    """流式图片识别 - SSE响应"""
    from fastapi.responses import StreamingResponse
    import json
    import base64

    async def generate():
        try:
            yield f"data: {json.dumps({'type': 'init', 'message': '开始分析流程图...'})}\n\n"

            # 解码图片
            image_data_str = request.image_data
            if "base64," in image_data_str:
                image_data_str = image_data_str.split("base64,")[1]

            image_data = base64.b64decode(image_data_str)

            # 进度消息
            yield f"data: {json.dumps({'type': 'progress', 'message': '🔍 正在分析图片结构...'})}\n\n"
            yield f"data: {json.dumps({'type': 'progress', 'message': '📊 正在识别节点形状...'})}\n\n"

            # 调用分析
            result = await vision_service.analyze_flowchart(
                image_data=image_data,
                preserve_layout=request.preserve_layout,
                fast_mode=request.fast_mode
            )

            # 返回结果
            result_dict = {
                "nodes": [...],
                "edges": [...],
                "mermaid_code": result.mermaid_code,
            }

            yield f"data: {json.dumps({'type': 'complete', 'result': result_dict})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

---

## 2. backend/app/services/ai_vision.py

### 修复 Claude API 调用 (L782)

**Before** ❌:
```python
response = await asyncio.to_thread(
    self.client.chat.completions.create,  # OpenAI API - 错误！
    model=model,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_b64
                }
            },
            {"type": "text", "text": prompt}
        ]
    }],
    max_tokens=max_tokens,
    temperature=0.2
)
```

**After** ✅:
```python
response = await asyncio.to_thread(
    self.client.messages.create,  # Anthropic API - 正确！
    model=model,
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": image_b64
                }
            },
            {"type": "text", "text": prompt}
        ]
    }],
    max_tokens=max_tokens,
    temperature=0.2
)
```

### 新增响应格式处理 (L851-862)
```python
# Anthropic SDK 标准格式：response.content[0].text
if is_claude_model and hasattr(response, 'content') and response.content:
    logger.info("[CUSTOM] Using Anthropic 'content' format")
    for content_block in response.content:
        if hasattr(content_block, 'text'):
            content = content_block.text
            logger.info(f"[CUSTOM] Extracted from Anthropic format, length: {len(content)}")
            break
        elif isinstance(content_block, dict) and 'text' in content_block:
            content = content_block['text']
            logger.info(f"[CUSTOM] Extracted from Anthropic dict format, length: {len(content)}")
            break
```

---

## 3. backend/app/api/chat_generator.py

### 修复 Claude Streaming (L122-142)

**Before** ❌:
```python
stream = vision_service.client.chat.completions.create(
    model=vision_service.model_name,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4096,
    temperature=0.2,
    stream=True,
)
```

**After** ✅:
```python
# 检测是否是 Claude 模型
is_claude_model = selected_provider == "custom" and vision_service.model_name and "claude" in vision_service.model_name.lower()

if is_claude_model:
    # 使用 Anthropic streaming API
    logger.info("[STREAM] Using Anthropic streaming API")
    stream = vision_service.client.messages.stream(
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

### 新增流式响应处理 (L148-166)

**Before** ❌:
```python
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

**After** ✅:
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

---

## 4. backend/app/models/schemas.py (L447-455)

### 更新 VisionToReactFlowRequest

**Before**:
```python
class VisionToReactFlowRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image")
    prompt: Optional[str] = Field(None, description="Additional context")
    provider: Literal["gemini", "openai", "claude", "siliconflow", "custom"] = "custom"
    api_key: Optional[str] = Field(None, description="API key")
    base_url: Optional[str] = Field(None, description="Base URL for custom provider")
    model_name: Optional[str] = Field(None, description="Model name")
```

**After**:
```python
class VisionToReactFlowRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image (with data:image prefix or without)")
    prompt: Optional[str] = Field(None, description="Additional context or instructions")
    provider: Literal["gemini", "openai", "claude", "siliconflow", "custom"] = "custom"
    api_key: Optional[str] = Field(None, description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Base URL for custom provider")
    model_name: Optional[str] = Field(None, description="Model name")
    preserve_layout: bool = Field(True, description="Preserve original node positions")  # 新增
    fast_mode: bool = Field(True, description="Use fast mode (simplified prompt)")       # 新增
```

---

## 5. frontend/components/FlowchartUploader.tsx

### 添加聊天消息辅助函数 (L36-40)
```typescript
const addChatMessage = useCallback((role: "user" | "assistant", content: string) => {
  useArchitectStore.setState((state) => ({
    chatHistory: [...state.chatHistory, { role, content }]
  }));
}, []);
```

### 更新 endpoint 和请求方式 (L82)

**Before**:
```typescript
const formData = new FormData();
formData.append("file", file);
formData.append("provider", modelConfig.provider || "gemini");

const response = await fetch("http://localhost:8001/api/vision/analyze-flowchart", {
  method: "POST",
  body: formData,
});
```

**After**:
```typescript
// 转换为 base64
const base64Image = await fileToBase64(file);

// JSON body
const requestBody = {
  image_data: base64Image,
  provider: modelConfig.provider || "gemini",
  preserve_layout: true,
  fast_mode: true,
  api_key: modelConfig.apiKey,
  base_url: modelConfig.baseUrl,
  model_name: modelConfig.modelName,
};

// 使用流式endpoint v2
const response = await fetch("http://localhost:8003/api/vision/analyze-flowchart-stream-v2", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
  },
  body: JSON.stringify(requestBody),
});

// SSE 流式解析
const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split("\n");

  for (const line of lines) {
    if (line.startsWith("data: ")) {
      const data = JSON.parse(line.slice(6));

      if (data.type === "init" || data.type === "progress") {
        addChatMessage("assistant", data.message);  // 显示进度
      } else if (data.type === "complete") {
        addChatMessage("assistant", data.message);
        analysisResult = data.result;
      } else if (data.type === "error") {
        addChatMessage("assistant", `❌ ${data.message}`);
        throw new Error(data.message);
      }
    }
  }
}
```

---

## 6. backend/app/core/config.py (L10)

### 端口配置

**Before**:
```python
API_PORT: int = int(os.getenv("PORT", 8000))
```

**After**:
```python
API_PORT: int = int(os.getenv("PORT", 8003))
```

---

## API 对照表

| SDK | 普通调用 | 流式调用 | 响应格式 |
|-----|---------|---------|---------|
| **OpenAI** | `client.chat.completions.create()` | `create(stream=True)` | `response.choices[0].message.content` |
| **Anthropic** | `client.messages.create()` | `client.messages.stream()` | `response.content[0].text` |

## 流式响应处理对照

### OpenAI
```python
for chunk in stream:
    delta = chunk.choices[0].delta.content
    print(delta)
```

### Anthropic
```python
with stream as s:
    for text in s.text_stream:
        print(text)
```
