from pydantic import BaseModel, Field
from typing import List, Optional, Literal


# React Flow 节点和边的数据模型
class NodeData(BaseModel):
    label: str
    shape: Optional[Literal["rectangle", "circle", "diamond", "start-event", "end-event", "intermediate-event", "task"]] = None
    iconType: Optional[str] = None  # Icon identifier (e.g., "play-circle", "stop-circle")
    color: Optional[str] = None  # Color class or value


class Position(BaseModel):
    x: float
    y: float


class Node(BaseModel):
    id: str
    type: Optional[str] = "default"
    position: Position
    data: NodeData


class Edge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None


class GraphData(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


# Mermaid 转换相关
class MermaidParseRequest(BaseModel):
    code: str = Field(..., description="Mermaid 代码")


class MermaidParseResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    success: bool = True
    message: Optional[str] = None


class GraphToMermaidRequest(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


class GraphToMermaidResponse(BaseModel):
    mermaid_code: str
    success: bool = True


# AI 模型配置
class ModelConfig(BaseModel):
    provider: Literal["gemini", "openai", "claude", "siliconflow", "custom"]
    api_key: str
    model_name: str
    base_url: Optional[str] = None


class ModelConfigResponse(BaseModel):
    success: bool
    message: str


# 模型预设配置（支持保存多个配置）
class ModelPreset(BaseModel):
    id: str  # 预设ID（如 "my-gemini", "company-openai"）
    name: str  # 显示名称（如 "个人 Gemini", "公司 OpenAI"）
    provider: Literal["gemini", "openai", "claude", "siliconflow", "custom"]
    api_key: str
    model_name: str
    base_url: Optional[str] = None
    is_default: bool = False  # 是否为默认配置
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ModelPresetCreate(BaseModel):
    name: str
    provider: Literal["gemini", "openai", "claude", "siliconflow", "custom"]
    api_key: str
    model_name: str
    base_url: Optional[str] = None
    is_default: bool = False


class ModelPresetUpdate(BaseModel):
    name: Optional[str] = None
    api_key: Optional[str] = None
    model_name: Optional[str] = None
    base_url: Optional[str] = None
    is_default: Optional[bool] = None


class ModelPresetListResponse(BaseModel):
    success: bool
    presets: List[ModelPreset]


class ModelPresetResponse(BaseModel):
    success: bool
    preset: Optional[ModelPreset] = None
    message: Optional[str] = None


# ========== Phase 2: 图片分析和架构优化 ==========

# 架构瓶颈
class ArchitectureBottleneck(BaseModel):
    node_id: str
    type: Literal["single_point_of_failure", "performance_bottleneck",
                   "scalability_issue", "security_concern"]
    severity: Literal["low", "medium", "high", "critical"]
    description: str
    recommendation: str


# 优化建议
class OptimizationSuggestion(BaseModel):
    id: str
    title: str
    description: str
    bottlenecks: List[ArchitectureBottleneck]
    optimized_nodes: List[Node]
    optimized_edges: List[Edge]
    optimized_mermaid: str
    impact: Literal["low", "medium", "high"]


# AI 分析结果
class AIAnalysis(BaseModel):
    bottlenecks: List[ArchitectureBottleneck] = []
    suggestions: List[OptimizationSuggestion] = []
    confidence: Optional[float] = None
    model_used: Optional[str] = None


# 图片分析响应
class ImageAnalysisResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    mermaid_code: str
    success: bool = True
    message: Optional[str] = None
    ai_analysis: Optional[AIAnalysis] = None

    # Phase 6: 流程图识别专用字段
    warnings: Optional[List[dict]] = None  # 识别警告（如：形状映射）
    flowchart_analysis: Optional[dict] = None  # 流程图分析（复杂度、类型等）


# 架构优化分析请求
class OptimizationAnalysisRequest(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


# 架构优化分析响应
class OptimizationAnalysisResponse(BaseModel):
    suggestions: List[OptimizationSuggestion]
    success: bool = True
    message: Optional[str] = None


# ========== Phase 3: Prompter 系统 ==========

# Prompter 场景预设
class PromptScenario(BaseModel):
    id: str
    name: str
    description: str
    system_prompt: str
    user_prompt_template: str
    category: Literal["refactoring", "security", "beautification", "custom"]
    icon: Optional[str] = None
    is_default: bool = False


# Prompter 场景列表
class PromptScenarioList(BaseModel):
    scenarios: List[PromptScenario]


# Prompter 执行请求
class PromptExecutionRequest(BaseModel):
    scenario_id: str
    nodes: List[Node]
    edges: List[Edge]
    user_input: Optional[str] = None
    mermaid_code: Optional[str] = None


# Prompter 执行响应
class PromptExecutionResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    mermaid_code: str
    ai_explanation: str
    success: bool = True
    message: Optional[str] = None


# ============================================================
# Phase 4: RAG Knowledge Base
# ============================================================

# Document metadata
class DocumentMetadata(BaseModel):
    filename: str
    file_type: Literal["pdf", "markdown", "docx"]
    upload_date: str
    num_chunks: int


# Document upload response
class DocumentUploadResponse(BaseModel):
    document_id: str
    chunks_created: int
    success: bool = True
    message: Optional[str] = None


# Document search request
class DocumentSearchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5, ge=1, le=20)


# Document chunk in search results
class DocumentChunk(BaseModel):
    chunk_id: str
    content: str
    score: float
    metadata: DocumentMetadata


# Document search response
class DocumentSearchResponse(BaseModel):
    chunks: List[DocumentChunk]
    query: str
    success: bool = True


# ============================================================
# Phase 4: Export Features
# ============================================================

# Export request for PPT/Slidev
class ExportRequest(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    mermaid_code: str
    title: Optional[str] = "Architecture Diagram"


# Speech script generation request
class SpeechScriptRequest(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    duration: Literal["30s", "2min", "5min"]


# Speech script response
class SpeechScriptResponse(BaseModel):
    script: str
    duration: str
    word_count: int
    success: bool = True


# ============================================================
# Phase 5: Chat Generator (Flowchart from Natural Language)
# ============================================================

# Flow template for quick start
class FlowTemplate(BaseModel):
    id: str
    name: str
    description: str
    category: Literal["architecture", "troubleshooting", "business", "algorithm", "devops"]
    example_input: str
    icon: Optional[str] = None


# Template list response
class FlowTemplateList(BaseModel):
    templates: List[FlowTemplate]


# Chat generation request
class ChatGenerationRequest(BaseModel):
    user_input: str
    template_id: Optional[str] = None
    provider: Optional[Literal["gemini", "openai", "claude", "siliconflow", "custom"]] = "gemini"
    diagram_type: Literal["flow", "architecture"] = "flow"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None


# Chat generation response
class ChatGenerationResponse(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    mermaid_code: str
    success: bool = True
    message: Optional[str] = None


# ============================================================
# Excalidraw Generation
# ============================================================


class ExcalidrawGenerateRequest(BaseModel):
    prompt: str
    style: Optional[str] = None
    width: Optional[int] = 1200
    height: Optional[int] = 800
    provider: Optional[Literal["gemini", "openai", "claude", "siliconflow", "custom"]] = "custom"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: Optional[str] = None


class ExcalidrawScene(BaseModel):
    elements: List[dict]
    appState: dict = Field(default_factory=dict)
    files: dict = Field(default_factory=dict)


class ExcalidrawGenerateResponse(BaseModel):
    scene: ExcalidrawScene
    success: bool = True
    message: Optional[str] = None


# ============================================================
# Phase 1 Enhancement: Professional Speech Script Generation
# ============================================================

# Script generation options
class ScriptOptions(BaseModel):
    tone: Literal["professional", "casual", "technical"] = "professional"
    audience: Literal["executive", "technical", "mixed"] = "mixed"
    focus_areas: List[str] = Field(default_factory=lambda: ["scalability", "performance"])


# Script content sections
class ScriptContent(BaseModel):
    intro: str
    body: str
    conclusion: str
    full_text: str


# Script metadata
class ScriptMetadata(BaseModel):
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    duration: Literal["30s", "2min", "5min"]
    word_count: int = 0
    rag_sources: List[str] = Field(default_factory=list)
    architecture_snapshot: Optional[dict] = None
    version: int = 0


# Script draft (for editing and saving)
class ScriptDraft(BaseModel):
    id: str
    content: ScriptContent
    metadata: ScriptMetadata
    version: int = 1


# Stream event for SSE
class StreamEvent(BaseModel):
    type: Literal["CONTEXT_SEARCH", "CONTEXT_FOUND", "GENERATION_START",
                  "TOKEN", "SECTION_COMPLETE", "COMPLETE", "ERROR"]
    data: dict = Field(default_factory=dict)


# Save draft response
class SaveDraftResponse(BaseModel):
    script_id: str
    version: int
    saved_at: str
    success: bool = True


# Refine section response
class RefinedSectionResponse(BaseModel):
    script_id: str
    section: Literal["intro", "body", "conclusion"]
    refined_text: str
    changes_summary: str
    success: bool = True


# Improvement suggestion
class ImprovementSuggestion(BaseModel):
    section: Literal["intro", "body", "conclusion", "overall"]
    issue: str
    suggestion: str
    priority: Literal["high", "medium", "low"]


# Improvement suggestions response
class ImprovementSuggestions(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=10.0)
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    suggestions: List[ImprovementSuggestion] = Field(default_factory=list)
    success: bool = True


# Enhanced speech script request (with RAG support)
class EnhancedSpeechScriptRequest(BaseModel):
    nodes: List[Node]
    edges: List[Edge]
    duration: Literal["30s", "2min", "5min"]
    options: ScriptOptions = Field(default_factory=ScriptOptions)


# ========== Vision to Diagram: 图片转流程图/架构图 ==========

# Vision to Excalidraw request
class VisionToExcalidrawRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image (with data:image prefix or without)")
    prompt: Optional[str] = Field(None, description="Additional context or instructions")
    provider: Literal["gemini", "openai", "claude", "siliconflow", "custom"] = "custom"
    api_key: Optional[str] = Field(None, description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Base URL for custom provider")
    model_name: Optional[str] = Field(None, description="Model name (e.g., claude-sonnet-4-5-20250929)")
    width: Optional[int] = Field(1200, description="Canvas width")
    height: Optional[int] = Field(800, description="Canvas height")


# Vision to React Flow request
class VisionToReactFlowRequest(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image (with data:image prefix or without)")
    prompt: Optional[str] = Field(None, description="Additional context or instructions")
    provider: Literal["gemini", "openai", "claude", "siliconflow", "custom"] = "custom"
    api_key: Optional[str] = Field(None, description="API key for the provider")
    base_url: Optional[str] = Field(None, description="Base URL for custom provider")
    model_name: Optional[str] = Field(None, description="Model name")
    preserve_layout: bool = Field(True, description="Preserve original node positions")
    fast_mode: bool = Field(True, description="Use fast mode (simplified prompt)")



# Excalidraw element (simplified, compatible with Excalidraw JSON format)
class ExcalidrawElement(BaseModel):
    id: str
    type: Literal["rectangle", "ellipse", "diamond", "arrow", "line", "text", "freedraw", "image"]
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    angle: Optional[float] = 0
    strokeColor: Optional[str] = "#000000"
    backgroundColor: Optional[str] = "#ffffff"
    fillStyle: Optional[str] = "hachure"
    strokeWidth: Optional[int] = 1
    strokeStyle: Optional[str] = "solid"
    roughness: Optional[int] = 1
    opacity: Optional[int] = 100
    points: Optional[List[List[float]]] = None  # For arrows and lines
    text: Optional[str] = None  # For text elements
    fontSize: Optional[int] = 20
    fontFamily: Optional[int] = 1
    textAlign: Optional[str] = "center"
    verticalAlign: Optional[str] = "middle"
    startBinding: Optional[dict] = None
    endBinding: Optional[dict] = None


# Excalidraw scene
class ExcalidrawScene(BaseModel):
    elements: List[dict]  # Use dict to allow flexible Excalidraw schema
    appState: Optional[dict] = Field(default_factory=lambda: {"viewBackgroundColor": "#ffffff"})
    files: Optional[dict] = Field(default_factory=dict)


# Vision to Excalidraw response
class VisionToExcalidrawResponse(BaseModel):
    success: bool
    scene: Optional[ExcalidrawScene] = None
    message: Optional[str] = None
    raw_response: Optional[str] = None  # For debugging


# Vision to React Flow response
class VisionToReactFlowResponse(BaseModel):
    success: bool
    nodes: Optional[List[Node]] = None
    edges: Optional[List[Edge]] = None
    message: Optional[str] = None
    raw_response: Optional[str] = None  # For debugging
