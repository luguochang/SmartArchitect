# 增量生成模式使用指南

## 问题排查：为什么追加后节点丢失了？

根据后端日志和代码分析，**验证逻辑工作正常**。如果你发现追加后原来的节点被去掉了，可能的原因有：

---

## 原因 1: 没有启用增量模式 ⚠️

### 症状
- 追加修改后，AI 重新生成了整个架构
- 原有节点丢失或被替换

### 解决方案
**必须勾选"增量模式"复选框！**

操作步骤：
1. 在第一次生成架构后，**勾选左侧面板的"增量模式（在现有架构上追加）"** 复选框
2. 确认看到提示："💡 将在现有 N 个节点基础上追加"
3. 然后再输入追加需求（如"添加缓存层"）
4. 点击生成

### 位置
- **文件**: `frontend/components/AiControlPanel.tsx` (lines 648-682)
- **UI位置**: 左侧 Chat 输入框下方

---

## 原因 2: 会话未保存或过期

### 症状
- 已勾选增量模式，但仍然丢失节点
- 后台日志显示: `Session xxx not found or expired`

### 解决方案
会话有 60 分钟 TTL，超过后会自动过期。

操作步骤：
1. 第一次生成架构后，勾选增量模式
2. **立即点击生成**（增量模式会自动保存会话）
3. 确认看到"✓ 会话已保存"提示
4. 在 60 分钟内进行追加生成

### 会话配置
- **TTL**: 60 分钟（可在 `backend/app/services/session_manager.py` 修改）
- **存储位置**: `backend/data/canvas_sessions/`

---

## 原因 3: 前端没有传递增量参数

### 如何验证
打开浏览器开发者工具（F12），查看 Network 请求：

1. 筛选 `chat-generator` 请求
2. 查看 Request Payload
3. 确认包含以下字段：
   ```json
   {
     "incremental_mode": true,
     "session_id": "canvas-xxxxx"
   }
   ```

### 如果缺失
前端代码可能有问题。检查：
- `frontend/lib/store/useArchitectStore.ts` (lines 568-585)

---

## 如何查看后台日志

### 方法 1: 启动后端时查看控制台

```bash
cd backend
venv\Scripts\python.exe -m app.main
```

关键日志标识：
```
[INCREMENTAL] Incremental mode enabled, loading session: canvas-xxxxx
[INCREMENTAL] Loaded 5 nodes, 4 edges
[INCREMENTAL] Building incremental prompt
[INCREMENTAL] Validating and merging incremental results
```

### 方法 2: 运行调试脚本

```bash
cd backend
venv\Scripts\python.exe debug_incremental_flow.py
```

这个脚本会：
1. 模拟创建初始架构（5 节点）
2. 保存会话
3. 模拟 AI 删除/修改节点
4. 执行验证逻辑
5. 输出详细的修复过程

---

## 验证逻辑工作正常的证据

运行 `debug_incremental_flow.py` 后，你应该看到：

```
步骤 6: 执行验证和修复逻辑
--------------------------------------------------------------------------------

开始验证...
WARNING - AI deleted 1 nodes: {'service-2'}, restoring them
WARNING - Node label changed: api-1 (API Gateway → Gateway), reverting to original
WARNING - Node position changed: api-1 (100.0, 100.0) → (150.0, 120.0), reverting to original
WARNING - AI deleted 2 edges: {...}, restoring them

✓ 验证完成
  - 验证后节点数: 6
  - 验证后节点: ['API Gateway', 'User Service', 'User DB', 'Order DB', 'Redis Cache', 'Order Service']

修复结果检查:
  ✓ service-2 已恢复: Order Service
  ✓ api-1 label 已恢复: API Gateway
  ✓ api-1 位置已恢复: (100.0, 100.0)

✓ 增量生成成功: 保留了所有原始节点，并添加了新节点
```

这证明：
- ✅ 删除的节点会自动恢复
- ✅ 修改的 label 会自动还原
- ✅ 移动的位置会自动还原
- ✅ 删除的边会自动恢复

---

## 正确的增量生成流程

### 步骤 1: 第一次生成
1. 输入："设计一个电商系统的架构"
2. 点击"生成流程图"
3. 等待生成完成（假设生成了 5 个节点）

