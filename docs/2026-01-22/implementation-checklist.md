# RAG集成实施清单

**项目**: SmartArchitect AI - RAG深度集成
**开始日期**: 2026-01-22
**预计完成**: 2026-02-26（Week 6）

---

## 📋 Phase 1: 专业演讲稿生成系统 (Week 1-2) 🔴

### 1.1 后端 - 数据模型扩展
- [x] 扩展 `backend/app/models/schemas.py`
  - [x] 添加 `ScriptOptions` 模型（tone, audience, focus_areas）
  - [x] 添加 `ScriptContent` 模型（intro, body, conclusion, full_text）
  - [x] 添加 `ScriptMetadata` 模型（created_at, duration, word_count, rag_sources）
  - [x] 添加 `ScriptDraft` 模型（id, content, metadata, version）
  - [x] 添加 `StreamEvent` 模型（type, data）
  - [x] 添加 `SaveDraftResponse` 模型
  - [x] 添加 `RefinedSectionResponse` 模型
  - [x] 添加 `ImprovementSuggestions` 模型

### 1.2 后端 - 演讲稿生成服务
- [x] 创建 `backend/app/services/speech_script_rag.py`
  - [x] 实现 `ProfessionalPromptBuilder` 类
    - [x] `build_script_prompt()` 方法（CO-STAR框架）
    - [x] `_format_architecture_detailed()` 方法
    - [x] `_format_rag_context_structured()` 方法
    - [x] `_extract_tech_stack()` 方法
    - [x] `_assess_complexity()` 方法
    - [x] `_generate_intro_template()` 方法
    - [x] `_generate_body_template()` 方法
    - [x] `_generate_conclusion_template()` 方法
    - [x] `_generate_quality_checklist()` 方法
    - [x] `_get_audience_concerns()` 方法
    - [x] `_get_audience_background()` 方法
    - [x] `_get_technical_depth()` 方法
    - [x] `_get_terminology_guidance()` 方法
    - [x] `_get_example_style()` 方法
  - [x] 实现 `RAGSpeechScriptGenerator` 类
    - [x] `generate_speech_script_stream()` 方法（流式生成）
    - [x] `build_context_query()` 方法
    - [x] `post_process_script()` 方法
    - [x] `estimate_duration()` 方法
    - [x] `extract_section()` 方法（章节提取）
    - [x] `_count_words()` 方法（中英文混合字数统计）

### 1.3 后端 - 演讲稿编辑服务
- [x] 创建 `backend/app/services/script_editor.py`
  - [x] 实现 `ScriptEditorService` 类
    - [x] `__init__()` - 创建存储目录
    - [x] `save_draft()` 方法（草稿保存）
    - [x] `load_draft()` 方法（草稿加载）
    - [x] `refine_section()` 方法（局部润色）
    - [x] `suggest_improvements()` 方法（AI改进建议）
    - [x] `_rebuild_full_text()` 方法
    - [x] `_summarize_changes()` 方法
    - [x] `_format_rag_context()` 方法

### 1.4 后端 - API端点
- [x] 更新 `backend/app/api/export.py`
  - [x] 添加 `POST /api/export/script-stream` 端点（流式生成）
    - [x] SSE响应设置
    - [x] 异步生成器实现
    - [x] 错误处理
  - [x] 添加 `PUT /api/export/script/{script_id}/draft` 端点（保存草稿）
  - [x] 添加 `GET /api/export/script/{script_id}/draft` 端点（加载草稿）
  - [x] 添加 `POST /api/export/script/{script_id}/refine` 端点（润色）
  - [x] 添加 `GET /api/export/script/{script_id}/suggestions` 端点（改进建议）

### 1.5 前端 - 数据模型
- [x] 创建 `frontend/types/script.ts`
  - [x] `ScriptOptions` 接口
  - [x] `ScriptContent` 接口
  - [x] `ScriptDraft` 接口
  - [x] `ImprovementSuggestion` 接口
  - [x] `StreamEvent` 接口

### 1.6 前端 - 演讲稿生成组件
- [x] 创建 `frontend/components/ScriptGenerator.tsx` (590行)
  - [x] 配置选项UI（时长、受众、重点领域）
  - [x] 生成按钮和加载状态
  - [x] 流式接收和打字机效果
  - [x] 进度日志显示
  - [x] 来源引用展示
  - [x] 生成完成后跳转到编辑器

