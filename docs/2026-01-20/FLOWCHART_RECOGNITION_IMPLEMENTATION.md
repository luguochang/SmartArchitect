# 流程图截图识别功能 - 完整实现方案

**功能目标：** 用户上传流程图截图（Visio/ProcessOn/手绘等），AI识别并转换为可编辑的ReactFlow图表

**技术栈：** Qwen2.5-VL（推荐）/ Gemini 2.5 Flash / Claude 3.5

**工作量：** 2-3天

---

## 📋 实现步骤总览

1. ✅ **扩展 AI Vision 服务** - 新增流程图识别方法
2. ✅ **新增 API 端点** - `/api/vision/analyze-flowchart`
3. ✅ **前端上传组件** - 拖拽上传 + 识别结果展示
4. ✅ **测试验证** - 多种流程图测试

---

## Step 1: 扩展 AI Vision 服务

### 文件：`backend/app/services/ai_vision.py`

#### 1.1 新增流程图Prompt构建方法

在 `AIVisionService` 类中添加：

```python
# 在第 240 行后添加（_build_analysis_prompt 方法后面）

def _build_flowchart_prompt(self, preserve_layout: bool = True) -> str:
    """
    构建流程图识别专用 Prompt

    与架构图的区别：
    - 关注流程图元素（开始/结束/判断/处理节点）
    - 支持 BPMN 标准形状
    - 强调连线方向和分支标签
    """

    # 支持的形状类型（从 SvgShapes.tsx 映射）
    supported_shapes = {
        "circle": "圆形 → start-event（开始）或 end-event（结束）",
        "rectangle": "矩形 → task（处理任务）",
        "diamond": "菱形 → decision（判断/决策）",
        "parallelogram": "平行四边形 → default with shape='parallelogram'（数据/输入输出）",
        "hexagon": "六边形 → default with shape='hexagon'（准备）",
        "trapezoid": "梯形 → default with shape='trapezoid'（手动操作）",
        "cylinder": "圆柱体 → database（数据库）",
        "document": "文档形 → default with shape='document'",
        "cloud": "云形 → default with shape='cloud'",
    }

    shapes_desc = "\\n".join([f"   - {shape}: {desc}" for shape, desc in supported_shapes.items()])

    layout_instruction = ""
    if preserve_layout:
        layout_instruction = """
4. **布局保留**：
   - 记录每个节点的相对位置（左上角坐标）
   - 参考原图的空间布局关系
   - x坐标从100开始，y坐标从50开始
   - 节点间距建议保持150-200px
"""
    else:
        layout_instruction = """
4. **自动布局**：
   - 忽略原图位置，使用标准布局
   - 从上到下、从左到右排列
   - x坐标从100开始，y坐标从50开始，每行间距200px
"""

    prompt = f"""
你是专业的流程图分析专家。请分析这张**流程图截图**，提取节点和连线关系。

## 识别规则

1. **节点类型识别**（根据形状判断）：
{shapes_desc}

   **重要：** 圆形节点需判断是开始还是结束：
   - 文本包含"开始"/"Start"/"启动" → type="start-event"
   - 文本包含"结束"/"End"/"完成" → type="end-event"
   - 无法判断时默认 → type="start-event"

2. **文本识别**：
   - 提取每个节点内的文本作为 label
   - 识别连线上的文本作为 edge.label
   - 如果节点无文本，label 设为 "未命名节点"

3. **连线识别**：
   - 识别箭头方向（起点节点 → 终点节点）
   - 判断连线类型：
     * 虚线 → animated: false（保持默认）
     * 实线 → animated: false
   - 提取判断分支标签（是/否、Yes/No、True/False、Y/N）

{layout_instruction}

## 输出格式（JSON）

返回 **纯 JSON 对象**，不要用 markdown 代码块包裹：

{{
  "nodes": [
    {{
      "id": "node_1",
      "type": "start-event",
      "position": {{"x": 100, "y": 50}},
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
    }},
    {{
      "id": "node_4",
      "type": "end-event",
      "position": {{"x": 300, "y": 500}},
      "data": {{
        "label": "结束",
        "shape": "circle"
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
  "mermaid_code": "graph TD\\n    node_1((开始))\\n    node_2[执行任务A]\\n    node_3{{条件判断}}\\n    node_4((结束))\\n    node_1 --> node_2\\n    node_2 --> node_3\\n    node_3 -->|是| node_4\\n    node_3 -->|否| node_5",
  "warnings": [
    {{"node_id": "node_X", "message": "原图为八边形，已映射为六边形（hexagon）"}}
  ],
  "analysis": {{
    "total_nodes": 4,
    "total_branches": 1,
    "flowchart_type": "业务流程图",
    "complexity": "简单",
    "description": "这是一个包含4个节点的简单流程图，从开始到结束经过一个判断节点"
  }}
}}

## 注意事项

- **所有节点必须有 position**（即使是自动布局也要给坐标）
- **edges 的 source 和 target 必须对应 nodes 的 id**
- **节点 id 必须唯一**（建议使用 node_1, node_2, node_3...）
- **不要输出 markdown 代码块**（如 ```json ... ```），直接输出 JSON
- **如果形状不在支持列表，选择最接近的形状，并在 warnings 中说明**
- **Mermaid 代码格式：**
  - 开始/结束节点：`nodeId((label))`
  - 处理节点：`nodeId[label]`
  - 判断节点：`nodeId{{label}}`
  - 连线：`node1 --> node2` 或 `node1 -->|label| node2`

现在开始分析图片，返回 JSON：
"""

    return prompt
```

