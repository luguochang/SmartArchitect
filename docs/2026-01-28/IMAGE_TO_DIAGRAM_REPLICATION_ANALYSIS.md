# 图片流程图复刻技术分析报告

## 1. 项目概述

**分析对象**: flowpilot-beta (参考项目)
**分析目标**: 理解图片上传→AI分析→流程图复刻的完整技术方案
**应用场景**: 整合到SmartArchitect项目，支持Excalidraw和React Flow两种渲染方式
**分析日期**: 2026-01-28

---

## 2. FlowPilot-Beta核心技术方案

### 2.1 整体架构

**技术栈**:
- **前端**: Next.js 15 + React 19 + TypeScript
- **AI集成**: Vercel AI SDK v5.0.89 (统一多provider接口)
- **图形渲染**: draw.io embed + Excalidraw + SVG
- **AI模型**: Claude Sonnet 4.5 (claude-sonnet-4-5-20250929)

**数据流**:
```
用户上传图片
    ↓
FileReader转换为base64 data URL
    ↓
消息parts数组: [{type:'text'}, {type:'file', url:'data:image/png;base64,...'}]
    ↓
POST /api/chat 发送到后端
    ↓
提取fileParts并格式化为Claude多模态消息
    ↓
构造prompt: 当前图表XML/JSON + 用户输入 + 图片
    ↓
Claude Vision API分析图片结构
    ↓
流式返回draw.io XML / Excalidraw JSON / SVG
    ↓
前端解析并渲染到对应canvas
```

---

### 2.2 图片上传与Base64转换

**关键文件**: `features/chat-panel/utils/attachments.ts`

```typescript
export interface SerializedAttachment {
    url: string;        // data:image/png;base64,iVBORw0KG...
    mediaType: string;  // image/png
}

export async function serializeAttachments(
    fileList: File[]
): Promise<SerializedAttachment[]> {
    const attachments: SerializedAttachment[] = [];

    for (const file of fileList) {
        const dataUrl = await new Promise<string>((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result as string);
            reader.onerror = () => reject(new Error(`无法读取附件「${file.name}」`));
            reader.readAsDataURL(file);  // 核心：转换为data URL
        });

        attachments.push({
            url: dataUrl,
            mediaType: file.type,
        });
    }

    return attachments;
}
```

**要点**:
- ✅ 使用浏览器原生FileReader API，无需后端存储
- ✅ 支持多图片上传（数组处理）
- ✅ 保留MIME type信息用于AI识别
- ✅ 错误处理：文件读取失败时抛出友好提示

---

### 2.3 后端API消息格式化

**关键文件**: `app/api/chat/route.ts` (lines 104-181)

```typescript
// 1. 提取最后一条消息的文件部分
const fileParts = lastMessage.parts?.filter((part: any) => part.type === 'file') || [];

// 2. 格式化文本内容（包含当前图表状态）
const formattedTextContent = `
Current diagram XML:
"""xml
${xml || ''}
"""
User input:
"""md
${safeUserText}
"""
Render mode: ${outputMode === "svg" ? "svg-only" : "drawio-xml"}`;

// 3. 构造多模态消息内容
const contentParts: any[] = [
    { type: 'text', text: formattedTextContent }
];

// 4. 添加图片部分
for (const filePart of fileParts) {
    contentParts.push({
        type: 'image',
        image: filePart.url,      // data:image/png;base64,...
        mimeType: filePart.mediaType
    });
}

// 5. 更新最后一条用户消息
enhancedMessages = [
    ...enhancedMessages.slice(0, -1),
    { ...lastModelMessage, content: contentParts }
];
```

**Claude API特殊处理** (针对某些自定义端点):
```typescript
// 将 data:image/png;base64,xxx 转换为Claude原生格式
const match = imageUrl.match(/^data:([^;]+);base64,(.+)$/);
return {
    type: "image",
    source: {
        type: "base64",
        media_type: match[1],  // "image/png"
        data: match[2]          // 纯base64字符串（不含前缀）
    }
};
```

---

### 2.4 Prompt Engineering策略

#### 2.4.1 系统提示词（Excalidraw模式）

