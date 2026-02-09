# 增量生成功能调试指南

## 概述

本文档说明如何使用和调试增量生成功能，以及如何查看详细的诊断日志。

## 功能说明

**增量生成模式**允许在现有架构/流程图基础上追加新内容，而不是重新生成整个图。

### 核心机制

1. **Session管理**：前端将当前画布保存到后端session（60分钟有效期）
2. **Prompt约束**：AI被明确告知保留所有现有节点，只允许添加新节点
3. **验证逻辑**：后端自动检测并恢复AI误删的节点
4. **语义验证**：检查原有概念是否丢失（关键词覆盖率>80%）

## 使用步骤

### 1. 初次生成

```
输入: "设计一个电商秒杀流程，用户点击秒杀按钮..."
结果: 生成16个节点（开始、点击按钮、检查库存、扣减库存、创建订单...）
```

前端会自动保存这16个节点到session。

### 2. 启用增量模式

在前端Chat Generator输入框上方，勾选"增量模式"复选框。

此时会显示提示：`💡 将在现有 16 个节点基础上追加`

### 3. 追加生成

```
输入: "1、库存扣减要加锁，防止超卖。2、支付失败要恢复库存。"
预期结果: 16个原始节点 + N个新增节点（锁定、恢复等）
```

## 诊断日志说明

### 关键日志标记

后端控制台会输出以下带特殊标记的日志（按时间顺序）：

#### 1. Session加载（初次或增量）

```
[INCREMENTAL] 🔄 Incremental mode enabled, loading session: canvas-abc123
[INCREMENTAL] ✅ Successfully loaded 16 nodes, 18 edges from session
[INCREMENTAL] Sample existing node IDs: ['start-1', 'click-1', 'check-stock-1', 'deduct-1', 'create-order-1']...
```

**验证点**：
- ✅ 如果看到"Successfully loaded 16 nodes"，说明session正确加载
- ❌ 如果看到"Session not found or expired"，说明session丢失，会降级为全新生成

#### 2. Prompt构建

```
[INCREMENTAL] Building incremental prompt
[CHAT-GEN] Prompt (first 200 chars): You are an expert systems architect tasked with INCREMENTALLY enhancing...
```

**验证点**：
- ✅ Prompt应包含"DO NOT SIMPLIFY"约束
- ✅ Prompt应包含所有16个现有节点的完整JSON

#### 3. AI响应

```
[CHAT-GEN] After normalization: 15 nodes, 15 edges
```

**验证点**：
- ⚠️ 如果AI返回的节点数**少于**原始节点数（如15 < 16），说明AI违规删除了节点
- 验证逻辑应该能自动修复这个问题

#### 4. 增量验证（关键！）

```
[INCREMENTAL-CHECK] incremental_mode=True, existing_nodes_count=16, will_validate=True
[INCREMENTAL] 🔍 BEFORE VALIDATION: AI returned 15 nodes, but we started with 16 nodes
[INCREMENTAL] ❌ CRITICAL: AI DELETED 1 nodes! This should be caught by validation.
[INCREMENTAL] Running validation logic...
```

**验证点**：
- ✅ 如果看到"BEFORE VALIDATION: AI returned 15 nodes"，说明AI确实删除了节点
- ✅ 验证逻辑正在执行

#### 5. 节点恢复检查

```
AI deleted 1 nodes: {'payment-restore-1'}, restoring them
Node label changed: stock-deduct-1 (扣减库存 → 库存扣减), reverting to original
```

**验证点**：
- ✅ 验证逻辑检测到缺失节点并恢复
- ✅ 检测到label修改并还原

#### 6. 语义验证

```
Semantic content lost: keywords {'restore', 'payment'} are missing in final architecture
CRITICAL: 1 nodes lost semantic content: ['支付失败恢复']
Semantic coverage: 75.0%
Semantic validation failed! AI simplified architecture. Keeping ALL original nodes to preserve content.
Falling back to safe mode: keeping all 16 original nodes + 2 new nodes
```

**验证点**：
- ⚠️ 如果语义覆盖率<80%，会触发**安全模式**
- ✅ 安全模式会强制保留所有16个原始节点 + AI新增的节点

#### 7. 验证结果

```
[INCREMENTAL] ✅ AFTER VALIDATION: 18 nodes (+3 restored)
[INCREMENTAL] Final result: 18 nodes (original 16 + new 2), 20 edges (original 18 + new 2)
```

**验证点**：
- ✅ 最终节点数应该 **≥** 原始节点数（16）
- ✅ 应该有新增节点（如示例中+2个新节点）

#### 8. 致命错误检查

```
[INCREMENTAL] ❌❌❌ FATAL: After validation, we STILL have fewer nodes! (15 < 16). This should NEVER happen!
```

**如果看到这条日志**：
- ❌ 说明验证逻辑失败了，这是BUG
- 请立即复制完整的后端日志并报告

