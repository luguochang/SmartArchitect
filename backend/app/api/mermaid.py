from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    MermaidParseRequest,
    MermaidParseResponse,
    GraphToMermaidRequest,
    GraphToMermaidResponse,
    Node,
    Edge,
    Position,
    NodeData,
)
import re
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


def parse_mermaid_to_graph(mermaid_code: str) -> tuple[list[Node], list[Edge]]:
    """将 Mermaid 代码解析为节点和边"""
    nodes = []
    edges = []
    node_map = {}

    lines = mermaid_code.strip().split("\n")
    y_offset = 0

    for line in lines:
        line = line.strip()
        if not line or line.startswith("graph"):
            continue

        # 解析节点定义
        # 支持格式: nodeId["label"], nodeId[("label")], nodeId[["label"]]
        node_match = re.search(r'(\w+)\[([\[\("]*)([^\]]+)([\]\)"]*)?\]', line)
        if node_match:
            node_id = node_match.group(1)
            label_content = node_match.group(3).strip('"\'()')

            # 确定节点类型
            node_type = "default"
            if "(" in line:
                node_type = "database"
            elif "[[" in line:
                node_type = "service"
            elif any(keyword in label_content.lower() for keyword in ["api"]):
                node_type = "api"
            elif any(keyword in label_content.lower() for keyword in ["gateway", "load balancer", "lb"]):
                node_type = "gateway"
            elif any(keyword in label_content.lower() for keyword in ["cache", "redis", "memcached"]):
                node_type = "cache"
            elif any(keyword in label_content.lower() for keyword in ["queue", "kafka", "rabbitmq", "mq"]):
                node_type = "queue"
            elif any(keyword in label_content.lower() for keyword in ["storage", "s3", "cdn"]):
                node_type = "storage"
            elif any(keyword in label_content.lower() for keyword in ["client", "frontend", "mobile", "web"]):
                node_type = "client"

            if node_id not in node_map:
                node = Node(
                    id=node_id,
                    type=node_type,
                    position=Position(x=100 + len(nodes) % 3 * 250, y=y_offset),
                    data=NodeData(label=label_content),
                )
                nodes.append(node)
                node_map[node_id] = True
                y_offset += 100

        # 解析边定义
        # 支持格式: source --> target, source -->|label| target
        edge_match = re.search(r'(\w+)\s*-->\s*(?:\|([^|]+)\|)?\s*(\w+)', line)
        if edge_match:
            source_id = edge_match.group(1)
            label = edge_match.group(2).strip() if edge_match.group(2) else None
            target_id = edge_match.group(3)

            edge = Edge(
                id=f"{source_id}-{target_id}",
                source=source_id,
                target=target_id,
                label=label,
            )
            edges.append(edge)

    return nodes, edges


def graph_to_mermaid(nodes: list[Node], edges: list[Edge]) -> str:
    """将节点和边转换为 Mermaid 代码"""
    mermaid_lines = ["graph TD"]

    # 添加节点定义
    for node in nodes:
        node_id = node.id
        label = node.data.label
        node_type = node.type or "default"

        if node_type == "database":
            mermaid_lines.append(f'    {node_id}[("{label}")]')
        elif node_type == "service":
            mermaid_lines.append(f'    {node_id}[["{label}"]]')
        else:
            # api, gateway, cache, queue, storage, client 都使用标准方框
            mermaid_lines.append(f'    {node_id}["{label}"]')

    # 添加边定义
    for edge in edges:
        label_part = f"|{edge.label}|" if edge.label else ""
        mermaid_lines.append(f"    {edge.source} -->{label_part} {edge.target}")

    return "\n".join(mermaid_lines)


@router.post("/mermaid/parse", response_model=MermaidParseResponse)
async def parse_mermaid(request: MermaidParseRequest):
    """将 Mermaid 代码解析为 React Flow 图数据"""
    try:
        nodes, edges = parse_mermaid_to_graph(request.code)
        return MermaidParseResponse(nodes=nodes, edges=edges, success=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse Mermaid code: {str(e)}")


@router.post("/graph/to-mermaid", response_model=GraphToMermaidResponse)
async def convert_graph_to_mermaid(request: GraphToMermaidRequest):
    """将 React Flow 图数据转换为 Mermaid 代码"""
    try:
        mermaid_code = graph_to_mermaid(request.nodes, request.edges)
        return GraphToMermaidResponse(mermaid_code=mermaid_code, success=True)
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to convert graph to Mermaid: {str(e)}"
        )