### 步骤 2: 启用增量模式
1. **勾选"增量模式（在现有架构上追加）"**
2. 确认看到："💡 将在现有 5 个节点基础上追加"
3. （可选）确认看到："✓ 会话已保存"

### 步骤 3: 追加需求
1. 输入："在服务和数据库之间添加 Redis 缓存层"
2. 点击"生成流程图"
3. 等待生成完成

### 预期结果
- 原有 5 个节点全部保留（ID、label、type、position 都不变）
- 新增 1-2 个 Redis 节点
- 所有原有边保留
- 新增边连接到缓存节点

---

## 如果仍然有问题

### 1. 检查后台日志

启动后端时观察控制台输出：

```bash
cd backend
venv\Scripts\python.exe -m app.main
```

在追加生成时，查找这些关键日志：

**✅ 正常情况（增量模式启用）：**
```
[INCREMENTAL] Incremental mode enabled, loading session: canvas-xxxxx
[INCREMENTAL] Loaded 5 nodes, 4 edges
[INCREMENTAL] Building incremental prompt
[INCREMENTAL] Validating and merging incremental results
[INCREMENTAL] After merge: 6 nodes (+1 new), 6 edges (+2 new)
```

**⚠️ 异常情况（增量模式未启用）：**
```
[CHAT-GEN] === START generate_flowchart ===
[CHAT-GEN] user_input: 添加 Redis 缓存层
# 缺少 [INCREMENTAL] 相关日志
```

如果看到异常情况，说明前端没有传递 `incremental_mode=true` 参数。

### 2. 检查浏览器控制台

F12 打开开发者工具，查看：
- Console 是否有错误
- Network → 找到 `chat-generator` 请求 → 查看 Payload

### 3. 检查 session_id

在 UI 上查看是否显示"✓ 会话已保存"，如果没有显示，说明会话保存失败。

---

## 技术细节

### Prompt 约束（确保 AI 不简化架构）

```
**CRITICAL CONSTRAINT: DO NOT SIMPLIFY THE EXISTING ARCHITECTURE**

ABSOLUTE RULES:
1. PRESERVE COMPLEXITY: Keep all existing nodes with their EXACT labels, types, and properties
2. NO DELETION: Do NOT delete any existing nodes or edges
3. NO MODIFICATION: Do NOT change existing node labels, types, positions, or colors
4. NO MERGE: Do NOT merge or consolidate existing nodes
5. NO REARRANGEMENT: Do NOT change the existing layout or structure
6. ONLY ADD: You may ONLY add new nodes and new edges
```

### 验证逻辑（修复 AI 错误）

**文件**: `backend/app/services/chat_generator.py` (lines 1271-1340)

检查：
- ✅ 缺失节点 → 自动恢复
- ✅ 修改的 label → 自动还原
- ✅ 修改的 type → 自动还原
- ✅ 移动的 position → 自动还原（阈值 20px）
- ✅ 重复 ID → 自动重命名
- ✅ 位置重叠 → 自动调整

### 边合并逻辑

**文件**: `backend/app/services/chat_generator.py` (lines 1359-1398)

- ✅ 检测删除的边 → 警告并恢复
- ✅ 检测修改的边 label → 保持原始值
- ✅ 合并新增的边

---

## 测试验证

运行单元测试确认功能正常：

```bash
cd backend
venv\Scripts\python.exe test_incremental.py
```

预期输出：
```
✓ 通过: 会话管理器
✓ 通过: Prompt 构建
✓ 通过: 验证逻辑
✓ 通过: 边合并
✓ 通过: Prompt 复杂度约束
✓ 通过: 节点属性保护

总计: 6/6 测试通过

✓ 所有测试通过!
```

---

## 联系支持

如果按照上述步骤仍然无法解决问题，请提供：

1. 后台日志（启动后端时的控制台输出）
2. 浏览器控制台截图（F12 → Console）
3. Network 请求截图（F12 → Network → chat-generator 请求 → Payload）
4. 具体操作步骤和预期结果

这样可以快速定位问题根源。

---

**最可能的原因：没有勾选"增量模式"复选框！** 请确认这一步。
