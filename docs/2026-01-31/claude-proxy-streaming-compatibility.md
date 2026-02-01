# Claude 中转站流式兼容性问题解决方案

**日期**: 2026-01-31
**问题**: ikuncode.cc 中转站集成导致原有 linkflow.run 的实时流式打印失效

---

## 问题背景

### 原始状态
- ✅ **linkflow.run** (`https://www.linkflow.run/v1`) + Claude 模型 → 实时流式正常
- ❌ **ikuncode.cc** (`https://api.ikuncode.cc`) + Claude 模型 → 报错 `Your request was blocked`

### 问题现象
用户切换到 ikuncode.cc 后：
1. 接口返回 `Your request was blocked`
2. 尝试修复后，linkflow.run 的实时流式也被破坏
3. 聊天框不再实时显示 AI 返回内容，而是等待几十秒后一次性显示

---

## 根本原因分析

### 1. 中转站差异

| 特性 | linkflow.run | ikuncode.cc |
|------|-------------|-------------|
| **User-Agent 检测** | ❌ 不阻拦 SDK | ✅ 阻拦 SDK |
| **Anthropic SDK** | ✅ 可用 | ❌ 被阻拦 |
| **OpenAI SDK** | ✅ 可用 | ❌ 被阻拦 |
| **Raw HTTP** | ✅ 可用 | ✅ 可用 |
| **实时流式** | ✅ 支持 | ✅ 支持 |

**关键发现**：
- ikuncode.cc 会检测并阻拦来自 Anthropic SDK 和 OpenAI SDK 的请求（基于 User-Agent）
- 但 ikuncode.cc **本身支持真正的实时流式**（通过测试验证）
- 只是必须使用 raw HTTP 请求才能绕过 User-Agent 检测

### 2. 失败的修改历史

#### 尝试 1: 对所有 custom + claude 使用特殊处理
```python
is_claude_model = (
    selected_provider == "custom" and
    "claude" in model_name.lower()
)
```
**失败原因**: 把 linkflow.run 也破坏了，linkflow 不需要特殊处理

#### 尝试 2: 使用 httpx.aiter_lines()
```python
async for line in response.aiter_lines():
    # 解析 SSE...
```
**失败原因**: `aiter_lines()` 会缓冲整个响应，导致所有 token 同时到达

#### 尝试 3: 没有正确解析 Claude SSE 格式
```python
if line.startswith("data: "):
    data = json.loads(line[6:])
    if data.get("type") == "content_block_delta":  # ❌ 永远不匹配
```
**失败原因**: Claude 的 SSE 格式使用 `event:` 和 `data:` 分开的行，需要跟踪 `current_event`

---

## 最终解决方案

### 核心思路
**精确识别 ikuncode.cc，只对它使用特殊处理，其他中转站保持原有逻辑**

### 代码实现

```python
# 检测是否是 ikuncode.cc
use_raw_http = (
    selected_provider == "custom" and
    vision_service.custom_base_url and
    "ikuncode.cc" in vision_service.custom_base_url.lower()
)

if use_raw_http:
    # ikuncode.cc：使用 raw HTTP streaming
    async with httpx.AsyncClient(timeout=120.0) as http_client:
        async with http_client.stream("POST", f"{clean_base_url}/v1/messages",
                                      headers=headers, json=data) as response:
            current_event = None
            buffer = ""

            # 使用 aiter_bytes() 避免缓冲
            async for chunk in response.aiter_bytes():
                buffer += chunk.decode('utf-8')

                # 手动按行分割
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()

                    if line.startswith("event: "):
                        current_event = line[7:]  # 保存事件类型
                    elif line.startswith("data: "):
                        data_json = json.loads(line[6:])
                        # 只在 content_block_delta 事件时输出
                        if current_event == "content_block_delta":
                            text = data_json.get("delta", {}).get("text", "")
                            if text:
                                accumulated += text
                                yield f"data: [TOKEN] {text}\n\n"
else:
    # linkflow.run 等：使用标准 SDK
    if is_claude_model:
        stream = vision_service.client.messages.stream(...)
        with stream as s:
            for text in s.text_stream:
                yield f"data: [TOKEN] {text}\n\n"
    else:
        stream = vision_service.client.chat.completions.create(stream=True, ...)
        for chunk in stream:
            yield f"data: [TOKEN] {text}\n\n"
```

### 关键技术点

1. **精确识别**: 通过 `base_url` 中是否包含 `"ikuncode.cc"` 来判断
2. **使用 aiter_bytes()**: 避免 `aiter_lines()` 的缓冲问题
3. **正确解析 Claude SSE**:
   - 跟踪 `current_event` 状态
   - 只在 `event: content_block_delta` 时输出 token
4. **URL 清理**: 避免重复拼接 `/v1`
5. **不破坏原有逻辑**: linkflow.run 继续使用 Anthropic SDK

---

## 测试验证

### 测试 1: ikuncode.cc 是否支持真流式

```python
# test_ikuncode_real_streaming.py
async with httpx.AsyncClient() as client:
    async with client.stream("POST", url, headers=headers, json=data) as response:
        async for chunk in response.aiter_bytes():
            print(f"[{elapsed:.3f}s] Chunk: {len(chunk)} bytes")
```

**结果**:
```
[3.428s] 首字节到达
[3.492s] Chunk #2: 128 bytes
[3.701s] Chunk #3: 128 bytes
[3.748s] Chunk #4: 132 bytes
...
```

✅ **结论**: ikuncode.cc 支持真流式，chunk 是逐步到达的（100-500ms 间隔）

### 测试 2: Claude SSE 格式