```typescript
const excalidrawSystemMessage = `
You are FlowPilot Excalidraw Expert. Output exactly one valid JSON object representing an Excalidraw scene, wrapped in a fenced \`\`\`json\`\`\` block.
Do NOT use any tool calls.

Priorities:
1. Valid JSON syntax (Standard Excalidraw Format).
2. Clear, hand-drawn style consistency.
3. Reasonable layout without overlaps.

Important:
- Use "arrow" type for connections. Use "startBinding" / "endBinding" to attach arrows to shapes.
- For "line", "arrow", "draw", "freedraw", the "points" array is MANDATORY (e.g. [[0,0], [50,50]]).
- Ensure all "id"s are unique strings.
- "groupIds" must be an array of strings if used.
- Do NOT output conversational text before or after the JSON block.
`;
```

**关键设计**:
- ✅ 明确输出格式：JSON对象 + 代码块包裹
- ✅ 禁用tool calls（避免AI尝试调用函数）
- ✅ 强调数据结构约束（points数组必须存在、id唯一性）
- ✅ 要求无额外文本（纯数据输出）

#### 2.4.2 用户消息格式

```text
Current diagram XML:
"""xml
<mxGraphModel>...</mxGraphModel>
"""
User input:
"""md
根据这张流程图生成对应的架构图
"""
Render mode: drawio-xml
```

**设计思路**:
- ✅ 提供当前状态（便于增量更新）
- ✅ 明确用户意图（自然语言描述）
- ✅ 指定输出格式（drawio/svg/excalidraw）
- ✅ 使用分隔符（"""xml/"""md）避免内容混淆

---

### 2.5 AI模型配置

**关键文件**: `lib/server-models.ts`

```typescript
export function resolveChatModel(runtime?: RuntimeModelConfig): ResolvedModel {
    const trimmedBaseUrl = runtime.baseUrl.trim();
    const provider = deriveProvider(trimmedBaseUrl);

    // 判断是否为Gemini模型
    const isGemini = runtime.modelId.toLowerCase().startsWith("gemini-");

    if (isGemini && !isOpenRouter) {
        // Google SDK需要调整base URL格式
        let googleBaseUrl = trimmedBaseUrl
            .replace(/\/v1\/chat\/completions\/?$/, "")
            .replace(/\/v1\/?$/, "");

        if (!googleBaseUrl.endsWith("/v1beta")) {
            googleBaseUrl = googleBaseUrl.replace(/\/$/, "") + "/v1beta";
        }

        const client = createGoogleGenerativeAI({
            apiKey: runtime.apiKey,
            baseURL: googleBaseUrl,
        });

        return {
            id: runtime.modelId,
            model: client(runtime.modelId),
            provider: "google",
        };
    }

    // OpenAI兼容接口（包括Claude、OpenRouter等）
    const client = createOpenAI({
        apiKey: runtime.apiKey,
        baseURL: trimmedBaseUrl,
    });

    return {
        id: runtime.modelId,
        model: client.chat(runtime.modelId),
        provider
    };
}
```

**支持的Providers**:
- `google` - Google Gemini (需要特殊URL处理)
- `openai` - OpenAI GPT系列
- `openrouter` - OpenRouter聚合服务
- `anthropic` - Anthropic Claude系列
- `custom` - 自定义OpenAI兼容端点

---

### 2.6 Excalidraw数据结构

**标准Excalidraw元素格式**:
```json
{
  "elements": [
    {
      "id": "unique-string-id",
      "type": "rectangle",
      "x": 100,
      "y": 100,
      "width": 200,
      "height": 100,
      "angle": 0,
      "strokeColor": "#000000",
      "backgroundColor": "#ffffff",
      "fillStyle": "hachure",
      "strokeWidth": 1,
      "strokeStyle": "solid",
      "roughness": 1,
      "opacity": 100,
      "groupIds": [],
      "roundness": null,
      "seed": 1234567890,
      "version": 1,
      "versionNonce": 123456789,
      "isDeleted": false,
      "boundElements": null,
      "updated": 1706400000000,
      "link": null,
      "locked": false,
      "text": "Node Label"
    },
    {
      "id": "arrow-id",
      "type": "arrow",
      "x": 300,
      "y": 150,
      "width": 200,
      "height": 0,
      "points": [[0, 0], [200, 0]],
      "startBinding": {
        "elementId": "unique-string-id",
        "focus": 0,
        "gap": 1
      },
      "endBinding": {
        "elementId": "target-id",
        "focus": 0,
        "gap": 1
      }
    }
  ],
  "appState": {
    "viewBackgroundColor": "#ffffff"
  },
  "files": {}
}
```

**关键字段**:
- `elements[]` - 必需，包含所有图形元素
- `type` - 图形类型：rectangle、ellipse、diamond、arrow、text等
- `points[]` - 对于线条/箭头类型必需
- `startBinding/endBinding` - 箭头连接点绑定
- `text` - 文本内容（但Excalidraw文本是单独的text类型元素）

---

### 2.7 流式响应实现

**后端流式API**:
```typescript
import { streamText } from "ai";

