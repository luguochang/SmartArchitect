# 真流式 Excalidraw 生成实现总结

## 核心发现

FlowPilot 能实现真流式的关键：**使用支持 multimodal 的文本流式API**，而不是纯 Vision API。

### Vision API vs Multimodal Text API

| API类型 | 流式支持 | 适用场景 |
|---------|---------|----------|
| Vision API (`generate_with_vision`) | ❌ **不支持**流式 | 纯图片识别任务 |
| Multimodal Text API (`messages.stream`) | ✅ **支持**流式 | 图片+文本混合输入 |

## 实现方案

### 后端：添加真流式Vision方法

已在 `backend/app/services/ai_vision.py` 添加新方法：

```python
async def generate_with_vision_stream(self, image_data: bytes, prompt: str):
    """
    🔥 真流式Vision生成：支持图片+文本的流式输出
    使用 multimodal streaming APIs (Claude/GPT-4 Vision)
    """
    # Claude 示例
    content = [
        {
            "type": "image",
            "source": {"type": "base64", "media_type": "image/png", "data": image_b64}
        },
        {
            "type": "text",
            "text": prompt
        }
    ]

    with self.client.messages.stream(
        model=self.model_name,
        messages=[{"role": "user", "content": content}],
        stream=True
    ) as stream:
        for text in stream.text_stream:
            yield text  # 🔥 实时yield token
```

### 后端端点：修改为真流式

修改 `/api/vision/generate-excalidraw-stream`：

```python
@router.post("/vision/generate-excalidraw-stream")
async def generate_excalidraw_from_image_stream(request: VisionToExcalidrawRequest):
    async def generate():
        yield f"data: {json.dumps({'type': 'init', 'message': 'Starting...'})}\n\n"

        # 🔥 使用真流式API
        json_buffer = ""
        parsed_elements = []

        async for token in vision_service.generate_with_vision_stream(image_bytes, prompt):
            json_buffer += token

            # 🔥 实时解析JSON片段
            new_elements = tryParseIncrementalElements(json_buffer, parsed_elements)

            for element in new_elements:
                normalized = normalizeElement(element)
                parsed_elements.append(normalized)
                yield f"data: {json.dumps({'type': 'element', 'element': normalized})}\n\n"

        yield f"data: {json.dumps({'type': 'complete'})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

### 前端：增量JSON解析（参考聊天框）

```typescript
// 复用聊天框的 tryParseAndRenderPartialElements 逻辑
async for (const chunk of convertImageToExcalidrawStreaming(file)) {
    if (chunk.type === "element") {
        elements.push(chunk.element);

        // 立即更新画板
        setExcalidrawScene({
            elements: [...elements],
            appState,
            files: {}
        });
    }
}
```

## 限制与说明

### ⚠️ 重要限制

1. **并非所有模型都支持 Vision Streaming**
   - ✅ 支持：Claude 3.5+, GPT-4 Vision, Gemini 2.0+
   - ❌ 不支持：旧版模型、部分自定义端点

2. **您配置的模型**：`claude-sonnet-4-5-20250929`
   - ✅ 理论上支持 multimodal streaming
   - ⚠️ 但依赖 `linkflow.run` 代理是否正确转发流式请求

3. **测试建议**
   - 先用官方 Claude API 测试（`https://api.anthropic.com`）
   - 确认流式工作后，再测试 linkflow 代理

## 当前状态

### ✅ 已完成
1. 后端新增 `generate_with_vision_stream` 方法
2. 支持 Claude、GPT-4 Vision 的真流式
3. 前端已有增量解析基础（聊天框实现）

### 🚧 需要完成
1. **修改后端端点** - 使用新的流式方法
2. **前端适配** - 接收token流并增量解析
3. **测试验证** - 确认 linkflow 支持流式

## 快速测试方案

**方案1：使用聊天框测试（最快）**
```
1. 切换到 Excalidraw 模式
2. 在聊天框输入："请帮我画一个流程图"
3. 应该看到真流式效果（因为聊天框已实现）
```

**方案2：完整实现图片上传流式（需要更多开发）**
```
1. 完成后端端点修改（增量JSON解析）
2. 前端复用聊天框的解析逻辑
3. 测试图片上传流式生成
```

## 结论

**技术上可行**，但需要：
1. 模型支持 multimodal streaming（您的Claude模型理论支持）
2. API代理正确转发流式请求（linkflow.run 需验证）
3. 实现增量JSON解析逻辑（参考FlowPilot/聊天框）

建议先测试聊天框的流式效果，确认基础架构工作后，再实现图片上传的真流式。
