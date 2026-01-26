# Phase 6 技术方案：画布闭环 + 流程图截图识别

**版本：** v0.6.0-proposal
**日期：** 2026-01-20
**状态：** 方案讨论中

---

## 一、当前系统现状分析

### 1.1 已实现功能清单（Phase 1-5）

| 模块 | 功能 | 技术栈 | 状态 |
|------|------|--------|------|
| **ReactFlow 画布** | 结构化架构图编辑 | React Flow + 10+自定义节点 | ✅ 完成 |
| **Mermaid 同步** | 可视化画布 ↔ Mermaid代码双向转换 | `/api/mermaid/*` | ✅ 完成 |
| **Excalidraw 画布** | 手绘风格白板 | @excalidraw/excalidraw | ✅ 完成 |
| **AI 视觉分析** | 架构图片 → ReactFlow图 | Vision API + Gemini/OpenAI/Claude | ✅ 完成 |
| **自然语言生成** | 文字描述 → 流程图 | Chat Generator + 模板系统 | ✅ 完成 |
| **AI Excalidraw** | Prompt → 手绘场景 | Excalidraw Generator + SiliconFlow | ✅ 完成 |
| **RAG 知识库** | 文档语义搜索 | ChromaDB + all-MiniLM-L6-v2 | ✅ 完成 |
| **多格式导出** | PPT/Slidev/演讲稿 | python-pptx + Markdown | ✅ 完成 |

### 1.2 核心问题识别

#### 问题1：两个画布功能割裂 ⚠️

**当前状态：**
```typescript
// ArchitectCanvas.tsx:152-160
export function ArchitectCanvas() {
  const { canvasMode } = useArchitectStore();

  if (canvasMode === "excalidraw") {
    return <ExcalidrawBoard />;  // 完全独立的Excalidraw
  }

  return <ArchitectCanvasInner />;  // ReactFlow画布
}
```

**存在的割裂：**
- ❌ ReactFlow 和 Excalidraw 通过 `canvasMode` 状态切换，**数据完全隔离**
- ❌ 在 ReactFlow 中创建的图，切换到 Excalidraw 后丢失
- ❌ 在 Excalidraw 中手绘的图，无法转为结构化的 ReactFlow 节点
- ❌ 用户无法在两种风格间自由切换和继承数据

**用户受影响的场景：**
1. 用户想先用 Excalidraw 快速手绘草图，然后转为结构化的 ReactFlow 图进行精细编辑
2. 用户想将 ReactFlow 的严谨架构图转为手绘风格用于演示文稿
3. 用户想在同一个项目中混用两种画布的优势

#### 问题2：缺失流程图截图识别功能 ⚠️

**当前能力：**
- ✅ `/api/vision/analyze` - 分析**架构图**（API、Service、Database等组件）
- ✅ Prompt工程针对架构组件识别

**缺失能力：**
- ❌ 无法识别**流程图**截图（流程节点、判断节点、连线方向）
- ❌ 无法识别 BPMN 标准流程图元素
- ❌ 无法保留原始布局（节点位置关系）

**用户受影响的场景：**
1. 用户从其他工具（Visio、ProcessOn、Draw.io）截图流程图，想导入到系统编辑
2. 用户拍摄白板上的手绘流程图照片，想转为数字化可编辑版本
3. 用户想复刻竞品的流程图设计并进行微调

---

## 二、技术方案设计

### 2.1 方案A：双向画布转换桥（解决割裂问题）

#### 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                     用户交互层                                │
├─────────────────────────────────────────────────────────────┤
│  ReactFlow 画布          ⟷          Excalidraw 画布          │
│  (结构化架构图)                       (手绘风格白板)           │
└──────────┬──────────────────────────────────┬───────────────┘
           │                                  │
           │        Canvas Converter          │
           │    (双向转换服务)                 │
           ▼                                  ▼
    ┌─────────────┐                  ┌──────────────┐
    │ ReactFlow   │                  │ Excalidraw   │
    │ Data Format │◄────────────────►│ Scene Format │
    └─────────────┘                  └──────────────┘
         │                                  │
         │                                  │
         ▼                                  ▼
    nodes: [...]                   elements: [...]
    edges: [...]                   appState: {...}
```

#### 数据格式映射表

| ReactFlow 元素 | Excalidraw 元素 | 转换规则 |
|---------------|-----------------|---------|
| `Node` (type="api") | `rectangle` + `text` | 宽200px, 高100px, 图标作为文本前缀 |
| `Node` (type="database") | `ellipse` + `text` | 圆形, 直径120px |
| `Node` (type="decision") | `diamond` + `text` | 菱形, 边长150px |
| `Edge` (animated) | `arrow` (strokeStyle="dashed") | 虚线箭头 |
| `Edge` (label) | `text` + `arrow` | 文本放在箭头中点 |
| `Node.position` | `element.x, element.y` | 直接映射坐标 |

#### API 端点设计

```python
# backend/app/api/canvas.py (新增)

POST /api/canvas/convert
{
  "source_format": "reactflow" | "excalidraw",
  "target_format": "excalidraw" | "reactflow",
  "data": { ... },  # ReactFlow nodes/edges 或 Excalidraw scene
  "options": {
    "preserve_layout": true,      # 保留原始布局
    "roughness": 1,               # Excalidraw 手绘风格强度(0-2)
    "stroke_color": "#000000",    # 默认线条颜色
    "auto_arrange": false         # 是否自动重排
  }
}

