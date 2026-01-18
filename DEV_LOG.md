# 开发日志 (Development Log)

本文件记录 SmartArchitect 项目的重要开发修改和待验证事项。

---

## 2026-01-18 - Excalidraw 流式打印功能实现

### 问题描述
用户反馈 Excalidraw 生成功能缺少流式打印效果，导致：
1. 前端没有实时反馈，用户只看到转圈圈，不知道后台在处理
2. 聊天框没有像 FlowCanvas 那样的打字机效果（typewriter effect）
3. 生成过程中没有进度提示

### 已完成的修改

#### 1. 前端 - 添加流式打印和打字机效果
**文件**: `frontend/lib/store/useArchitectStore.ts` (lines 667-827)

**主要改动**:
- 添加 `updateChatStatus(message)` 函数：
  - 功能：替换最后一条 assistant 消息，实现打字机效果
  - 参考了 FlowCanvas 的实现模式（lines 445-590）

- 添加 `updateJsonLog(token)` 函数：
  - 功能：在日志面板中累积显示 JSON 生成内容
  - 显示格式：`[生成中] {jsonBuffer}`

- 添加进度状态更新：
  - 初始化：🎨 正在生成 Excalidraw 场景...
  - 提示词构建：📝 正在构建提示词...
  - AI 绘制：🤖 AI 正在绘制场景...\n已生成 X tokens
  - 完成：✅ Excalidraw 场景生成完成\n- 元素数量: X\n- 生成方式: AI 智能生成

- Token 更新频率：每 50 个 token 更新一次聊天状态

#### 2. 前端 - 添加调试日志
**文件**: `frontend/lib/store/useArchitectStore.ts` (lines 746-760)

**主要改动**:
- 添加原始 chunk 数据日志：`[Excalidraw STREAM DEBUG] Raw chunk`
- 添加解析后 parts 计数日志：`[Excalidraw STREAM DEBUG] Parts count`
- 添加内容处理日志：`[Excalidraw STREAM DEBUG] Processing content`

**目的**: 调试流式数据接收和解析问题

#### 3. 后端 - 恢复生成质量参数
**文件**: `backend/app/services/excalidraw_generator.py` (lines 125-172)

**主要改动**:
- 恢复元素数量：从 3-5 个恢复到 **8-15 个元素**
- 恢复详细提示词：包含 rectangles, ellipses, arrows, lines, text 等多种元素类型
- 保留严格的 JSON 格式要求：无 markdown fence、无尾随逗号

**原因**: 用户反馈生成质量变差，之前为了避免 JSON 解析错误而过度简化了

#### 4. 后端 - 优化 AI 生成参数
**文件**: `backend/app/services/ai_vision.py` (lines 757-763)

**主要改动**:
- `max_tokens`: 4096 → **8192** (确保 JSON 能完整生成)
- `temperature`: 0.2 → **0.1** (降低温度，更确定性的输出)

**目的**: 提高生成质量和一致性，减少 JSON 解析失败

### 后端流式端点实现（已存在）
**文件**: `backend/app/api/excalidraw.py` (lines 58-194)

后端已实现 `/api/excalidraw/generate-stream` 端点，支持 SSE 流式输出：
- `[START]` - 开始生成
- `[CALL]` - 调用 AI
- `[TOKEN] <text>` - 每个 token 内容
- `[RESULT] {...}` - 最终结果（JSON）
- `[END]` - 完成
- `[ERROR]` - 错误信息

流式生成通过 `vision_service.generate_with_stream(prompt)` 实现，支持 siliconflow、openai、custom 等 provider。

### 待验证事项

#### 重要：流式打印未生效问题

**现象**:
从前端日志来看：
```
[Excalidraw] Starting generation for: github的热力图提交画个出来
[Excalidraw] Parsed RESULT: {hasScene: true, elementsCount: 14, success: true}
[Excalidraw] Setting scene with 14 elements
```

前端**直接收到 RESULT**，没有看到 `[START]`、`[CALL]`、`[TOKEN]` 的日志输出。

