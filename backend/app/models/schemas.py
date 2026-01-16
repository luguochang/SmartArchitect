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
