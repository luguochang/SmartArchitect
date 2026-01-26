# 前端流式输出调试指南

## 问题确认

后端测试结果：**✅ 后端流式输出正常**
- Token每隔20-30毫秒实时发送
- 不存在批量缓冲问题

## 前端调试步骤

### 1. 刷新前端页面
```
按 Ctrl+Shift+R (硬刷新，清除缓存)
```

### 2. 打开浏览器开发者工具
```
按 F12
切换到 Console 标签
```

### 3. 触发生成
```
输入："生成一个简单的开始到结束的流程"
点击生成按钮
```

### 4. 观察Console日志

**如果是实时流式，应该看到**：
```
[STREAM] 开始读取流...
[STREAM] 等待读取chunk 1...
[STREAM] 收到chunk 1, size: 35, done: false        <-- 立即到达
[STREAM LOG] [START] building prompt
[STREAM] 等待读取chunk 2...
[STREAM] 收到chunk 2, size: 42, done: false        <-- 0.5秒后到达
[STREAM LOG] [CALL] contacting provider...
[STREAM] 等待读取chunk 3...
[STREAM] 收到chunk 3, size: 18, done: false        <-- 立即到达
[STREAM LOG] [TOKEN] {
[STREAM ASSISTANT] {
[STREAM] 等待读取chunk 4...
[STREAM] 收到chunk 4, size: 20, done: false        <-- 0.02秒后到达
[STREAM LOG] [TOKEN]
[STREAM ASSISTANT] {
... (持续输出)
```

**如果有缓冲问题，会看到**：
```
[STREAM] 开始读取流...
[STREAM] 等待读取chunk 1...
(长时间等待 10-15秒)                               <-- 问题！
[STREAM] 收到chunk 1, size: 50000, done: false     <-- 一次性收到大量数据
[STREAM LOG] [START] building prompt
[STREAM LOG] [CALL] contacting provider...
[STREAM LOG] [TOKEN] {
[STREAM LOG] [TOKEN]
... (快速批量输出)
```

## 判断标准

### ✅ 正常流式（期望）
- `等待读取chunk` 和 `收到chunk` 交替快速出现
- 每个chunk size较小（10-100 bytes）
- 日志实时滚动，间隔短

### ❌ 批量缓冲（问题）
- `等待读取chunk 1` 后长时间无输出
- 然后突然收到一个巨大chunk (几千到几万bytes)
- 或收到很多个chunk但间隔为0ms

## 可能的问题和解决方案

### 问题1：浏览器缓冲响应

**现象**：第一个chunk延迟10-15秒才到达

**原因**：某些浏览器会缓冲SSE响应

**解决方案**：修改后端响应头
```python
headers={
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "X-Accel-Buffering": "no",
    "Connection": "keep-alive",
}
```

### 问题2：Fetch API配置问题

**现象**：所有chunk一次性到达

**原因**：fetch没有正确设置流式模式

**解决方案**：使用ReadableStream API
```typescript
const response = await fetch(url, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Accept": "text/event-stream",
    "Cache-Control": "no-cache"  // 添加
  },
  body: JSON.stringify(body),
});
```

### 问题3：代理服务器缓冲

**现象**：开发环境正常，部署后批量

**原因**：Nginx/Apache等代理缓冲响应

**解决方案**：配置代理
```nginx
proxy_buffering off;
proxy_cache off;
```

## 测试完成后

**请将Console日志的前50行发给我**，格式示例：
```
[STREAM] 开始读取流...
[STREAM] 等待读取chunk 1...
[STREAM] 收到chunk 1, size: 35, done: false
[STREAM LOG] [START] building prompt
...
```

我会根据日志判断问题并修复。

## 预期结果

如果一切正常，你应该：
1. **点击生成后立即**看到 [START] 消息（而不是转圈圈）
2. **0.5秒左右**看到 [CALL] 消息
3. **之后每隔几十毫秒**看到新的 [TOKEN] 消息
4. **页面上的日志区域实时滚动**，像打字机一样
5. **不再有"转圈圈后批量显示"的问题**