```
event: message_start
data: {"type":"message_start",...}

event: content_block_delta
data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello"}}

event: content_block_delta
data: {"type":"content_block_delta","delta":{"type":"text_delta","text":" world"}}
```

✅ **结论**: 必须解析 `event:` 行来识别事件类型

---

## 其他中转站兼容性分析

### 可能的中转站类型

#### 类型 A: 完全兼容型（如 linkflow.run）
- **特征**: 不阻拦 SDK User-Agent
- **兼容方式**: 使用标准 Anthropic/OpenAI SDK
- **无需特殊处理**: ✅

#### 类型 B: User-Agent 阻拦型（如 ikuncode.cc）
- **特征**: 阻拦 SDK，但允许 raw HTTP
- **兼容方式**: 使用 raw HTTP + 手动解析 SSE
- **需要特殊处理**: ✅

#### 类型 C: 假流式型
- **特征**: 声称支持流式，但实际是缓冲完整响应后才发送
- **表现**: 所有 chunk 在同一时刻到达
- **兼容方式**: 无法真正实现实时流式
- **建议**: 提示用户切换中转站

#### 类型 D: 不支持流式型
- **特征**: 只支持非流式 API
- **兼容方式**: 降级到非流式模式
- **需要特殊处理**: ✅

### 通用兼容策略

#### 方案 1: 黑名单模式（当前实现）
```python
# 只对已知有问题的中转站特殊处理
if "ikuncode.cc" in base_url:
    use_raw_http = True
```

**优点**:
- ✅ 不影响未知中转站
- ✅ 保持原有逻辑稳定

**缺点**:
- ❌ 需要手动添加每个有问题的中转站
- ❌ 用户使用新中转站时可能遇到问题

#### 方案 2: 白名单模式
```python
# 只对已知兼容的中转站使用 SDK
if "linkflow.run" in base_url or "anthropic.com" in base_url:
    use_sdk = True
else:
    use_raw_http = True
```

**优点**:
- ✅ 新中转站默认使用 raw HTTP（更安全）

**缺点**:
- ❌ 可能对兼容的中转站也用 raw HTTP（性能略差）

#### 方案 3: 自动检测模式
```python
# 先尝试 SDK，失败后自动降级到 raw HTTP
try:
    stream = client.messages.stream(...)
except (AuthenticationError, PermissionError):
    # 降级到 raw HTTP
    use_raw_http = True
```

**优点**:
- ✅ 自动适配所有中转站
- ✅ 无需维护列表

**缺点**:
- ❌ 首次请求会失败（用户体验差）
- ❌ 增加复杂度

#### 方案 4: 配置标识模式（推荐）
在前端 AI 配置中添加一个选项：

```typescript
interface ModelConfig {
  provider: string;
  baseUrl: string;
  apiKey: string;
  modelName: string;
  // 新增：中转站兼容模式
  compatibilityMode?: "auto" | "sdk" | "raw-http";
}
```

**优点**:
- ✅ 用户可以手动选择
- ✅ 支持所有中转站
- ✅ 可以保存配置

**缺点**:
- ❌ 增加用户配置复杂度

---

## 推荐方案

### 当前方案（黑名单模式）已足够

**理由**:
1. ✅ **覆盖主流中转站**: linkflow.run（SDK）+ ikuncode.cc（raw HTTP）
2. ✅ **代码简单**: 只需检查 URL 中是否包含特定字符串
3. ✅ **不影响未知中转站**: 默认使用 SDK，大部分中转站都兼容
4. ✅ **易于扩展**: 发现新的有问题的中转站时，只需添加一行判断

### 是否需要在 AI 配置中添加标识？

**建议**: **暂时不需要**

**原因**:
1. 当前黑名单模式已经能自动识别 ikuncode.cc
2. 大部分中转站都兼容 SDK，不需要特殊处理
3. 添加配置选项会增加用户困惑（"我应该选哪个？"）
4. 如果未来遇到更多特殊中转站，再考虑添加配置

### 未来扩展建议

如果遇到新的有问题的中转站，只需修改判断逻辑：

```python
# 需要使用 raw HTTP 的中转站列表
RAW_HTTP_PROVIDERS = ["ikuncode.cc", "example.com", "another-provider.com"]

use_raw_http = (
    selected_provider == "custom" and
    vision_service.custom_base_url and
    any(provider in vision_service.custom_base_url.lower()
        for provider in RAW_HTTP_PROVIDERS)
)
```

---

## 总结

### 问题根源
1. ikuncode.cc 阻拦 SDK 的 User-Agent
2. 盲目修改导致破坏了 linkflow.run 的正常流式
3. 没有正确解析 Claude 的 SSE 格式

### 解决方案
1. **精确识别** ikuncode.cc，只对它使用 raw HTTP
2. **使用 aiter_bytes()** 避免缓冲
3. **正确解析 SSE** 格式（跟踪 event 类型）
4. **保持原有逻辑** 不变（linkflow.run 继续用 SDK）

### 兼容性
- ✅ **当前方案已足够**: 黑名单模式覆盖主流中转站
- ✅ **无需添加配置**: 自动识别，用户无感知
- ✅ **易于扩展**: 发现新问题中转站时，添加到列表即可

### 关键经验
1. **不要过度泛化**: 不要对所有情况都用特殊处理
2. **先测试再修改**: 先验证中转站是否真的支持流式
3. **保持简单**: 能用简单方案就不要复杂化
4. **不破坏原有功能**: 修改时确保不影响已有的正常功能

---

## 相关文件

- **后端**: `backend/app/api/chat_generator.py` (line 122-244)
- **测试**: `test_ikuncode_real_streaming.py`
- **分析**: `linkflow_vs_ikuncode_analysis.md`