### 1.7 前端 - 演讲稿编辑组件
- [x] 创建 `frontend/components/ScriptEditor.tsx` (420行)
  - [x] 三栏布局（intro/body/conclusion）
  - [x] Textarea编辑器
  - [x] 自动保存功能（debounce 2s）
  - [x] 字数统计
  - [x] 润色按钮
  - [x] AI改进建议面板
  - [x] 状态栏（保存状态、字数验证）

### 1.8 前端 - 润色对话框
- [x] 创建 `frontend/components/RefineDialog.tsx` (220行)
  - [x] 反馈输入框
  - [x] 快速建议按钮（6个预设动作）
  - [x] 示例建议展示
  - [x] 提交和取消按钮
  - [x] 加载状态显示

### 1.9 前端 - ExportMenu集成
- [x] 更新 `frontend/components/ExportMenu.tsx`
  - [x] 添加ScriptGenerator和ScriptEditor导入
  - [x] 添加workflow状态管理
  - [x] 替换旧的三个脚本按钮为单一"生成演讲稿"按钮
  - [x] 实现handleScriptComplete回调
  - [x] 集成modal组件

### 1.10 后端测试
- [x] 创建 `backend/tests/test_speech_script_rag.py` (600+行)
  - [x] 单元测试（12个测试）
    - [x] 测试Prompt构建（3种时长：30s/2min/5min）
    - [x] 测试受众自适应
    - [x] 测试流式生成（Mock数据）
    - [x] 测试上下文查询构建
    - [x] 测试时长估算
    - [x] 测试章节提取
    - [x] 测试服务工厂函数
  - [x] 集成测试（2个测试，使用自定义Claude API）
    - [x] 测试实际API调用（非流式）
    - [x] 测试实际API调用（流式）
  - [x] 测试结果：14/14通过 ✓

### 1.11 前端测试
- [ ] 手动测试完整workflow
  - [ ] Export Menu → 生成演讲稿按钮 → ScriptGenerator打开
  - [ ] 配置选项 → 开始生成 → 流式显示
  - [ ] 生成完成 → 自动跳转ScriptEditor
  - [ ] 编辑内容 → 自动保存
  - [ ] 点击润色按钮 → RefineDialog打开
  - [ ] 提交润色反馈 → 内容更新

### 1.12 验收标准
- [ ] 生成演讲稿专业度评分 > 8/10（人工评估）
- [ ] CO-STAR框架prompt生成结构化脚本（intro/body/conclusion）
- [ ] 二次编辑功能可用（编辑+润色+改进建议）
- [ ] 流式传输流畅（首token延迟 < 3s）
- [ ] 中英文字数统计准确

---

## 📋 Phase 2: RAG服务增强（简化版） (Week 2-3) 🟡

### 2.1 数据模型
- [ ] 更新 `backend/app/models/schemas.py`
  - [ ] 添加 `SimpleGraphFeatures` 模型
  - [ ] 添加 `DocumentMetadata` 模型
  - [ ] 添加 `EnhancedSearchResult` 模型

### 2.2 RAG增强服务
- [ ] 创建 `backend/app/services/rag_enhanced.py`
  - [ ] 实现 `EnhancedRAGService` 类
    - [ ] `hybrid_search()` 方法（混合检索）
    - [ ] `simple_graph_similarity_search()` 方法
    - [ ] `extract_simple_graph_features()` 方法
    - [ ] `calculate_similarity()` 方法
    - [ ] `vectorize_node_types()` 方法
    - [ ] `classify_topology_simple()` 方法
    - [ ] `rerank()` 方法（cross-encoder）

### 2.3 元数据提取
- [ ] 增强 `backend/app/services/rag.py`
  - [ ] `extract_metadata_from_text()` 方法
  - [ ] `identify_tech_stack()` 方法
  - [ ] `assess_complexity()` 方法
  - [ ] 修改上传流程，自动提取元数据

### 2.4 测试
- [ ] 测试简化图相似度搜索
- [ ] 测试元数据提取准确率
- [ ] 测试混合检索效果
- [ ] 测试reranking性能

### 2.5 验收
- [ ] 结构相似度搜索准确率 > 70%
- [ ] 元数据过滤准确率 > 85%
- [ ] RAG查询延迟 < 2s（首次）, < 500ms（缓存）

---

## 📋 Phase 3: RAG驱动PPT生成 (Week 4-5) 🟡

### 3.1 数据模型
- [ ] 更新 `backend/app/models/schemas.py`
  - [ ] 添加 `PresentationOptions` 模型
  - [ ] 添加 `ContentPlan` 模型
  - [ ] 添加 `SlideData` 模型
  - [ ] 添加 `EnhancedSlideData` 模型