## 如何查看日志

### 方法1：直接查看控制台

启动后端时，日志会直接输出到控制台：

```bash
cd backend
venv\Scripts\python.exe -m app.main
```

查看增量生成时的日志输出（带🔄 ✅ ❌等符号的行）。

### 方法2：使用监控脚本（推荐）

```bash
cd backend
venv\Scripts\python.exe -m app.main 2>&1 | python monitor_incremental_logs.py
```

这会实时解析和高亮显示增量生成相关的日志。

## 常见问题诊断

### 问题1：节点数减少了（16 → 15）

**可能原因**：

1. **增量模式未启用**
   - 检查日志：应该看到`[INCREMENTAL] 🔄 Incremental mode enabled`
   - 如果没有：检查前端是否勾选了"增量模式"

2. **Session丢失或过期**
   - 检查日志：应该看到`[INCREMENTAL] ✅ Successfully loaded 16 nodes`
   - 如果看到`Session not found`：session已过期（60分钟），需要重新生成

3. **验证逻辑未执行**
   - 检查日志：应该看到`[INCREMENTAL-CHECK] will_validate=True`
   - 如果是False：检查`incremental_mode`和`existing_nodes`是否都有值

4. **验证逻辑执行但失败**
   - 检查日志：应该看到`[INCREMENTAL] ✅ AFTER VALIDATION: X nodes (+Y restored)`
   - 如果恢复数为0但AI删除了节点：可能是BUG

### 问题2：语义内容丢失

**症状**：节点数增加了（16 → 18），但原有的某些功能模块消失了

**诊断**：

```bash
# 运行语义验证测试
cd backend
venv\Scripts\python.exe validate_semantic_coverage.py
```

**解决方案**：
- 语义验证会自动触发"安全模式"
- 检查日志中是否有`Falling back to safe mode`
- 如果没有触发，可能是关键词覆盖率刚好>80%，但实际上内容变化了

### 问题3：新增节点位置重叠

**症状**：AI添加的节点和原有节点重叠在一起

**诊断**：

查找日志：
```
Position overlap: shifted node-xyz to x=1500
```

**解决方案**：
- 位置冲突解决逻辑会自动右移300px
- 如果仍然重叠，可能需要手动调整

## 预期行为总结

### ✅ 正常增量生成

```
初始: 16节点 → 增量请求"添加锁和恢复" → AI返回17节点 → 验证通过 → 最终17节点
```

### ✅ AI误删，验证修复

```
初始: 16节点 → 增量请求 → AI返回15节点 → 验证检测到缺失1个 → 恢复1个 → 最终16节点
```

### ✅ 语义丢失，安全模式

```
初始: 16节点 → 增量请求 → AI返回17节点（但删除了"支付"概念，添加了"库存细节"）
→ 语义覆盖率75% → 触发安全模式 → 保留所有16个原始节点 + AI的17个节点 → 最终33节点（重复）
```
*注：安全模式会产生重复节点，用户需要手动清理*

### ❌ 异常：验证失败

```
初始: 16节点 → 增量请求 → AI返回15节点 → 验证执行 → 仍然15节点 → ❌❌❌ FATAL错误
```
*这种情况不应该发生，请报告BUG*

## 报告问题时需要提供

如果遇到节点丢失问题，请提供以下信息：

1. **完整后端日志**（从启动到生成完成）
2. **前端请求参数**：
   - 初次生成的user_input
   - 增量生成的user_input
   - incremental_mode值
   - session_id值
3. **预期结果 vs 实际结果**：
   - 初始节点数
   - 增量后预期节点数
   - 实际得到的节点数
4. **前端控制台日志**（F12打开，Console标签）

## 测试脚本

### 单元测试

```bash
cd backend
venv\Scripts\python.exe -m pytest test_incremental.py -v
```

**所有测试应该通过（6/6）**

### 端到端测试（真实AI调用）

```bash
cd backend
venv\Scripts\python.exe e2e_test_incremental.py
```

**这会：**
1. 生成一个5节点的初始架构
2. 保存到session
3. 增量生成（添加缓存层）
4. 验证所有5个原始节点都保留
5. 输出详细的节点对比

## 最后的检查清单

在报告"增量生成节点减少"问题前，请确认：

- [ ] 前端确实勾选了"增量模式"
- [ ] 后端日志中有`[INCREMENTAL] 🔄 Incremental mode enabled`
- [ ] 后端日志中有`[INCREMENTAL] ✅ Successfully loaded X nodes`
- [ ] 后端日志中有`[INCREMENTAL-CHECK] will_validate=True`
- [ ] 后端日志中有`[INCREMENTAL] ✅ AFTER VALIDATION`显示恢复的节点数
- [ ] Session没有过期（生成间隔<60分钟）
- [ ] 没有手动清空过画布（会删除session）

如果以上都确认了，但节点仍然减少，那就是真正的BUG，请提供完整日志！
