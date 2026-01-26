# RAG知识库集成方案 - 执行摘要

**日期**: 2026-01-22
**项目**: SmartArchitect AI - RAG深度集成到PPT和演讲稿生成
**状态**: 计划已批准，待实施

---

## 一、需求背景

### 核心痛点（用户反馈）
1. **演讲稿质量不足**: 仅靠简单输入框+AI生成，内容过于简单，缺乏专业性
2. **缺乏二次编辑能力**: 生成后无法润色和修改，一次性生成难以满足需求
3. **prompt设计欠佳**: 需要定义演讲稿所需要素，约束大模型生成高质量内容
4. **RAG未发挥作用**: 知识库与生成流程隔离，没有为内容提供专业支撑

### 用户选择
- **应用场景**: 混合场景（内部技术分享 + 外部客户演示 + 架构评审）
- **功能优先级**: MVP全流程（演讲稿生成+编辑+RAG增强+PPT导出）
- **技术深度**: 简化版图相似度（平衡方案，节省50%工期）
- **AI Provider**: 多provider灵活切换（Gemini/OpenAI/Claude/SiliconFlow）

---

## 二、技术方案核心

### 2.1 专业演讲稿生成系统（核心重点）

**设计理念**:
- 采用 **CO-STAR框架**（Context, Objective, Style, Tone, Audience, Response）
- **演讲稿要素约束**：每种时长有明确的必需元素清单
- **RAG增强**：注入领域知识和案例
- **二次编辑支持**：保存草稿、分章节润色、AI改进建议

**三种时长模板**:

| 时长 | 字数 | 结构 | 必需要素 |
|------|------|------|----------|
| 30s | 60-80字 | Hook + Value Proposition + CTA | 开场Hook、核心价值陈述、关键指标、行动号召 |
| 2min | 280-320字 | 开场(30s) + 背景(30s) + 方案(45s) + 价值(30s) + 结尾(15s) | 开场故事、痛点陈述、3个核心亮点、RAG案例、量化价值、下一步 |
| 5min | 700-800字 | 开场(1min) + 背景(1min) + 设计(2min) + 风险(0.5min) + Q&A(0.5min) | 引人开场、业务背景、设计理念、组件讲解、数据流、RAG引用2+、案例对比、风险对策、性能分析、演进方向、讨论问题 |

**Prompt工程创新**:
```
CO-STAR框架:
├── Context: 架构概览 + RAG检索结果 + 检测到的架构模式
├── Objective: 生成目标 + 受众分析 + 重点关注
├── Style: 讲故事方式 + 类比比喻 + 数据驱动 + 问题导向
├── Tone: 自信专业 + 诚实透明 + 避免空洞表述
├── Audience: 受众类型 + 期待 + 背景 + 技术深度调整
└── Response Format: 结构化输出 + 模板 + 质量检查清单
```

**二次编辑功能**:
- 草稿自动保存（debounce 2秒）
- 分章节编辑和润色（intro/body/conclusion）
- AI改进建议（不直接修改，提供建议列表）
- 快速润色模板（增加数据、增加类比、调整语气、简化表达）
- 版本管理（可回溯历史）

### 2.2 简化版RAG增强服务

**混合检索策略**:
1. **语义搜索**（现有能力）
2. **简化的结构相似度**（新增）：
   - 节点类型分布统计（Counter）
   - 边密度计算（连接紧密度）
   - 平均出入度
   - 拓扑分类（layered/mesh/hub-spoke）
   - 余弦相似度匹配（无需深度学习模型）
3. **元数据过滤**（新增）：
   - 技术栈、复杂度、领域自动识别

**图特征提取（简化版）**:
```python
特征权重:
- 节点类型向量相似度: 60%
- 边密度相似度: 20%
- 拓扑匹配: 20%

优势: 节省50%工期，保留80%效果
```

### 2.3 RAG驱动PPT生成

