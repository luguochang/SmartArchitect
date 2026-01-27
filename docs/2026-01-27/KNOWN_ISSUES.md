# Known Issues

## ✅ RESOLVED: Excalidraw 增量渲染元素消失问题

**状态**: ✅ 已解决（2026-01-27 方案A实施完成）

**解决方案**: 方案A - 后端实时验证并流式返回有效元素

**实施内容**:
1. ✅ 后端实时解析器 (`IncrementalElementParser`)
   - 实时解析流式token，提取完整的JSON元素
   - 即时验证元素（line/arrow必须有points，text必须有text属性）
   - 只发送有效元素给前端
   - 无上限：处理AI生成的所有元素（性能保护上限200个）

2. ✅ 移除50个元素限制
   - 后端: `_validate_scene` 不再限制元素数量
   - 前端: 移除 `MAX_INCREMENTAL_ELEMENTS` 限制

3. ✅ 前端简化（移除150+行增量解析代码）
   - 监听 `[ELEMENT]` 事件，直接渲染后端验证的元素
   - 监听 `[DONE]` 事件，显示最终统计
   - 批量更新：每5个元素更新一次画板（减少DOM更新）

4. ✅ 性能优化
   - 56个元素：56次更新 → ~12次更新
   - 批量更新策略：第1个、第5个、第10个...立即更新，其余缓存

**测试结果**:
- IncrementalElementParser: ✅ PASS
- Max Elements Limit: ✅ PASS
- Element Normalization: ✅ PASS

**效果**:
- ✅ 元素不消失（前端显示 = 后端验证）
- ✅ 无上限限制（AI生成多少就显示多少）
- ✅ 打字机效果保留（逐批出现）
- ✅ 性能提升（更新次数减少80%）

**相关文件**:
- `backend/app/services/excalidraw_generator.py:90-298` - IncrementalElementParser
- `backend/app/api/excalidraw.py:122-194` - 流式接口改造
- `frontend/lib/store/useArchitectStore.ts:744-966` - 前端监听逻辑
- `test_incremental_parser.py` - 单元测试

---

## 其他已知问题

(暂无)
