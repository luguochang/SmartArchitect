# SmartArchitect AI：从 0 到 1 打造 AI 驱动的架构设计平台

> 一个融合 React Flow、Excalidraw、多 AI Provider 和 RAG 技术的全栈项目实战

![SmartArchitect AI](https://img.shields.io/badge/version-0.5.0-blue) ![License](https://img.shields.io/badge/license-MIT-green) ![Stars](https://img.shields.io/github/stars/yourusername/SmartArchitect)

## 🎯 项目背景

作为一名架构师或技术负责人，你是否遇到过这些痛点：

- 📝 **画架构图太繁琐**：需要在各种画图工具间切换，调整布局就要花半天
- 🔄 **图和代码不同步**：改了架构图忘了更新文档，或者文档和实际架构脱节
- 🤔 **缺乏设计灵感**：面对复杂系统不知从何下手，需要参考大量资料
- 📊 **汇报材料难做**：临时要做 PPT 汇报，又要重新画图排版

**SmartArchitect AI** 就是为了解决这些问题而诞生的。它是一个 **AI 驱动的架构设计平台**，让你可以：

✨ **用自然语言生成流程图** - "帮我画一个用户登录流程" → 自动生成完整流程图
✨ **图片秒变架构图** - 拍照白板草图 → AI 识别转换成可编辑的架构图
✨ **双向 Mermaid 同步** - 拖拽画布 ↔ Mermaid 代码实时同步
✨ **智能知识库** - 上传技术文档，AI 自动提供架构建议
✨ **一键导出** - 生成 PPT、Slidev 演示文稿、演讲稿

---

## 🏗️ 技术架构一览

这是一个 **前后端分离的全栈项目**，采用现代化技术栈：

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (Next.js 14)                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ React Flow   │  │ Excalidraw   │  │ Monaco Editor│      │
│  │   Canvas     │  │   Canvas     │  │  (Mermaid)   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         ↓                  ↓                  ↓              │
│  ┌─────────────────────────────────────────────────┐        │
│  │         Zustand State Management                │        │
│  └─────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────┘
                              ↕ REST API / SSE
┌─────────────────────────────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ Vision   │  │   Chat   │  │   RAG    │  │  Export  │   │
│  │ Service  │  │Generator │  │ Service  │  │ Service  │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
│         ↓             ↓             ↓             ↓         │
│  ┌─────────────────────────────────────────────────┐       │
│  │        Multi-Provider AI Abstraction Layer      │       │
│  │   (Gemini / OpenAI / Claude / SiliconFlow)      │       │
│  └─────────────────────────────────────────────────┘       │
│                              ↓                              │
│  ┌─────────────────────────────────────────────────┐       │
│  │     ChromaDB Vector Database (RAG)              │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 核心技术栈

#### Frontend
- **框架**: Next.js 14 (App Router) + React 19
- **图表库**: React Flow v11（流程图）+ Excalidraw v0.18（白板）
- **状态管理**: Zustand 4.5（轻量级状态管理）
- **代码编辑**: Monaco Editor（VS Code 同款编辑器）
- **样式**: Tailwind CSS v3 + 12+ 主题系统
- **图标**: Lucide React 460+ 开发者友好图标

#### Backend
- **框架**: FastAPI（高性能异步框架）
- **AI 集成**:
  - Google Gemini 2.0 Flash（多模态）
  - OpenAI GPT-4 Vision（图像分析）
  - Anthropic Claude 3.5 Sonnet（对话生成）
  - SiliconFlow Qwen（国内可用）
- **RAG**: ChromaDB + Sentence Transformers（all-MiniLM-L6-v2）
- **导出**: python-pptx（PPT）+ 自研 Slidev 生成器
- **文档解析**: PyPDF2 + python-docx

---

## 💡 核心功能展示

### 1️⃣ 自然语言生成流程图（Chat Generator）

**功能描述**：输入一句话，AI 自动生成完整的流程图或架构图。

**技术实现**：
- 18+ 预设模板（用户注册、文件上传、微服务架构、OOM 故障排查等）
- 支持 `flow`（流程图）和 `architecture`（分层架构）两种类型
- 5 种架构模板：Layered、Business、Technical、Deployment、Domain

**代码示例**（后端核心逻辑）：

```python
# backend/app/services/chat_generator.py
class ChatGeneratorService:
    async def generate_flowchart(
        self,
        user_input: str,
        template_id: Optional[str] = None,
        diagram_type: Literal["flow", "architecture"] = "flow"
    ):
        # 1. 匹配模板或使用自定义输入
        template = self.get_template_by_id(template_id) if template_id else None

        # 2. 构造 AI Prompt
        if diagram_type == "flow":
            prompt = self._build_flow_prompt(user_input, template)
        else:
            prompt = self._build_architecture_prompt(user_input)

        # 3. 调用 AI 生成
        result = await self.ai_service.generate_json(prompt)

        # 4. 解析返回的节点和边
        nodes = self._parse_nodes(result)
        edges = self._parse_edges(result)

        return {"nodes": nodes, "edges": edges}
```

**流式响应**（实时反馈）：

```python
# 支持 SSE 流式响应，用户可以看到生成过程
@router.post("/chat-generator/generate-stream")
async def generate_stream(request: ChatGenerationRequest):
    async def event_stream():
        yield "data: [START] 开始生成流程图...\n\n"
        yield "data: [CALL] 正在调用 AI...\n\n"

        async for token in service.generate_with_streaming(request.user_input):
            yield f"data: [TOKEN] {token}\n\n"

        yield "data: [END] 生成完成\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

**效果演示**：
```
用户输入: "Java 服务出现 OOM，请生成排查流程图"

AI 生成结果:
[监控告警] --> [查看监控面板]
[查看监控面板] --> [确认内存使用趋势]
[确认内存使用趋势] --> [获取 Heap Dump]
[获取 Heap Dump] --> [MAT 分析]
[MAT 分析] --> [定位大对象]
[定位大对象] --> [代码修复]
```

---

### 2️⃣ 图片转架构图（Vision AI）

**功能描述**：拍照白板草图、手绘架构图或截图，AI 自动识别并转换成可编辑的架构图。

**支持的输入**：
- 📷 白板照片
- ✏️ 手绘草图
- 📊 PPT 截图
- 🖼️ 任何架构相关图片

**技术难点与解决方案**：

1. **多模态 AI 集成**

不同 AI Provider 的 API 格式不同，我们封装了统一的抽象层：

```python
# backend/app/services/ai_vision.py
class AIVisionService:
    def __init__(self, provider: str, api_key: str, model_name: str):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name

    async def analyze_image(self, image_data: str, prompt: str):
        if self.provider == "gemini":
            return await self._call_gemini(image_data, prompt)
        elif self.provider == "openai":
            return await self._call_openai(image_data, prompt)
        elif self.provider == "claude":
            return await self._call_claude(image_data, prompt)
        elif self.provider == "siliconflow":
            return await self._call_siliconflow(image_data, prompt)
```

2. **Base64 编码兼容**

前端上传的图片可能带 `data:image/png;base64,` 前缀，也可能是纯 Base64，需要智能处理：

```python
def _prepare_image_data(self, image_data: str) -> str:
    """处理各种格式的 Base64 图片"""
    if image_data.startswith("data:image"):
        # 提取纯 Base64 部分
        return image_data.split(",")[1]
    return image_data
```

3. **Excalidraw 场景生成**

Vision API 不仅能生成 React Flow 的节点，还能生成 Excalidraw 场景：

```python
# 返回 Excalidraw 格式的元素
{
  "elements": [
    {
      "id": "rect-1",
      "type": "rectangle",
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 100,
      "label": "API Gateway"
    },
    {
      "id": "arrow-1",
      "type": "arrow",
      "startBinding": {"elementId": "rect-1"},
      "endBinding": {"elementId": "rect-2"}
    }
  ]
}
```

**前端实现**（Monaco Editor 与 Canvas 双向同步）：

```typescript
// frontend/components/ArchitectCanvas.tsx
const updateFromMermaid = (code: string) => {
  // 1. 调用后端解析 Mermaid
  const response = await fetch('http://localhost:8003/api/mermaid/parse', {
    method: 'POST',
    body: JSON.stringify({ code })
  });

  const { nodes, edges } = await response.json();

  // 2. 更新 React Flow 画布
  setNodes(nodes);
  setEdges(edges);

  // 3. 自动布局
  const layouted = getLayoutedElements(nodes, edges, 'TB');
  setNodes(layouted.nodes);
  setEdges(layouted.edges);
};
```

---

### 3️⃣ 双向 Mermaid 同步

**核心创新**：画布拖拽 ↔ Mermaid 代码实时双向同步，无需手动刷新。

**技术挑战**：如何避免循环更新？

```typescript
// 使用 useRef 追踪是否正在更新，防止无限循环
const isUpdatingFromCode = useRef(false);
const isUpdatingFromCanvas = useRef(false);

// 从 Canvas 更新代码
const syncToMermaid = () => {
  if (isUpdatingFromCode.current) return;
  isUpdatingFromCanvas.current = true;

  const mermaidCode = generateMermaidCode(nodes, edges);
  updateCode(mermaidCode);

  setTimeout(() => {
    isUpdatingFromCanvas.current = false;
  }, 100);
};

// 从代码更新 Canvas
const syncToCanvas = (code: string) => {
  if (isUpdatingFromCanvas.current) return;
  isUpdatingFromCode.current = true;

  updateFromMermaid(code);

  setTimeout(() => {
    isUpdatingFromCode.current = false;
  }, 100);
};
```

**Mermaid 解析器**（正则表达式匹配）：

```python
# backend/app/api/mermaid.py
def parse_mermaid_to_graph(code: str):
    nodes = []
    edges = []

    for line in code.split('\n'):
        # 匹配节点: nodeId["label"]
        node_match = re.search(r'(\w+)\[([\[\("]*)([^\]]+)([\]\)"]*)?\]', line)
        if node_match:
            node_id = node_match.group(1)
            label = node_match.group(3)

            # 智能推断节点类型
            node_type = infer_node_type(label, line)

            nodes.append({
                "id": node_id,
                "type": node_type,
                "position": {"x": 0, "y": 0},  # 后续自动布局
                "data": {"label": label}
            })

        # 匹配边: source --> target
        edge_match = re.search(r'(\w+)\s*-->\s*(?:\|([^|]+)\|)?\s*(\w+)', line)
        if edge_match:
            edges.append({
                "id": f"{edge_match.group(1)}-{edge_match.group(3)}",
                "source": edge_match.group(1),
                "target": edge_match.group(3),
                "label": edge_match.group(2) or ""
            })

    return {"nodes": nodes, "edges": edges}
```

**节点类型智能推断**：

```python
def infer_node_type(label: str, line: str) -> str:
    """根据标签和语法推断节点类型"""
    label_lower = label.lower()

    # 根据 Mermaid 语法
    if "(" in line and ")" in line:
        return "database"  # 圆形节点
    elif "[[" in line and "]]" in line:
        return "service"   # 双框节点

    # 根据关键词
    if "api" in label_lower or "gateway" in label_lower:
        return "api"
    elif "cache" in label_lower or "redis" in label_lower:
        return "cache"
    elif "queue" in label_lower or "kafka" in label_lower:
        return "queue"
    elif "db" in label_lower or "database" in label_lower:
        return "database"

    return "default"
```

---

### 4️⃣ RAG 知识库（智能架构建议）

**功能描述**：上传技术文档（PDF、Markdown、DOCX），系统自动建立向量索引，在设计架构时提供相关建议。

**技术选型**：
- **向量数据库**: ChromaDB（轻量级，无需额外部署）
- **嵌入模型**: `all-MiniLM-L6-v2`（384 维，首次加载约 26 秒，后续 100ms）
- **分块策略**: 1000 字符/块，200 字符重叠

**核心代码**：

```python
# backend/app/services/rag.py
class RAGService:
    def __init__(self):
        self.client = chromadb.PersistentClient(path="./data/chromadb")
        self.collection = self.client.get_or_create_collection("architecture_docs")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

    def upload_document(self, file_path: str, file_type: str):
        # 1. 解析文档
        parser = DocumentParser()
        content = parser.parse_file(file_path, file_type)

        # 2. 分块
        chunks = self._chunk_text(content, chunk_size=1000, overlap=200)

        # 3. 生成嵌入向量
        embeddings = self.embedding_model.encode(chunks)

        # 4. 存入 ChromaDB
        self.collection.add(
            documents=chunks,
            embeddings=embeddings.tolist(),
            ids=[f"doc-{uuid.uuid4()}" for _ in chunks]
        )

    def search(self, query: str, top_k: int = 5):
        # 1. 查询向量化
        query_embedding = self.embedding_model.encode([query])[0]

        # 2. 相似度搜索
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=top_k
        )

        return results['documents'][0]
