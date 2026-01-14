import json
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Any

from fastapi import HTTPException
from app.api.mermaid import parse_mermaid_to_graph, graph_to_mermaid
from app.models.schemas import (
    FlowTemplate,
    FlowTemplateList,
    ChatGenerationRequest,
    ChatGenerationResponse,
    Node,
    Edge,
)
from app.services.ai_vision import create_vision_service

logger = logging.getLogger(__name__)


class ChatGeneratorService:
    """Chat-based flowchart generation service (mock-first)."""

    def __init__(self):
        self.templates_path = Path(__file__).parent.parent / "data" / "flow_templates.json"
        self.templates: List[FlowTemplate] = []
        self._load_templates()

    def _load_templates(self):
        """Load templates from JSON file."""
        try:
            with open(self.templates_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.templates = [FlowTemplate(**tpl) for tpl in data["templates"]]
            logger.info(f"Loaded {len(self.templates)} flow templates")
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            self.templates = []

    def get_all_templates(self) -> FlowTemplateList:
        """Get all templates."""
        return FlowTemplateList(templates=self.templates)

    def get_template(self, template_id: str) -> Optional[FlowTemplate]:
        """Get template by ID."""
        for tpl in self.templates:
            if tpl.id == template_id:
                return tpl
        return None

    def _build_generation_prompt(self, request: ChatGenerationRequest) -> str:
        """Build generation prompt for flow or architecture diagrams."""
        template_context = ""
        if request.template_id:
            template = self.get_template(request.template_id)
            if template:
                template_context = f"""
Reference Template: {template.name}
Template Description: {template.description}
Example Input: "{template.example_input}"
Expected Style/Category: {template.category}

Please generate a similar flowchart following this template's style.
"""

        if request.diagram_type == "architecture":
            return f"""You are a professional systems architect. Generate a layered architecture map (no edges needed).

Requirements:
- Output JSON with "layers": [
    {{"name": "infrastructure", "items": []}},
    {{"name": "middleware", "items": []}},
    {{"name": "backend", "items": []}},
    {{"name": "frontend", "items": []}},
    {{"name": "data", "items": []}}
  ]
- Each item: {{"label": "...", "tech_stack": ["..."], "note": "...", "iconType": "box"}}
- Do NOT return edges. Focus on listing components per layer.
- Keep counts reasonable (3-8 items per layer). Include empty list if not applicable.
- Return ONLY JSON, no prose.
{template_context}
User Request: "{request.user_input}"
"""

        system_prompt = f"""You are a professional flowchart generation expert. Convert user descriptions into clear, simple flowcharts.

**AVAILABLE NODE TYPES (choose appropriate for the scenario):**
For general processes:
- start: Start point (圆形/circle, use for beginning)
- end: End point (圆形/circle, use for termination)
- process: Process step (矩形/rectangle, use for actions/tasks)
- decision: Decision point (菱形/diamond, use for yes/no choices)
- data: Data/Input/Output (平行四边形/parallelogram)
- document: Document/Report (文档形状)
- subprocess: Sub-process (圆角矩形/rounded rectangle)

For technical systems (ONLY if user explicitly requests technical architecture):
- api: API Gateway
- service: Microservice
- database: Database
- cache: Cache
- queue: Message Queue
- storage: File Storage

**LAYOUT RULES:**
- Top-to-bottom flow (start at x=250, y=100)
- Vertical spacing: 150-200px between levels
- Horizontal spacing: 200-250px for parallel branches
- Keep it simple and clean

**GENERATION RULES:**
1. Analyze user input to determine if it's a general process or technical system
2. For general processes (like "约会流程", "做饭流程", "购物流程"):
   - Use ONLY basic nodes: start, process, decision, end
   - Generate 5-10 nodes (keep it simple)
   - Clear sequential flow
3. For technical systems (like "微服务架构", "API设计"):
   - Use technical nodes: api, service, database, etc.
   - Can be more complex (10-15 nodes)

**OUTPUT FORMAT:**
{{
  "nodes": [
    {{"id": "start", "type": "start", "position": {{"x": 250, "y": 100}}, "data": {{"label": "开始"}}}},
    {{"id": "step1", "type": "process", "position": {{"x": 250, "y": 250}}, "data": {{"label": "步骤1"}}}},
    {{"id": "decision1", "type": "decision", "position": {{"x": 250, "y": 400}}, "data": {{"label": "判断条件?"}}}},
    {{"id": "end", "type": "end", "position": {{"x": 250, "y": 650}}, "data": {{"label": "结束"}}}}
  ],
  "edges": [
    {{"id": "e1", "source": "start", "target": "step1"}},
    {{"id": "e2", "source": "step1", "target": "decision1"}},
    {{"id": "e3", "source": "decision1", "target": "end", "label": "是"}}
  ],
  "mermaid_code": "graph TB\\n  start[开始]-->step1[步骤1]-->decision1{{判断条件?}}-->end[结束]"
}}

{template_context}

**User Request:** "{request.user_input}"

Analyze the request and generate an appropriate flowchart. Return ONLY valid JSON, no markdown blocks or prose."""
        return system_prompt

    async def _call_ai_text_generation(self, vision_service, prompt: str, provider: str) -> dict:
        """Call AI provider (placeholder)."""
        if provider == "gemini":
            response = await vision_service._analyze_with_gemini_text(prompt)
        elif provider == "openai":
            response = await vision_service._analyze_with_openai_text(prompt)
        elif provider == "claude":
            response = await vision_service._analyze_with_claude_text(prompt)
        elif provider == "siliconflow":
            response = await vision_service._analyze_with_siliconflow_text(prompt)
        else:
            response = await vision_service._analyze_with_custom_text(prompt)
        return response

    def _bpmn_colors(self):
        return {
            "start": "#16a34a",
            "end": "#dc2626",
            "intermediate": "#ca8a04",
            "task": "#2563eb",
        }

    def _safe_json(self, payload: Any) -> dict:
        """Normalize AI payload into dict."""
        if payload is None:
            return {}
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, str):
            # Clean markdown code blocks (```json ... ``` or ``` ... ```)
            cleaned = payload.strip()
            if cleaned.startswith("```"):
                # Remove opening ```json or ```
                lines = cleaned.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remove closing ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned = "\n".join(lines)
            return json.loads(cleaned)
        if hasattr(payload, "model_dump"):  # pydantic models
            return payload.model_dump()
        return json.loads(json.dumps(payload, default=str))

    def _normalize_architecture_graph(self, ai_data: dict):
        """Normalize architecture JSON (layers/items) into nodes; edges stay empty."""
        layers = (
            ai_data.get("layers")
            or ai_data.get("sections")
            or ai_data.get("architecture")
            or []
        )
        nodes = []
        edges = []
        layer_colors = {
            "infrastructure": "#0ea5e9",
            "middleware": "#6366f1",
            "backend": "#22c55e",
            "frontend": "#f59e0b",
            "data": "#a855f7",
            "observability": "#14b8a6",
        }

        def add_node(layer_idx: int, item_idx: int, label: str, layer_name: str, note: str = "", icon: str = "box"):
            x = 120 + item_idx * 240
            y = 120 + layer_idx * 180
            color = layer_colors.get(layer_name.lower(), "#64748b")
            nodes.append(
                {
                    "id": f"{layer_name}-{item_idx}",
                    "type": "frame",
                    "position": {"x": x, "y": y},
                    "data": {
                        "label": label,
                        "shape": "task",
                        "iconType": icon,
                        "color": color,
                        "layer": layer_name,
                        "note": note,
                        "layerColor": color,
                    },
                }
            )

        if isinstance(layers, dict):
            layers = [{"name": k, "items": v} for k, v in layers.items()]

        for layer_idx, layer in enumerate(layers):
            name = layer.get("name") if isinstance(layer, dict) else f"layer-{layer_idx}"
            items = layer.get("items", []) if isinstance(layer, dict) else []
            for item_idx, item in enumerate(items):
                if isinstance(item, dict):
                    label = item.get("label") or item.get("name") or f"{name}-{item_idx}"
                    note = item.get("note") or ", ".join(item.get("tech_stack", []) or [])
                    icon = item.get("iconType") or "box"
                else:
                    label = str(item)
                    note = ""
                    icon = "box"
                add_node(layer_idx, item_idx, label, name or f"layer-{layer_idx}", note, icon)

        mermaid_lines = ["# Architecture Overview"]
        for layer in layers:
            lname = layer.get("name") if isinstance(layer, dict) else str(layer)
            mermaid_lines.append(f"- {lname}:")
            items = layer.get("items", []) if isinstance(layer, dict) else []
            for item in items:
                if isinstance(item, dict):
                    label = item.get("label") or item.get("name") or "component"
                    note = item.get("note") or ", ".join(item.get("tech_stack", []) or [])
                    mermaid_lines.append(f"  - {label} ({note})")
                else:
                    mermaid_lines.append(f"  - {item}")
        mermaid_code = "\n".join(mermaid_lines)
        return nodes, edges, mermaid_code

    def _ensure_positions(self, nodes: List[dict]) -> List[dict]:
        """Guarantee each node has position/data/type for React Flow."""
        cleaned = []
        start_x, start_y, step_x, step_y = 120, 120, 260, 180
        for idx, node in enumerate(nodes):
            n = node.model_dump() if hasattr(node, "model_dump") else dict(node)
            label_value = n.pop("label", None)
            if "position" not in n or not isinstance(n.get("position"), dict):
                # Accept legacy x/y fields
                x = n.pop("x", None)
                y = n.pop("y", None)
                col, row = idx % 4, idx // 4
                n["position"] = {
                    "x": x if isinstance(x, (int, float)) else start_x + col * step_x,
                    "y": y if isinstance(y, (int, float)) else start_y + row * step_y + (50 if col % 2 else 0),
                }
            else:
                if "x" not in n["position"]:
                    n["position"]["x"] = start_x + (idx % 4) * step_x
                if "y" not in n["position"]:
                    n["position"]["y"] = start_y + (idx // 4) * step_y

            n.setdefault("type", "default")
            if "data" not in n or not isinstance(n["data"], dict):
                n["data"] = {}
            if label_value is not None:
                n["data"].setdefault("label", label_value)
            n["data"].setdefault("label", n.get("id", "node"))
            cleaned.append(n)
        return cleaned

    def _ensure_edges(self, edges: List[dict]) -> List[dict]:
        """Ensure edges have ids and required fields."""
        cleaned = []
        for idx, edge in enumerate(edges):
            e = edge.model_dump() if hasattr(edge, "model_dump") else dict(edge)
            if not e.get("source") or not e.get("target"):
                continue
            e.setdefault("id", e.get("id") or f"e{idx}")
            cleaned.append(e)
        return cleaned

    def _normalize_ai_graph(self, ai_data: dict) -> Tuple[List[dict], List[dict], str]:
        """Normalize AI response into nodes/edges/mermaid_code."""
        nodes = ai_data.get("nodes") or []
        edges = ai_data.get("edges") or []
        mermaid_code = (
            ai_data.get("mermaid_code")
            or ai_data.get("mermaid")
            or ai_data.get("mermaidCode")
            or ""
        )

        # If only mermaid is returned, parse it
        if (not nodes) and mermaid_code:
            try:
                parsed_nodes, parsed_edges = parse_mermaid_to_graph(mermaid_code)
                nodes = [n.model_dump() if hasattr(n, "model_dump") else dict(n) for n in parsed_nodes]
                edges = [e.model_dump() if hasattr(e, "model_dump") else dict(e) for e in parsed_edges]
            except Exception as e:
                logger.warning(f"Failed to parse mermaid from AI response: {e}")

        nodes = self._ensure_positions(nodes)
        edges = self._ensure_edges(edges)

        # Auto-wire edges sequentially if missing but multiple nodes exist
        if not edges and len(nodes) > 1:
            sorted_nodes = sorted(nodes, key=lambda n: (n["position"]["x"], n["position"]["y"]))
            auto_edges = []
            for idx in range(len(sorted_nodes) - 1):
                src = sorted_nodes[idx]["id"]
                tgt = sorted_nodes[idx + 1]["id"]
                auto_edges.append({"id": f"e{idx}", "source": src, "target": tgt, "label": None})
            edges = self._ensure_edges(auto_edges)

        if not mermaid_code and nodes:
            try:
                mermaid_code = graph_to_mermaid(
                    [Node(**n) for n in nodes],
                    [Edge(**e) for e in edges],
                )
            except Exception as e:
                logger.warning(f"Failed to rebuild mermaid code: {e}")
                mermaid_code = ""

        return nodes, edges, mermaid_code

    def _mock_microservice_architecture(self):
        c = self._bpmn_colors()
        nodes = [
            {"id": "start-1", "type": "default", "position": {"x": 50, "y": 200},
             "data": {"label": "开始", "shape": "start-event", "iconType": "play-circle", "color": c["start"]}},
            {"id": "client-1", "type": "client", "position": {"x": 200, "y": 200},
             "data": {"label": "Web Client"}},
            {"id": "gateway-1", "type": "gateway", "position": {"x": 500, "y": 200},
             "data": {"label": "API Gateway", "shape": "diamond"}},
            {"id": "gateway-2", "type": "gateway", "position": {"x": 800, "y": 100},
             "data": {"label": "认证通过?", "shape": "diamond"}},
            {"id": "api-1", "type": "api", "position": {"x": 1100, "y": 100},
             "data": {"label": "Auth Service"}},
            {"id": "cache-1", "type": "cache", "position": {"x": 800, "y": 300},
             "data": {"label": "Redis Cache"}},
            {"id": "service-1", "type": "service", "position": {"x": 1100, "y": 300},
             "data": {"label": "Order Service", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "queue-1", "type": "queue", "position": {"x": 1400, "y": 200},
             "data": {"label": "RabbitMQ"}},
            {"id": "service-2", "type": "service", "position": {"x": 1700, "y": 200},
             "data": {"label": "Inventory Service", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "database-1", "type": "database", "position": {"x": 1400, "y": 400},
             "data": {"label": "MySQL"}},
            {"id": "storage-1", "type": "storage", "position": {"x": 1700, "y": 400},
             "data": {"label": "OSS Storage"}},
            {"id": "end-1", "type": "default", "position": {"x": 2000, "y": 200},
             "data": {"label": "结束", "shape": "end-event", "iconType": "stop-circle", "color": c["end"]}},
        ]
        edges = [
            {"id": "e0", "source": "start-1", "target": "client-1", "label": "用户请求"},
            {"id": "e1", "source": "client-1", "target": "gateway-1", "label": "HTTPS Request"},
            {"id": "e2", "source": "gateway-1", "target": "gateway-2", "label": "验证Token"},
            {"id": "e3", "source": "gateway-2", "target": "api-1", "label": "是"},
            {"id": "e4", "source": "gateway-2", "target": "cache-1", "label": "否"},
            {"id": "e5", "source": "cache-1", "target": "service-1", "label": "Cache Miss"},
            {"id": "e6", "source": "service-1", "target": "queue-1", "label": "异步订单"},
            {"id": "e7", "source": "queue-1", "target": "service-2", "label": "消费消息"},
            {"id": "e8", "source": "service-1", "target": "database-1", "label": "查询订单"},
            {"id": "e9", "source": "service-2", "target": "database-1", "label": "更新库存"},
            {"id": "e10", "source": "service-2", "target": "storage-1", "label": "上传发货单"},
            {"id": "e11", "source": "service-2", "target": "end-1", "label": "结束"},
        ]
        mermaid_code = """graph LR
    start-1(("开始"))
    client-1["Web Client"]
    gateway-1{"API Gateway"}
    gateway-2{"认证通过?"}
    api-1["Auth Service"]
    cache-1["Redis Cache"]
    service-1["Order Service"]
    queue-1["RabbitMQ"]
    service-2["Inventory Service"]
    database-1["MySQL"]
    storage-1["OSS Storage"]
    end-1(("结束"))

    start-1 -->|用户请求| client-1
    client-1 -->|HTTPS Request| gateway-1
    gateway-1 -->|验证Token| gateway-2
    gateway-2 -->|是| api-1
    gateway-2 -->|否| cache-1
    cache-1 -->|Cache Miss| service-1
    service-1 -->|异步订单| queue-1
    queue-1 -->|消费消息| service-2
    service-1 -->|查询订单| database-1
    service-2 -->|更新库存| database-1
    service-2 -->|上传发货单| storage-1
    service-2 -->|结束| end-1"""
        return {"nodes": nodes, "edges": edges, "mermaid_code": mermaid_code}

    def _mock_high_concurrency(self):
        c = self._bpmn_colors()
        nodes = [
            {"id": "start-1", "type": "default", "position": {"x": -150, "y": 200},
             "data": {"label": "开始", "shape": "start-event", "iconType": "play-circle", "color": c["start"]}},
            {"id": "client-1", "type": "client", "position": {"x": 100, "y": 200}, "data": {"label": "Mobile App"}},
            {"id": "gateway-1", "type": "gateway", "position": {"x": 400, "y": 200},
             "data": {"label": "API Gateway\n(限流 10000 QPS)", "shape": "diamond"}},
            {"id": "cache-1", "type": "cache", "position": {"x": 700, "y": 200},
             "data": {"label": "Redis\n(缓存前置)"}},
            {"id": "gateway-2", "type": "gateway", "position": {"x": 1000, "y": 200},
             "data": {"label": "缓存命中?", "shape": "diamond"}},
            {"id": "queue-1", "type": "queue", "position": {"x": 1300, "y": 100},
             "data": {"label": "Kafka Queue\n(削峰)" }},
            {"id": "service-1", "type": "service", "position": {"x": 1600, "y": 100},
             "data": {"label": "Order Service", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "database-1", "type": "database", "position": {"x": 1900, "y": 100},
             "data": {"label": "MySQL\n(订单表)"}},
            {"id": "storage-1", "type": "storage", "position": {"x": 1900, "y": 300},
             "data": {"label": "OSS\n(订单凭证)"}},
            {"id": "client-2", "type": "client", "position": {"x": 1300, "y": 300},
             "data": {"label": "返回失败"}},
            {"id": "end-1", "type": "default", "position": {"x": 2200, "y": 200},
             "data": {"label": "结束", "shape": "end-event", "iconType": "stop-circle", "color": c["end"]}},
        ]
        edges = [
            {"id": "e0", "source": "start-1", "target": "client-1", "label": "入口"},
            {"id": "e1", "source": "client-1", "target": "gateway-1", "label": "高并发请求"},
            {"id": "e2", "source": "gateway-1", "target": "cache-1", "label": "限流通过"},
            {"id": "e3", "source": "cache-1", "target": "gateway-2", "label": "检查缓存"},
            {"id": "e4", "source": "gateway-2", "target": "queue-1", "label": "是"},
            {"id": "e5", "source": "gateway-2", "target": "client-2", "label": "否"},
            {"id": "e6", "source": "queue-1", "target": "service-1", "label": "消费"},
            {"id": "e7", "source": "service-1", "target": "database-1", "label": "创建订单"},
            {"id": "e8", "source": "service-1", "target": "storage-1", "label": "存储凭证"},
            {"id": "e9", "source": "service-1", "target": "end-1", "label": "结束"},
        ]
        mermaid_code = """graph LR
    start-1(("开始"))
    client-1["Mobile App"]
    gateway-1{"API Gateway<br/>(限流 10000 QPS)"}
    cache-1["Redis<br/>(缓存前置)"]
    gateway-2{"缓存命中?"}
    queue-1["Kafka Queue<br/>(削峰)"]
    service-1["Order Service"]
    database-1["MySQL<br/>(订单表)"]
    storage-1["OSS<br/>(订单凭证)"]
    client-2["返回失败"]
    end-1(("结束"))

    start-1 -->|入口| client-1
    client-1 -->|高并发请求| gateway-1
    gateway-1 -->|限流通过| cache-1
    cache-1 -->|检查缓存| gateway-2
    gateway-2 -->|是| queue-1
    gateway-2 -->|否| client-2
    queue-1 -->|消费| service-1
    service-1 -->|创建订单| database-1
    service-1 -->|存储凭证| storage-1
    service-1 -->|结束| end-1"""
        return {"nodes": nodes, "edges": edges, "mermaid_code": mermaid_code}

    def _mock_oom_investigation(self):
        c = self._bpmn_colors()
        nodes = [
            {"id": "start-1", "type": "default", "position": {"x": 250, "y": 50},
             "data": {"label": "检测到服务器 OOM 告警", "shape": "start-event", "iconType": "alert-circle", "color": c["start"]}},
            {"id": "check-1", "type": "default", "position": {"x": 250, "y": 180},
             "data": {"label": "查看 JVM 堆内存使用率", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "decision-1", "type": "gateway", "position": {"x": 250, "y": 310},
             "data": {"label": "堆内存 > 90%?", "shape": "diamond"}},
            {"id": "step-heap-yes", "type": "default", "position": {"x": 100, "y": 440},
             "data": {"label": "生成 heap dump", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "step-heap-no", "type": "default", "position": {"x": 400, "y": 440},
             "data": {"label": "检查直接内存/元空间", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "step-analyze", "type": "default", "position": {"x": 100, "y": 570},
             "data": {"label": "用 MAT 分析 heap dump", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "step-threads", "type": "default", "position": {"x": 400, "y": 570},
             "data": {"label": "分析线程栈和 GC 日志", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "decision-2", "type": "gateway", "position": {"x": 100, "y": 700},
             "data": {"label": "发现内存泄漏?", "shape": "diamond"}},
            {"id": "step-leak-yes", "type": "default", "position": {"x": 100, "y": 830},
             "data": {"label": "修复泄漏代码并回归", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "step-leak-no", "type": "default", "position": {"x": 250, "y": 830},
             "data": {"label": "优化内存配置/限流", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "end-1", "type": "default", "position": {"x": 175, "y": 960},
             "data": {"label": "重启服务并监控", "shape": "end-event", "iconType": "stop-circle", "color": c["end"]}},
        ]
        edges = [
            {"id": "e1", "source": "start-1", "target": "check-1"},
            {"id": "e2", "source": "check-1", "target": "decision-1"},
            {"id": "e3", "source": "decision-1", "target": "step-heap-yes", "label": "是"},
            {"id": "e4", "source": "decision-1", "target": "step-heap-no", "label": "否"},
            {"id": "e5", "source": "step-heap-yes", "target": "step-analyze"},
            {"id": "e6", "source": "step-heap-no", "target": "step-threads"},
            {"id": "e7", "source": "step-analyze", "target": "decision-2"},
            {"id": "e8", "source": "decision-2", "target": "step-leak-yes", "label": "是"},
            {"id": "e9", "source": "decision-2", "target": "step-leak-no", "label": "否"},
            {"id": "e10", "source": "step-leak-yes", "target": "end-1"},
            {"id": "e11", "source": "step-leak-no", "target": "end-1"},
            {"id": "e12", "source": "step-threads", "target": "step-leak-no"},
        ]
        mermaid_code = """graph TD
    start-1(("检测到服务器 OOM 告警"))
    check-1["查看 JVM 堆内存使用率"]
    decision-1{"堆内存 > 90%?"}
    step-heap-yes["生成 heap dump"]
    step-heap-no["检查直接内存/元空间"]
    step-analyze["用 MAT 分析 heap dump"]
    step-threads["分析线程栈和 GC 日志"]
    decision-2{"发现内存泄漏?"}
    step-leak-yes["修复泄漏代码并回归"]
    step-leak-no["优化内存配置/限流"]
    end-1(("重启服务并监控"))

    start-1 --> check-1
    check-1 --> decision-1
    decision-1 -->|是| step-heap-yes
    decision-1 -->|否| step-heap-no
    step-heap-yes --> step-analyze
    step-heap-no --> step-threads
    step-analyze --> decision-2
    decision-2 -->|是| step-leak-yes
    decision-2 -->|否| step-leak-no
    step-leak-yes --> end-1
    step-leak-no --> end-1
        step-threads --> step-leak-no"""
        return {"nodes": nodes, "edges": edges, "mermaid_code": mermaid_code}

    def _mock_architecture_overview(self):
        """Mock layered architecture map with no edges."""
        layers = [
            ("infrastructure", ["VPC/Subnet", "Load Balancer", "Object Storage", "Monitoring"]),
            ("middleware", ["API Gateway", "Kafka", "Redis", "Config Center"]),
            ("backend", ["User Service", "Order Service", "Payment Worker"]),
            ("frontend", ["Web SPA", "Mobile App", "BFF"]),
            ("data", ["MySQL", "ClickHouse", "Data Lake"]),
        ]
        colors = {
            "infrastructure": "#0ea5e9",
            "middleware": "#6366f1",
            "backend": "#22c55e",
            "frontend": "#f59e0b",
            "data": "#a855f7",
        }
        nodes = []
        frame_width = 1100
        frame_height = 180
        for li, (layer, items) in enumerate(layers):
            nodes.append(
                {
                    "id": f"{layer}-frame",
                    "type": "layerFrame",
                    "position": {"x": 60, "y": 100 + li * (frame_height + 20)},
                    "data": {
                        "label": layer.capitalize(),
                        "color": colors.get(layer, "#64748b"),
                        "width": frame_width,
                        "height": frame_height,
                    },
                    "draggable": False,
                }
            )
            for idx, label in enumerate(items):
                layer_tag = layer.capitalize()
                display_label = f"[{layer_tag}] {label}"
                nodes.append(
                    {
                        "id": f"{layer}-{idx}",
                        "type": "frame",
                        "position": {"x": 120 + idx * 240, "y": 140 + li * (frame_height + 20)},
                        "data": {
                            "label": display_label,
                            "shape": "task",
                            "iconType": "box",
                            "color": colors.get(layer, "#64748b"),
                            "layer": layer,
                            "note": layer_tag,
                            "layerColor": colors.get(layer, "#64748b"),
                        },
                    }
                )
        mermaid_lines = ["# Architecture Overview (mock)"]
        for layer, items in layers:
            mermaid_lines.append(f"- {layer}:")
            for label in items:
                mermaid_lines.append(f"  - {label}")
        return {"nodes": nodes, "edges": [], "mermaid_code": "\n".join(mermaid_lines)}

    async def generate_flowchart(
        self,
        request: ChatGenerationRequest,
        provider: str = "gemini",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None,
    ) -> ChatGenerationResponse:
        """Generate flowchart or architecture diagram via AI."""

        logger.info(f"Generating flowchart for input: {request.user_input[:50]}...")
        logger.info(f"Template ID: {request.template_id}")

        try:
            selected_provider = provider or request.provider or "gemini"
            logger.info(f"[CHAT-GEN] === START generate_flowchart ===")
            logger.info(f"[CHAT-GEN] user_input: {request.user_input[:100] if request.user_input else 'None'}...")
            logger.info(f"[CHAT-GEN] template_id: {request.template_id}")
            logger.info(f"[CHAT-GEN] diagram_type from request: {request.diagram_type}")

            # auto-detect architecture mode by template category if diagram_type not explicitly set
            effective_diagram_type = request.diagram_type or "flow"
            if request.template_id:
                tpl = self.get_template(request.template_id)
                if tpl and tpl.category == "architecture":
                    effective_diagram_type = "architecture"

            logger.info(f"[CHAT-GEN] Effective diagram type: {effective_diagram_type}")

            vision_service = create_vision_service(
                provider=selected_provider,
                api_key=api_key or request.api_key,
                base_url=base_url or request.base_url,
                model_name=model_name or request.model_name,
            )

            prompt_request = request.model_copy(update={"diagram_type": effective_diagram_type})
            prompt = self._build_generation_prompt(prompt_request)

            logger.info(f"[CHAT-GEN] Calling AI with provider: {selected_provider}")
            logger.info(f"[CHAT-GEN] Prompt (first 200 chars): {prompt[:200]}...")
            ai_raw = await self._call_ai_text_generation(vision_service, prompt, selected_provider)
            logger.info(f"[CHAT-GEN] AI raw response (first 500 chars): {ai_raw[:500]}...")
            ai_data = self._safe_json(ai_raw)
            logger.info(f"[CHAT-GEN] Parsed AI data keys: {list(ai_data.keys())}")

            if effective_diagram_type == "architecture":
                nodes, edges, mermaid_code = self._normalize_architecture_graph(ai_data)
                # Architecture diagrams don't show edges
                edges = []
            else:
                nodes, edges, mermaid_code = self._normalize_ai_graph(ai_data)

            logger.info(f"[CHAT-GEN] After normalization: {len(nodes)} nodes, {len(edges)} edges")

            if not nodes:
                logger.warning(
                    "[CHAT-GEN] AI response missing nodes; raw keys: %s",
                    list(ai_data.keys()),
                )
                raise ValueError("AI response missing nodes; please retry with clearer input.")

            # If AI result is completely empty, use template mock as last resort
            # Changed from < 3 nodes to == 0 nodes to be less aggressive
            should_use_fallback = (
                effective_diagram_type == "flow"
                and len(nodes) == 0
                and request.template_id  # Only use template mock if a template was selected
            )

            if should_use_fallback:
                logger.warning(
                    "[CHAT-GEN] AI returned NO nodes; using template fallback"
                )
                if request.template_id == "microservice-architecture":
                    mock_result = self._mock_microservice_architecture()
                elif request.template_id == "high-concurrency-system":
                    mock_result = self._mock_high_concurrency()
                else:
                    mock_result = self._mock_oom_investigation()
                nodes = mock_result["nodes"]
                edges = mock_result["edges"]
                mermaid_code = mock_result["mermaid_code"]
                message = (
                    f"AI returned no nodes; using template mock"
                )
            else:
                message = f"Generated via {selected_provider}"
                logger.info(f"[CHAT-GEN] Using AI result (not falling back to mock)")

            logger.info(
                f"[CHAT-GEN] Generated via {selected_provider}: {len(nodes)} nodes, {len(edges)} edges"
            )
            return ChatGenerationResponse(
                nodes=nodes,
                edges=edges,
                mermaid_code=mermaid_code,
                success=True,
                message=message,
            )

        except Exception as e:
            logger.error(f"Flowchart generation failed: {e}", exc_info=True)
            # DO NOT return mock data - let the error propagate to the client
            raise HTTPException(
                status_code=500,
                detail=f"AI generation failed: {str(e)}. Please check your API key and try again."
            )


def create_chat_generator_service() -> ChatGeneratorService:
    """Create service instance."""
    return ChatGeneratorService()
