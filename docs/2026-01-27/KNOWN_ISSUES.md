# Known Issues

## 🐛 Excalidraw 增量渲染元素消失问题

**状态**: ⚠️ 未解决 (暂时保留打字机效果，接受部分元素消失)

**发现时间**: 2026-01-27

**影响范围**: Excalidraw 流式生成功能

### 问题描述

用户在使用 Excalidraw 流式生成时，会看到以下现象：
1. 流式过程中，画板逐渐显示元素（打字机效果）✅
2. 生成结束后，画板上部分元素消失 ❌

**用户体验**：看到内容逐渐增多，但最后只剩下一部分，部分内容消失了。

### 根本原因

**前端增量解析的元素 ≠ 后端验证后的最终元素**

#### 详细流程

1. **AI 生成阶段**
   - AI 生成 54 个元素的 JSON（可能有些格式不正确）
   - 后端通过流式接口逐 token 发送给前端

2. **前端增量解析阶段**
   ```typescript
   // frontend/lib/store/useArchitectStore.ts:807-888
   tryParseAndRenderPartialElements() {
     // 实时解析 JSON token，提取完整的元素
     // 达到 50 个元素上限后停止
     if (parsedElements.length >= MAX_INCREMENTAL_ELEMENTS) {
       console.warn("⚠️ Reached max limit of 50 elements");
       return;
     }
   }
   ```
   - 前端解析到前 50 个元素：`[A, B, C, D(无效格式), E, F, ..., 第50个]`
   - 画板显示这 50 个元素（包含格式无效的）

3. **后端验证阶段**
   ```python
   # backend/app/services/excalidraw_generator.py:245-484
   def _validate_scene(self, ai_data: dict, width: int, height: int):
       max_elems = 50
       for elem in elements[:max_elems]:
           # 严格验证每个元素
           if etype not in ["rectangle", "ellipse", "diamond", ...]:
               logger.warning(f"❌ Skipping unsupported element type")
               continue
           if etype in ["line", "arrow"] and not points:
               logger.warning(f"❌ Skipping {etype} without points array")
               continue
           # ... 更多验证
           cleaned.append(base)
   ```
   - 后端验证所有元素，过滤掉无效的（如 D 元素）
   - 只保留前 50 个**有效**元素：`[A, B, C, E, F, ..., 第51个有效元素]`
   - 返回这 50 个有效元素给前端

4. **前端最终更新阶段**
   ```typescript
   // Line 938-985: 收到 [RESULT] 事件
   if (result.scene?.elements) {
     hasReceivedFinalResult = true;  // 阻止增量更新
     const finalScene = {
       elements: result.scene.elements,  // 使用后端验证后的元素
       appState: result.scene.appState,
       files: result.scene.files
     };
     set({ excalidrawScene: finalScene });  // 覆盖前端增量解析的数据
   }
   ```
   - 前端用后端的 50 个有效元素覆盖之前显示的 50 个元素
   - **结果**：D 元素消失了，第51个有效元素出现了
   - **用户感受**：有些元素不见了

### 问题示例

| 阶段 | 元素列表 | 画板显示 |
|------|----------|----------|
| **增量解析** | `[title, mon, wed, cell-1(无效), fri, cell-2, ..., cell-49]` (50个) | 显示 50 个元素 |
| **后端验证** | `[title, mon, wed, fri, cell-2, ..., cell-49, cell-50]` (50个有效) | - |
| **最终覆盖** | 后端返回的 50 个有效元素 | 显示 50 个元素（cell-1消失，cell-50出现）|

### 相关日志

**前端日志** (`frontend/lib/store/useArchitectStore.ts`):
```javascript
[Excalidraw INCREMENTAL] ✅ Parsed 50 elements  // 前端解析了50个
⚠️ Reached max limit of 50 elements  // 达到上限停止
🔍 [Excalidraw] Received [RESULT]: {rawElementsCount: 50}  // 后端返回50个
✅ [ExcalidrawBoard] Updating canvas with 50 elements  // 覆盖更新
```

**后端日志** (`backend/app/services/excalidraw_generator.py`):
```
✅ JSON parsed, raw elements count: 54  // AI 生成了54个
❌ Skipping element 'xxx' without points array  // 过滤无效元素
✅ Validation complete: 50/50 elements passed (filtered 4)  // 过滤了4个
```

### 已尝试的解决方案

#### 方案 1: 禁用增量渲染 ❌
- **实现**: 注释掉 `tryParseAndRenderPartialElements()`
- **效果**: 没有元素消失问题
- **缺点**: **失去打字机效果**，用户体验变差
- **状态**: 已回滚

#### 方案 2: 竞态条件防护 ⚠️
- **实现**: 添加 `hasReceivedFinalResult` 标志
- **效果**: 防止增量更新在最终结果后继续执行
- **缺点**: 无法解决增量元素与最终元素不一致的问题
- **状态**: 已实现，但问题依然存在

### 可能的解决方案（未实现）

#### 方案 A: 后端实时验证并流式返回有效元素 ⭐ 推荐
**原理**: 后端在流式过程中就进行验证，只发送有效元素