const result = await streamText({
    model: resolvedModel.model,
    system: systemMessage,
    messages: enhancedMessages,
    maxTokens: 4000,
    temperature: 0.7,
    abortSignal: abortSignal,
});

// Vercel AI SDK自动处理流式响应
return result.toResponse();
```

**前端消费流式响应**:
```typescript
import { useChat } from "ai/react";

const { messages, sendMessage, status } = useChat({
    api: "/api/chat",
    onFinish: (message) => {
        // 提取XML/JSON内容并更新图表
        const content = message.content;
        const extracted = extractDiagramContent(content);
        updateDiagram(extracted);
    }
});
```

---

## 3. 整合到SmartArchitect的可行性分析

### 3.1 Excalidraw渲染方案

#### ✅ 技术可行性：**高**

**原因**:
1. SmartArchitect已集成Excalidraw组件（Phase 5完成）
2. Excalidraw数据格式标准且文档完善
3. AI可直接输出JSON格式的Excalidraw scene
4. 已有Excalidraw生成API (`/api/excalidraw/generate`)

**整合步骤**:

1. **扩展现有API** (`backend/app/api/excalidraw.py`):
   ```python
   class ExcalidrawFromImageRequest(BaseModel):
       image_base64: str  # 新增：base64图片数据
       prompt: str
       provider: Optional[str] = "siliconflow"

   @router.post("/excalidraw/generate-from-image")
   async def generate_excalidraw_from_image(request: ExcalidrawFromImageRequest):
       # 1. 构造多模态消息
       messages = [
           {
               "role": "user",
               "content": [
                   {"type": "text", "text": excalidraw_system_prompt + "\n\n" + request.prompt},
                   {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{request.image_base64}"}}
               ]
           }
       ]

       # 2. 调用AI服务
       response = await ai_service.generate_with_vision(messages, request.provider)

       # 3. 解析JSON
       scene = parse_excalidraw_json(response)

       return {"success": True, "scene": scene}
   ```

2. **前端图片上传组件** (`frontend/components/ImageUploadModal.tsx`):
   ```typescript
   const handleImageUpload = async (file: File) => {
       const base64 = await fileToBase64(file);

       const response = await fetch('/api/excalidraw/generate-from-image', {
           method: 'POST',
           body: JSON.stringify({
               image_base64: base64.split(',')[1],  // 去掉data:image前缀
               prompt: "复刻这张流程图的结构和布局",
               provider: selectedProvider
           })
       });

       const { scene } = await response.json();
       excalidrawAPI.updateScene(scene);  // 更新Excalidraw画布
   };
   ```

3. **Prompt Engineering**:
   ```python
   EXCALIDRAW_VISION_PROMPT = """
   Analyze the uploaded image and replicate its flowchart/architecture diagram structure in Excalidraw JSON format.

   Output a valid JSON object with the following structure:
   {
       "elements": [
           {
               "id": "unique-id",
               "type": "rectangle" | "ellipse" | "diamond" | "arrow" | "text",
               "x": number,
               "y": number,
               "width": number,
               "height": number,
               "text": "label text" (for shapes with text),
               "points": [[x1,y1], [x2,y2]] (for arrows/lines),
               "strokeColor": "#000000",
               "backgroundColor": "#ffffff"
           }
       ],
       "appState": {"viewBackgroundColor": "#ffffff"}
   }

   Rules:
   1. Preserve the spatial layout from the image
   2. Use appropriate shape types (rectangle for boxes, diamond for decision points, etc.)
   3. Create text elements separately for labels
   4. Connect shapes with arrow elements using startBinding/endBinding
   5. Ensure all IDs are unique
   """
   ```

**限制与解决方案**:
- ❌ **问题**: Excalidraw文本需要独立的text类型元素，不能直接嵌入shape
- ✅ **解决**: 在AI prompt中明确说明：`"Create separate text elements positioned near each shape for labels"`
- ❌ **问题**: AI生成的布局可能重叠
- ✅ **解决**: 在prompt中要求保持合理间距，或后处理时应用布局算法

**复杂度评估**: ⭐⭐⭐ (中等)
- 后端新增1个API endpoint
- 前端复用现有Excalidraw组件，新增上传功能
- 需要较多prompt调优工作

---

### 3.2 React Flow渲染方案

#### ⚠️ 技术可行性：**中等偏高**（需额外处理自定义节点）

**挑战**:
1. React Flow节点是自定义组件（ApiNode、ServiceNode等）
2. 需要AI理解SmartArchitect的节点类型系统
3. 节点有特殊的shape配置（`lib/utils/nodeShapes.ts`）

**技术方案**:

#### 方案A：AI直接生成SmartArchitect节点格式

**Prompt示例**:
```python
REACTFLOW_VISION_PROMPT = """
Analyze the uploaded architecture diagram and convert it to SmartArchitect React Flow format.

Output a JSON object with this structure:
{
    "nodes": [
        {
            "id": "1",
            "type": "api" | "service" | "database" | "cache" | "client" | "queue" | "gateway" | "container",
            "position": {"x": 100, "y": 100},
            "data": {
                "label": "API Gateway",
                "shape": "rectangle" | "circle" | "diamond" | "hexagon" | "start-event" | "end-event",
                "iconType": "server" | "database" | "zap",
                "color": "#3b82f6"
            }
        }
    ],
    "edges": [
        {
            "id": "e1-2",
            "source": "1",
            "target": "2",
            "label": "HTTP"
        }
    ]
}

Available node types:
- api: API services (iconType: server)
- service: Backend services (iconType: settings)
- database: Databases (iconType: database)
- cache: Cache systems (iconType: zap)
- client: Client applications (iconType: monitor)
- queue: Message queues (iconType: list)
- gateway: API gateways (iconType: cloud)
- container: Generic containers (iconType: package)

Available shapes:
- rectangle: Standard boxes
- circle: Circular nodes (for start/end points)
- diamond: Decision/gateway nodes
- hexagon: Integration points
- start-event: BPMN start event (green circle)
- end-event: BPMN end event (red circle)
- intermediate-event: BPMN intermediate event (orange circle)
- task: BPMN task (rounded rectangle)

Rules:
1. Analyze image components and map to appropriate node types
2. Preserve spatial layout (x, y coordinates)
3. Use correct iconType for each node type
4. Connect nodes with edges (source/target IDs must match node IDs)
"""
```

**后端实现**:
```python
from app.models.schemas import Node, Edge, Position, NodeData

@router.post("/vision/analyze-to-reactflow")
async def analyze_image_to_reactflow(request: VisionToReactFlowRequest):
    # 1. 构造多模态消息
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": REACTFLOW_VISION_PROMPT},
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{request.image_base64}"}}
            ]
        }
    ]

    # 2. 调用AI
    response = await ai_vision_service.generate(messages, request.provider, request.api_key)

    # 3. 解析JSON
    diagram_data = json.loads(extract_json_from_response(response))

    # 4. 验证数据结构
    nodes = [Node(**node_data) for node_data in diagram_data["nodes"]]
    edges = [Edge(**edge_data) for edge_data in diagram_data["edges"]]

    # 5. 返回标准格式
    return {
        "success": True,
        "nodes": [node.dict() for node in nodes],
        "edges": [edge.dict() for edge in edges]
    }