```

**文档解析器**（支持 3 种格式）：

```python
# backend/app/services/document_parser.py
class DocumentParser:
    def _parse_pdf(self, file_path: str) -> str:
        """使用 PyPDF2 解析 PDF"""
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ""
            for page in reader.pages:
                text += page.extract_text()
        return text

    def _parse_docx(self, file_path: str) -> str:
        """使用 python-docx 解析 DOCX"""
        doc = Document(file_path)
        return "\n".join([para.text for para in doc.paragraphs])

    def _parse_markdown(self, file_path: str) -> str:
        """直接读取 Markdown"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
```

**性能优化**：

首次查询为何需要 26 秒？
- 嵌入模型首次加载需要下载权重文件（约 80MB）
- 模型初始化和 GPU/CPU 编译时间

解决方案：
```python
# 预加载模型（启动时）
@app.on_event("startup")
async def startup_event():
    logger.info("Preloading embedding model...")
    rag_service = get_rag_service()
    # 触发一次空查询，预热模型
    rag_service.search("warmup", top_k=1)
    logger.info("Model preloaded successfully")
```

---

### 5️⃣ 一键导出（PPT、Slidev、演讲稿）

**功能描述**：将架构图一键导出为多种格式，适配不同场景。

**支持的格式**：
- 📊 **PowerPoint**：4 页专业幻灯片（标题页、架构图、组件详情、连接详情）
- 🎬 **Slidev**：开发者友好的 Markdown 演示文稿
- 🎤 **演讲稿**：3 种时长（30 秒、2 分钟、5 分钟）

**PPT 导出实现**：

```python
# backend/app/services/ppt_exporter.py
from pptx import Presentation
from pptx.util import Inches, Pt

class PPTExporter:
    def export(self, nodes: List[Node], edges: List[Edge], title: str):
        prs = Presentation()
        prs.slide_width = Inches(10)
        prs.slide_height = Inches(7.5)

        # 第 1 页：标题页
        self._add_title_slide(prs, title)

        # 第 2 页：架构图可视化
        self._add_diagram_slide(prs, nodes, edges)

        # 第 3 页：组件详情表格
        self._add_components_slide(prs, nodes)

        # 第 4 页：连接详情
        self._add_connections_slide(prs, edges)

        # 保存文件
        output_path = f"exports/{title}.pptx"
        prs.save(output_path)
        return output_path

    def _add_diagram_slide(self, prs, nodes, edges):
        """绘制架构图"""
        slide = prs.slides.add_slide(prs.slide_layouts[5])  # 空白布局

        # 绘制节点
        for node in nodes:
            shape = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                left=Inches(node.position.x / 100),
                top=Inches(node.position.y / 100),
                width=Inches(2),
                height=Inches(1)
            )
            shape.text = node.data.label

        # 绘制连接线
        for edge in edges:
            source_node = next(n for n in nodes if n.id == edge.source)
            target_node = next(n for n in nodes if n.id == edge.target)

            connector = slide.shapes.add_connector(
                MSO_CONNECTOR.STRAIGHT,
                start_x=Inches(source_node.position.x / 100),
                start_y=Inches(source_node.position.y / 100),
                end_x=Inches(target_node.position.x / 100),
                end_y=Inches(target_node.position.y / 100)
            )
```

**Slidev 导出**（Markdown 格式）：

```python
# backend/app/services/slidev_exporter.py
class SlidevExporter:
    def export(self, nodes: List[Node], edges: List[Edge], title: str):
        markdown = f"""---