Response:
{
  "success": true,
  "converted_data": { ... },  # 转换后的数据
  "metadata": {
    "nodes_count": 10,
    "edges_count": 8,
    "conversion_time_ms": 45
  }
}
```

#### 转换服务实现思路

```python
# backend/app/services/canvas_converter.py (新增)

class CanvasConverter:
    """双向画布数据转换器"""

    def reactflow_to_excalidraw(
        self,
        nodes: List[Node],
        edges: List[Edge],
        options: ConversionOptions
    ) -> ExcalidrawScene:
        """
        ReactFlow 结构化图 → Excalidraw 手绘风格

        步骤：
        1. 遍历 nodes，根据 type 映射到 Excalidraw 形状
        2. 计算节点边界框，添加文本元素
        3. 遍历 edges，绘制箭头连线
        4. 应用手绘风格参数 (roughness)
        5. 返回完整 scene (elements + appState)
        """
        elements = []

        # 节点类型映射表
        shape_mapping = {
            "api": "rectangle",
            "service": "rectangle",
            "database": "ellipse",
            "cache": "ellipse",
            "queue": "rectangle",
            "gateway": "diamond",
            "decision": "diamond",
            "start-event": "ellipse",
            "end-event": "ellipse",
            "task": "rectangle",
        }

        for node in nodes:
            shape_type = shape_mapping.get(node.type, "rectangle")

            # 创建形状元素
            shape_element = {
                "id": f"shape_{node.id}",
                "type": shape_type,
                "x": node.position.x,
                "y": node.position.y,
                "width": 200,
                "height": 100,
                "strokeColor": options.stroke_color,
                "backgroundColor": self._get_color_by_type(node.type),
                "roughness": options.roughness,
                "strokeStyle": "solid",
                "fillStyle": "hachure",
            }
            elements.append(shape_element)

            # 创建文本元素
            text_element = {
                "id": f"text_{node.id}",
                "type": "text",
                "x": node.position.x + 10,
                "y": node.position.y + 40,
                "text": node.data.label,
                "fontSize": 16,
                "fontFamily": 1,  # Hand-drawn font
                "textAlign": "center",
                "containerId": shape_element["id"],
            }
            elements.append(text_element)

        # 处理边
        for edge in edges:
            source_node = self._find_node(nodes, edge.source)
            target_node = self._find_node(nodes, edge.target)

            # 计算起点和终点坐标
            start_x = source_node.position.x + 100
            start_y = source_node.position.y + 100
            end_x = target_node.position.x + 100
            end_y = target_node.position.y

            # 创建箭头元素
            arrow_element = {
                "id": f"arrow_{edge.id}",
                "type": "arrow",
                "x": start_x,
                "y": start_y,
                "width": end_x - start_x,
                "height": end_y - start_y,
                "strokeColor": options.stroke_color,
                "roughness": options.roughness,
                "strokeStyle": "dashed" if edge.animated else "solid",
                "startArrowhead": None,
                "endArrowhead": "arrow",
            }
            elements.append(arrow_element)

            # 如果有标签，添加文本
            if edge.label:
                label_element = {
                    "id": f"label_{edge.id}",
                    "type": "text",
                    "x": (start_x + end_x) / 2,
                    "y": (start_y + end_y) / 2 - 10,
                    "text": edge.label,
                    "fontSize": 14,
                }
                elements.append(label_element)

        return {
            "elements": elements,
            "appState": {
                "viewBackgroundColor": "#ffffff",
                "currentItemStrokeColor": options.stroke_color,
            }
        }

    def excalidraw_to_reactflow(
        self,
        scene: ExcalidrawScene,
        options: ConversionOptions
    ) -> Tuple[List[Node], List[Edge]]:
        """
        Excalidraw 手绘图 → ReactFlow 结构化图

        步骤：
        1. 提取所有形状元素（rectangle, ellipse, diamond）
        2. 提取每个形状内的文本元素（通过 containerId）
        3. 提取所有箭头元素
        4. 推断节点类型（通过形状 + 文本关键词）
        5. 构建 nodes 和 edges

        挑战：
        - Excalidraw 没有明确的节点概念，需要启发式识别
        - 箭头连接需要通过坐标计算推断
        """
        nodes = []
        edges = []

        # Step 1: 提取形状和文本的对应关系
        shapes = [e for e in scene["elements"] if e["type"] in ["rectangle", "ellipse", "diamond"]]
        texts = [e for e in scene["elements"] if e["type"] == "text"]
        arrows = [e for e in scene["elements"] if e["type"] == "arrow"]

        # Step 2: 为每个形状创建 ReactFlow 节点
        for shape in shapes:
            # 查找关联的文本
            label = ""
            for text in texts:
                if text.get("containerId") == shape["id"]:
                    label = text["text"]
                    break

            # 推断节点类型
            node_type = self._infer_node_type(shape["type"], label)

            node = Node(
                id=shape["id"],
                type=node_type,
                position=Position(x=shape["x"], y=shape["y"]),
                data=NodeData(label=label or "未命名")
            )
            nodes.append(node)

        # Step 3: 处理箭头，推断边的连接关系
        for arrow in arrows:
            # 计算箭头起点和终点坐标
            start_x = arrow["x"]
            start_y = arrow["y"]
            end_x = arrow["x"] + arrow["width"]
            end_y = arrow["y"] + arrow["height"]

            # 查找距离起点最近的节点 (source)
            source_node = self._find_nearest_node(shapes, start_x, start_y)
            # 查找距离终点最近的节点 (target)
            target_node = self._find_nearest_node(shapes, end_x, end_y)

            if source_node and target_node:
                edge = Edge(
                    id=arrow["id"],
                    source=source_node["id"],
                    target=target_node["id"],
                    animated=arrow.get("strokeStyle") == "dashed",
                )
                edges.append(edge)

        return nodes, edges

    def _infer_node_type(self, shape_type: str, label: str) -> str:
        """根据形状和文本推断节点类型"""
        label_lower = label.lower()

        # 关键词匹配
        if "api" in label_lower or "接口" in label_lower:
            return "api"
        elif "database" in label_lower or "数据库" in label_lower:
            return "database"
        elif "cache" in label_lower or "缓存" in label_lower:
            return "cache"
        elif shape_type == "diamond":
            return "decision"
        elif shape_type == "ellipse" and ("开始" in label_lower or "start" in label_lower):
            return "start-event"
        elif shape_type == "ellipse" and ("结束" in label_lower or "end" in label_lower):
            return "end-event"
        else:
            return "default"