#### 1.2 新增流程图分析方法

```python
# 在 analyze_architecture 方法后添加（约 268 行）

async def analyze_flowchart(
    self,
    image_data: bytes,
    preserve_layout: bool = True
) -> ImageAnalysisResponse:
    """
    分析流程图截图

    Args:
        image_data: 图片二进制数据
        preserve_layout: 是否保留原图布局

    Returns:
        ImageAnalysisResponse: 包含 nodes, edges, mermaid_code, warnings
    """
    prompt = self._build_flowchart_prompt(preserve_layout)

    try:
        logger.info(f"[FLOWCHART] Starting analysis with {self.provider}, preserve_layout={preserve_layout}")

        if self.provider == "gemini":
            result = await self._analyze_with_gemini(image_data, prompt)
        elif self.provider == "openai":
            result = await self._analyze_with_openai(image_data, prompt)
        elif self.provider == "claude":
            result = await self._analyze_with_claude(image_data, prompt)
        elif self.provider == "siliconflow":
            raise ValueError("SiliconFlow provider is text-only. Use gemini/openai/claude for image analysis.")
        elif self.provider == "custom":
            result = await self._analyze_with_custom(image_data, prompt)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

        logger.info(f"[FLOWCHART] Analysis completed: {len(result.nodes)} nodes, {len(result.edges)} edges")

        # 添加warnings到响应（如果有）
        # warnings 已经在 JSON 中，_build_response 会处理

        return result

    except Exception as e:
        logger.error(f"Flowchart analysis failed with {self.provider}: {e}", exc_info=True)
        raise
```

#### 1.3 更新 _build_response 方法以支持 warnings