**可能原因**:
1. **后端缓冲问题**: 服务器或中间件可能缓冲了流式输出，导致所有数据一次性发送
2. **Provider 不支持流式**: 当前使用的 provider 可能不支持真正的流式输出
3. **异常降级**: 代码可能走了非流式的降级路径（excalidraw.py line 143-164 的异常处理）

**需要验证**:
1. 重启前端后，再次测试 Excalidraw 生成
2. 查看前端控制台的 `[Excalidraw STREAM DEBUG]` 日志：
   - Raw chunk 是否包含 `[START]`、`[CALL]`、`[TOKEN]` 等标记
   - Parts count 是多次小批量还是一次性大批量
3. 查看后端控制台日志：
   - 是否有 `[EXCALIDRAW-STREAM]` 开头的日志
   - 是否有 `Streaming completed` 或 `Stream iteration completed` 日志
   - 是否有异常或降级提示

**测试步骤**:
```bash
# 1. 重启前端
cd frontend
npm run dev

# 2. 在浏览器中打开开发者工具 Console
# 3. 输入测试提示词，例如: "画一个用户登录流程图"
# 4. 记录所有 [Excalidraw STREAM DEBUG] 日志
# 5. 记录后端控制台所有 [EXCALIDRAW-STREAM] 相关日志
```

#### 其他待验证
1. **打字机效果**: 聊天框是否按预期更新状态消息（而非每次追加新消息）
2. **JSON 显示**: 日志面板是否显示 `[生成中]` 的 JSON 累积内容
3. **生成质量**: 8-15 个元素的生成效果是否满足用户预期
4. **Canvas 显示**: Excalidraw 画布是否正确显示生成的图形（scrollToContent 是否生效）

### 调试建议

如果流式打印仍未生效：

1. **检查 Provider 配置**: 确认使用的是 siliconflow/openai/custom，而非 gemini（gemini 不支持此流式实现）

2. **检查后端日志**: 查找是否有以下关键日志：
   ```
   [EXCALIDRAW-STREAM] Starting generation
   [EXCALIDRAW-STREAM] Starting AI streaming...
   [STREAM] Initiating stream with base_url=...
   [STREAM] Stream created successfully, starting to iterate chunks
   ```

3. **强制刷新**: 浏览器硬刷新（Ctrl+Shift+R）清除缓存

4. **网络检查**: 在浏览器 Network 面板查看 `/api/excalidraw/generate-stream` 请求：
   - Response 类型是否为 `text/event-stream`
   - 是否有 `Transfer-Encoding: chunked` header
   - 响应是否是分块接收（多个小块）还是一次性接收

### 关键代码位置

- **前端流式处理**: `frontend/lib/store/useArchitectStore.ts:667-827`
- **后端流式端点**: `backend/app/api/excalidraw.py:58-194`
- **AI 流式生成**: `backend/app/services/ai_vision.py:609-783` (generate_with_stream 方法)
- **Excalidraw 提示词**: `backend/app/services/excalidraw_generator.py:125-172`
- **Canvas 更新逻辑**: `frontend/components/ExcalidrawBoard.tsx:20-60`

### 参考实现

FlowCanvas 的流式打印实现作为参考：
- **文件**: `frontend/lib/store/useArchitectStore.ts:445-590`
- **关键模式**: `updateChatStatus()` 替换最后一条消息，`updateJsonLog()` 累积 JSON

---

## 下次开发要点

1. 首先验证流式打印功能是否正常工作
2. 根据调试日志定位问题（前端接收 vs 后端发送）
3. 如果后端未发送流式数据，检查 provider 配置和异常降级逻辑
4. 如果前端未正确解析，检查 SSE 数据格式和分块逻辑

---

## 环境信息

- **开发日期**: 2026-01-18
- **开发环境**: 本地（用户明天将在公司环境继续开发）
- **前端端口**: http://localhost:3000
- **后端端口**: http://localhost:8000
- **当前分支**: dev
- **修改文件数**: 3 个文件被修改

## Git 状态（修改前）
```
M backend/app/api/chat_generator.py
?? temp_append.txt
?? test_stream.py
```

## Git 状态（修改后，待提交）
```
M frontend/lib/store/useArchitectStore.ts
M backend/app/services/excalidraw_generator.py
M backend/app/services/ai_vision.py
```