```

#### 前端集成方案

```typescript
// frontend/lib/store/useArchitectStore.ts (新增 action)

export const useArchitectStore = create<ArchitectStore>((set, get) => ({
  // ... 现有状态

  // 新增：画布转换功能
  convertCanvas: async (targetFormat: "reactflow" | "excalidraw") => {
    const state = get();
    const currentFormat = state.canvasMode;

    if (currentFormat === targetFormat) {
      toast.info("已经在目标画布模式");
      return;
    }

    const sourceData = currentFormat === "reactflow"
      ? { nodes: state.nodes, edges: state.edges }
      : { scene: state.excalidrawScene };

    try {
      const response = await fetch('http://localhost:8000/api/canvas/convert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          source_format: currentFormat,
          target_format: targetFormat,
          data: sourceData,
          options: {
            preserve_layout: true,
            roughness: 1,
          }
        })
      });

      const result = await response.json();

      if (targetFormat === "reactflow") {
        set({
          nodes: result.converted_data.nodes,
          edges: result.converted_data.edges,
          canvasMode: "reactflow"
        });
      } else {
        set({
          excalidrawScene: result.converted_data,
          canvasMode: "excalidraw"
        });
      }

      toast.success(`已转换为${targetFormat === "reactflow" ? "结构化" : "手绘"}模式`);
    } catch (error) {
      toast.error("转换失败");
    }
  }
}));
```

```typescript
// frontend/components/CanvasSwitcher.tsx (新增组件)

export function CanvasSwitcher() {
  const { canvasMode, convertCanvas } = useArchitectStore();

  return (
    <div className="flex gap-2 rounded-lg bg-white p-1 shadow-md dark:bg-slate-800">
      <button
        onClick={() => {
          if (canvasMode === "excalidraw") {
            convertCanvas("reactflow");
          } else {
            useArchitectStore.setState({ canvasMode: "reactflow" });
          }
        }}
        className={canvasMode === "reactflow" ? "active" : ""}
      >
        <Grid3x3 className="h-4 w-4" />
        结构化
      </button>

      <button
        onClick={() => {
          if (canvasMode === "reactflow") {
            convertCanvas("excalidraw");
          } else {
            useArchitectStore.setState({ canvasMode: "excalidraw" });
          }
        }}
        className={canvasMode === "excalidraw" ? "active" : ""}
      >
        <Brush className="h-4 w-4" />
        手绘
      </button>
    </div>
  );
}
```

---

### 2.2 方案B：流程图截图识别（新功能）

#### 需求分析

**目标用户场景：**
1. 产品经理截图了 Visio 流程图，想导入系统进行二次编辑
2. 开发人员拍摄白板上的业务流程图，想数字化存档
3. 用户看到竞品的流程图设计，想复刻并优化

**技术挑战：**
- 流程图元素多样：矩形、菱形、圆形、平行四边形、箭头等
- 文本识别：中英文混合，字体大小不一
- 布局保留：需要识别相对位置关系
- 连线方向：判断箭头方向（单向/双向）

#### 技术选型（2025最新）

##### 选项1：VLM 端到端识别（推荐）

**优势：**
- 一次调用完成识别，无需复杂pipeline
- 理解图表语义，不只是OCR
- 可以修复手绘不规范的图

**推荐模型：**

| 模型 | 优势 | 缺点 | 成本 | 已集成 |
|------|------|------|------|--------|
| **Qwen2.5-VL** | 文档/图表理解强，多语言OCR | 需要SiliconFlow API | $0.001/次 | ✅ 是 |
| **Gemini 2.5 Flash** | 响应快(2-3s)，多模态 | 图表识别中等 | $0.0003/次 | ✅ 是 |
| **Claude 3.5 Sonnet** | 图表理解最强，推理准确 | 慢(5-8s)，贵 | $0.003/次 | ✅ 是 |
| **DeepSeek-OCR-3B** | 开源，可本地部署 | 需要自建服务 | 免费 | ❌ 否 |

**实现方案：**
```python
# backend/app/services/ai_vision.py (扩展现有服务)