```python
# 在 _build_response 方法中添加 warnings 处理（约 553 行）

def _build_response(self, result_json: Dict[str, Any]) -> ImageAnalysisResponse:
    """构建响应对象"""
    try:
        # 解析节点
        nodes = [
            Node(
                id=node["id"],
                type=node.get("type", "default"),
                position=Position(**node["position"]),
                data=NodeData(
                    label=node["data"]["label"],
                    shape=node["data"].get("shape"),  # 添加 shape 支持
                )
            )
            for node in result_json.get("nodes", [])
        ]

        # 解析边
        edges = [
            Edge(
                id=edge["id"],
                source=edge["source"],
                target=edge["target"],
                label=edge.get("label")
            )
            for edge in result_json.get("edges", [])
        ]

        # 解析 AI 分析（如果有）
        ai_analysis = None
        if "ai_analysis" in result_json and result_json["ai_analysis"]:
            ai_data = result_json["ai_analysis"]
            ai_analysis = AIAnalysis(
                bottlenecks=[
                    ArchitectureBottleneck(**b)
                    for b in ai_data.get("bottlenecks", [])
                ],
                suggestions=[
                    OptimizationSuggestion(**s)
                    for s in ai_data.get("suggestions", [])
                ],
                confidence=ai_data.get("confidence"),
                model_used=ai_data.get("model_used")
            )

        # 提取 warnings（流程图识别专用）
        warnings = result_json.get("warnings", [])

        # 提取 analysis（流程图分析）
        flowchart_analysis = result_json.get("analysis", {})

        return ImageAnalysisResponse(
            nodes=nodes,
            edges=edges,
            mermaid_code=result_json.get("mermaid_code", ""),
            success=True,
            ai_analysis=ai_analysis,
            warnings=warnings,  # 新增字段
            flowchart_analysis=flowchart_analysis  # 新增字段
        )

    except Exception as e:
        logger.error(f"Failed to build response: {e}")
        raise ValueError(f"Invalid response structure: {str(e)}")
```

---

## Step 2: 更新 Pydantic Schemas

### 文件：`backend/app/models/schemas.py`

在 `ImageAnalysisResponse` 类中添加新字段：

```python
# 在第 100 行后添加

class ImageAnalysisResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    mermaid_code: str
    success: bool = True
    ai_analysis: Optional[AIAnalysis] = None

    # Phase 6: 流程图识别专用字段
    warnings: Optional[List[dict]] = None  # 识别警告（如：形状映射）
    flowchart_analysis: Optional[dict] = None  # 流程图分析（复杂度、类型等）
```

---

## Step 3: 新增 API 端点

### 文件：`backend/app/api/vision.py`

在现有的 `/vision/analyze` 后添加新端点：

