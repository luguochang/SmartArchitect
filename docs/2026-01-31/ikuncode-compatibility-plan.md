# ikuncode 兼容性完整分析和修改计划

## 当前状态总结

### ✅ 已修改（Flow Canvas 聊天框流式）
- **文件**: `backend/app/api/chat_generator.py:79` (`generate_flowchart_stream`)
- **修改内容**: 检测 ikuncode.cc，使用 raw HTTP streaming
- **状态**: ✅ 工作正常

### ❌ 未修改的端点

#### 1. Excalidraw 聊天框流式
- **文件**: `backend/app/api/excalidraw.py:75` (`generate_excalidraw_scene_stream`)
- **调用**: `vision_service.generate_with_stream(prompt)`
- **问题**: `generate_with_stream` 方法中的 Claude 分支使用 `self.client.messages.stream()`
- **影响**: ikuncode.cc 会被阻拦

#### 2. Flow Canvas 图片上传
- **文件**: `backend/app/api/vision.py:31` (`analyze_architecture_image`)
- **调用**: `vision_service.analyze_architecture(image_data)`
- **类型**: **非流式**
- **问题**: 内部调用 `_analyze_with_custom_text` 已修复，但需要验证

#### 3. Excalidraw 图片上传
- **可能复用**: `/api/vision/analyze` 或有独立端点
- **需要检查**: 是否存在独立端点

---

## 关键发现

### `generate_with_stream` 方法分析

**位置**: `backend/app/services/ai_vision.py:1294`

**当前逻辑**:
```python
async def generate_with_stream(self, prompt: str):
    if self.provider == "openai":
        # OpenAI streaming
        stream = self.client.chat.completions.create(stream=True, ...)

    elif self.provider == "claude" or (
        self.provider == "custom" and "claude" in self.model_name.lower()
    ):
        # Claude streaming - 使用 SDK
        with self.client.messages.stream(...) as stream:
            for text in stream.text_stream:
                yield text

    elif self.provider == "siliconflow" or self.provider == "custom":
        # SiliconFlow/Custom (OpenAI-compatible)
        stream = self.client.chat.completions.create(stream=True, ...)
```

**问题**:
1. ❌ 对于 `custom` + `claude` 模型，走的是 Claude 分支
2. ❌ 使用 `self.client.messages.stream()`，会被 ikuncode.cc 阻拦
3. ❌ 没有检测 ikuncode.cc 并使用 raw HTTP

---

## 修改策略

### 原则
1. **不破坏现有功能**: linkflow.run 必须继续正常工作
2. **精确识别**: 只对 ikuncode.cc 使用特殊处理
3. **统一逻辑**: 在 `generate_with_stream` 方法中统一处理，避免重复代码

### 方案 A: 在 `generate_with_stream` 中添加 ikuncode 检测（推荐）

**优点**:
- ✅ 统一处理，所有调用 `generate_with_stream` 的地方都自动兼容
- ✅ 代码集中，易于维护
- ✅ Excalidraw 和其他未来功能自动兼容

**缺点**:
- ⚠️ 需要小心处理，避免破坏现有逻辑

**实现**:
```python
async def generate_with_stream(self, prompt: str):
    # 检测是否是 ikuncode.cc
    use_raw_http = (
        self.provider == "custom" and
        self.custom_base_url and
        "ikuncode.cc" in self.custom_base_url.lower()
    )

    if use_raw_http:
        # ikuncode.cc: 使用 raw HTTP streaming
        import httpx
        clean_base_url = self.custom_base_url.rstrip('/')
        if clean_base_url.endswith('/v1'):
            clean_base_url = clean_base_url[:-3]

        headers = {
            "x-api-key": self.custom_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        data = {
            "model": self.model_name,
            "max_tokens": 16384,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True
        }

        async with httpx.AsyncClient(timeout=120.0) as http_client:
            async with http_client.stream("POST", f"{clean_base_url}/v1/messages",
                                          headers=headers, json=data) as response:
                current_event = None
                buffer = ""

                async for chunk in response.aiter_bytes():
                    buffer += chunk.decode('utf-8')

                    while '\n' in buffer:
                        line, buffer = buffer.split('\n', 1)
                        line = line.strip()

                        if line.startswith("event: "):
                            current_event = line[7:]
                        elif line.startswith("data: "):
                            data_json = json.loads(line[6:])
                            if current_event == "content_block_delta":
                                text = data_json.get("delta", {}).get("text", "")
                                if text:
                                    yield text

    elif self.provider == "claude" or (
        self.provider == "custom" and "claude" in self.model_name.lower()
    ):
        # linkflow.run 等: 使用 Claude SDK
        with self.client.messages.stream(...) as stream:
            for text in stream.text_stream:
                yield text

    # ... 其他 provider 逻辑不变
```