class VisionService:
    async def analyze_flowchart_image(
        self,
        image_data: bytes,
        preserve_layout: bool = True
    ) -> ImageAnalysisResponse:
        """
        专门识别流程图截图

        与 analyze_architecture 的区别：
        - Prompt 专注于流程图元素（开始/结束/处理/判断节点）
        - 节点类型映射到 BPMN 标准
        - 更强调布局和连线方向识别
        """

        prompt = self._build_flowchart_prompt(preserve_layout)

        # 调用VLM（Gemini/Claude/Qwen）
        result = await self._call_vlm(image_data, prompt)

        # 解析响应，验证流程图结构
        nodes, edges = self._parse_flowchart_response(result)

        return ImageAnalysisResponse(
            nodes=nodes,
            edges=edges,
            mermaid_code=self._generate_mermaid(nodes, edges),
            ai_analysis=result.get("analysis")
        )

    def _build_flowchart_prompt(self, preserve_layout: bool) -> str:
        return f"""
你是一个专业的流程图分析专家。请分析这张流程图截图，提取以下信息：

## 识别规则
1. **节点类型识别**：
   - 圆形/圆角矩形 → 开始/结束节点 (type="start-event" 或 "end-event")
   - 矩形 → 处理节点 (type="task")
   - 菱形 → 判断节点 (type="decision")
   - 平行四边形 → 输入/输出节点 (type="default", shape="parallelogram")
   - 圆柱体 → 数据库节点 (type="database")

2. **文本识别**：
   - 提取每个节点内的文本作为 label
   - 识别连线上的文本作为 edge.label

3. **连线识别**：
   - 识别箭头方向（起点节点 → 终点节点）
   - 判断连线类型（实线/虚线）
   - 提取判断分支标签（是/否、True/False、Y/N）

4. **布局保留**（{"启用" if preserve_layout else "禁用"}）：
   {"- 记录每个节点的相对位置（左上角坐标）" if preserve_layout else "- 忽略位置，只识别逻辑关系"}
   {"- 保持原图的空间布局关系" if preserve_layout else ""}

## 输出格式（JSON）
{{
  "nodes": [
    {{
      "id": "node_1",
      "type": "start-event",
      "position": {{"x": 100, "y": 50}},  // 如果 preserve_layout=true
      "data": {{
        "label": "开始",
        "shape": "circle"
      }}
    }},
    {{
      "id": "node_2",
      "type": "task",
      "position": {{"x": 100, "y": 200}},
      "data": {{
        "label": "执行任务A",
        "shape": "rectangle"
      }}
    }},
    {{
      "id": "node_3",
      "type": "decision",
      "position": {{"x": 100, "y": 350}},
      "data": {{
        "label": "条件判断",
        "shape": "diamond"
      }}
    }}
  ],
  "edges": [
    {{
      "id": "edge_1",
      "source": "node_1",
      "target": "node_2",
      "label": ""
    }},
    {{
      "id": "edge_2",
      "source": "node_2",
      "target": "node_3",
      "label": ""
    }},
    {{
      "id": "edge_3",
      "source": "node_3",
      "target": "node_4",
      "label": "是"
    }},
    {{
      "id": "edge_4",
      "source": "node_3",
      "target": "node_5",
      "label": "否"
    }}
  ],
  "analysis": {{
    "total_nodes": 5,
    "total_branches": 2,
    "flowchart_type": "业务流程图",
    "complexity": "中等",
    "recommendations": ["建议添加异常处理分支"]
  }}
}}

## 注意事项
- 确保每个节点的 id 唯一
- edges 的 source 和 target 必须对应 nodes 的 id
- 所有节点必须有 position（即使 preserve_layout=false，也要给默认值）
- label 不能为空，如果图中无文本则标记为 "未命名节点"
"""
```

##### 选项2：OCR + CV Pipeline（高精度场景）

**适用场景：**
- 手绘流程图（线条不规则）
- 需要极高准确率
- 离线部署需求

**技术架构：**
```
图片输入
  ↓
1. 预处理（OpenCV）
   - 二值化
   - 去噪
   - 边缘增强
  ↓
2. 形状检测（OpenCV + 启发式规则）
   - 轮廓检测
   - 形状分类（矩形/菱形/圆形）
   - 坐标提取
  ↓
3. OCR识别（PaddleOCR-VL-0.9B）
   - 文本检测
   - 文本识别
   - 边界框匹配
  ↓
4. 连线分析（自研算法）
   - 线段检测（霍夫变换）
   - 箭头识别
   - 拓扑关系推断
  ↓
5. 数据组装
   - 生成 nodes/edges JSON
```

**实现复杂度：**
- 开发周期：7-10天
- 维护成本：高（规则调优）
- 准确率：80-90%

**对比结论：**
建议**优先使用选项1（VLM）**，理由：
1. 开发速度快（2-3天）
2. 维护成本低
3. 准确率高（90-95%）
4. 可扩展性强（支持手绘、多语言）

如果VLM效果不佳，再考虑选项2作为补充。

#### API 设计

```python
# backend/app/api/vision.py (新增端点)