```python
# 在第 154 行后添加（vision_health_check 后面）

@router.post("/vision/analyze-flowchart", response_model=ImageAnalysisResponse)
async def analyze_flowchart_screenshot(
    file: UploadFile = File(..., description="Flowchart screenshot (PNG/JPG/WEBP)"),
    provider: str = Query("gemini", description="AI provider: gemini, openai, claude, custom"),
    preserve_layout: bool = Query(True, description="Preserve original node positions"),
    api_key: Optional[str] = Form(None, description="Optional API key"),
    base_url: Optional[str] = Form(None, description="Custom provider base URL"),
    model_name: Optional[str] = Form(None, description="Custom model name"),
):
    """
    识别流程图截图，转换为可编辑的 ReactFlow 格式

    **功能特点：**
    - 支持多种流程图工具截图（Visio、ProcessOn、Draw.io等）
    - 识别 BPMN 标准节点（开始/结束/任务/判断）
    - 支持手绘流程图照片
    - 可选保留原始布局或自动重排

    **与 /vision/analyze 的区别：**
    - /vision/analyze: 针对架构图（API、Service、Database等）
    - /vision/analyze-flowchart: 针对流程图（开始/结束/判断等）

    **参数：**
    - file: 流程图截图文件（支持 PNG/JPG/WEBP，最大10MB）
    - provider: AI模型提供商
      - gemini: Google Gemini 2.5 Flash（推荐，速度快）
      - openai: GPT-4 Vision
      - claude: Claude 3.5 Sonnet（准确率高）
      - custom: 自定义API（需提供 base_url 和 model_name）
    - preserve_layout: 是否保留原图布局
      - true: 尽量保持节点位置关系
      - false: AI自动优化布局
    - api_key: 可选的API密钥（优先使用，否则使用环境变量）

    **返回：**
    - nodes: ReactFlow 节点数组（匹配现有17种形状）
    - edges: 连线数组
    - mermaid_code: Mermaid 代码
    - warnings: 识别警告（如：未支持的形状映射）
    - flowchart_analysis: 流程分析（复杂度、分支数等）

    **示例响应：**
    ```json
    {
      "nodes": [
        {
          "id": "node_1",
          "type": "start-event",
          "position": {"x": 100, "y": 50},
          "data": {"label": "开始", "shape": "circle"}
        }
      ],
      "edges": [...],
      "warnings": [
        {"node_id": "node_3", "message": "原图为八边形，已映射为六边形"}
      ],
      "flowchart_analysis": {
        "total_nodes": 5,
        "total_branches": 2,
        "complexity": "中等"
      }
    }
    ```
    """

    # 验证文件类型
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. "
                   f"Allowed: {', '.join(ALLOWED_CONTENT_TYPES)}"
        )

    # 读取文件
    try:
        image_data = await file.read()
    except Exception as e:
        logger.error(f"Failed to read file: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to read file: {str(e)}"
        )

    # 验证文件大小
    file_size = len(image_data)
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large: {file_size / 1024 / 1024:.2f}MB. Max: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
        )

    if file_size == 0:
        raise HTTPException(status_code=400, detail="Empty file")

    # 验证 provider
    if provider not in ["gemini", "openai", "claude", "custom"]:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported provider: {provider}. Allowed: gemini, openai, claude, custom"
        )

    # 验证自定义 provider
    if provider == "custom":
        if not base_url:
            raise HTTPException(status_code=400, detail="base_url required for custom provider")
        if not model_name:
            raise HTTPException(status_code=400, detail="model_name required for custom provider")

    # 创建 Vision Service
    try:
        vision_service = create_vision_service(
            provider,
            api_key=api_key,
            base_url=base_url,
            model_name=model_name
        )
    except Exception as e:
        logger.error(f"Failed to initialize {provider} service: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize AI service: {str(e)}"
        )

    # 分析流程图
    try:
        logger.info(f"[FLOWCHART API] Analyzing with {provider}, size: {file_size} bytes, preserve_layout: {preserve_layout}")

        result = await vision_service.analyze_flowchart(
            image_data=image_data,
            preserve_layout=preserve_layout
        )

        logger.info(f"[FLOWCHART API] Success: {len(result.nodes)} nodes, {len(result.edges)} edges")

        # 记录警告（如果有）
        if result.warnings:
            logger.warning(f"[FLOWCHART API] Warnings: {result.warnings}")

        return result

    except ValueError as e:
        # AI 响应解析错误
        logger.error(f"AI response parsing error: {e}")
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse AI response: {str(e)}"
        )

    except Exception as e:
        # 其他错误
        logger.error(f"Flowchart analysis failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Flowchart analysis failed: {str(e)}"
        )
```

---

## Step 4: 前端上传组件

### 文件：`frontend/components/FlowchartUploader.tsx`（新建）

