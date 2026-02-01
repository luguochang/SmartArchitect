# linkflow.run vs ikuncode.cc 深度分析

## 当前状态

### ✅ linkflow.run - 正常工作
- **Base URL**: `https://www.linkflow.run/v1`
- **流式**: ✅ 实时流式打印正常
- **使用方式**: Anthropic SDK
- **代码路径**: 标准 SDK streaming

### ❌ ikuncode.cc - 被阻拦
- **Base URL**: `https://api.ikuncode.cc`
- **错误**: `Your request was blocked`
- **问题**: SDK 的 User-Agent 被阻拦

## 测试记录

### 测试 1: API 格式测试（test_ikuncode_simple.py）

| 方法 | 端点 | 结果 |
|------|------|------|
| Anthropic SDK | `/v1/messages` | ❌ `Your request was blocked` |
| OpenAI SDK | `/v1/chat/completions` | ❌ `Your request was blocked` |
| Raw HTTP (httpx) | `/v1/messages` | ✅ 成功 |

**结论**: ikuncode.cc 阻拦 SDK 的 User-Agent，但允许 raw HTTP

### 测试 2: 流式响应格式（test_claude_sse_format.py）

```
[Line 1] 'event: message_start'
[Line 2] 'data: {"type":"message_start",...}'
[Line 9] 'event: content_block_delta'
[Line 10] 'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Hello to"}}'
[Line 13] 'event: content_block_delta'
[Line 14] 'data: {"type":"content_block_delta","delta":{"type":"text_delta","text":" you!"}}'
```

**结论**: Claude 使用 `event:` 和 `data:` 分开的 SSE 格式

### 测试 3: 流式时序测试（test_backend_streaming_timing.py）

**问题发现**: 所有 90 个 token 在同一时刻到达（间隔 0.000s）

```
[7.36s] TOKEN 1
[7.36s] TOKEN 2
[7.36s] TOKEN 3
...
[7.36s] TOKEN 90
```

**原因**: httpx 的 `aiter_lines()` 会缓冲整个响应

## 核心差异分析

### linkflow.run 为什么能正常工作？

```python
# 使用 Anthropic SDK
stream = vision_service.client.messages.stream(
    model=vision_service.model_name,
    messages=[{"role": "user", "content": prompt}],
    max_tokens=4096,
    temperature=0.2,
)

# Anthropic SDK 内部处理了流式响应
with stream as s:
    for text in s.text_stream:
        yield f"data: [TOKEN] {text}\n\n"
```

**关键点**:
1. ✅ linkflow.run **不阻拦** Anthropic SDK 的 User-Agent
2. ✅ Anthropic SDK 内部正确处理了 SSE 流式响应
3. ✅ `text_stream` 是实时的，不缓冲

### ikuncode.cc 为什么被阻拦？

```python
# 同样使用 Anthropic SDK
stream = vision_service.client.messages.stream(...)
```

**问题**:
1. ❌ ikuncode.cc **阻拦** Anthropic SDK 的 User-Agent
2. ❌ 返回 `Your request was blocked`

## 我的修改历史和失败原因

### 尝试 1: 使用 raw HTTP + aiter_lines()
```python
async for line in response.aiter_lines():
    if line.startswith("data: "):
        data = json.loads(line[6:])
        if data.get("type") == "content_block_delta":
            yield text
```

**失败原因**:
- ❌ `aiter_lines()` 会缓冲整个响应
- ❌ 所有 token 同时到达，不是实时的

### 尝试 2: 使用 raw HTTP + aiter_bytes()
```python
async for chunk in response.aiter_bytes():
    buffer += chunk.decode('utf-8')
    while '\n' in buffer:
        line, buffer = buffer.split('\n', 1)
        # 解析 SSE...
```

**失败原因**:
- ❌ 没有正确解析 `event:` 和 `data:` 的配对关系
- ❌ 可能还是有缓冲问题

### 尝试 3: 对所有 custom + claude 使用特殊处理

**失败原因**:
- ❌ 把 linkflow.run 也破坏了
- ❌ linkflow.run 不需要特殊处理

### 尝试 4: 只对 ikuncode.cc 使用特殊处理

**当前状态**:
- ✅ linkflow.run 恢复正常
- ❌ ikuncode.cc 还是假流式（如果有的话）

## 关键问题

### 问题 1: 为什么 ikuncode.cc 的 raw HTTP 是假流式？

**可能原因**:
1. **上游问题**: ikuncode.cc 本身不支持真正的流式？
2. **缓冲问题**: httpx 的 `aiter_bytes()` 还是有缓冲？
3. **解析问题**: SSE 解析逻辑有问题？

### 问题 2: linkflow.run 的 Anthropic SDK 为什么是真流式？

**原因**:
- Anthropic SDK 内部使用了正确的流式处理
- SDK 可能用了 `httpx-sse` 或类似库
- SDK 处理了所有 SSE 细节

## 解决方案思路

### 方案 A: 模仿 Anthropic SDK 的实现

查看 Anthropic SDK 源码，看它是如何处理流式的：
```python
# anthropic/lib/streaming/_messages.py
class MessageStream:
    def __iter__(self):
        # SDK 内部如何处理流式？
```

### 方案 B: 使用 httpx-sse 库

```python
from httpx_sse import aconnect_sse

async with aconnect_sse(client, "POST", url, json=data) as event_source:
    async for sse in event_source.aiter_sse():
        if sse.event == "content_block_delta":
            yield sse.data
```

### 方案 C: 直接测试 ikuncode.cc 是否支持真流式

写一个简单的测试，直接用 raw HTTP 请求 ikuncode.cc，看是否真的实时返回：

```python
async with httpx.AsyncClient() as client:
    async with client.stream("POST", url, json=data) as response:
        start = time.time()
        async for chunk in response.aiter_bytes():
            print(f"[{time.time() - start:.2f}s] Received {len(chunk)} bytes")
```

## 下一步行动

1. **先测试**: 验证 ikuncode.cc 是否真的支持实时流式
2. **如果支持**: 找到正确的解析方式
3. **如果不支持**: 告知用户 ikuncode.cc 不支持真流式

## 讨论问题

1. **你确认 ikuncode.cc 官方支持流式吗？** 还是它只是把完整响应包装成 SSE 格式？
2. **你之前用其他工具测试过 ikuncode.cc 的流式吗？** 比如 curl 或 Postman？
3. **linkflow.run 和 ikuncode.cc 的价格/速度差异大吗？** 是否值得花时间兼容 ikuncode？

---

**总结**: 我之前的问题是没有搞清楚 linkflow 和 ikuncode 的差异就盲目修改，导致把正常的也破坏了。现在需要先彻底测试清楚 ikuncode.cc 是否真的支持实时流式。