```python
# backend/app/api/excalidraw.py
async def event_stream():
    validated_elements = []
    async for token in vision_service.generate_with_stream(prompt):
        yield f"data: [TOKEN] {token}\n\n"
        accumulated += token

        # 实时验证：尝试解析并验证元素
        new_elements = try_parse_and_validate_partial(accumulated)
        if new_elements:
            # 只发送新增的有效元素
            for elem in new_elements:
                yield f"data: [ELEMENT] {json.dumps(elem)}\n\n"
                validated_elements.append(elem)
```

**前端配合**:
```typescript
// 收到 [ELEMENT] 事件时直接渲染，不需要自己解析
if (content.startsWith("[ELEMENT]")) {
  const element = JSON.parse(content.replace("[ELEMENT]", ""));
  validatedElements.push(element);
  scheduleSceneUpdate(validatedElements);
}
```

**优点**:
- ✅ 前端显示的元素 = 后端验证的元素
- ✅ 保留打字机效果
- ✅ 没有元素消失问题

**缺点**:
- ❌ 需要重构后端流式接口
- ❌ 实时验证可能影响性能

**实现难度**: 🔴🔴🔴 中等

---

#### 方案 B: 前端使用与后端相同的验证逻辑 ⭐
**原理**: 前端增量解析时应用与后端相同的验证规则

```typescript
// frontend/lib/store/useArchitectStore.ts
const validateElement = (elem: any): boolean => {
  // 复制后端的验证逻辑
  if (!elem.id || !elem.type) return false;

  // Line/arrow 必须有 points
  if (["line", "arrow"].includes(elem.type)) {
    if (!elem.points || !Array.isArray(elem.points) || elem.points.length === 0) {
      console.warn(`❌ Skipping ${elem.type} element without points`);
      return false;
    }
  }

  // Text 必须有 text 属性
  if (elem.type === "text") {
    if (!elem.text) {
      console.warn(`❌ Skipping text element without text property`);
      return false;
    }
  }

  return true;
};

// 在增量解析时应用验证
if (element.id && !parsedElements.some(e => e.id === element.id)) {
  if (validateElement(element)) {  // ✅ 添加验证
    parsedElements.push(element);
  }
}
```

**优点**:
- ✅ 前端显示的元素更接近后端验证的结果
- ✅ 保留打字机效果
- ✅ 实现相对简单

**缺点**:
- ⚠️ 前后端验证逻辑需要保持同步
- ⚠️ 仍可能有微小差异（如坐标归一化）

**实现难度**: 🟡🟡 简单

---

#### 方案 C: 增量显示 + 差异动画过渡
**原理**: 接受元素会变化的事实，用动画让过渡更自然

```typescript
// 收到最终结果时
if (result.scene?.elements) {
  const incrementalIds = new Set(parsedElements.map(e => e.id));
  const finalIds = new Set(result.scene.elements.map(e => e.id));

  // 找出消失的元素
  const disappearing = parsedElements.filter(e => !finalIds.has(e.id));
  // 找出新增的元素
  const appearing = result.scene.elements.filter(e => !incrementalIds.has(e.id));

  if (disappearing.length > 0 || appearing.length > 0) {
    console.log(`🔄 Transitioning: ${disappearing.length} out, ${appearing.length} in`);
    // 添加淡出/淡入动画
    // ...
  }

  set({ excalidrawScene: finalScene });
}
```

**优点**:
- ✅ 保留打字机效果
- ✅ 用户能理解元素在"优化"（而非消失）

**缺点**:
- ❌ 治标不治本
- ❌ Excalidraw 可能不支持元素级动画

**实现难度**: 🟡🟡🟡 中等

---

#### 方案 D: 提高元素上限到 100
**原理**: 给更大的缓冲空间，减少达到上限的概率

```python
# backend/app/services/excalidraw_generator.py
max_elems = 100  # 从 50 提升到 100
```

```typescript
// frontend/lib/store/useArchitectStore.ts
const MAX_INCREMENTAL_ELEMENTS = 100;  // 从 50 提升到 100
```

**优点**:
- ✅ 实现超简单
- ✅ 减少元素消失的概率

**缺点**:
- ❌ 治标不治本
- ❌ 仍然可能出现元素消失

**实现难度**: 🟢 极简单

---

### 推荐方案组合

**短期方案 (快速改善)**:
1. **方案 D**: 提高上限到 100 （5分钟）
2. **方案 B**: 前端添加基础验证逻辑（30分钟）

**长期方案 (彻底解决)**:
3. **方案 A**: 后端实时验证并流式返回有效元素（2-3小时）

### 相关代码位置

**前端**:
- `frontend/lib/store/useArchitectStore.ts:747-888` - 增量解析逻辑
- `frontend/lib/store/useArchitectStore.ts:938-985` - 最终结果处理
- `frontend/components/ExcalidrawBoard.tsx:58-75` - 画板更新逻辑

**后端**:
- `backend/app/api/excalidraw.py:123-170` - 流式接口实现
- `backend/app/services/excalidraw_generator.py:245-484` - 元素验证逻辑
- `backend/app/services/excalidraw_generator.py:339` - 元素数量上限

### 临时解决方法

**如果用户遇到元素消失问题**:
1. 简化提示词，减少元素数量（少于50个不会有问题）
2. 多生成几次，选择效果最好的一次
3. 使用非流式接口（如果有的话）

### 备注

- 问题记录时间: 2026-01-27
- 记录人: Claude (AI Assistant)
- 影响版本: 0.5.0+
- 优先级: P2 (中等，影响体验但不阻塞功能)

---

## 其他已知问题

(暂无)
