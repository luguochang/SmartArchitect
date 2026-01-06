from pydantic import BaseModel, Field
from typing import List, Optional, Literal


# React Flow 节点和边的数据模型
class NodeData(BaseModel):
    label: str


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
    provider: Literal["gemini", "openai", "claude", "custom"]
    api_key: str
    model_name: str
    base_url: Optional[str] = None


class ModelConfigResponse(BaseModel):
    success: bool
    message: str