```

**前端整合**:
```typescript
const handleImageUpload = async (file: File) => {
    const base64 = await fileToBase64(file);

    const response = await fetch('http://localhost:8000/api/vision/analyze-to-reactflow', {
        method: 'POST',
        body: JSON.stringify({
            image_base64: base64.split(',')[1],
            provider: 'gemini',
            api_key: apiKey
        })
    });

    const { nodes, edges } = await response.json();

    // 更新React Flow画布
    setNodes(nodes);
    setEdges(edges);

    // 触发自动布局
    fitView();
};
```

#### 方案B：两步法（先生成Mermaid，再转换）

**优势**: 利用现有的Mermaid转换能力

```python
@router.post("/vision/analyze-to-mermaid")
async def analyze_image_to_mermaid(request: VisionAnalyzeRequest):
    prompt = """
    Analyze this diagram and generate equivalent Mermaid code.
    Identify node types (API, Service, Database, etc.) and connections.
    """

    # 1. AI生成Mermaid代码
    mermaid_code = await ai_vision_service.analyze_image(request.image_base64, prompt)

    # 2. 调用现有的Mermaid解析API
    from app.api.mermaid import parse_mermaid
    diagram_data = parse_mermaid({"code": mermaid_code})

    return diagram_data
```

**对比**:
| 方案 | 优势 | 劣势 |
|------|------|------|
| A: 直接生成 | 精确控制节点类型和样式 | 需要AI深度理解自定义格式 |
| B: Mermaid中转 | 复用现有解析器，稳定性高 | Mermaid表达能力有限，可能丢失样式信息 |

**推荐**: 方案A（直接生成），因为：
- SmartArchitect已有完整的节点类型系统
- AI模型（Claude Sonnet 4.5）有足够的推理能力
- 可以通过few-shot examples提升准确率

**复杂度评估**: ⭐⭐⭐⭐ (较高)
- 需要编写详细的prompt template（包含所有节点类型定义）
- 需要extensive测试确保AI理解节点类型映射
- 需要处理AI输出的后验证和修正

---

## 4. 关键技术要点总结

### 4.1 Prompt Engineering最佳实践

1. **明确输出格式**:
   - 使用代码块包裹（```json```、```xml```）
   - 禁止额外文本输出
   - 指定JSON schema或XML规则

2. **提供当前状态**:
   - 在每次请求中包含当前图表数据
   - 便于AI进行增量更新而非全量重建

3. **约束与规则**:
   - 列出non-negotiable规则（如ID唯一性、必需字段）
   - 强调优先级顺序
   - 明确不允许的行为（如tool calls）

4. **领域知识注入**:
   - 提供可用的节点类型列表
   - 说明图形类型的语义（rectangle=box, diamond=decision）
   - 包含示例（few-shot learning）

### 4.2 数据结构设计

**统一的图形数据交换格式**:
```typescript
interface DiagramData {
    format: "reactflow" | "excalidraw" | "mermaid";
    nodes: Node[];
    edges: Edge[];
    metadata?: {
        sourceImage?: string;  // 原始图片base64
        generatedBy?: string;  // AI模型标识
        timestamp?: number;
    };
}
```

### 4.3 错误处理策略

1. **AI输出验证**:
   ```python
   def validate_reactflow_output(data: dict) -> ValidationResult:
       # 1. JSON schema验证
       # 2. 引用完整性检查（edge的source/target必须存在）
       # 3. 数据类型检查（position必须有x和y）
       # 4. 业务逻辑验证（节点type必须在允许列表中）
   ```

2. **Fallback机制**:
   - AI生成失败 → 返回mock数据提示用户
   - JSON解析失败 → 尝试正则提取或请求AI重新生成
   - 节点类型未知 → 映射到default类型

3. **用户反馈循环**:
   - 允许用户标记"不准确"的生成结果
   - 收集错误案例用于prompt优化

---

## 5. 实施建议与优先级

### 阶段1：Excalidraw实现（优先级：高）
**工作量**: 3-5天

- [ ] 后端新增 `/api/excalidraw/generate-from-image` endpoint
- [ ] 实现base64图片处理逻辑
- [ ] 编写Excalidraw专用system prompt
- [ ] 前端新增图片上传组件（可复用现有UI）
- [ ] 测试与prompt调优（关键：布局准确性）

### 阶段2：React Flow实现（优先级：中）
**工作量**: 5-7天

- [ ] 后端新增 `/api/vision/analyze-to-reactflow` endpoint
- [ ] 编写详细的节点类型说明文档（给AI）
- [ ] 实现few-shot prompt template
- [ ] 前端整合到现有canvas组件
- [ ] 大量测试不同类型的架构图

### 阶段3：增强功能（优先级：低）
**工作量**: 2-3天

- [ ] 支持多图片批量上传
- [ ] 实现图片+文本混合输入（"这是数据库，这是API"）
- [ ] 添加"迭代优化"功能（生成后继续调整）
- [ ] 实现样式迁移（保留原图配色方案）

---

## 6. 风险与挑战

### 6.1 AI准确性
- **风险**: AI可能无法正确识别复杂的架构图组件
- **缓解**: 使用Claude Sonnet 4.5等高能力模型，编写详细prompt

### 6.2 布局保真度
- **风险**: AI生成的坐标可能导致重叠或不合理布局
- **缓解**: 在prompt中强调布局规则，后处理应用自动布局算法

### 6.3 自定义节点映射
- **风险**: React Flow自定义节点类型难以让AI理解
- **缓解**: 提供丰富的few-shot examples，建立节点类型映射表

### 6.4 成本控制
- **风险**: 图片+流式生成消耗大量tokens
- **缓解**: 实现请求限流，优化prompt长度，支持本地模型

---

## 7. 关键代码片段参考

### 7.1 Base64转换工具函数

```typescript
// frontend/lib/utils/imageUtils.ts
export async function fileToBase64(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result as string);
        reader.onerror = (error) => reject(error);
        reader.readAsDataURL(file);
    });
}

