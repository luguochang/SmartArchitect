# RAG 知识库与 Prompt 管理系统设计方案

**日期：** 2026-01-20
**状态：** 技术方案待讨论
**优先级：** ⭐⭐⭐⭐

---

## 核心问题

### 问题1：无用户认证的 RAG 存储策略

**现状：**
- 后端已实现 ChromaDB 向量数据库（`backend/app/services/rag.py`）
- API 端点已存在（`/api/rag/upload`, `/api/rag/search`）
- 前端完全未集成（缺少 `DocumentUploadModal.tsx`）
- **关键矛盾：** 系统无用户认证，但 RAG 需要持久化存储

**用户场景分析：**
1. **单用户本地部署** - 个人学习/内部使用，所有文档共享
2. **多用户共享知识库** - 团队协作，公共文档池
3. **临时会话知识库** - 仅在浏览器会话期间有效

---

## 方案设计

### 方案A：全局共享知识库（推荐 ⭐⭐⭐⭐⭐）

**设计理念：**
将 RAG 作为全局架构知识库，所有用户共享同一个向量数据库集合。

**技术架构：**
```
用户1 ──┐
用户2 ──┼──> ChromaDB 集合 "architecture_docs"
用户3 ──┘     （全局共享）
```

**实现细节：**

1. **后端保持现有设计：**
```python
# backend/app/services/rag.py
class RAGService:
    def __init__(self):
        self.collection_name = "architecture_docs"  # 全局唯一集合
        self.client = chromadb.PersistentClient(path="./chroma_data")

    def upload_document(self, file: UploadFile, metadata: dict = None):
        """上传文档到全局知识库"""
        # 添加上传时间戳作为元数据
        metadata = metadata or {}
        metadata["uploaded_at"] = datetime.now().isoformat()
        # 处理和向量化...
```

2. **前端新增组件：**
```typescript
// frontend/components/DocumentUploadModal.tsx
export function DocumentUploadModal() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const handleUpload = async () => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch('http://localhost:8000/api/rag/upload', {
      method: 'POST',
      body: formData
    });

    // 成功后自动刷新文档列表
  };

  return (
    <Modal>
      <input type="file" accept=".pdf,.md,.docx" onChange={...} />
      <button onClick={handleUpload}>上传到知识库</button>
    </Modal>
  );
}
```

3. **文档管理界面：**
```typescript
// frontend/components/DocumentLibrary.tsx
export function DocumentLibrary() {
  const [documents, setDocuments] = useState([]);

  // GET /api/rag/list-documents (需新增API)
  useEffect(() => {
    fetch('http://localhost:8000/api/rag/list-documents')
      .then(res => res.json())
      .then(data => setDocuments(data.documents));
  }, []);

  return (
    <div>
      <h3>全局知识库文档</h3>
      <ul>
        {documents.map(doc => (
          <li key={doc.id}>
            {doc.filename} ({doc.chunks}个片段)
            <button onClick={() => deleteDoc(doc.id)}>删除</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

**优点：**
- ✅ 实现简单，无需修改后端架构
- ✅ 所有用户共享架构知识，提升 AI 生成质量
- ✅ 适合团队协作场景
- ✅ ChromaDB 支持大规模文档（百万级）

**缺点：**
- ❌ 无法实现文档私有化
- ❌ 误删文档影响所有用户
- ❌ 需要管理员角色控制上传权限（可选）

**适用场景：**
- 个人本地部署
- 小团队内部使用
- 公共架构知识库

---

### 方案B：基于 Session 的临时知识库

**设计理念：**
使用浏览器 Session ID 作为虚拟用户标识，为每个会话创建独立集合。

**技术架构：**
```
用户1 (session_abc) ──> ChromaDB 集合 "docs_session_abc"
用户2 (session_xyz) ──> ChromaDB 集合 "docs_session_xyz"
                        （会话结束后可清理）
```

**实现细节：**

1. **后端生成 Session ID：**
```python
# backend/app/api/rag.py
from fastapi import Request, Response
import uuid

@router.post("/rag/init-session")
async def init_rag_session(response: Response):
    """初始化 RAG 会话，返回 session_id"""
    session_id = str(uuid.uuid4())
    response.set_cookie(key="rag_session_id", value=session_id, max_age=86400)

    # 创建会话专属集合
    collection_name = f"docs_session_{session_id}"
    rag_service.create_collection(collection_name)

    return {"session_id": session_id, "collection": collection_name}