@router.post("/vision/analyze-flowchart", response_model=ImageAnalysisResponse)
async def analyze_flowchart_screenshot(
    file: UploadFile = File(..., description="Flowchart screenshot"),
    provider: str = Query("gemini", description="AI provider"),
    target_format: Literal["reactflow", "excalidraw"] = Query("reactflow"),
    preserve_layout: bool = Query(True, description="Preserve original node positions"),
    api_key: Optional[str] = Form(None),
):
    """
    识别流程图截图，转换为可编辑格式

    与 /vision/analyze 的区别：
    - 专门优化流程图元素识别（开始/结束/判断节点）
    - 支持布局保留选项
    - 支持直接输出 Excalidraw 格式

    参数：
    - file: 流程图截图（支持 PNG/JPG/WEBP）
    - provider: AI模型提供商（gemini/claude/qwen）
    - target_format: 输出格式（reactflow=结构化，excalidraw=手绘）
    - preserve_layout: 是否保留原图布局
    - api_key: 可选的API密钥

    返回：
    - nodes: ReactFlow 节点数组
    - edges: ReactFlow 边数组
    - mermaid_code: Mermaid 代码
    - ai_analysis: AI分析结果（流程复杂度、建议等）
    - excalidraw_scene: （如果 target_format="excalidraw"）
    """

    # 读取图片
    image_data = await file.read()

    # 创建Vision服务
    vision_service = create_vision_service(provider, api_key=api_key)

    # 分析流程图
    result = await vision_service.analyze_flowchart_image(
        image_data,
        preserve_layout=preserve_layout
    )

    # 如果需要转为Excalidraw格式
    if target_format == "excalidraw":
        converter = CanvasConverter()
        scene = converter.reactflow_to_excalidraw(
            result.nodes,
            result.edges,
            options=ConversionOptions(roughness=1)
        )
        result.excalidraw_scene = scene

    return result
```

#### 前端集成

```typescript
// frontend/components/FlowchartScreenshotUploader.tsx (新增组件)