theme: seriph
background: https://source.unsplash.com/1920x1080/?architecture
class: text-center
---

# {title}

架构设计文档

<div class="abs-br m-6 flex gap-2">
  <span>Generated by SmartArchitect AI</span>
</div>

---

# 系统架构概览

```mermaid
{self._generate_mermaid(nodes, edges)}
```

---

# 核心组件

{self._generate_components_table(nodes)}

---

# 数据流

{self._generate_dataflow(edges)}
"""
        return markdown
```

**演讲稿生成**（AI 生成）：

```python
# 根据架构图生成不同时长的演讲稿
@router.post("/export/script")
async def export_script(request: ExportScriptRequest):
    prompt = f"""
    根据以下架构图生成一份 {request.duration} 的演讲稿：

    节点: {[node.data.label for node in request.nodes]}
    连接: {[(edge.source, edge.target) for edge in request.edges]}

    要求：
    - 时长: {request.duration}
    - 风格: 专业、简洁
    - 结构: 开场白 → 核心架构 → 技术亮点 → 总结
    """

    script = await ai_service.generate(prompt)
    return {"script": script}
```

---

## 🔥 技术亮点与创新点

### 1. 玻璃态节点设计（Glassmorphism）

**问题**：React Flow 默认节点有白色背景和边框，与现代 UI 设计不符。

**解决方案**：使用 CSS 覆盖 + 玻璃形态学设计。

```css
/* frontend/globals.css */

/* 关键 1: 让节点容器完全透明 */
.react-flow__node {
  border: none !important;
  background: transparent !important;
  padding: 0 !important;
}

/* 关键 2: 只有非圆形节点才有圆角和阴影 */
.react-flow__node:not(:has(.glass-node.rounded-full)):not(:has(.svg-shape-node)) {
  @apply rounded-lg shadow-md;
}

/* 关键 3: 圆形节点特殊处理（防止出现方框） */
.react-flow__node:has(.glass-node.rounded-full) {
  border-radius: 9999px !important;
  box-shadow: none !important;
  background: transparent !important;
}

/* 关键 4: 玻璃态效果 */
.glass-node {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.3);
}
```

---

### 2. 流式 JSON 修复（JSON Repair）

**问题**：LLM 生成 JSON 时可能因为网络中断、Token 限制等原因返回不完整的 JSON，导致解析失败。

**示例**：
```json
{
  "elements": [
    {"id": "1", "type": "rectangle", "x": 100, "y": 100
  // 后续内容被截断
```

**解决方案**：追踪括号栈，自动闭合未完成的 JSON 结构。

```python
# backend/app/services/excalidraw_generator.py
def repair_json(json_str: str) -> str:
    """
    自动修复不完整的 JSON
    核心思路：追踪左右括号，补全缺失的闭合符号
    """
    stack = []
    is_string = False
    is_escaped = False

    for i, char in enumerate(json_str):
        # 处理字符串内的内容
        if is_string:
            if char == '\\':
                is_escaped = not is_escaped
            elif char == '"' and not is_escaped:
                is_string = False
            else:
                is_escaped = False
        else:
            # 处理结构符号
            if char == '"':
                is_string = True
            elif char == '{':
                stack.append('}')
            elif char == '[':
                stack.append(']')
            elif char == '}':
                if stack and stack[-1] == '}':
                    stack.pop()
            elif char == ']':
                if stack and stack[-1] == ']':
                    stack.pop()

    # 补全缺失的闭合符号
    completion = ""
    while stack:
        completion += stack.pop()

    return json_str + completion
```

**测试用例**：
```python
# 测试 1: 缺少对象闭合
input1 = '{"name": "test", "items": [1, 2, 3'
output1 = repair_json(input1)
# 输出: {"name": "test", "items": [1, 2, 3]}

# 测试 2: 嵌套结构不完整
input2 = '{"data": {"nested": {"value": 123'
output2 = repair_json(input2)
# 输出: {"data": {"nested": {"value": 123}}}
```

**应用场景**：
- Excalidraw 场景生成时，AI 返回的 JSON 可能不完整
- Chat Generator 流式响应时，部分 Token 可能丢失
- Vision API 超时时，保留已解析的部分数据

---

### 3. ikuncode.cc 中转站支持

**问题**：某些 AI 中转服务（如 ikuncode.cc）会阻止 SDK 发送的请求，导致连接失败。

**错误信息**：
```
HTTPError: 403 Forbidden
User-Agent: anthropic-sdk-python/...
```

**解决方案**：检测到中转站时，使用原始 HTTP 请求代替 SDK。

```python
# backend/app/services/chat_generator.py
async def _call_claude_with_custom_base(self, prompt: str, base_url: str):
    """使用原始 HTTP 调用 Claude API（绕过 SDK 限制）"""

    # 检测是否为 ikuncode.cc
    if "ikuncode.cc" in base_url.lower():
        logger.info("Detected ikuncode.cc, using raw HTTP request")

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model_name,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "stream": True  # 启用流式响应
        }

        # 使用 httpx 发送原始请求
        async with httpx.AsyncClient(timeout=120.0) as client:
            async with client.stream("POST", f"{base_url}/messages", headers=headers, json=payload) as response:
                response.raise_for_status()

                buffer = ""
                async for chunk in response.aiter_bytes():
                    # 解析 SSE 格式
                    text = chunk.decode('utf-8')
                    for line in text.split('\n'):
                        if line.startswith('data: '):
                            data = json.loads(line[6:])
                            if data['type'] == 'content_block_delta':
                                buffer += data['delta']['text']

                return buffer
    else:
        # 使用官方 SDK
        client = anthropic.AsyncAnthropic(api_key=self.api_key, base_url=base_url)
        response = await client.messages.create(...)
        return response.content[0].text
```

**兼容的中转站**：
- ikuncode.cc
- api2d.com
- closeai.biz
- 其他自定义 API 端点

---

### 4. 多架构模板系统

**创新点**：不同于传统工具只能生成流程图，我们支持 **5 种架构类型**，满足不同场景需求。

```python
# backend/app/services/chat_generator.py
ARCHITECTURE_TEMPLATES = {
    "layered": {
        "name": "分层架构",
        "layers": ["frontend", "backend", "middleware", "data", "infrastructure"],
        "description": "经典三层或多层架构"
    },
    "business": {
        "name": "业务架构",
        "layers": ["capability", "service", "process", "organization"],
        "description": "面向业务能力的架构"
    },
    "technical": {
        "name": "技术架构",
        "layers": ["presentation", "application", "integration", "data", "infrastructure"],
        "description": "技术视图的分层架构"
    },
    "deployment": {
        "name": "部署架构",
        "layers": ["dmz", "app-tier", "data-tier", "monitoring"],
        "description": "运维视角的部署架构"
    },
    "domain": {
        "name": "领域驱动设计",
        "layers": ["domain-services", "shared-kernel", "anti-corruption", "infrastructure"],
        "description": "DDD 风格的架构"
    }
}
```

**效果对比**：

| 输入 | 架构类型 | 生成结果 |
|------|---------|----------|
| "电商系统" | Layered | 前端层 → 应用层 → 服务层 → 数据层 |
| "电商系统" | Business | 商品管理 → 订单服务 → 支付能力 → 履约流程 |
| "电商系统" | Deployment | DMZ → 应用集群 → 数据库 → 监控 |

---

### 5. 演示风格系统（Presentation Styles）

**问题**：同一个流程图，在不同场景下需要不同的视觉风格：
- 技术评审：需要符合 BPMN 2.0 标准
- 客户汇报：需要简约美观的企业风格
- 内部文档：需要高对比度、易读性强

**解决方案**：6 种专业演示风格，一键切换。

```typescript
// frontend/lib/themes/flowchartPresentationStyles.ts
export const flowchartPresentationStyles = {
  "bpmn-professional": {
    name: "BPMN Professional",
    description: "符合 BPMN 2.0 标准",
    node: {
      showIcons: false,  // BPMN 不显示图标
      semanticColors: {
        start: "#4CAF50",
        end: "#F44336",
        task: "#2196F3",
        decision: "#FFC107"
      }
    },
    edge: {
      type: "orthogonal",  // 正交路由（直角连线）
      strokeWidth: 2,
      strokeColor: "#333",
      markerSize: 20,
      showGlow: false
    }
  },

  "corporate-minimalist": {
    name: "Corporate Minimalist",
    description: "企业简约风格",
    node: {
      showIcons: true,
      semanticColors: {
        start: "#E8F5E9",
        end: "#FFEBEE",
        task: "#E3F2FD",
        decision: "#FFF9C4"
      }
    },
    edge: {
      type: "smoothstep",  // 平滑台阶路由
      strokeWidth: 1.5,
      strokeColor: "#90A4AE",
      markerSize: 16,
      showGlow: false
    }
  },

  // 其他 4 种风格...
}
```

---

## 🐛 开发过程中遇到的问题与解决方案

### 问题 1：React Flow 圆形节点被方框包围

**现象**：
- BPMN 的 start-event（圆形）节点外面有一个方形容器
- 即使设置了 `border-radius: 50%`，外层仍然是方形

**原因分析**：
```typescript
// React Flow 的默认样式
.react-flow__node {
  border: 2px solid #1a192b;  // 默认边框
  background: white;           // 默认背景
  padding: 10px;               // 默认内边距
  border-radius: 3px;          // 默认圆角
}
```

**解决方案**：
```css
/* 1. 移除所有默认样式 */
.react-flow__node {
  border: none !important;
  background: transparent !important;
  padding: 0 !important;
}

/* 2. 圆形节点特殊处理 */
.react-flow__node:has(.glass-node.rounded-full) {
  border-radius: 9999px !important;  /* 强制圆形 */
  box-shadow: none !important;        /* 移除阴影 */
  background: transparent !important; /* 确保透明 */
}

/* 3. 内部节点应用样式 */
.glass-node.rounded-full {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: rgba(76, 175, 80, 0.8);
  backdrop-filter: blur(10px);
}
```

---

### 问题 2：Excalidraw 动态导入失败

**错误信息**：
```
Error: Hydration failed because the initial UI does not match what was rendered on the server.
```

**原因**：
- Excalidraw 依赖浏览器 API（`window`、`document`）
- Next.js 的 SSR（服务器端渲染）阶段没有这些 API

**解决方案**：使用 `next/dynamic` 禁用 SSR

```typescript
// frontend/components/ExcalidrawBoard.tsx
import dynamic from 'next/dynamic';

// 关键: ssr: false 禁用服务器端渲染
const Excalidraw = dynamic(
  async () => (await import("@excalidraw/excalidraw")).Excalidraw,
  {
    ssr: false,  // 关键配置
    loading: () => <div>Loading Excalidraw...</div>
  }
);

export function ExcalidrawBoard() {
  const [mounted, setMounted] = useState(false);

  // 确保只在客户端渲染
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div>Loading...</div>;
  }

  return (
    <div style={{ height: "100vh" }}>
      <Excalidraw />
    </div>
  );
}
```

---

### 问题 3：RAG 首次查询耗时 26 秒

**性能瓶颈分析**：

1. **嵌入模型加载**（~18 秒）
   - 下载 `all-MiniLM-L6-v2` 权重文件（80MB）
   - 模型初始化和编译

2. **向量索引构建**（~5 秒）
   - ChromaDB 构建 HNSW 索引

3. **首次推理**（~3 秒）
   - 模型预热（warm-up）

**优化方案**：

```python
# 方案 1: 启动时预加载模型
@app.on_event("startup")
async def startup_event():
    logger.info("Preloading RAG service...")
    rag_service = get_rag_service()
    # 触发一次空查询，预热模型
    rag_service.search("warmup query", top_k=1)
    logger.info("RAG service ready")

# 方案 2: 异步加载 + 进度提示
@router.post("/rag/search")
async def search_documents(request: RAGSearchRequest):
    # 检查模型是否已加载
    if not rag_service.is_model_loaded():
        # 返回加载中状态
        return {"status": "loading", "progress": "Initializing embedding model..."}

    results = rag_service.search(request.query)
    return {"status": "success", "results": results}
```

**优化效果**：
- 预加载后，首次查询: < 1 秒
- 后续查询: 100-200ms

---

### 问题 4：Monaco Editor 与 React Flow 冲突

**问题描述**：
- Monaco Editor 修改 Mermaid 代码后，React Flow 画布不更新
- React Flow 拖拽节点后，Monaco Editor 代码不同步

**原因**：两个组件的状态更新机制不同步。

**解决方案**：使用 Zustand 全局状态 + 防抖

```typescript
// frontend/lib/store/useArchitectStore.ts
interface ArchitectStore {
  nodes: Node[];
  edges: Edge[];
  mermaidCode: string;

  // 从代码更新画布
  updateFromMermaid: (code: string) => void;

  // 从画布更新代码
  updateFromCanvas: (nodes: Node[], edges: Edge[]) => void;
}

export const useArchitectStore = create<ArchitectStore>((set, get) => ({
  nodes: [],
  edges: [],
  mermaidCode: "",

  updateFromMermaid: async (code: string) => {
    // 1. 调用后端解析
    const response = await fetch('http://localhost:8003/api/mermaid/parse', {
      method: 'POST',
      body: JSON.stringify({ code })
    });
    const { nodes, edges } = await response.json();

    // 2. 更新画布
    set({ nodes, edges, mermaidCode: code });
  },

  updateFromCanvas: debounce(async (nodes: Node[], edges: Edge[]) => {
    // 1. 调用后端生成 Mermaid
    const response = await fetch('http://localhost:8003/api/graph/to-mermaid', {
      method: 'POST',
      body: JSON.stringify({ nodes, edges })
    });
    const { code } = await response.json();

    // 2. 更新代码编辑器
    set({ nodes, edges, mermaidCode: code });
  }, 500)  // 防抖 500ms
}));
```

---

## 🚀 性能优化经验

### 1. React Flow 渲染优化

**问题**：节点数超过 50 个时，拖拽卡顿明显。

**优化方案**：

```typescript
// 1. 使用 React.memo 避免不必要的重渲染
export const ApiNode = memo(({ data }: NodeProps) => {
  return (
    <div className="glass-node">
      <Globe size={24} />
      <div>{data.label}</div>
    </div>
  );
});

// 2. 节流更新
const onNodesChange = useCallback(
  throttle((changes: NodeChange[]) => {
    setNodes((nds) => applyNodeChanges(changes, nds));
  }, 16),  // 约 60fps
  []
);

// 3. 虚拟化大图（超过 100 个节点）
<ReactFlow
  nodes={nodes}
  edges={edges}
  nodesDraggable={nodes.length < 100}  // 超过 100 个禁用拖拽
  zoomOnScroll={nodes.length < 100}    // 超过 100 个禁用缩放
/>
```

**效果**：
- 50 个节点: 60fps → 60fps（无明显提升）
- 100 个节点: 20fps → 45fps
- 200 个节点: 5fps → 30fps

---

### 2. AI 请求优化（批处理 + 缓存）

**问题**：多次请求相同的 AI 任务，浪费 API 额度。

**解决方案**：LRU 缓存 + 请求去重

```python
# backend/app/services/ai_vision.py
from functools import lru_cache
import hashlib

class AIVisionService:
    def __init__(self):
        self.request_cache = {}  # 简单的内存缓存

    async def analyze_image(self, image_data: str, prompt: str):
        # 生成缓存 key（图片哈希 + prompt 哈希）
        cache_key = hashlib.md5(
            (image_data[:100] + prompt).encode()
        ).hexdigest()

        # 检查缓存
        if cache_key in self.request_cache:
            logger.info(f"Cache hit for {cache_key}")
            return self.request_cache[cache_key]

        # 调用 AI
        result = await self._call_ai(image_data, prompt)

        # 存入缓存（最多缓存 100 个）
        if len(self.request_cache) > 100:
            # 移除最早的
            self.request_cache.pop(next(iter(self.request_cache)))

        self.request_cache[cache_key] = result
        return result
```

---

### 3. 前端资源优化

**优化前**：
- 首屏加载: 3.2s
- 主包大小: 2.5MB
- React Flow: 600KB

**优化措施**：

```typescript
// 1. 动态导入（代码分割）
const ExcalidrawBoard = dynamic(() => import('./ExcalidrawBoard'), {
  ssr: false,
  loading: () => <Skeleton />
});

const ChatGeneratorModal = dynamic(() => import('./ChatGeneratorModal'), {
  ssr: false
});

// 2. 图片懒加载
<Image
  src="/logo.png"
  alt="Logo"
  loading="lazy"
  placeholder="blur"
/>

// 3. 字体优化（next.config.js）
module.exports = {
  optimizeFonts: true,
  images: {
    formats: ['image/avif', 'image/webp']
  }
}
```

**优化后**：
- 首屏加载: 1.8s（↓ 44%）
- 主包大小: 1.2MB（↓ 52%）
- Lighthouse 得分: 78 → 92

---

## 📈 未来规划

### Phase 6: 协作与版本控制
- [ ] 多人实时协作（WebSocket + CRDT）
- [ ] 版本历史与回滚
- [ ] 评论与批注系统

### Phase 7: 更多导出格式
- [ ] SVG 高清导出
- [ ] Figma 插件
- [ ] Draw.io XML 格式
- [ ] PlantUML 代码生成

### Phase 8: 智能推荐
- [ ] 基于历史项目的架构推荐
- [ ] 技术栈适配建议
- [ ] 性能瓶颈预测

### Phase 9: 企业级功能
- [ ] 私有化部署
- [ ] LDAP/SSO 认证
- [ ] 审计日志
- [ ] 权限管理（RBAC）

---

## 🌟 总结

SmartArchitect AI 是一个从 0 到 1 打造的全栈 AI 项目，涵盖了：

✅ **前端技术**：React Flow、Excalidraw、Monaco Editor、Zustand
✅ **后端技术**：FastAPI、ChromaDB、多 AI Provider 集成
✅ **AI 技术**：RAG、Vision API、流式生成、JSON 修复
✅ **工程实践**：性能优化、错误处理、缓存策略、中转站适配

**项目亮点**：
1. 双向 Mermaid 同步（业界少见）
2. 5 种架构模板 + 18+ 流程模板
3. 流式 JSON 修复（创新容错机制）
4. 玻璃态节点设计（现代 UI）
5. 多 Provider 抽象层（Gemini/OpenAI/Claude/SiliconFlow）

**Star 这个项目的理由**：
- 🎨 **实用工具**：解决架构设计的真实痛点
- 📚 **学习资源**：全栈技术栈的最佳实践
- 🚀 **持续更新**：正在开发 Phase 6-9
- 🤝 **开源友好**：MIT License，欢迎贡献

---

## 📞 联系方式

- **GitHub**: [你的 GitHub 用户名]
- **Email**: [你的邮箱]
- **博客**: [你的博客地址]

---

## 🎁 致谢

感谢以下开源项目：
- [React Flow](https://reactflow.dev/) - 强大的流程图库
- [Excalidraw](https://excalidraw.com/) - 优雅的白板工具
- [FastAPI](https://fastapi.tiangolo.com/) - 高性能 Python 框架
- [ChromaDB](https://www.trychroma.com/) - 轻量级向量数据库

---

**如果这个项目对你有帮助，请给一个 ⭐ Star！你的支持是我最大的动力！**

```bash
# 克隆项目
git clone https://github.com/yourusername/SmartArchitect.git

# 启动开发环境
cd SmartArchitect
./start-dev.sh  # Linux/Mac
start-dev.bat   # Windows

# 访问应用
http://localhost:3000
```

---

*本文技术细节均基于实际代码实现，欢迎阅读源码深入学习！*