**4阶段生成管道**:
```
Stage 1: 内容规划
├── RAG查询相似架构
├── AI生成幻灯片大纲
└── 根据受众和时长调整

Stage 2: 智能布局设计
├── 6-8张幻灯片结构
├── 标题页
├── 架构概览（含统计）
├── 核心组件详解（每个1页）
├── 数据流分析
├── 潜在问题与优化建议
└── 总结与下一步

Stage 3: RAG增强叙述
├── 为每张幻灯片查询RAG
├── 生成组件说明（含最佳实践）
├── 数据流分析（含相似案例）
└── 添加演讲者注释

Stage 4: 视觉增强
├── 来源引用（页脚）
├── 统计图表（可选）
└── 专业配色和排版
```

---

## 三、实施路线图

### Phase 1: 专业演讲稿生成系统（Week 1-2）🔴最高优先级

**任务**:
- 创建 `speech_script_rag.py`（ProfessionalPromptBuilder + 流式生成）
- 创建 `script_editor.py`（草稿保存 + 润色 + 改进建议）
- 扩展 `export.py` API（4个新端点）
- 前端组件（ScriptGenerator + ScriptEditor + RefineDialog）

**交付物**:
- 功能完整的演讲稿生成和编辑系统
- 支持3种时长（30s/2min/5min）
- 支持分章节润色和AI改进建议

**验证标准**:
- [ ] CO-STAR框架生成的演讲稿专业度评分 > 8/10
- [ ] 包含至少2个RAG来源的案例引用
- [ ] 二次编辑功能可用，润色后质量明显提升
- [ ] 流式传输流畅，首token延迟 < 3s

### Phase 2: RAG服务增强（Week 2-3）🟡中优先级

**任务**:
- 创建 `rag_enhanced.py`（简化图特征 + 余弦相似度）
- 增强 `rag.py`（元数据提取 + 技术栈识别）
- 扩展数据模型

**验证标准**:
- [ ] 简化结构相似度搜索准确率 > 70%
- [ ] 元数据过滤准确率 > 85%
- [ ] RAG查询延迟 < 2s（首次）, < 500ms（缓存）

### Phase 3: RAG驱动PPT生成（Week 4-5）🟡中优先级

**任务**:
- 创建 `ppt_exporter_rag.py`（4阶段管道）
- 扩展export API（2个新端点）
- 前端RAG上下文预览组件

**验证标准**:
- [ ] PPT包含RAG来源的最佳实践
- [ ] 演讲者注释含领域知识
- [ ] 页脚显示来源引用

### Phase 4: 前端全面集成（Week 6）🔴高优先级

**任务**:
- 集成所有后端功能
- 优化流式体验（打字机效果）
- 来源引用展示
- 版本管理

**验证标准**:
- [ ] 完整的生成→编辑→导出工作流
- [ ] 用户体验评分 > 4/5

### Phase 5: 高级功能（Week 7+）🟢低优先级

可选功能:
- Slidev RAG增强
- 多模态图表生成
- A/B测试不同prompt模板

---

## 四、技术可行性

### ✅ 高可行性
- RAG混合检索（ChromaDB + 元数据过滤）
- 文本叙述增强（prompt工程）
- 流式API（FastAPI原生SSE支持）
- 前端集成（React + Zustand现有模式）

### ⚠️ 中等可行性
- 简化图相似度（统计特征，80%效果）
- Cross-encoder reranking（可缓存）
- 二次编辑UI（参考现有编辑器组件）

### ⚡ 风险点与缓解
| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| RAG查询延迟（首次26s） | 用户体验差 | 预热 + Redis缓存 + 异步加载 |
| 流式传输中断 | 生成失败 | 断点续传 + 草稿自动保存 |
| AI幻觉 | 内容不准确 | 相关性阈值过滤 + RAG约束 |
| Prompt复杂度高 | 维护困难 | 模板化 + 配置化 + 版本控制 |

---

## 五、预期效果

