# Excalidraw修复状态摘要

## 当前状态：❌ 未解决

### 核心问题
1. **AI生成JSON过长**（10,556字符，482行）- 超出parser处理能力
2. **Missing comma错误**在10K+ JSON中repair失败
3. **前端streaming渲染不工作** - 画板不跟随流式输出绘制

---

## 已完成的7个修复

✅ **Fix 1**: Backend JSON repair（3种策略：bracket tracking + regex comma fix + 组合）
✅ **Fix 2**: FlowPilot风格的regex代码块提取
✅ **Fix 3**: OpenAI client timeout（120s + max_retries=2）- 修复无限重试
✅ **Fix 4**: Prompt优化（降低到8-15元素）
✅ **Fix 5**: Frontend debug日志增强
✅ **Fix 6**: Provider默认改为"custom"
✅ **Fix 7**: Style改为"balanced"

---

## 3个未解决问题

❌ **Problem 1: AI Still Generates 10K+ Chars**
- Root Cause: Prompt alone不足以限制输出
- Solution: 需要添加 `max_tokens=2000` 参数hard-limit

❌ **Problem 2: JSON Repair Not Working for Long JSON**
- Root Cause: 10K+ JSON中多个comma错误，repair策略不够robust
- Solution: 需要truncation策略或incremental parsing

❌ **Problem 3: No Progressive Rendering**
- Root Cause: 未知（需要测试收集browser console logs）
- Solution: 检查frontend streaming logic是否真正触发re-render

---

## 最高优先级建议：添加max_tokens限制

### 在哪里改
**文件**: `backend/app/services/ai_vision.py` - `generate_with_stream` method

### OpenAI/Custom Provider (约line 615)
```python
stream = self.client.chat.completions.create(
    model=self.model_name,
    messages=[{"role": "user", "content": prompt}],
    stream=True,
    temperature=0.2,
    max_tokens=2000,  # ⭐ ADD THIS LINE
)
```

### Claude Provider (约line 650)
```python
with self.client.messages.stream(
    model=self.model_name,
    max_tokens=2000,  # ⭐ ADD THIS LINE
    temperature=0.2,
    messages=[{"role": "user", "content": prompt}],
) as stream:
```

**原理**: 2000 tokens ≈ 8000 chars，足够10-15个Excalidraw元素，防止10K+溢出

---

## 下次调试清单

### 1. 测试Timeout修复
```bash
# 重启backend
cd D:\file\openproject\SmartArchitect\backend
python -m app.main
```
- [ ] 确认没有OpenAI SDK `_retry_request` 无限循环
- [ ] 检查是否120秒后正常timeout

### 2. 收集Frontend Logs
打开浏览器控制台（F12），测试生成，检查：
- [ ] 是否看到 `[Streaming] Accumulated xxx chars`？
- [ ] 是否看到 `[Streaming] ✅ Updated Excalidraw with X elements`？
- [ ] 画板是否有任何变化？

### 3. 如果JSON还是10K+ chars
- [ ] 实施 **max_tokens=2000** 修复（最重要！）
- [ ] 重新测试

---

## 参考位置

- **完整报告**: `D:\file\openproject\SmartArchitect\EXCALIDRAW_DEBUG_REPORT.md`
- **FlowPilot参考**: `D:\file\openproject\reference\flowpilot-beta`
  - Prompt: `app/api/chat/route.ts` line 67-82
  - JSON Repair: `lib/json-repair.ts`
  - Streaming: `app/api/chat/route.ts` line 216-729
  - Sanitization: `components/excalidraw-editor.tsx` line 61-138

- **测试文件**: `backend/test_json_repair_improved.py`（2/3 passing）

---

**创建时间**: 2026-01-16 16:30
**Status**: 准备换环境继续调试
