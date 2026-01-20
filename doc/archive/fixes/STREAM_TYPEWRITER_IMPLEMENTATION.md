# 流式输出打字机效果实现记录

## 实现日期
2026-01-15

## 问题背景

### 原始问题
1. **浏览器缓冲问题**：前端收到的流式响应被浏览器缓冲成一个大chunk（8KB+），导致无法实时显示
2. **日志显示混乱**：每个token字符都显示为单独一行，导致日志区域有400+行重复内容
3. **内容重复**：聊天区域和日志区域都显示完整JSON，造成冗余

### 解决方案
- **后端**：增强响应头防止浏览器/代理缓冲
- **前端**：优化日志显示逻辑，实现方案C（日志区域打字机效果）

---

## 已完成的修改

### 1. 后端响应头优化

**文件**：`backend/app/api/chat_generator.py`

**位置**：Lines 181-191

**修改内容**：
```python
return StreamingResponse(
    event_stream(),
    media_type="text/event-stream",
    headers={
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # 禁用nginx缓冲
        "Content-Encoding": "none",  # 防止压缩缓冲
        "Transfer-Encoding": "chunked",  # 强制分块传输
    },
)
```

**效果**：
- ✅ 后端流式输出正常（已验证，token每20-30ms发送）
- ✅ 前端接收到小chunk（10-100 bytes），不再是8KB大chunk

---

### 2. 前端流式处理逻辑重构

**文件**：`frontend/lib/store/useArchitectStore.ts`

**位置**：Lines 381-472

#### 2.1 日志处理函数

**修改前**：所有内容（包括每个token）都加到日志数组
```typescript
pushLog(content);  // 所有内容都记录
if (content.startsWith("[TOKEN]")) {
  appendAssistant(content.replace("[TOKEN]", "").trimStart());
}
```

**修改后**：
```typescript
// 1. 只记录关键事件
const pushLog = (line: string) => {
  logs.push(line);
  console.log(`[STREAM LOG] ${line.substring(0, 50)}`);
  set({ generationLogs: [...logs] });
};

// 2. 聊天状态更新
const updateChatStatus = (message: string) => {
  statusMessage = message;
  set((state) => {
    const newHistory = [...state.chatHistory];
    const last = newHistory[newHistory.length - 1];
    if (last && last.role === "assistant") {
      newHistory[newHistory.length - 1] = { role: "assistant", content: statusMessage };
    } else {
      newHistory.push({ role: "assistant", content: statusMessage });
    }
    return { chatHistory: newHistory };
  });
};

// 3. JSON打字机效果（在日志区域）
let jsonBuffer = "";
const updateJsonLog = (token: string) => {
  jsonBuffer += token;
  const generatingIndex = logs.findIndex(log => log.startsWith("[生成中]"));
  if (generatingIndex !== -1) {
    logs[generatingIndex] = `[生成中] ${jsonBuffer}`;
  } else {
    logs.push(`[生成中] ${jsonBuffer}`);
  }
  set({ generationLogs: [...logs] });
};
```

#### 2.2 事件处理逻辑

**修改后**（Lines 440-472）：
```typescript
if (content.startsWith("[START]")) {
  pushLog(content);
  updateChatStatus("📝 正在构建提示词...");
} else if (content.startsWith("[CALL]")) {
  pushLog(content);
  updateChatStatus("🤖 AI 正在思考...");
  isGenerating = true;
} else if (content.startsWith("[RESULT]")) {
  // 移除"[生成中]"条目
  const generatingIndex = logs.findIndex(log => log.startsWith("[生成中]"));
  if (generatingIndex !== -1) {
    logs.splice(generatingIndex, 1);
  }
  pushLog(content);
  const match = content.match(/nodes=(\d+), edges=(\d+)/);
  if (match) {
    const [_, nodeCount, edgeCount] = match;
    updateChatStatus(`✅ 流程图生成完成\n- 节点数: ${nodeCount}\n- 连线数: ${edgeCount}`);
  }
} else if (content.startsWith("[END]")) {
  pushLog(content);
} else if (content.startsWith("[ERROR]")) {
  pushLog(content);
  updateChatStatus(`❌ 生成失败: ${content.replace("[ERROR]", "").trim()}`);
}

// Token累积（打字机效果）
if (content.startsWith("[TOKEN]")) {
  const token = content.replace("[TOKEN]", "").trimStart();
  updateJsonLog(token);
  continue;
}
```

---

### 3. 前端UI样式优化

**文件**：`frontend/components/AiControlPanel.tsx`

**位置**：Lines 263-279

**修改内容**：
```tsx
{generationLogs.map((log, idx) => (
  <div
    key={`log-${idx}`}
    className={`rounded-lg bg-gradient-to-br from-emerald-50 to-teal-50 px-3 py-2 text-xs font-mono text-emerald-900 dark:from-emerald-900/30 dark:to-teal-900/30 dark:text-emerald-50 ${
      log.startsWith("[生成中]")
        ? "overflow-x-auto whitespace-nowrap max-w-full"
        : "whitespace-pre-wrap break-words"
    }`}
  >
    {log}
  </div>
))}
```

**效果**：
- `[生成中]` 条目：横向滚动，不换行
- 其他日志：正常换行显示

---

## 实现效果

### 页面显示效果

#### 日志区域（绿色框）
```
[START] building prompt
[CALL] contacting provider...
[生成中] {"nodes":[{"id":"start","type":"start","position":{"x":250,"y":100},"data":{"label":"开始"}},{"id":"step1"...
         ↑↑↑ 这一行实时增长，横向滚动，打字机效果
[RESULT] nodes=7, edges=7
[END] done
```

#### 聊天区域（大对话框）
```
You: 生成一天的约会流程