@router.post("/rag/upload")
async def upload_document(request: Request, file: UploadFile):
    session_id = request.cookies.get("rag_session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="No RAG session")

    collection_name = f"docs_session_{session_id}"
    rag_service.upload_to_collection(collection_name, file)
```

2. **前端管理 Session：**
```typescript
// frontend/lib/ragSession.ts
export async function initRagSession() {
  const response = await fetch('/api/rag/init-session', {
    method: 'POST',
    credentials: 'include'  // 启用 Cookie
  });
  const { session_id } = await response.json();
  localStorage.setItem('rag_session_id', session_id);
  return session_id;
}
```

3. **定期清理过期集合：**
```python
# backend/app/tasks/cleanup.py
import asyncio
from datetime import datetime, timedelta

async def cleanup_expired_sessions():
    """每天清理超过7天未活跃的会话集合"""
    collections = rag_service.list_collections()
    for coll in collections:
        if coll.startswith("docs_session_"):
            last_update = coll.metadata.get("last_active")
            if datetime.now() - last_update > timedelta(days=7):
                rag_service.delete_collection(coll.name)
```

**优点：**
- ✅ 数据隔离，互不干扰
- ✅ 支持多用户并发
- ✅ 自动清理机制节省存储

**缺点：**
- ❌ 实现复杂度高
- ❌ Cookie 失效后数据丢失
- ❌ 无法跨设备访问
- ❌ 增加 ChromaDB 集合数量（性能影响）

**适用场景：**
- 公共 Demo 站点
- 临时测试需求

---

### 方案C：LocalStorage + 后端混合存储

**设计理念：**
文档元数据存储在浏览器 LocalStorage，向量数据存储在后端统一集合，通过标签过滤。

**技术架构：**
```
前端 LocalStorage:
{
  "user_docs": ["doc1_hash", "doc2_hash"],
  "doc1_hash": { filename: "架构图.pdf", chunks: 5 }
}

后端 ChromaDB:
Collection "architecture_docs"
├── Chunk 1 (metadata: {doc_hash: "doc1_hash", owner: "local"})
├── Chunk 2 (metadata: {doc_hash: "doc1_hash", owner: "local"})
```

**实现细节：**

1. **前端管理文档列表：**
```typescript
// frontend/lib/localRag.ts
export function getUserDocuments(): string[] {
  const stored = localStorage.getItem('rag_user_docs');
  return stored ? JSON.parse(stored) : [];
}

export function addUserDocument(docHash: string, metadata: any) {
  const docs = getUserDocuments();
  docs.push(docHash);
  localStorage.setItem('rag_user_docs', JSON.stringify(docs));
  localStorage.setItem(`rag_doc_${docHash}`, JSON.stringify(metadata));
}
```

2. **后端搜索时过滤：**
```python
@router.post("/rag/search")
async def search_documents(request: SearchRequest):
    # 获取用户上传的文档 hash 列表（从请求体传入）
    user_doc_hashes = request.user_doc_hashes or []

    # 在全局集合中搜索，但只返回用户文档的结果
    results = rag_service.search(
        query=request.query,
        filter={"doc_hash": {"$in": user_doc_hashes}}  # ChromaDB 过滤语法
    )
    return results
```

**优点：**
- ✅ 兼顾全局共享和个人隔离
- ✅ 跨设备访问（通过导出/导入 LocalStorage）
- ✅ 后端只存一份向量数据

**缺点：**
- ❌ LocalStorage 有大小限制（5-10MB）
- ❌ 清空浏览器数据后丢失
- ❌ 需要前后端协作过滤逻辑

**适用场景：**
- 个人使用为主，偶尔共享
- 对数据持久性要求不高

---

## Prompt 提示词管理系统设计

### 需求分析

**用户场景：**
1. **快速选择预设 Prompt** - 常见任务（架构优化、安全加固、性能优化）
2. **自定义 Prompt 模板** - 用户可保存常用提示词
3. **Prompt 历史记录** - 查看和重用历史输入

### 技术方案

#### 1. 预设 Prompt 库（硬编码）

**后端配置：**
```python
# backend/app/services/prompt_templates.py
PRESET_PROMPTS = {
    "architecture-optimize": {
        "id": "architecture-optimize",
        "name": "架构优化建议",
        "category": "optimization",
        "template": "请分析当前架构图，提供优化建议：\n1. 性能瓶颈分析\n2. 可扩展性改进\n3. 成本优化方案",
        "icon": "🚀",
        "tags": ["optimization", "architecture"]
    },
    "security-review": {
        "id": "security-review",
        "name": "安全加固审查",
        "category": "security",
        "template": "对当前架构进行安全审计：\n1. 暴露面分析\n2. 数据流安全性\n3. 认证授权机制\n4. 加密传输建议",
        "icon": "🔒",
        "tags": ["security", "audit"]
    },
    "cost-analysis": {
        "id": "cost-analysis",
        "name": "成本分析",
        "category": "business",
        "template": "分析架构的云服务成本：\n1. 计算资源评估\n2. 存储成本\n3. 网络流量费用\n4. 优化建议",
        "icon": "💰",
        "tags": ["cost", "cloud"]
    },
    "microservice-split": {
        "id": "microservice-split",
        "name": "微服务拆分建议",
        "category": "refactor",
        "template": "建议如何将单体架构拆分为微服务：\n1. 服务边界划分\n2. 数据库拆分策略\n3. 通信机制设计\n4. 迁移路径",
        "icon": "🔀",
        "tags": ["microservice", "refactor"]
    }
}

@router.get("/prompts/presets")
async def get_preset_prompts():
    """获取所有预设 Prompt"""
    return {"prompts": list(PRESET_PROMPTS.values())}

@router.get("/prompts/presets/{prompt_id}")
async def get_preset_prompt(prompt_id: str):
    """获取单个预设 Prompt"""
    if prompt_id not in PRESET_PROMPTS:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return PRESET_PROMPTS[prompt_id]
```

**前端快速选择组件：**
```typescript
// frontend/components/PromptQuickSelect.tsx
import { useState, useEffect } from 'react';

interface Prompt {
  id: string;
  name: string;
  template: string;
  icon: string;
  category: string;
}

export function PromptQuickSelect({ onSelect }: { onSelect: (text: string) => void }) {
  const [presets, setPresets] = useState<Prompt[]>([]);
  const [category, setCategory] = useState<string>('all');

  useEffect(() => {
    fetch('http://localhost:8000/api/prompts/presets')
      .then(res => res.json())
      .then(data => setPresets(data.prompts));
  }, []);

  const filteredPrompts = category === 'all'
    ? presets
    : presets.filter(p => p.category === category);

  return (
    <div className="prompt-quick-select">
      <h4>快速选择提示词</h4>

      {/* 分类标签 */}
      <div className="categories">
        <button onClick={() => setCategory('all')}>全部</button>
        <button onClick={() => setCategory('optimization')}>优化</button>
        <button onClick={() => setCategory('security')}>安全</button>
        <button onClick={() => setCategory('business')}>业务</button>
        <button onClick={() => setCategory('refactor')}>重构</button>
      </div>

      {/* Prompt 卡片 */}
      <div className="prompt-grid">
        {filteredPrompts.map(prompt => (
          <div
            key={prompt.id}
            className="prompt-card"
            onClick={() => onSelect(prompt.template)}
          >
            <span className="icon">{prompt.icon}</span>
            <span className="name">{prompt.name}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**集成到聊天界面：**
```typescript
// frontend/components/AiControlPanel.tsx (修改)
export function AiControlPanel() {
  const [userInput, setUserInput] = useState('');
  const [showPromptSelect, setShowPromptSelect] = useState(false);

  const handlePromptSelect = (promptText: string) => {
    setUserInput(promptText);  // 填充到输入框
    setShowPromptSelect(false);
  };

  return (
    <div>
      {/* 快速选择按钮 */}
      <button onClick={() => setShowPromptSelect(!showPromptSelect)}>
        ⚡ 快速提示词
      </button>

      {/* 弹出选择器 */}
      {showPromptSelect && (
        <PromptQuickSelect onSelect={handlePromptSelect} />
      )}

      {/* 聊天输入框 */}
      <textarea
        value={userInput}
        onChange={e => setUserInput(e.target.value)}
        placeholder="输入架构需求，或点击上方快速选择..."
      />
    </div>
  );
}
```

---

#### 2. 用户自定义 Prompt（LocalStorage 存储）

**实现方案：**
```typescript
// frontend/lib/customPrompts.ts
interface CustomPrompt {
  id: string;
  name: string;
  template: string;
  createdAt: string;
}

export function saveCustomPrompt(name: string, template: string): CustomPrompt {
  const prompts = getCustomPrompts();
  const newPrompt: CustomPrompt = {
    id: `custom_${Date.now()}`,
    name,
    template,
    createdAt: new Date().toISOString()
  };

  prompts.push(newPrompt);
  localStorage.setItem('custom_prompts', JSON.stringify(prompts));
  return newPrompt;
}

export function getCustomPrompts(): CustomPrompt[] {
  const stored = localStorage.getItem('custom_prompts');
  return stored ? JSON.parse(stored) : [];
}

export function deleteCustomPrompt(id: string) {
  const prompts = getCustomPrompts().filter(p => p.id !== id);
  localStorage.setItem('custom_prompts', JSON.stringify(prompts));
}
```

**前端管理界面：**
```typescript
// frontend/components/CustomPromptManager.tsx
export function CustomPromptManager() {
  const [prompts, setPrompts] = useState<CustomPrompt[]>([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editName, setEditName] = useState('');
  const [editTemplate, setEditTemplate] = useState('');

  useEffect(() => {
    setPrompts(getCustomPrompts());
  }, []);

  const handleSave = () => {
    const newPrompt = saveCustomPrompt(editName, editTemplate);
    setPrompts([...prompts, newPrompt]);
    setIsEditing(false);
    setEditName('');
    setEditTemplate('');
  };

  return (
    <div>
      <h3>我的自定义提示词</h3>

      {/* 自定义 Prompt 列表 */}
      <ul>
        {prompts.map(prompt => (
          <li key={prompt.id}>
            <strong>{prompt.name}</strong>
            <p>{prompt.template.substring(0, 50)}...</p>
            <button onClick={() => deleteCustomPrompt(prompt.id)}>删除</button>
          </li>
        ))}
      </ul>

      {/* 新建按钮 */}
      <button onClick={() => setIsEditing(true)}>+ 新建提示词</button>

      {/* 编辑对话框 */}
      {isEditing && (
        <Modal>
          <input
            placeholder="提示词名称"
            value={editName}
            onChange={e => setEditName(e.target.value)}
          />
          <textarea
            placeholder="提示词内容模板"
            value={editTemplate}
            onChange={e => setEditTemplate(e.target.value)}
          />
          <button onClick={handleSave}>保存</button>
          <button onClick={() => setIsEditing(false)}>取消</button>
        </Modal>
      )}
    </div>
  );
}
```

---

#### 3. Prompt 历史记录（可选）

**LocalStorage 方案：**
```typescript
// frontend/lib/promptHistory.ts
export function addToHistory(promptText: string) {
  const history = getHistory();
  history.unshift({
    text: promptText,
    timestamp: new Date().toISOString()
  });

  // 只保留最近 50 条
  const trimmed = history.slice(0, 50);
  localStorage.setItem('prompt_history', JSON.stringify(trimmed));
}

export function getHistory() {
  const stored = localStorage.getItem('prompt_history');
  return stored ? JSON.parse(stored) : [];
}
```

**历史记录面板：**
```typescript
// frontend/components/PromptHistory.tsx
export function PromptHistory({ onSelect }: { onSelect: (text: string) => void }) {
  const [history, setHistory] = useState([]);

  useEffect(() => {
    setHistory(getHistory());
  }, []);

  return (
    <div className="prompt-history">
      <h4>历史提示词</h4>
      <ul>
        {history.map((item, idx) => (
          <li key={idx} onClick={() => onSelect(item.text)}>
            <span className="text">{item.text.substring(0, 60)}...</span>
            <span className="time">{new Date(item.timestamp).toLocaleString()}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
```

---

## 推荐实现方案

### RAG 知识库：方案 A（全局共享）⭐⭐⭐⭐⭐

**理由：**
1. ✅ **实现简单** - 后端已就绪，只需前端集成
2. ✅ **符合产品定位** - 架构设计工具，知识共享有利于提升 AI 质量
3. ✅ **适合目标用户** - 个人开发者、小团队内部使用
4. ✅ **无维护负担** - 无需清理机制、Session 管理

**后续扩展路径：**
- Phase 7: 添加文档标签和分类
- Phase 8: 支持文档权限（如果引入用户系统）

---

### Prompt 管理：混合方案（预设 + LocalStorage）⭐⭐⭐⭐⭐

**理由：**
1. ✅ **预设 Prompt** - 硬编码在后端，新手友好
2. ✅ **自定义 Prompt** - LocalStorage 存储，无需后端支持
3. ✅ **快速迭代** - 添加新预设只需修改配置文件

**UI 设计建议：**
```
┌─────────────────────────────────────────┐
│  ⚡ 快速提示词                           │
│  ┌─────┬─────┬─────┬─────┐              │
│  │ 🚀  │ 🔒  │ 💰  │ 🔀  │  ← 预设      │
│  │优化 │安全 │成本 │拆分 │              │
│  └─────┴─────┴─────┴─────┘              │
│                                          │
│  📌 我的自定义                           │
│  • 日志架构优化                          │
│  • K8s 部署建议                          │
│                                          │
│  🕒 历史记录                             │
│  • "分析支付流程安全性..." (10分钟前)    │
│  • "设计高并发架构..." (1小时前)         │
└─────────────────────────────────────────┘
```

---

## 实现清单

### Phase 6.1: RAG 知识库前端集成（2天）

**Day 1: 核心组件**
- [ ] 创建 `DocumentUploadModal.tsx` - 文档上传界面
- [ ] 创建 `DocumentLibrary.tsx` - 文档列表管理
- [ ] 集成到 `AiControlPanel.tsx` - 添加"知识库"标签页
- [ ] 后端新增 API：`GET /api/rag/list-documents`（返回已上传文档列表）

**Day 2: 测试与优化**
- [ ] 测试 PDF/Markdown/DOCX 上传流程
- [ ] 验证搜索功能（调用现有 `/api/rag/search`）
- [ ] 错误处理（文件格式错误、大小超限）
- [ ] UI 优化（上传进度条、文档预览）

---

### Phase 6.2: Prompt 管理系统（1-2天）

**Day 1: 预设 Prompt**
- [ ] 后端创建 `prompt_templates.py` - 预设 Prompt 配置
- [ ] 新增 API：`GET /api/prompts/presets`
- [ ] 前端创建 `PromptQuickSelect.tsx` - 快速选择组件
- [ ] 集成到聊天输入框

**Day 2: 自定义 + 历史（可选）**
- [ ] 创建 `CustomPromptManager.tsx` - 自定义管理界面
- [ ] 创建 `PromptHistory.tsx` - 历史记录面板
- [ ] LocalStorage 工具函数（`lib/customPrompts.ts`, `lib/promptHistory.ts`）
- [ ] 导入/导出功能（JSON 格式）

---

## 技术风险

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| RAG 首次查询慢（26秒） | 高 | 中 | 添加加载提示，后台预热模型 |
| LocalStorage 容量限制（5MB） | 低 | 低 | 限制自定义 Prompt 数量（最多 100 个）|
| 文档误删影响所有用户 | 中 | 高 | 添加删除确认对话框 + 软删除（标记为已删除）|
| ChromaDB 集合过大性能下降 | 低 | 中 | 定期清理过期文档，添加文档数量限制 |

---

## 未来扩展方向

### Phase 7+（可选）

1. **用户认证系统**
   - 基于 JWT 的轻量级认证
   - 文档私有化和权限管理

2. **Prompt 社区分享**
   - 公共 Prompt 仓库（GitHub Gist 集成）
   - 点赞、评论、Fork 机制

3. **智能 Prompt 推荐**
   - 根据架构图类型推荐合适的 Prompt
   - AI 自动优化用户输入的 Prompt

4. **多语言支持**
   - Prompt 国际化（中文/English）
   - AI 响应语言自适应

---

## 参考文档

- `backend/app/services/rag.py` - 现有 RAG 服务实现
- `backend/app/api/rag.py` - 现有 RAG API 端点
- `doc/2026-01-20/FLOWCHART_RECOGNITION_IMPLEMENTATION.md` - 实现模式参考
- `doc/TODO.md` - 功能状态跟踪

---

**文档状态：** 待用户确认方案
**下一步：** 确认 RAG 存储策略（全局 vs Session）和 Prompt 管理优先级后开始实现