### 3.2 PPT导出服务
- [ ] 创建 `backend/app/services/ppt_exporter_rag.py`
  - [ ] 实现 `RAGPowerfulPPTExporter` 类
    - [ ] `generate_intelligent_presentation()` 方法
    - [ ] `plan_slide_content()` 方法（内容规划）
    - [ ] `design_slide_layouts()` 方法（布局设计）
    - [ ] `enhance_with_rag()` 方法（RAG增强）
    - [ ] `add_visual_enhancements()` 方法（视觉增强）
    - [ ] `generate_component_explanation()` 方法
    - [ ] `analyze_flow_with_context()` 方法
    - [ ] `add_source_attribution()` 方法

### 3.3 API端点
- [ ] 更新 `backend/app/api/export.py`
  - [ ] 添加 `POST /api/export/ppt-enhanced` 端点
  - [ ] 添加 `POST /api/rag/preview` 端点（上下文预览）

### 3.4 前端组件
- [ ] 创建 `frontend/components/RAGContextPreview.tsx`
  - [ ] 显示找到的文档数
  - [ ] 显示检测到的架构模式
  - [ ] 显示来源徽章
- [ ] 更新 `frontend/components/ExportMenu.tsx`
  - [ ] 添加RAG增强选项
  - [ ] 集成上下文预览

### 3.5 测试
- [ ] 测试PPT生成流程
- [ ] 测试RAG上下文注入
- [ ] 测试来源引用显示

### 3.6 验收
- [ ] 生成的PPT包含RAG最佳实践
- [ ] 演讲者注释含领域知识
- [ ] 页脚显示来源引用

---

## 📋 Phase 4: 前端全面集成 (Week 6) 🔴

### 4.1 状态管理
- [ ] 更新 `frontend/lib/store/useArchitectStore.ts`
  - [ ] 添加 `ragExportOptions` 状态
  - [ ] 添加 `contextPreview` 状态
  - [ ] 添加 `scriptDrafts` 状态
  - [ ] 添加 `currentScriptId` 状态

### 4.2 综合导出菜单
- [ ] 创建 `frontend/components/EnhancedExportMenu.tsx`
  - [ ] 整合所有导出选项
  - [ ] RAG上下文预览
  - [ ] 配置选项UI
  - [ ] 演讲稿编辑入口

### 4.3 优化用户体验
- [ ] 流式打字机效果优化
- [ ] 加载状态优化
- [ ] 错误处理和提示
- [ ] 响应式布局

### 4.4 版本管理
- [ ] 演讲稿历史版本列表
- [ ] 版本对比功能
- [ ] 版本回滚

### 4.5 测试
- [ ] 端到端测试完整工作流
- [ ] 性能测试
- [ ] 用户体验测试

### 4.6 验收
- [ ] 完整的生成→编辑→导出工作流
- [ ] 打字机效果流畅
- [ ] 用户体验评分 > 4/5

---

## 📋 Phase 5: 高级功能（可选） (Week 7+) 🟢

### 5.1 Slidev RAG增强
- [ ] 创建 `backend/app/services/slidev_exporter_rag.py`
- [ ] 添加RAG叙述到Slidev模板

### 5.2 多模态图表生成
- [ ] 创建 `backend/app/services/chart_generator.py`
- [ ] 实现性能图表生成
- [ ] PPT嵌入

### 5.3 A/B测试框架
- [ ] Prompt模板对比测试
- [ ] 质量评分系统

### 5.4 导出分析仪表板
- [ ] 追踪导出质量
- [ ] 识别问题模式

---

## 📊 进度总览

### 完成情况
- Phase 1: 0/10 (0%)
- Phase 2: 0/5 (0%)
- Phase 3: 0/6 (0%)
- Phase 4: 0/6 (0%)
- Phase 5: 0/4 (0%)

**总体进度**: 0/31 (0%)

### 当前状态
- 🚀 **开始时间**: 2026-01-22
- 🎯 **当前Phase**: Phase 1 - 专业演讲稿生成系统
- ⏰ **下一步**: 扩展数据模型（schemas.py）

---

## 📝 更新日志

### 2026-01-22
- ✅ 创建实施清单文档
- ⏳ 准备开始Phase 1开发

---

**备注**:
- 每完成一个子任务，将 `- [ ]` 改为 `- [x]`
- 每天更新进度总览和更新日志
- 遇到问题记录在文档底部的"问题与解决"章节