export function base64ToBlob(base64: string, mimeType: string): Blob {
    const byteString = atob(base64.split(',')[1]);
    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeType });
}
```

### 7.2 多模态消息构造（后端）

```python
# backend/app/services/ai_vision.py
def build_vision_message(
    text_prompt: str,
    image_base64: str,
    current_state: Optional[str] = None
) -> List[Dict]:
    content = [{"type": "text", "text": text_prompt}]

    if current_state:
        content.insert(0, {
            "type": "text",
            "text": f"Current diagram state:\n```json\n{current_state}\n```\n\n"
        })

    content.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/png;base64,{image_base64}"}
    })

    return [{"role": "user", "content": content}]
```

### 7.3 JSON响应解析

```python
import re
import json

def extract_json_from_response(response: str) -> str:
    """从AI响应中提取JSON内容（处理代码块包裹）"""
    # 尝试匹配 ```json ... ``` 代码块
    json_pattern = r'```json\s*(.*?)\s*```'
    match = re.search(json_pattern, response, re.DOTALL)

    if match:
        return match.group(1)

    # 尝试匹配 {...} 对象
    json_obj_pattern = r'\{.*\}'
    match = re.search(json_obj_pattern, response, re.DOTALL)

    if match:
        return match.group(0)

    # 直接返回原始响应（可能本身就是JSON）
    return response