```typescript
"use client";

import { useState, useCallback } from "react";
import { Upload, Loader2, CheckCircle2, AlertCircle, X } from "lucide-react";
import { useArchitectStore } from "@/lib/store/useArchitectStore";
import { toast } from "sonner";

interface UploadResult {
  nodes: any[];
  edges: any[];
  warnings?: Array<{ node_id: string; message: string }>;
  flowchart_analysis?: {
    total_nodes: number;
    total_branches: number;
    complexity: string;
    flowchart_type: string;
  };
}

export function FlowchartUploader() {
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<UploadResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragActive, setDragActive] = useState(false);

  const { modelConfig, setNodes, setEdges } = useArchitectStore();

  const handleFile = useCallback(
    async (file: File) => {
      // 验证文件类型
      const validTypes = ["image/png", "image/jpeg", "image/jpg", "image/webp"];
      if (!validTypes.includes(file.type)) {
        toast.error("仅支持 PNG、JPG、WEBP 格式");
        return;
      }

      // 验证文件大小（10MB）
      if (file.size > 10 * 1024 * 1024) {
        toast.error("文件过大，最大支持10MB");
        return;
      }

      setUploading(true);
      setError(null);
      setResult(null);

      const formData = new FormData();
      formData.append("file", file);
      formData.append("provider", modelConfig.provider || "gemini");
      formData.append("preserve_layout", "true");
      if (modelConfig.apiKey) {
        formData.append("api_key", modelConfig.apiKey);
      }

      try {
        toast.info("正在识别流程图...");

        const response = await fetch("http://localhost:8000/api/vision/analyze-flowchart", {
          method: "POST",
          body: formData,
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || "识别失败");
        }

        const data: UploadResult = await response.json();

        setResult(data);

        // 应用到画布
        setNodes(data.nodes);
        setEdges(data.edges);

        // 成功提示
        toast.success(
          `识别成功！共 ${data.nodes.length} 个节点，${data.edges.length} 条连线`
        );

        // 显示警告（如果有）
        if (data.warnings && data.warnings.length > 0) {
          toast.warning(`注意：${data.warnings.length} 个节点的形状被映射`);
        }
      } catch (err: any) {
        console.error("Upload error:", err);
        setError(err.message || "识别失败");
        toast.error(err.message || "识别失败，请重试");
      } finally {
        setUploading(false);
      }
    },
    [modelConfig, setNodes, setEdges]
  );

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setDragActive(false);

      const files = e.dataTransfer.files;
      if (files && files[0]) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
  }, []);

  const handleFileInput = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files[0]) {
        handleFile(files[0]);
      }
    },
    [handleFile]
  );

  return (
    <div className="space-y-4">
      {/* 上传区域 */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`
          relative rounded-xl border-2 border-dashed p-8 text-center transition-all
          ${
            dragActive
              ? "border-indigo-500 bg-indigo-50 dark:bg-indigo-950"
              : "border-slate-300 bg-white dark:border-slate-600 dark:bg-slate-800"
          }
          ${uploading ? "pointer-events-none opacity-60" : "cursor-pointer hover:border-indigo-400"}
        `}
      >
        <input
          type="file"
          accept="image/png,image/jpeg,image/jpg,image/webp"
          onChange={handleFileInput}
          className="hidden"
          id="flowchart-upload-input"
          disabled={uploading}
        />

        <label htmlFor="flowchart-upload-input" className="cursor-pointer">
          {uploading ? (
            <div className="flex flex-col items-center gap-3">
              <Loader2 className="h-12 w-12 animate-spin text-indigo-600" />
              <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                正在识别流程图...
              </p>
              <p className="text-xs text-slate-500">
                使用 {modelConfig.provider || "Gemini"} 模型分析中
              </p>
            </div>
          ) : (
            <div className="flex flex-col items-center gap-3">
              <Upload className="h-12 w-12 text-slate-400" />
              <div>
                <p className="text-sm font-medium text-slate-700 dark:text-slate-300">
                  上传流程图截图
                </p>
                <p className="mt-1 text-xs text-slate-500">
                  或拖拽文件到此处
                </p>
              </div>
              <div className="mt-2 rounded-lg bg-slate-100 px-3 py-1 text-xs text-slate-600 dark:bg-slate-700 dark:text-slate-400">
                支持 PNG、JPG、WEBP，最大 10MB
              </div>
            </div>
          )}
        </label>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="flex items-start gap-3 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-900 dark:bg-red-950">
          <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
          <div className="flex-1">
            <p className="text-sm font-medium text-red-900 dark:text-red-100">
              识别失败
            </p>
            <p className="mt-1 text-xs text-red-700 dark:text-red-300">{error}</p>
          </div>
          <button
            onClick={() => setError(null)}
            className="text-red-600 hover:text-red-800 dark:text-red-400"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* 成功结果 */}
      {result && (
        <div className="space-y-3 rounded-lg border border-green-200 bg-green-50 p-4 dark:border-green-900 dark:bg-green-950">
          <div className="flex items-start gap-3">
            <CheckCircle2 className="h-5 w-5 text-green-600 dark:text-green-400" />
            <div className="flex-1">
              <p className="text-sm font-medium text-green-900 dark:text-green-100">
                识别成功！
              </p>
              <p className="mt-1 text-xs text-green-700 dark:text-green-300">
                {result.nodes.length} 个节点，{result.edges.length} 条连线
              </p>
            </div>
            <button
              onClick={() => setResult(null)}
              className="text-green-600 hover:text-green-800 dark:text-green-400"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* 流程图分析 */}
          {result.flowchart_analysis && (
            <div className="mt-3 rounded-lg bg-white p-3 dark:bg-slate-800">
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div>
                  <span className="text-slate-500">类型：</span>
                  <span className="ml-1 font-medium text-slate-900 dark:text-white">
                    {result.flowchart_analysis.flowchart_type}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">复杂度：</span>
                  <span className="ml-1 font-medium text-slate-900 dark:text-white">
                    {result.flowchart_analysis.complexity}
                  </span>
                </div>
                <div>
                  <span className="text-slate-500">分支数：</span>
                  <span className="ml-1 font-medium text-slate-900 dark:text-white">
                    {result.flowchart_analysis.total_branches}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* 警告信息 */}
          {result.warnings && result.warnings.length > 0 && (
            <div className="mt-3 space-y-1">
              <p className="text-xs font-medium text-amber-900 dark:text-amber-100">
                识别警告：
              </p>
              {result.warnings.map((warning, idx) => (
                <p key={idx} className="text-xs text-amber-700 dark:text-amber-300">
                  • {warning.message}
                </p>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 使用提示 */}
      <div className="rounded-lg bg-blue-50 p-4 dark:bg-blue-950">
        <p className="text-xs font-medium text-blue-900 dark:text-blue-100">
          💡 支持的流程图工具
        </p>
        <ul className="mt-2 space-y-1 text-xs text-blue-700 dark:text-blue-300">
          <li>• Visio 导出的流程图</li>
          <li>• ProcessOn 截图</li>
          <li>• Draw.io / diagrams.net</li>
          <li>• 白板手绘流程图照片</li>
          <li>• 其他标准流程图工具</li>
        </ul>
      </div>
    </div>
  );
}
```