### 方案 B: 在每个端点单独处理

**优点**:
- ✅ 不影响 `generate_with_stream` 的现有逻辑

**缺点**:
- ❌ 代码重复
- ❌ 每个端点都要修改
- ❌ 未来新功能容易遗漏

---

## 图片上传的特殊性

### 图片上传是非流式的

**Flow Canvas 图片上传**:
```python
# backend/app/api/vision.py:161
result = await vision_service.analyze_architecture(
    image_data=image_data,
    analyze_bottlenecks=analyze_bottlenecks
)
```

**内部调用链**:
1. `analyze_architecture()` →
2. `_analyze_with_custom()` →
3. `_analyze_with_custom_text()` ✅ 已修复

**结论**:
- ✅ 图片上传已经兼容 ikuncode（通过之前修复的 `_analyze_with_custom_text`）
- ✅ 无需额外修改

---

## 修改计划

### 第一步: 修改 `generate_with_stream` 方法
- **文件**: `backend/app/services/ai_vision.py:1294`
- **修改**: 添加 ikuncode.cc 检测和 raw HTTP streaming
- **影响**: Excalidraw 聊天框流式自动兼容

### 第二步: 验证图片上传
- **测试**: 使用 ikuncode.cc 上传图片
- **预期**: 应该已经工作（因为 `_analyze_with_custom_text` 已修复）

### 第三步: 测试所有功能
1. ✅ Flow Canvas 聊天框流式（已测试）
2. ⏳ Excalidraw 聊天框流式（待测试）
3. ⏳ Flow Canvas 图片上传（待测试）
4. ⏳ Excalidraw 图片上传（待测试，如果存在）

---

## 风险评估

### 高风险
- ❌ 修改 `generate_with_stream` 可能影响 linkflow.run
- ❌ Excalidraw 的流式渲染逻辑复杂，可能有特殊处理

### 中风险
- ⚠️ 图片上传虽然已修复，但未测试

### 低风险
- ✅ Flow Canvas 聊天框已验证工作

---

## 建议

### 推荐方案: 方案 A（统一处理）

**理由**:
1. 代码集中，易于维护
2. 自动兼容所有使用 `generate_with_stream` 的地方
3. 逻辑清晰：检测 ikuncode → raw HTTP，否则 → SDK

### 实施步骤

1. **先备份**: 保存当前工作的 `ai_vision.py`
2. **修改 `generate_with_stream`**: 添加 ikuncode 检测
3. **测试 linkflow.run**: 确保不破坏现有功能
4. **测试 ikuncode.cc**:
   - Excalidraw 聊天框流式
   - Flow Canvas 图片上传
   - Excalidraw 图片上传（如果存在）
5. **如果出问题**: 立即回滚，改用方案 B

---

## 总结

### 需要修改的地方
1. ✅ `chat_generator.py:generate_flowchart_stream` - 已修改
2. ❌ `ai_vision.py:generate_with_stream` - **需要修改**
3. ✅ `ai_vision.py:_analyze_with_custom_text` - 已修改（图片上传用）

### 修改后的覆盖范围
- ✅ Flow Canvas 聊天框流式
- ✅ Excalidraw 聊天框流式（通过 `generate_with_stream`）
- ✅ Flow Canvas 图片上传（通过 `_analyze_with_custom_text`）
- ✅ Excalidraw 图片上传（如果复用 vision API）

### 关键点
1. **精确识别**: 只对 ikuncode.cc 特殊处理
2. **不破坏现有**: linkflow.run 继续使用 SDK
3. **统一逻辑**: 在 `generate_with_stream` 中统一处理
4. **小心测试**: 修改后全面测试所有功能