def parse_ai_diagram_response(response: str, format: str) -> Dict:
    json_str = extract_json_from_response(response)

    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {e}\nResponse: {json_str[:200]}")

    # 根据格式验证必需字段
    if format == "reactflow":
        if "nodes" not in data or "edges" not in data:
            raise ValueError("Missing required fields: nodes and edges")
    elif format == "excalidraw":
        if "elements" not in data:
            raise ValueError("Missing required field: elements")

    return data
```

---

## 8. 测试计划

### 8.1 单元测试

```python
# tests/test_vision_to_diagram.py
import pytest
from app.services.vision_to_diagram import extract_json_from_response, parse_ai_diagram_response

def test_extract_json_from_code_block():
    response = '```json\n{"nodes": [], "edges": []}\n```'
    result = extract_json_from_response(response)
    assert result == '{"nodes": [], "edges": []}'

def test_parse_reactflow_response():
    response = '```json\n{"nodes": [{"id": "1", "type": "api", "position": {"x": 0, "y": 0}, "data": {"label": "API"}}], "edges": []}\n```'
    data = parse_ai_diagram_response(response, "reactflow")
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["type"] == "api"
```

### 8.2 集成测试

```python
@pytest.mark.asyncio
async def test_excalidraw_from_image_workflow():
    # 1. 准备测试图片
    with open("tests/fixtures/sample_flowchart.png", "rb") as f:
        image_data = base64.b64encode(f.read()).decode()

    # 2. 调用API
    response = client.post("/api/excalidraw/generate-from-image", json={
        "image_base64": image_data,
        "prompt": "复刻这张流程图",
        "provider": "gemini"
    })

    # 3. 验证响应
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "scene" in data
    assert "elements" in data["scene"]
    assert len(data["scene"]["elements"]) > 0