### 集成到 AiControlPanel

```typescript
// frontend/components/AiControlPanel.tsx

// 在 imports 中添加
import { FlowchartUploader } from "./FlowchartUploader";

// 在 Tab 列表中添加
<Tab value="upload">
  <Upload className="h-4 w-4" />
  截图识别
</Tab>

// 在 Tab 内容中添加
{activeTab === "upload" && (
  <div className="space-y-4 p-4">
    <h3 className="text-sm font-semibold text-slate-900 dark:text-white">
      流程图截图识别
    </h3>
    <FlowchartUploader />
  </div>
)}
```

---

## Step 5: 测试验证

### 5.1 后端测试

创建测试文件：`backend/tests/test_flowchart_vision.py`

```python
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_flowchart_analyze_no_file():
    """测试：未上传文件"""
    response = client.post("/api/vision/analyze-flowchart")
    assert response.status_code == 422  # Validation error

def test_flowchart_analyze_invalid_provider():
    """测试：不支持的provider"""
    # 创建测试图片（1x1 PNG）
    import io
    from PIL import Image

    img = Image.new('RGB', (1, 1), color='white')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)

    files = {"file": ("test.png", img_bytes, "image/png")}
    data = {"provider": "invalid"}

    response = client.post("/api/vision/analyze-flowchart", files=files, data=data)
    assert response.status_code == 400
    assert "Unsupported provider" in response.json()["detail"]

# 需要真实图片和API key的测试（跳过）
@pytest.mark.skip(reason="Requires real image and API key")
def test_flowchart_analyze_with_gemini():
    """测试：使用Gemini识别流程图"""
    # 使用真实流程图截图测试
    pass
```