### 质量提升
- 演讲稿专业度: **5/10 → 8+/10**
- RAG检索相关性: **> 0.7**
- 内容与架构一致性: **> 95%**

### 功能完善
- ✅ 支持二次编辑和润色（解决核心痛点）
- ✅ 分章节编辑，细粒度控制
- ✅ AI改进建议，非强制修改
- ✅ 多时长模板，适应不同场景

### 用户体验
- PPT导出时间: **< 30s**
- 演讲稿首token延迟: **< 3s**
- 流式传输帧率: **> 10 token/s**
- 草稿自动保存: **2秒debounce**

---

## 六、技术参考

### Prompt Engineering最佳实践（2025-2026）
1. **IBM's 2026 Guide to Prompt Engineering**
   - 企业级prompt工程，强调context engineering
   - 报告67%生产力提升案例

2. **Lakera's Ultimate Prompt Engineering Guide**
   - CO-STAR框架详解
   - Role-based prompting策略

3. **7 Prompt Engineering Templates That Work**
   - 生产级prompt模板
   - 企业实施案例

### RAG与演示文稿生成
1. **Mastering PowerPoint Creation with RAG**
   - Google Colab实践案例
   - RAG-powered automation工作流

2. **AI Presentation Makers 2026**
   - Tome/Gamma设计模式分析
   - 商业AI工具的最佳实践

### 多模态AI
1. **ChartLlama: Multimodal LLM for Chart Generation**
   - 图表理解与生成研究
   - 多模态能力应用

2. **Claude 4/GPT-4V能力分析**
   - 最新多模态模型评测
   - 图表理解benchmark

---

## 七、关键文件路径

### 新建文件
- `backend/app/services/speech_script_rag.py` - 专业演讲稿生成
- `backend/app/services/script_editor.py` - 二次编辑服务
- `backend/app/services/rag_enhanced.py` - 增强RAG服务
- `backend/app/services/ppt_exporter_rag.py` - RAG驱动PPT
- `frontend/components/ScriptGenerator.tsx` - 生成界面
- `frontend/components/ScriptEditor.tsx` - 编辑器
- `frontend/components/RefineDialog.tsx` - 润色对话框
- `frontend/components/RAGContextPreview.tsx` - 上下文预览

### 需修改文件
- `backend/app/api/export.py` - 扩展7个新端点
- `backend/app/services/rag.py` - 添加元数据提取
- `backend/app/models/schemas.py` - 扩展数据模型
- `frontend/components/ExportMenu.tsx` - 增强导出选项
- `frontend/lib/store/useArchitectStore.ts` - 扩展状态

---

## 八、下一步行动

### 立即开始（推荐）
从Phase 1开始实施：
1. 创建 `ProfessionalPromptBuilder` 类
2. 实现流式生成pipeline
3. 开发二次编辑功能
4. 构建前端编辑器组件

### 或进一步讨论
- 技术细节澄清
- 优先级调整
- 资源分配

---

## 九、成功标准

### 最终验收
- [ ] 生成的演讲稿包含领域知识（非空洞模板）
- [ ] 演讲稿引用至少2个RAG具体案例
- [ ] 所有来源可追溯（引用标注）
- [ ] 用户反馈专业性评分 > 8/10
- [ ] 技术团队评估可用性 > 85%

### 里程碑
- Week 2: 演讲稿生成系统可用
- Week 3: RAG增强服务完成
- Week 5: PPT生成集成RAG
- Week 6: 完整用户体验交付

---

**项目预期工期**: 5-6周核心功能，7+周完整功能

**关键成功因素**:
1. 专业Prompt模板质量（CO-STAR框架）
2. RAG检索准确性（混合检索策略）
3. 二次编辑用户体验（流畅、直观）
4. 多provider稳定性（降级策略）

**风险应对**:
- 每周进度评审
- 快速迭代验证
- 用户反馈驱动优化
- 保持技术简化原则