```

### 8.3 E2E测试

使用Playwright模拟用户操作：
```typescript
test('Upload image and generate Excalidraw diagram', async ({ page }) => {
    await page.goto('http://localhost:3000');

    // 点击上传按钮
    await page.click('[data-testid="upload-image-btn"]');

    // 选择文件
    const fileInput = await page.$('input[type="file"]');
    await fileInput?.setInputFiles('tests/fixtures/sample_flowchart.png');

    // 等待生成完成
    await page.waitForSelector('[data-testid="excalidraw-canvas"]', { timeout: 30000 });

    // 验证画布有内容
    const elements = await page.evaluate(() => {
        const api = (window as any).excalidrawAPI;
        return api.getSceneElements();
    });

    expect(elements.length).toBeGreaterThan(0);
});
```

---

## 9. 参考资源

### 官方文档
- Excalidraw API: https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api
- React Flow: https://reactflow.dev/api-reference
- Vercel AI SDK: https://sdk.vercel.ai/docs
- Claude Vision: https://docs.anthropic.com/claude/docs/vision

### 示例项目
- FlowPilot-Beta: `D:\file\openproject\reference\flowpilot-beta`
- SmartArchitect Vision API: `backend/app/api/vision.py`

### Prompt模板库
建议创建 `backend/prompts/vision_to_diagram/` 目录存储各类prompt模板

---

## 10. 结论与建议

### 10.1 技术可行性总结

| 方案 | 可行性 | 实施难度 | 推荐指数 |
|------|--------|---------|---------|
| Excalidraw渲染 | ✅ 高 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐⭐ 强烈推荐 |
| React Flow渲染 | ⚠️ 中高 | ⭐⭐⭐⭐ 较高 | ⭐⭐⭐⭐ 推荐（需更多测试） |

### 10.2 实施路线图

```
Week 1: Excalidraw基础实现
  ├─ Day 1-2: 后端API开发 + prompt编写
  ├─ Day 3-4: 前端集成 + UI组件
  └─ Day 5: 测试与优化

Week 2: React Flow实现
  ├─ Day 1-2: 节点类型系统文档化
  ├─ Day 3-4: API开发 + few-shot prompt
  └─ Day 5: 前端集成

Week 3: 测试与优化
  ├─ Day 1-2: 各类图表测试
  ├─ Day 3: 性能优化（prompt压缩、响应缓存）
  └─ Day 4-5: 文档编写 + 演示视频
```

### 10.3 最终建议

1. **优先实现Excalidraw方案**，因为：
   - 数据格式标准化程度高
   - 已有成熟的参考实现（flowpilot-beta）
   - 对AI的要求相对较低（标准JSON结构）
   - 用户体验好（手绘风格，适合演示）

2. **React Flow作为增强功能**，因为：
   - 需要AI深度理解自定义节点类型
   - 需要大量测试确保准确性
   - 但对于架构图领域更专业

3. **关键成功因素**：
   - ✅ 高质量的prompt engineering
   - ✅ 充分的测试用例覆盖
   - ✅ 用户友好的错误提示
   - ✅ 迭代优化机制（允许用户修正AI输出）

---

**文档版本**: 1.0
**作者**: Claude Code
**最后更新**: 2026-01-28
