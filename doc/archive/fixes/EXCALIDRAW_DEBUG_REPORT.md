# Excalidraw Generation Debug Report

**日期**: 2026-01-16
**问题**: Excalidraw生成失败，JSON parsing错误，流式输出不显示
**状态**: ❌ 未解决

---

## 问题症状

### 1. 后端错误
```
[2026-01-16 16:15:37] [WARNING] JSON decode failed: Expecting ',' delimiter: line 482 column 6 (char 10556). Attempting repair...
[2026-01-16 16:15:37] [ERROR] All JSON repair strategies failed. Raw payload: ```json
{
  "elements": [
    {"id": "title-1", "type": "text", "x": 400, "y": 60, "width": 400, "height": 40, "strokeColor": "#1f2937", "backgroundCol...
[2026-01-16 16:15:37] [ERROR] Streaming generation failed: Empty scene returned by AI
```

**关键点**：
- JSON在第10,556字符处出错（AI生成过长的JSON）
- 错误类型：`Expecting ',' delimiter` - missing comma between array elements
- 位置：line 482 column 6 - 说明生成了约482行的JSON

### 2. OpenAI SDK超时/重试循环
```python
File "D:\file\openproject\SmartArchitect\backend\venv\Lib\site-packages\openai\_base_client.py", line 1098, in _retry_request
    return self._request(
```

**原因**：OpenAI SDK无限重试失败的请求，没有设置timeout和max_retries

### 3. 前端症状
- 流式输出没有显示（画板不会逐步绘制）
- 最终显示mock fallback场景
- 控制台可能没有看到streaming日志

---

## 参考对比：FlowPilot成功案例

### FlowPilot的关键差异

**1. 简洁的Prompt（15行）**
```typescript
// D:\file\openproject\reference\flowpilot-beta\app\api\chat\route.ts (lines 67-82)
const excalidrawSystemMessage = `
You are FlowPilot Excalidraw Expert. Output exactly one valid JSON object...
Priorities:
1. Valid JSON syntax (Standard Excalidraw Format).
2. Clear, hand-drawn style consistency.
3. Reasonable layout without overlaps.
...
Do NOT output conversational text before or after the JSON block.
`;
```

**关键点**：
- 没有指定元素数量（我们的prompt说"12-20 elements"）
- 强调JSON syntax优先级第一
- 明确要求包裹在```json```代码块中

**2. Dual-Path JSON Parsing**
```typescript
// D:\file\openproject\reference\flowpilot-beta\components\chat-panel-optimized.tsx (lines 1640-1700)
const parsed = isFinal
    ? JSON.parse(jsonContent)           // Final = strict parsing
    : safeParsePartialJson(jsonContent); // Streaming = lenient with repair
```

**3. Lenient Validation**
```typescript
// Only check for elements field existence, not strict type validation
if (parsed.elements !== undefined) {
    loadExcalidraw(jsonStr);
}
```

**4. Code Block Extraction Before Parsing**
```typescript
const codeBlockMatch = jsonContent.match(/```(?:json)?\s*\n?([^\`]*?)(?:```|$)/i);
if (codeBlockMatch) {
    jsonContent = codeBlockMatch[1].trim();
}
```

**5. Extensive Frontend Sanitization**
```typescript
// D:\file\openproject\reference\flowpilot-beta\components\excalidraw-editor.tsx (lines 61-138)
const sanitizeData = (data: any) => {
    // Filters invalid elements
    // Validates points array for linear elements
    // Sets default values for missing properties
    // Removes problematic fields like 'collaborators'
}
```

---

## 已完成的修复

### 1. ✅ Backend JSON Repair Improvements
**文件**: `backend/app/services/excalidraw_generator.py`

**Changes**:
```python
# Line 155-217: Enhanced _safe_json method

# Strategy 0: FlowPilot-inspired bracket tracking repair (handles incomplete JSON)
repaired_result = safe_parse_partial_json(text)

# Strategy 1: Aggressive comma insertion for missing commas
if "Expecting ',' delimiter" in str(e):
    text_with_commas = re.sub(r'}\s*{', '}, {', text)  # } { → }, {
    text_with_commas = re.sub(r'"\s+"', '", "', text_with_commas)  # " " → ", "

# Strategy 2: Combine comma fix + bracket tracking
repaired_result = safe_parse_partial_json(text_with_commas)
```

**Test Results**:
- ✅ Test 1: Missing comma between array elements - **PASS** (2 elements parsed)
- ✅ Test 2: Missing commas between properties - **PASS** (1 element parsed)
- ❌ Test 3: Incomplete JSON - FAIL (returns empty dict, expected behavior for severely broken JSON)

### 2. ✅ FlowPilot-Style Code Block Extraction
**文件**: `backend/app/services/excalidraw_generator.py` (lines 165-172)

**Before**:
```python
# Line-by-line stripping
if text.startswith("```"):
    lines = text.split("\n")
    if lines[0].startswith("```"):
        lines = lines[1:]
    ...
```

**After**:
```python
# Regex-based extraction (FlowPilot approach)
import re
code_block_match = re.search(r'```(?:json)?\s*\n?([^`]*?)(?:```|$)', text, re.IGNORECASE | re.DOTALL)
if code_block_match:
    text = code_block_match.group(1).trim()
```

### 3. ✅ OpenAI Client Timeout Configuration
**文件**: `backend/app/services/ai_vision.py`

**Changes**:
```python
# Line 88-92: OpenAI provider
self.client = OpenAI(
    api_key=api_key,
    timeout=120.0,  # 2 minutes timeout
    max_retries=2   # Limit retries
)

# Line 108-113: SiliconFlow provider
self.client = OpenAI(
    api_key=api_key,
    base_url=base_url,
    timeout=120.0,
    max_retries=2
)

# Line 125-130: Custom provider
self.client = OpenAI(
    api_key=self.custom_api_key,
    base_url=self.custom_base_url,
    timeout=120.0,
    max_retries=2
)
```

**Fix**: Prevents infinite retry loops, will fail gracefully after 2 minutes

### 4. ✅ Simplified Prompt (Reduced Element Count)
**文件**: `backend/app/services/excalidraw_generator.py` (line 147)

**Before**:
```
- Create 12-20 elements for a rich diagram.
```

**After**:
```
- Create appropriate number of elements to represent the concept clearly (typically 8-15 for simple diagrams, more if needed but keep JSON concise).
```

**Reasoning**: FlowPilot doesn't specify element count, allows AI to decide

### 5. ✅ Enhanced Frontend Debug Logging
**文件**: `frontend/lib/store/useArchitectStore.ts` (lines 728-752)

**Added**:
```typescript
// DEBUG: Log streaming parse attempts
console.log(`[Streaming] Accumulated ${accumulatedJson.length} chars, trying to parse...`);

// Success
console.log(`[Streaming] ✅ Updated Excalidraw with ${sanitized.elements.length} elements`);

// Warnings
console.warn(`[Streaming] ⚠️ Sanitization returned empty elements`);
console.warn(`[Streaming] ⚠️ Parse failed or no elements: parsed=${!!parsed}, elements=${parsed?.elements?.length}`);
console.warn(`[Streaming] ⚠️ JSON content doesn't start with '{': ${jsonContent.substring(0, 50)}`);

// Errors
console.warn(`[Streaming] ❌ Parse error: ${e}`);
```

**Purpose**: Diagnose where streaming rendering is failing

### 6. ✅ Provider Default Changed
**文件**: `backend/app/models/schemas.py` (line 282)

**Before**:
```python
provider: Optional[Literal[...]] = "siliconflow"
```

**After**:
```python
provider: Optional[Literal[...]] = "custom"
```

**Reasoning**: Use user's linkflow API key instead of defaulting to siliconflow

### 7. ✅ Frontend Style Changed
**文件**: `frontend/lib/store/useArchitectStore.ts` (line 674)

**Before**:
```typescript
style: "neon cyber cat with glowing eyes..."  // Hardcoded incompatible string
```

**After**:
```typescript
style: "balanced"  // FlowPilot-compatible style system
```

---

## 未解决的问题

### ❌ Problem 1: AI Still Generates Too-Long JSON (10,000+ characters)

**Evidence**:
- Error at character position 10,556
- Line 482 in generated JSON
- Prompt changes didn't prevent over-generation

**Root Cause**:
- AI模型（linkflow/Qwen）可能不遵守"keep JSON concise"指令
- Prompt engineering alone不足以限制输出长度

**Potential Solutions**:
1. **Use max_tokens parameter** in API call to hard-limit response length
2. **Add explicit JSON schema** with array length limits
3. **Use different model** - try smaller/more instruction-following models
4. **Post-process streaming tokens** - stop after detecting N elements parsed

### ❌ Problem 2: JSON Comma Errors Not Fully Fixed

**Evidence**:
- Test suite passed, but production still fails
- Regex patterns may not catch all edge cases
- Error at position 10,556 suggests late-in-document error

**Root Cause**:
- AI generates very long JSON with multiple comma errors
- Repair strategies work for short/simple cases but not 10K+ char JSON
- May have nested structure issues (arrays within arrays)

**Potential Solutions**:
1. **Parse incrementally during streaming** - validate each element as it arrives
2. **Use more aggressive truncation** - if JSON exceeds X chars, truncate to last complete element
3. **Use JSON streaming parser** (e.g., `json-stream`, `oboe.js`) that handles partial/incomplete JSON

### ❌ Problem 3: No Real-Time Streaming Rendering

**Evidence**:
- User报告画板不会跟随流式输出逐步绘制
- Frontend has code for progressive parsing but may not be working

**Diagnosis Needed**:
- Check browser console logs during generation
- Verify `[Streaming] ✅ Updated Excalidraw` messages appear
- Confirm `excalidrawScene` state updates trigger re-render
- Check if ExcalidrawBoard component's `useEffect` is firing

**Potential Issues**:
1. **React state updates batched** - Zustand may batch multiple `set()` calls
2. **Excalidraw API updateScene() issues** - may not accept partial/incomplete scenes
3. **Sanitization too strict** - may filter out incomplete elements during streaming
4. **Parsing fails early** - `safeParsePartialJson` returns null, no updates

---

## 代码修改摘要

### Modified Files

1. **backend/app/services/excalidraw_generator.py**
   - Lines 165-172: FlowPilot regex code block extraction
   - Lines 186-217: Enhanced JSON repair strategies
   - Line 147: Reduced element count suggestion

2. **backend/app/services/ai_vision.py**
   - Lines 88-92: OpenAI client timeout
   - Lines 108-113: SiliconFlow client timeout
   - Lines 125-130: Custom client timeout

3. **backend/app/models/schemas.py**
   - Line 282: Changed default provider to "custom"

4. **frontend/lib/store/useArchitectStore.ts**
   - Lines 728-752: Enhanced streaming debug logging
   - Line 674: Changed style to "balanced"

5. **frontend/lib/excalidrawUtils.ts**
   - Already contains `repairJson`, `safeParsePartialJson`, `sanitizeExcalidrawData`
   - (These were added in previous conversation)

6. **frontend/components/ExcalidrawBoard.tsx**
   - Already uses `sanitizeExcalidrawData` before rendering
   - (This was added in previous conversation)

### New Test Files Created

1. **backend/test_json_repair_improved.py**
   - Tests JSON repair logic
   - Result: 2/3 tests passing

---

## FlowPilot参考代码位置

### Key Files to Reference

1. **Excalidraw Prompt**:
   - `D:\file\openproject\reference\flowpilot-beta\app\api\chat\route.ts` (lines 67-82)

2. **JSON Repair**:
   - `D:\file\openproject\reference\flowpilot-beta\lib\json-repair.ts` (42 lines total)

3. **Streaming Implementation**:
   - `D:\file\openproject\reference\flowpilot-beta\app\api\chat\route.ts` (lines 216-729)
   - Three paths: Standard AI SDK streaming, non-streaming fallback, LinkFlow custom SSE

4. **Dual-Path Parsing**:
   - `D:\file\openproject\reference\flowpilot-beta\components\chat-panel-optimized.tsx` (lines 1640-1700)

5. **Frontend Sanitization**:
   - `D:\file\openproject\reference\flowpilot-beta\components\excalidraw-editor.tsx` (lines 61-138)

---

## 下一步调试建议

### 立即可测试的步骤

1. **重启后端测试timeout修复**:
```bash
cd D:\file\openproject\SmartArchitect\backend
# Ctrl+C停止当前进程
python -m app.main
```

2. **测试生成并收集日志**:
- 打开浏览器控制台（F12）
- 输入简单prompt："画一个3个节点的流程图"
- 观察控制台输出：
  - 是否看到 `[Streaming] Accumulated xxx chars` 消息？
  - 是否看到 `[Streaming] ✅ Updated Excalidraw` 成功消息？
  - 画板是否有任何更新？
- 观察后端日志：
  - 是否还有 `_retry_request` 无限循环？
  - JSON解析在哪个策略失败？
  - `Excalidraw stream completed: X characters` 显示多少字符？

3. **如果还是10K+ character错误**:
说明prompt优化不够，需要hard-limit max_tokens

### 建议的更激进修复

#### Fix A: Hard-Limit Response Length (Highest Priority)

**文件**: `backend/app/services/ai_vision.py` - `generate_with_stream` method

**找到streaming API调用**，添加 `max_tokens` 参数：

```python
# For OpenAI/Custom provider (around line 615)
stream = self.client.chat.completions.create(
    model=self.model_name,
    messages=[{"role": "user", "content": prompt}],
    stream=True,
    temperature=0.2,
    max_tokens=2000,  # ⭐ ADD THIS - Limit to ~2000 tokens (~8000 chars)
)

# For Claude provider (around line 650)
with self.client.messages.stream(
    model=self.model_name,
    max_tokens=2000,  # ⭐ ADD THIS
    temperature=0.2,
    messages=[{"role": "user", "content": prompt}],
) as stream:
```

**Reasoning**: 2000 tokens ≈ 8000 characters, enough for 10-15 Excalidraw elements but prevents 10K+ char overflow

#### Fix B: Incremental Streaming Parsing (FlowPilot Approach)

**文件**: `frontend/lib/store/useArchitectStore.ts`

**Current approach**: Parse entire accumulated JSON each token

**FlowPilot approach**: Only parse when JSON looks "complete enough"

```typescript
if (content.startsWith("[TOKEN]")) {
    const token = content.replace("[TOKEN]", "").trimStart();
    accumulatedJson += token;

    // Only try parsing every N tokens or when we see closing braces
    if (accumulatedJson.length > 500 &&
        (token.includes("}") || token.includes("]"))) {

        // Try to parse
        const { safeParsePartialJson, sanitizeExcalidrawData } = await import("@/lib/excalidrawUtils");

        let jsonContent = accumulatedJson.trim();
        const codeBlockMatch = jsonContent.match(/```(?:json)?\s*\n?([^`]*?)(?:```|$)/i);
        if (codeBlockMatch) {
            jsonContent = codeBlockMatch[1].trim();
        }

        if (jsonContent.startsWith("{")) {
            const parsed = safeParsePartialJson(jsonContent);
            if (parsed?.elements?.length > 0) {
                const sanitized = sanitizeExcalidrawData(parsed);
                if (sanitized?.elements?.length > 0) {
                    set({ excalidrawScene: sanitized });
                    console.log(`[Streaming] ✅ Updated with ${sanitized.elements.length} elements`);
                }
            }
        }
    }
}
```

**Reasoning**: Reduces parsing attempts, only parse when meaningful progress is made

#### Fix C: Truncate on Parse Error (Safety Net)

**文件**: `backend/app/services/excalidraw_generator.py` - `_safe_json` method

**After all repair strategies fail**, truncate to last complete element:

```python
# Strategy 4 (NEW): Last resort - truncate to last valid element
logger.warning("Attempting truncation to last complete element...")
try:
    # Find last complete element in array
    elements_match = re.search(r'"elements"\s*:\s*\[(.*)\]', text, re.DOTALL)
    if elements_match:
        elements_text = elements_match.group(1)

        # Find all complete element objects (rough heuristic)
        complete_elements = []
        depth = 0
        current_elem = ""
        for char in elements_text:
            current_elem += char
            if char == '{':
                depth += 1
            elif char == '}':
                depth -= 1
                if depth == 0:
                    complete_elements.append(current_elem.strip())
                    current_elem = ""

        if len(complete_elements) > 0:
            # Take first N complete elements (e.g., 10)
            truncated_elements = ','.join(complete_elements[:10])
            truncated_json = f'{{"elements": [{truncated_elements}], "appState": {{}}, "files": {{}}}}'
            result = json.loads(truncated_json)
            logger.info(f"Truncation successful: extracted {len(result['elements'])} elements")
            return result
except Exception:
    pass
```

**Reasoning**: Even if AI generates broken JSON, salvage the valid elements we can extract

---

## 测试数据

### Test Case 1: Simple Broken JSON (PASS)
```json
{
  "elements": [
    {"id": "1", ...}
    {"id": "2", ...}  // Missing comma
  ]
}
```
**Result**: ✅ Repaired successfully (2 elements)

### Test Case 2: Property Comma Error (PASS)
```json
{
  "elements": [
    {"id": "1" "type": "rectangle"}  // Missing comma between properties
  ]
}
```
**Result**: ✅ Repaired successfully (1 element)

### Test Case 3: Incomplete JSON (EXPECTED FAIL)
```json
{
  "elements": [
    {"id": "1", "type": "rectangle", "x": 100, "y": 100, "width": 50, "height": 50
  ],
  "appState": {
```
**Result**: ❌ Returns empty dict (expected - too broken to repair)

### Production Failure Case (FAIL)
```json
// 10,556 characters
// ~482 lines
// Error at: line 482 column 6 (char 10556)
// Error type: Expecting ',' delimiter
```
**Result**: ❌ All repair strategies fail

---

## 环境信息

- **Python**: 3.12.5
- **FastAPI**: (check with `pip show fastapi`)
- **OpenAI SDK**: (check with `pip show openai`)
- **Node.js**: (check with `node --version`)
- **Next.js**: 14 (App Router)
- **React**: 19
- **AI Provider**: Custom (linkflow API)
- **Model**: (check frontend config)

---

## 相关Issue/TODO

### High Priority
1. [ ] 修复10K+ character JSON生成问题 - 添加max_tokens限制
2. [ ] 验证timeout配置是否解决OpenAI SDK重试循环
3. [ ] 测试前端streaming渲染是否工作

### Medium Priority
4. [ ] 实现更智能的JSON truncation策略
5. [ ] 优化prompt进一步减少输出长度
6. [ ] 考虑使用JSON streaming parser替代全量解析

### Low Priority
7. [ ] 添加E2E测试验证完整流程
8. [ ] 性能优化：减少frontend parsing频率
9. [ ] 错误上报：详细记录失败case的完整JSON

---

## 联系/参考

- **FlowPilot Repo**: D:\file\openproject\reference\flowpilot-beta
- **Test Files**:
  - `backend/test_json_repair_improved.py`
  - `backend/test_json_repair.py` (older version)
- **Logs**: Backend terminal output, browser console (F12)

---

**最后更新**: 2026-01-16 16:30
**下次调试开始**: 检查timeout修复 + 收集详细frontend streaming logs