运行测试：

```bash
cd backend
python -m pytest tests/test_flowchart_vision.py -v
```

### 5.2 手动测试流程

1. **启动后端服务**
   ```bash
   cd backend
   python -m app.main
   ```

2. **启动前端服务**
   ```bash
   cd frontend
   npm run dev
   ```

3. **访问测试页面**
   - 打开 http://localhost:3000
   - 点击 AI 控制面板
   - 切换到"截图识别"Tab

4. **准备测试图片**
   - 简单流程图（3-5个节点）
   - 中等流程图（10-15个节点）
   - 复杂流程图（20+个节点）
   - 手绘流程图照片

5. **上传测试**
   - 拖拽图片或点击上传
   - 观察识别结果
   - 检查警告信息
   - 验证节点位置是否合理

### 5.3 识别准确率验证

准备测试用例：

| 测试图片 | 节点数 | 预期识别率 | 关键验证点 |
|---------|--------|-----------|-----------|
| Visio标准流程图 | 5 | >95% | 形状、文本、连线 |
| ProcessOn截图 | 10 | >90% | 布局保留 |
| 手绘流程图 | 8 | >80% | 形状近似识别 |
| BPMN流程图 | 15 | >85% | 泳道、事件节点 |

---

## 📝 完整文件清单

### 后端修改

```
backend/
├── app/
│   ├── services/
│   │   └── ai_vision.py         # 新增 analyze_flowchart 方法
│   ├── models/
│   │   └── schemas.py           # 新增 warnings、flowchart_analysis 字段
│   └── api/
│       └── vision.py            # 新增 /vision/analyze-flowchart 端点
└── tests/
    └── test_flowchart_vision.py # 新增测试文件
```

### 前端新增

```
frontend/
└── components/
    └── FlowchartUploader.tsx    # 新增上传组件
```

### 前端修改

```
frontend/
└── components/
    └── AiControlPanel.tsx       # 集成上传组件
```

---

## 🚀 部署建议

### 生产环境配置

```python
# backend/app/core/config.py

# 推荐使用 Gemini（性价比最高）
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# 或使用 Claude（准确率最高）
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# 图片上传限制
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_CONTENT_TYPES = ["image/png", "image/jpeg", "image/jpg", "image/webp"]

# 超时设置（流程图识别可能较慢）
VISION_TIMEOUT = 60  # 60秒
```

### 性能优化

1. **图片压缩**（可选）
   ```python
   from PIL import Image
   import io

   def compress_image(image_data: bytes, max_size: int = 1024) -> bytes:
       """压缩图片以加快传输"""
       img = Image.open(io.BytesIO(image_data))

       # 如果图片过大，缩小尺寸
       if img.width > max_size or img.height > max_size:
           img.thumbnail((max_size, max_size))

       output = io.BytesIO()
       img.save(output, format='JPEG', quality=85)
       return output.getvalue()
   ```

2. **结果缓存**
   ```python
   from functools import lru_cache
   import hashlib

   def get_image_hash(image_data: bytes) -> str:
       """计算图片哈希"""
       return hashlib.md5(image_data).hexdigest()

   # 使用 Redis 缓存识别结果
   # cache_key = f"flowchart:{image_hash}"
   ```

---

## 🎯 下一步扩展

完成基础功能后，可以考虑：

1. **批量上传** - 一次上传多张流程图
2. **OCR增强** - 对模糊图片预处理
3. **形状学习** - 用户纠正后训练自定义形状识别
4. **版本对比** - 对比两张流程图的差异

---

**创建日期：** 2026-01-20
**预计工作量：** 2-3天
**优先级：** ⭐⭐⭐⭐⭐ 最高