export function FlowchartScreenshotUploader() {
  const [uploading, setUploading] = useState(false);
  const { modelConfig, canvasMode, setNodes, setEdges, setExcalidrawScene } = useArchitectStore();

  const handleFileUpload = async (file: File) => {
    setUploading(true);

    const formData = new FormData();
    formData.append("file", file);
    formData.append("provider", modelConfig.provider);
    formData.append("target_format", canvasMode);
    formData.append("preserve_layout", "true");
    formData.append("api_key", modelConfig.apiKey);

    try {
      const response = await fetch('http://localhost:8000/api/vision/analyze-flowchart', {
        method: 'POST',
        body: formData
      });

      const result = await response.json();

      if (canvasMode === "reactflow") {
        setNodes(result.nodes);
        setEdges(result.edges);
        toast.success(`识别成功！共${result.nodes.length}个节点`);
      } else {
        setExcalidrawScene(result.excalidraw_scene);
        toast.success("已转为手绘风格，可以继续编辑");
      }

      // 显示AI分析结果
      if (result.ai_analysis) {
        toast.info(
          `流程复杂度：${result.ai_analysis.complexity}\n` +
          `分支数：${result.ai_analysis.total_branches}`
        );
      }
    } catch (error) {
      toast.error("识别失败，请检查图片质量");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="rounded-lg border-2 border-dashed border-slate-300 p-8 text-center">
      <Upload className="mx-auto h-12 w-12 text-slate-400" />
      <p className="mt-4 text-sm text-slate-600">
        上传流程图截图
      </p>
      <input
        type="file"
        accept="image/png,image/jpeg,image/jpg,image/webp"
        onChange={(e) => e.target.files?.[0] && handleFileUpload(e.target.files[0])}
        className="hidden"
        id="flowchart-upload"
      />
      <label
        htmlFor="flowchart-upload"
        className="mt-4 inline-block cursor-pointer rounded-lg bg-indigo-600 px-4 py-2 text-white hover:bg-indigo-700"
      >
        {uploading ? "识别中..." : "选择文件"}
      </label>
      <p className="mt-2 text-xs text-slate-400">
        支持 Visio、ProcessOn、Draw.io 等工具的截图
      </p>
    </div>
  );
}
```

在 `AiControlPanel.tsx` 中集成：

```typescript
// 新增Tab：截图识别
<Tab value="screenshot">
  <Upload className="h-4 w-4" />
  截图识别
</Tab>

// Tab内容
{activeTab === "screenshot" && (
  <FlowchartScreenshotUploader />
)}
```

---

### 2.3 完整闭环架构

```
┌──────────────────────────────────────────────────────────────┐
│                      用户输入来源                              │
├──────────────────────────────────────────────────────────────┤
│                                                                │
│  1️⃣ 自然语言      2️⃣ 架构图片      3️⃣ 流程图截图    4️⃣ 手绘草图  │
│  "订单处理流程"   (架构图)        (Visio/白板)     (Excalidraw) │
│       │              │                │                │       │
│       ▼              ▼                ▼                ▼       │
│  Chat Generator  Vision API    Flowchart Vision   直接编辑    │
│       │              │                │                │       │
└───────┼──────────────┼────────────────┼────────────────┼───────┘
        │              │                │                │
        └──────────────┴────────────────┴────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  统一处理引擎     │
                    │  (Backend API)  │
                    └─────────────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
                ▼                           ▼
        ┌──────────────┐          ┌──────────────┐
        │  ReactFlow   │ ◄────►   │ Excalidraw   │
        │  结构化画布   │  转换器   │  手绘画布     │
        └──────────────┘          └──────────────┘
                │                           │
                ├───────────────────────────┤
                │                           │
                ▼                           ▼
        ┌───────────────────────────────────────┐
        │          导出层                        │
        ├───────────────────────────────────────┤
        │  Mermaid  │  PPT  │  Slidev  │  图片  │
        └───────────────────────────────────────┘
```

**数据流向：**
1. **输入阶段** - 4种输入方式汇集到统一引擎
2. **处理阶段** - AI分析/转换为标准格式（ReactFlow nodes/edges）
3. **展示阶段** - 双画布自由切换，数据互通
4. **输出阶段** - 多格式导出

**关键创新点：**
- ✅ 所有输入最终都能进入两种画布
- ✅ 用户可以在严谨架构图和手绘风格间无缝切换
- ✅ 截图复刻 → 编辑微调 → 导出演示 的完整闭环

---

## 三、实现优先级和工作量评估

### 3.1 优先级排序（MVP → 完整版）

| 阶段 | 功能 | 优先级 | 工作量 | 依赖 | 预期效果 |
|------|------|--------|--------|------|---------|
| **MVP** | 流程图截图识别（VLM方案） | ⭐⭐⭐⭐⭐ | 2-3天 | 无 | 解决核心痛点 |
| **MVP** | ReactFlow → Excalidraw 转换 | ⭐⭐⭐⭐ | 3-4天 | 无 | 单向闭环 |
| **完整版** | Excalidraw → ReactFlow 转换 | ⭐⭐⭐ | 4-5天 | 依赖上一项 | 双向闭环 |
| **增强** | 布局优化算法（dagre/elk） | ⭐⭐ | 2-3天 | 无 | 自动美化 |
| **增强** | OCR Pipeline（高精度方案） | ⭐ | 7-10天 | VLM效果不佳时 | 提升准确率 |

### 3.2 MVP 开发计划（5-7天）

#### Day 1-2: 流程图截图识别

**后端任务：**
- [ ] 扩展 `ai_vision.py`，新增 `analyze_flowchart_image()` 方法
- [ ] 优化 prompt，针对流程图元素
- [ ] 新增 `/api/vision/analyze-flowchart` 端点
- [ ] 编写单元测试（3个测试用例）

**前端任务：**
- [ ] 创建 `FlowchartScreenshotUploader.tsx` 组件
- [ ] 集成到 `AiControlPanel.tsx`
- [ ] UI/UX 优化（拖拽上传、进度提示）

**验收标准：**
- 能识别基本的矩形、菱形、箭头
- 准确率 ≥ 85%
- 响应时间 ≤ 5秒

#### Day 3-5: ReactFlow → Excalidraw 转换

**后端任务：**
- [ ] 创建 `canvas_converter.py` 服务
- [ ] 实现 `reactflow_to_excalidraw()` 方法
- [ ] 节点类型映射表（10种节点类型）
- [ ] 新增 `/api/canvas/convert` 端点
- [ ] 编写单元测试（5个测试用例）

**前端任务：**
- [ ] Store 新增 `convertCanvas()` action
- [ ] 创建 `CanvasSwitcher.tsx` 组件
- [ ] 在工具栏集成切换按钮
- [ ] 转换动画和加载状态

**验收标准：**
- 10种节点类型都能正确转换
- 位置、颜色、标签无丢失
- 转换时间 ≤ 1秒

#### Day 6-7: 测试和文档

- [ ] 端到端测试（3个完整流程）
- [ ] 性能优化（大图处理）
- [ ] 编写 API 文档
- [ ] 更新 CLAUDE.md
- [ ] 录制功能演示视频

### 3.3 技术风险评估

| 风险 | 概率 | 影响 | 缓解措施 |
|------|------|------|---------|
| VLM识别流程图准确率不足 | 中 | 高 | 准备OCR Pipeline备选方案 |
| Excalidraw → ReactFlow 转换困难 | 高 | 中 | MVP阶段暂不实现，收集用户反馈 |
| 大图性能问题（50+节点） | 低 | 中 | 服务端限制节点数，前端虚拟化渲染 |
| 用户不理解两种画布区别 | 中 | 低 | 增加引导提示和示例 |

---

## 四、技术细节补充

### 4.1 VLM Prompt 工程优化

**当前架构图Prompt的问题：**
```python
# backend/app/services/ai_vision.py:50-80 (现有Prompt)
# 问题：过于关注"架构组件"（API、Service、Database）
# 对流程图元素（判断节点、循环）识别不足
```

**优化方向：**
1. **分类识别** - 先让AI判断图片类型（架构图 vs 流程图 vs UML）
2. **模板化Prompt** - 不同图表类型使用不同prompt模板
3. **Few-shot Learning** - 提供示例图片和预期输出

**示例Prompt（流程图专用）：**
```python
FLOWCHART_PROMPT_TEMPLATE = """
# 任务
你是流程图识别专家。分析这张流程图，提取节点和连线关系。

# 流程图元素标准
1. **开始/结束** - 圆形或圆角矩形，type="start-event"/"end-event"
2. **处理步骤** - 矩形，type="task"
3. **判断分支** - 菱形，type="decision"
4. **数据** - 平行四边形，type="default", shape="parallelogram"
5. **连线** - 箭头，记录起点终点和标签（是/否）

# 输出JSON Schema
{{
  "nodes": [
    {{"id": "n1", "type": "start-event", "position": {{"x": 0, "y": 0}}, "data": {{"label": "开始"}}}}
  ],
  "edges": [
    {{"id": "e1", "source": "n1", "target": "n2", "label": ""}}
  ]
}}

# 规则
- 确保 edges.source/target 对应 nodes.id
- position 必须有，即使不保留布局也给默认值
- label 为空时使用 "未命名"
- 判断节点的分支标签必须提取（是/否、True/False）

现在开始分析图片。
"""
```

### 4.2 坐标系统统一

**挑战：** ReactFlow 和 Excalidraw 的坐标系统不同

| 属性 | ReactFlow | Excalidraw | 转换规则 |
|------|-----------|------------|---------|
| 原点 | 左上角 (0, 0) | 左上角 (0, 0) | ✅ 相同 |
| 节点位置 | `node.position.x/y` | `element.x/y` | 直接映射 |
| 节点锚点 | 左上角 | 左上角 | ✅ 相同 |
| 边连接点 | 自动计算（handle） | 手动坐标 | 需计算中心点 |
| 缩放 | `zoom` | `appState.zoom.value` | 映射关系 |

**转换示例：**
```python
# ReactFlow Node → Excalidraw Rectangle
reactflow_node = {
    "id": "1",
    "position": {"x": 100, "y": 200},
    "data": {"label": "API Gateway"}
}

excalidraw_element = {
    "id": "shape_1",
    "type": "rectangle",
    "x": reactflow_node["position"]["x"],  # 直接映射
    "y": reactflow_node["position"]["y"],
    "width": 200,  # 固定宽度
    "height": 100,
}

# ReactFlow Edge → Excalidraw Arrow
# 需要计算起点和终点的中心坐标
source_center_x = source_node.position.x + 100  # 节点宽度一半
source_center_y = source_node.position.y + 50   # 节点高度一半
target_center_x = target_node.position.x + 100
target_center_y = target_node.position.y + 50

arrow_element = {
    "type": "arrow",
    "x": source_center_x,
    "y": source_center_y,
    "width": target_center_x - source_center_x,
    "height": target_center_y - source_center_y,
}
```

### 4.3 性能优化策略

**潜在性能瓶颈：**
1. 大图转换（100+节点） - O(n²) 复杂度
2. VLM API 调用延迟（3-8秒）
3. 前端大量 DOM 操作

**优化措施：**

```python
# 1. 后端：批量处理 + 缓存
class CanvasConverter:
    def __init__(self):
        self._cache = {}  # LRU缓存转换结果

    def reactflow_to_excalidraw(self, nodes, edges):
        # 缓存键：nodes/edges的哈希
        cache_key = self._compute_hash(nodes, edges)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # 并行处理节点（使用asyncio）
        tasks = [self._convert_node(node) for node in nodes]
        elements = await asyncio.gather(*tasks)

        # ...
```

```typescript
// 2. 前端：懒加载 + 虚拟化
const convertCanvas = async (targetFormat) => {
  // 显示骨架屏
  setLoading(true);

  // 分批转换（每批50个节点）
  const batchSize = 50;
  for (let i = 0; i < nodes.length; i += batchSize) {
    const batch = nodes.slice(i, i + batchSize);
    await convertBatch(batch);

    // 渐进式渲染，避免UI卡顿
    await new Promise(resolve => setTimeout(resolve, 100));
  }

  setLoading(false);
};
```

---

## 五、用户体验设计

### 5.1 功能入口设计

**推荐方案：** 统一的"智能输入面板"

```
┌────────────────────────────────────────┐
│  🎨 创建新图                             │
├────────────────────────────────────────┤
│  📝 自然语言描述                          │
│     "用户登录验证流程"                    │
│     [生成流程图]                         │
├────────────────────────────────────────┤
│  📷 上传截图                             │
│     [选择文件] 或 拖拽到此处               │
│     ✓ 流程图截图  ✓ 架构图  ✓ 手绘草图    │
├────────────────────────────────────────┤
│  ✏️ 手动绘制                             │
│     [结构化模式] [手绘模式]               │
└────────────────────────────────────────┘
```

### 5.2 画布切换交互

**方案1：** 无感知自动切换（推荐）
- 用户选择"手绘模式"时，自动转换现有图表
- 显示转换预览 → 用户确认 → 切换画布

**方案2：** 手动触发转换
- 工具栏增加"转为手绘"/"转为结构化"按钮
- 点击后弹窗提示："将转换为手绘风格，是否继续？"

### 5.3 错误处理

**截图识别失败场景：**
1. 图片模糊 → 提示"请上传清晰的截图"
2. 无法识别元素 → 提示"未检测到流程图元素，请尝试架构图分析"
3. VLM超时 → 自动降级到OCR方案（如果实现）

**转换失败场景：**
1. 节点过多（>200） → 提示"图表过大，建议拆分为多个子图"
2. 数据格式错误 → 显示技术错误详情 + 联系方式

---

## 六、测试策略

### 6.1 测试用例设计

#### 流程图截图识别

| 用例ID | 输入 | 预期输出 | 优先级 |
|--------|------|---------|--------|
| FC-001 | 标准Visio流程图截图（5节点） | 识别所有节点和连线，准确率100% | P0 |
| FC-002 | 手绘流程图照片（不规则） | 识别主要元素，准确率≥80% | P1 |
| FC-003 | BPMN流程图（泳道图） | 识别节点，泳道作为分组 | P2 |
| FC-004 | 中英文混合流程图 | 正确识别中英文标签 | P0 |
| FC-005 | 大型流程图（50+节点） | 识别成功，耗时≤10秒 | P1 |

#### 画布转换

| 用例ID | 输入 | 预期输出 | 优先级 |
|--------|------|---------|--------|
| CV-001 | 10节点ReactFlow图 → Excalidraw | 保留所有节点、位置、标签 | P0 |
| CV-002 | 带动画边的ReactFlow图 | Excalidraw中显示为虚线 | P1 |
| CV-003 | Excalidraw手绘图 → ReactFlow | 识别形状，生成节点 | P2 |
| CV-004 | 复杂嵌套节点（Frame） | 正确处理分组关系 | P2 |

### 6.2 性能基准

| 指标 | 目标值 | 测量方法 |
|------|--------|---------|
| 截图识别响应时间 | ≤ 5秒 | 中等复杂度图（20节点） |
| 画布转换时间 | ≤ 1秒 | 50节点图 |
| 大图转换时间 | ≤ 3秒 | 200节点图 |
| VLM识别准确率 | ≥ 85% | 人工标注100张测试图 |
| 前端帧率 | ≥ 30fps | 转换过程中 |

---

## 七、未来扩展方向

### 7.1 Phase 7 候选功能

1. **实时协作** ⭐⭐⭐⭐
   - WebSocket 多人同时编辑
   - 光标位置同步
   - 冲突解决

2. **版本控制** ⭐⭐⭐⭐
   - Git集成
   - 图表diff可视化
   - 回滚和分支

3. **AI 辅助优化** ⭐⭐⭐
   - 自动检测流程冗余
   - 推荐最佳实践
   - 性能瓶颈分析

4. **更多导出格式** ⭐⭐⭐
   - SVG/PNG高清图
   - PlantUML
   - C4 Model

5. **移动端支持** ⭐⭐
   - 响应式设计
   - 触摸手势
   - 离线编辑

### 7.2 技术债务

- [ ] 补全自动布局（dagre/elk算法）
- [ ] Mermaid → Excalidraw 直接转换（目前需经过ReactFlow）
- [ ] 统一错误处理机制
- [ ] 完善TypeScript类型定义

---

## 八、总结与建议

### 8.1 核心价值

**Phase 6 解决的核心问题：**
1. ✅ **画布闭环** - ReactFlow ↔ Excalidraw 自由切换
2. ✅ **截图复刻** - 任意流程图截图 → 可编辑图表
3. ✅ **降低门槛** - 用户不需要从零开始，可以基于现有图表修改

**商业价值：**
- 用户留存率提升（更多输入方式 = 更多使用场景）
- 与竞品差异化（Visio/ProcessOn 没有AI识别 + 双画布）
- 形成闭环生态（输入 → 编辑 → 导出）

### 8.2 实施建议

**推荐路径：MVP → 迭代**

1. **Week 1-2: MVP开发**
   - 流程图截图识别（VLM方案）
   - ReactFlow → Excalidraw 单向转换
   - 基础UI集成

2. **Week 3: 用户测试**
   - 邀请10-20个用户内测
   - 收集反馈（识别准确率、转换效果）
   - 优化Prompt和转换规则

3. **Week 4+: 完整版**
   - 根据反馈决定是否实现 Excalidraw → ReactFlow
   - 性能优化（大图处理）
   - 编写文档和教程

**不建议一次性全部实现的原因：**
- Excalidraw → ReactFlow 转换技术难度高（启发式算法复杂）
- 用户可能更关心"截图复刻"而非"手绘转结构化"
- 迭代开发可以快速验证价值

### 8.3 技术选型建议

| 技术点 | 推荐方案 | 理由 |
|--------|---------|------|
| 流程图识别 | Qwen2.5-VL (SiliconFlow) | 性价比最高，已集成 |
| 备选方案 | Gemini 2.5 Flash | 响应最快 |
| 转换器架构 | 自研 Python 服务 | 灵活可控，易扩展 |
| 前端状态管理 | Zustand（现有） | 无需引入新依赖 |
| 测试框架 | Pytest（现有） | 保持一致性 |

---

## 附录

### A. 相关资源链接

**VLM 模型文档：**
- [Qwen2.5-VL API文档](https://docs.siliconflow.cn/docs/qwen2-vl)
- [Gemini 2.5 Flash Vision](https://ai.google.dev/gemini-api/docs/vision)
- [Claude 3.5 Sonnet Vision](https://docs.anthropic.com/claude/docs/vision)

**Excalidraw 开发文档：**
- [Excalidraw Scene Format](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api#scene-data)
- [Element Types](https://docs.excalidraw.com/docs/@excalidraw/excalidraw/api#element)

**React Flow 文档：**
- [Custom Nodes](https://reactflow.dev/learn/customization/custom-nodes)
- [Data Flow](https://reactflow.dev/learn/advanced-use/state-management)

### B. 竞品分析

| 产品 | 截图识别 | 双画布 | AI生成 | 差异化 |
|------|---------|--------|--------|--------|
| **SmartArchitect (本系统)** | ✅ 计划中 | ✅ 计划中 | ✅ 已有 | AI驱动全流程 |
| Visio | ❌ 无 | ❌ 无 | ❌ 无 | 传统桌面软件 |
| ProcessOn | ❌ 无 | ❌ 无 | ⚠️ 基础 | 在线协作 |
| Draw.io | ❌ 无 | ❌ 无 | ❌ 无 | 开源免费 |
| Miro | ⚠️ 基础OCR | ❌ 无 | ⚠️ 基础 | 白板协作 |
| Excalidraw | ❌ 无 | ❌ 无 | ❌ 无 | 纯手绘 |

**结论：** 如果实现 Phase 6，将成为**首个支持截图识别 + 双画布的AI架构图工具**。

### C. 开源协议建议

如果计划开源，建议：
- **MIT License** - 最宽松，利于商业化
- **Apache 2.0** - 保护专利，适合企业使用
- **AGPL 3.0** - 防止云服务商白嫖（如果提供SaaS）

---

**文档版本：** v1.0
**最后更新：** 2026-01-20
**作者：** Claude (Anthropic)
**审阅状态：** 待讨论
