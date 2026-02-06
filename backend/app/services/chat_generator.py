import json
import logging
import math
import time
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
    Position,
    NodeData,
)
from app.services.ai_vision import create_vision_service
from app.services.model_presets import get_model_presets_service
from app.services.session_manager import get_session_manager

logger = logging.getLogger(__name__)


# Architecture type templates configuration
ARCHITECTURE_TEMPLATES = {
    "layered": {
        "name": "分层架构",
        "name_en": "Layered Architecture",
        "layers": ["frontend", "backend", "middleware", "data", "infrastructure"],
        "default_columns": 5,
        "show_edges": False,
        "description": "通用前后端分层架构，适用于Web应用、微服务等",
    },
    "business": {
        "name": "业务架构",
        "name_en": "Business Architecture",
        "layers": ["capability", "service", "process", "organization"],
        "default_columns": 6,
        "show_edges": False,  # Business architecture focuses on layers, not connections
        "description": "业务能力地图，展示企业能力、服务、流程和组织关系",
    },
    "technical": {
        "name": "技术架构",
        "name_en": "Technical Architecture",
        "layers": ["presentation", "application", "integration", "data", "infrastructure"],
        "default_columns": 5,
        "show_edges": True,  # Technical architecture shows API calls and data flow
        "edge_type": "data-flow",
        "description": "技术系统架构，展示应用组件之间的技术依赖和数据流",
    },
    "deployment": {
        "name": "部署架构",
        "name_en": "Deployment Architecture",
        "layers": ["dmz", "app-tier", "data-tier", "monitoring"],
        "default_columns": 4,
        "show_edges": True,  # Deployment shows network connectivity
        "edge_type": "network",
        "description": "基础设施部署架构，展示网络拓扑、服务器、容器编排",
    },
    "domain": {
        "name": "领域架构",
        "name_en": "Domain-Driven Architecture",
        "layers": ["domain-services", "shared-kernel", "anti-corruption", "infrastructure"],
        "default_columns": 4,
        "show_edges": True,
        "edge_type": "dependency",
        "description": "领域驱动设计架构，展示有界上下文和领域服务",
    },
}


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
            # Get architecture type template
            arch_type = request.architecture_type or "layered"
            template = ARCHITECTURE_TEMPLATES.get(arch_type, ARCHITECTURE_TEMPLATES["layered"])

            # Build layer-specific guidance with STRONG differentiation
            layer_examples = ""
            if arch_type == "business":
                layer_examples = """
**🏢 BUSINESS ARCHITECTURE - Focus on BUSINESS CAPABILITIES:**
CRITICAL: This is a BUSINESS view, NOT technical implementation!

**Required Layers (use EXACTLY these names):**
1. "capability" (能力层) - 10-15 business capabilities
   - Examples: 访客管理, 车辆管理, 安防监控, 能源管理, 物业服务, 智能楼宇, 环境监测, 资产管理, 应急指挥, 数据分析, 统一认证, 消息通知
   - Use category: "service" for all capability items
   - NO tech stack - focus on WHAT the business does

2. "service" (服务层) - 5-8 business service systems
   - Examples: 访客预约系统, 车辆识别系统, 视频监控平台, 能耗分析平台, 物业工单系统
   - Use category: "platform"
   - Add tech_stack ONLY if relevant to business stakeholders

3. "process" (流程层) - 3-5 key business processes
   - Examples: 访客入园流程, 车辆进出流程, 应急响应流程
   - Use category: "default"

4. "organization" (组织层) - 3-5 organizational units
   - Examples: 运营中心, 安保部门, 物业部门, IT部门
   - Use category: "default"

**STRICT RULES:**
- NO database/cache/queue components (those are technical!)
- NO infrastructure components (K8s, Docker, etc.)
- Focus on BUSINESS VALUE and CAPABILITIES
- Use business-friendly language (Chinese preferred)
"""
            elif arch_type == "technical":
                layer_examples = """
**⚙️ TECHNICAL ARCHITECTURE - Focus on TECHNICAL COMPONENTS:**
CRITICAL: This is a TECHNICAL view showing HOW systems are built!

**Required Layers (use EXACTLY these names):**
1. "presentation" (表现层) - 3-5 UI components
   - Examples: React前端, Vue管理后台, 移动端App, 小程序
   - Use category: "api"
   - tech_stack: ["React", "TypeScript"], ["Vue", "Element UI"], etc.

2. "application" (应用层) - 6-10 application services
   - Examples: 用户服务, 订单服务, 支付服务, 通知服务, 认证服务
   - Use category: "service"
   - tech_stack: ["Spring Boot", "Java"], ["FastAPI", "Python"], etc.

3. "integration" (集成层) - 4-6 integration components
   - Examples: API Gateway, 消息队列, ESB总线, 服务网格
   - Use category: "network"
   - tech_stack: ["Kong"], ["Kafka"], ["Istio"], etc.

4. "data" (数据层) - 4-6 data storage systems
   - Examples: MySQL主库, Redis缓存, MongoDB文档库, Elasticsearch搜索
   - Use category: "database"
   - tech_stack: ["MySQL 8.0"], ["Redis Cluster"], etc.

5. "infrastructure" (基础设施层) - 3-5 infrastructure components
   - Examples: Kubernetes集群, Docker容器, Nginx负载均衡, 云服务器
   - Use category: "infrastructure"
   - tech_stack: ["K8s"], ["Docker"], ["Nginx"], etc.

**STRICT RULES:**
- MUST include tech_stack for every item
- Use technical terminology (API, Service, Gateway, etc.)
- Show HOW components interact (include edges!)
- Focus on IMPLEMENTATION details
"""
            elif arch_type == "deployment":
                layer_examples = """
**🚀 DEPLOYMENT ARCHITECTURE - Focus on INFRASTRUCTURE TOPOLOGY:**
CRITICAL: This is a DEPLOYMENT view showing WHERE systems run!

**Required Layers (use EXACTLY these names):**
1. "dmz" (DMZ区) - 3-4 edge components
   - Examples: Nginx负载均衡, WAF防火墙, CDN节点, SSL终结
   - Use category: "network"
   - tech_stack: ["Nginx", "HAProxy"], ["ModSecurity"], etc.
   - note: Include IP ranges or network segments

2. "app-tier" (应用层) - 5-8 application deployment units
   - Examples: K8s Pod (订单服务), Docker容器 (用户服务), Tomcat实例
   - Use category: "compute"
   - tech_stack: ["K8s Deployment"], ["Docker Compose"], etc.
   - note: Include replica counts (e.g., "3副本")

3. "data-tier" (数据层) - 3-5 data storage deployments
   - Examples: MySQL主从集群, Redis哨兵集群, MinIO对象存储
   - Use category: "storage"
   - tech_stack: ["MySQL 8.0 主从"], ["Redis Sentinel"], etc.
   - note: Include HA configuration

4. "monitoring" (监控层) - 3-4 monitoring/logging systems
   - Examples: Prometheus监控, Grafana可视化, ELK日志, Jaeger链路追踪
   - Use category: "platform"
   - tech_stack: ["Prometheus"], ["Grafana"], ["Elasticsearch"], etc.

**STRICT RULES:**
- MUST include deployment details (replicas, HA, network)
- Show PHYSICAL/LOGICAL deployment topology
- Include edges for network connections
- Focus on OPERATIONS and INFRASTRUCTURE
"""
            elif arch_type == "domain":
                layer_examples = """
**🎯 DOMAIN-DRIVEN ARCHITECTURE - Focus on BOUNDED CONTEXTS:**
CRITICAL: This is a DDD view showing domain boundaries!

**Required Layers (use EXACTLY these names):**
1. "domain-services" (领域服务层) - 5-8 bounded contexts
   - Examples: 订单域, 用户域, 支付域, 库存域, 物流域
   - Use category: "service"
   - note: Include domain responsibilities

2. "shared-kernel" (共享内核层) - 2-4 shared components
   - Examples: 通用工具类, 领域事件总线, 共享值对象
   - Use category: "platform"

3. "anti-corruption" (防腐层) - 2-3 integration adapters
   - Examples: 外部支付适配器, 第三方物流适配器
   - Use category: "network"

4. "infrastructure" (基础设施层) - 3-4 infrastructure services
   - Examples: 数据持久化, 消息发布, 缓存服务
   - Use category: "infrastructure"

**STRICT RULES:**
- Use DDD terminology (Bounded Context, Aggregate, etc.)
- Show domain boundaries clearly
- Include edges for domain events
"""
            else:  # layered (default/generic)
                layer_examples = """
**🏢 LAYERED ARCHITECTURE - Generic multi-tier structure:**

**Required Layers (use EXACTLY these names):**
1. "frontend" (前端层) - 2-4 client applications
2. "backend" (后端层) - 4-6 backend services
3. "middleware" (中间件层) - 3-5 middleware components
4. "data" (数据层) - 3-4 data storage systems
5. "infrastructure" (基础设施层) - 2-3 infrastructure components

**RULES:**
- Generic architecture, suitable for most systems
- Balance between business and technical views
"""

            # Edge generation guidance
            edge_guidance = ""
            if template.get("show_edges", False):
                edge_guidance = """
**EDGE/CONNECTION RULES:**
- Include "edges" array to show dependencies/data flow
- Each edge: {{"source": "layer-item-id", "target": "layer-item-id", "label": "connection type"}}
- Example: {{"source": "application-0", "target": "integration-0", "label": "API调用"}}
- Keep edge labels concise (API调用, 数据流, 网络连接, etc.)
"""
            else:
                edge_guidance = """
**EDGE RULE:** Do NOT include "edges" array - this architecture type focuses on layer organization.
"""

            return f"""You are a professional systems architect. Generate a {template['name']} ({template['name_en']}) with clear hierarchy and organization.

**ARCHITECTURE TYPE:** {template['name']}
**DESCRIPTION:** {template['description']}

**CRITICAL OUTPUT FORMAT:**
1. Return ONLY valid JSON (no markdown code blocks)
2. Structure:
   {{
     "layers": [
       {{
         "name": "layer-name",
         "layout": {{ "columns": 4-6 }},
         "items": [
           {{"label": "Component Name", "tech_stack": ["Technology"], "note": "Description", "category": "service"}}
         ]
       }}
     ],
     "edges": [...]  // Only if showing dependencies
   }}

{layer_examples}

3. **GRID LAYOUT SUPPORT:**
   - Each layer can specify "layout": {{ "columns": N }}
   - Default columns: {template.get('default_columns', 4)}
   - For layers with many items (10+), use more columns (5-6)
   - For simple layers (< 5 items), use fewer columns (3-4)

4. **Item Format:**
   - "label": Component/service name (Chinese if user input is Chinese)
   - "tech_stack": Array of technologies used (e.g., ["React", "Next.js"])
   - "note": Brief description or tech stack summary
   - "category": Optional category for icon selection ("service", "database", "api", "platform", etc.)

5. **SMART CARD DISTRIBUTION:**
   - Capability/service layers: 6-12 items across 4-6 columns
   - Application layer: 5-10 items across 3-5 columns
   - Integration layer: 3-6 items across 3-4 columns
   - Data layer: 3-5 items across 3-4 columns
   - Automatically wrap items into multiple rows

{edge_guidance}

**EXAMPLE OUTPUT (Smart Park Business Architecture):**
{{
  "layers": [
    {{
      "name": "capability",
      "layout": {{ "columns": 6 }},
      "items": [
        {{"label": "访客管理", "category": "service", "note": "访客预约与登记"}},
        {{"label": "车辆管理", "category": "service", "note": "车辆识别与停车"}},
        {{"label": "安防监控", "category": "service", "note": "视频监控与预警"}},
        {{"label": "能源管理", "category": "service", "note": "能耗分析与优化"}},
        {{"label": "物业服务", "category": "service", "note": "工单与投诉处理"}},
        {{"label": "智能楼宇", "category": "service", "note": "楼宇自控与调节"}},
        {{"label": "环境监测", "category": "service", "note": "空气质量与温湿度"}},
        {{"label": "资产管理", "category": "service", "note": "资产盘点与追踪"}},
        {{"label": "应急指挥", "category": "service", "note": "应急响应与调度"}},
        {{"label": "数据分析", "category": "platform", "note": "数据可视化与报表"}},
        {{"label": "统一认证", "category": "platform", "note": "单点登录与权限"}},
        {{"label": "消息通知", "category": "platform", "note": "消息推送与提醒"}}
      ]
    }},
    {{
      "name": "application",
      "layout": {{ "columns": 5 }},
      "items": [
        {{"label": "访客预约系统", "tech_stack": ["Vue", "Spring Boot"], "note": "访客预约与审批"}},
        {{"label": "车辆识别系统", "tech_stack": ["TensorFlow", "FastAPI"], "note": "车牌识别与抓拍"}},
        {{"label": "视频监控平台", "tech_stack": ["WebRTC", "Node.js"], "note": "视频流处理"}},
        {{"label": "能耗分析平台", "tech_stack": ["Grafana", "InfluxDB"], "note": "能耗数据分析"}},
        {{"label": "物业工单系统", "tech_stack": ["React", "Django"], "note": "工单流转处理"}}
      ]
    }},
    {{
      "name": "integration",
      "layout": {{ "columns": 4 }},
      "items": [
        {{"label": "API Gateway", "tech_stack": ["Kong"], "note": "统一网关"}},
        {{"label": "ESB总线", "tech_stack": ["Kafka"], "note": "消息总线"}},
        {{"label": "IoT平台", "tech_stack": ["EMQ X"], "note": "设备接入"}},
        {{"label": "数据交换", "tech_stack": ["DataX"], "note": "数据同步"}}
      ]
    }},
    {{
      "name": "data",
      "layout": {{ "columns": 5 }},
      "items": [
        {{"label": "业务数据库", "tech_stack": ["PostgreSQL"], "note": "主数据库"}},
        {{"label": "时序数据库", "tech_stack": ["InfluxDB"], "note": "IoT数据"}},
        {{"label": "图数据库", "tech_stack": ["Neo4j"], "note": "关系图谱"}},
        {{"label": "缓存层", "tech_stack": ["Redis Cluster"], "note": "分布式缓存"}},
        {{"label": "数据湖", "tech_stack": ["MinIO"], "note": "对象存储"}}
      ]
    }}
  ]
}}

{template_context}
**User Request:** "{request.user_input}"

Generate {template['name']} with optimal layout, clear layer organization, and appropriate item distribution.
"""

        system_prompt = f"""You are a professional flowchart generation expert. Create beautiful, well-organized flowcharts with optimal layout.

**AVAILABLE NODE TYPES:**
Basic Flow (for general processes):
- start: Start point (use shape="start-event" for BPMN style circle)
- end: End point (use shape="end-event" for BPMN style circle)
- process: Process/Task (use shape="task" for modern card style, or "rectangle" for simple box)
- decision: Decision/Gateway (use shape="diamond" for yes/no branches)
- data: Data Input/Output (use shape="parallelogram")
- subprocess: Sub-process (use shape="rounded-rectangle")

Technical Nodes (ONLY for technical architecture):
- api, service, database, cache, queue, storage, client, gateway

**LAYOUT ALGORITHM - CRITICAL (BALANCED GRID):**
1. **Main spine**: Start near center (x=0, y=100). Keep the core flow mostly top-to-bottom.
2. **Horizontal spread**: Use a 3-5 column grid with x positions spaced ~220-280px (e.g., -420, -200, 0, 220, 440). Do NOT stack everything in one column or only on the left.
3. **Decision branches**:
   - Place branch nodes at the SAME y-level as the decision.
   - Mirror positions left/right (e.g., x=-240 for "No", x=+240 for "Yes") to keep symmetry.
   - Rejoin branches after 1-2 steps at a centered node.
4. **Parallel processes**: Keep siblings aligned horizontally on the same y. Use even spacing (±240/±480 from center) so the layout feels balanced.
5. **Long flows**: After every 3-4 steps, gently shift the spine to an adjacent column (x=+200 or -200) to avoid a single vertical line while keeping flow mostly downward.
6. **Edge directions**:
   - Sequential: Vertical (top to bottom)
   - Branches: Diagonal or horizontal
   - Avoid all edges exiting from the same side; balance entry/exit points.

**LAYOUT EXAMPLE (Decision Flow):**
{{
  "nodes": [
    {{"id": "start", "type": "default", "position": {{"x": 400, "y": 100}},
      "data": {{"label": "开始", "shape": "start-event", "color": "#16a34a"}}}},
    {{"id": "step1", "type": "default", "position": {{"x": 400, "y": 280}},
      "data": {{"label": "提交申请", "shape": "task", "color": "#2563eb"}}}},
    {{"id": "decision1", "type": "gateway", "position": {{"x": 400, "y": 460}},
      "data": {{"label": "审批通过?", "shape": "diamond"}}}},
    {{"id": "yes-branch", "type": "default", "position": {{"x": 400, "y": 640}},
      "data": {{"label": "发放通知", "shape": "task", "color": "#2563eb"}}}},
    {{"id": "no-branch", "type": "default", "position": {{"x": 50, "y": 640}},
      "data": {{"label": "驳回并说明原因", "shape": "task", "color": "#dc2626"}}}},
    {{"id": "end", "type": "default", "position": {{"x": 400, "y": 820}},
      "data": {{"label": "结束", "shape": "end-event", "color": "#dc2626"}}}}
  ],
  "edges": [
    {{"id": "e1", "source": "start", "target": "step1"}},
    {{"id": "e2", "source": "step1", "target": "decision1"}},
    {{"id": "e3", "source": "decision1", "target": "yes-branch", "label": "是"}},
    {{"id": "e4", "source": "decision1", "target": "no-branch", "label": "否"}},
    {{"id": "e5", "source": "yes-branch", "target": "end"}},
    {{"id": "e6", "source": "no-branch", "target": "end"}}
  ]
}}

**STYLING RULES:**
1. Use BPMN shapes for clean look:
   - start-event: Green (#16a34a)
   - end-event: Red (#dc2626)
   - task: Blue (#2563eb)
   - gateway/decision: No color override (default gray)
2. DO NOT use iconType field - system provides default icons
3. Label text should be concise (5-15 Chinese chars, 3-8 English words)
4. For loops: Position loop-back nodes to the right (+350px)

**GENERATION RULES:**
1. Analyze user input to identify:
   - Decision points (questions, conditions, branches)
   - Sequential steps
   - Parallel processes
   - Loop logic
2. For simple flows (5-8 nodes):
   - Linear top-to-bottom with 1-2 decisions
3. For complex flows (10-15 nodes):
   - Multiple decision branches
   - Use horizontal space for clarity
4. Avoid cluttered layouts:
   - Max 3 parallel branches
   - Clear visual separation between branches

**OUTPUT FORMAT:**
{{
  "nodes": [...],  // Array of node objects with position/type/data
  "edges": [...],  // Array of edge objects with source/target/label
  "mermaid_code": "graph TB\\n..."  // Optional Mermaid syntax
}}

{template_context}

**User Request:** "{request.user_input}"

Generate a well-laid-out flowchart. Focus on clarity and visual balance. Return ONLY valid JSON, no markdown blocks."""
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

    def _calculate_frame_size(self, items_count: int, columns: int = 4) -> dict:
        """
        Calculate dynamic frame size based on number of items and columns.

        Args:
            items_count: Number of items in the layer
            columns: Number of columns in grid layout (default: 4)

        Returns:
            dict with 'width' and 'height' in pixels
        """
        item_width = 240  # Width of each component card
        item_height = 100  # Height of each component card
        padding = 60  # Frame padding
        gap = 20  # Gap between items
        header_height = 40  # Layer header height

        # Calculate actual columns (don't exceed items count)
        actual_columns = min(items_count, columns) if items_count > 0 else columns

        # Calculate rows needed
        rows = (items_count + columns - 1) // columns if items_count > 0 else 1

        # Calculate dimensions
        width = actual_columns * item_width + (actual_columns - 1) * gap + padding * 2
        height = rows * item_height + (rows - 1) * gap + padding * 2 + header_height

        return {
            "width": max(width, 800),  # Minimum width for aesthetics
            "height": max(height, 150),  # Minimum height
        }

    def _normalize_architecture_graph(self, ai_data: dict, architecture_type: str = "layered"):
        """
        Normalize architecture JSON (layers/items) into nodes with LayerFrame backgrounds.
        Supports dynamic sizing and grid layout.

        Args:
            ai_data: AI-generated architecture data
            architecture_type: Type of architecture (layered, business, technical, deployment, domain)

        Returns:
            Tuple of (nodes, edges, mermaid_code)
        """
        try:
            layers = (
                ai_data.get("layers")
                or ai_data.get("sections")
                or ai_data.get("architecture")
                or ai_data.get("groups")
                or []
            )
            # Extract edges if provided (for technical/deployment architectures)
            ai_edges = ai_data.get("edges", [])
        except Exception:
            return [], [], ""

        nodes = []
        edges = []

        # Enhanced layer colors with more types
        layer_colors = {
            # Layered architecture
            "frontend": "#f59e0b",      # Orange
            "backend": "#22c55e",       # Green
            "middleware": "#6366f1",    # Indigo
            "data": "#a855f7",          # Purple
            "infrastructure": "#0ea5e9", # Sky blue
            "observability": "#14b8a6", # Teal
            # Business architecture
            "capability": "#f59e0b",    # Orange
            "service": "#22c55e",       # Green
            "process": "#6366f1",       # Indigo
            "organization": "#a855f7",  # Purple
            # Technical architecture
            "presentation": "#f59e0b",  # Orange
            "application": "#22c55e",   # Green
            "integration": "#6366f1",   # Indigo
            # Deployment architecture
            "dmz": "#ef4444",           # Red
            "app-tier": "#22c55e",      # Green
            "data-tier": "#a855f7",     # Purple
            "monitoring": "#14b8a6",    # Teal
            # Domain architecture
            "domain-services": "#22c55e",     # Green
            "shared-kernel": "#6366f1",       # Indigo
            "anti-corruption": "#f59e0b",     # Orange
        }

        # Get template configuration
        template = ARCHITECTURE_TEMPLATES.get(architecture_type, ARCHITECTURE_TEMPLATES["layered"])
        default_columns = template.get("default_columns", 4)

        # Configuration for layout
        frame_padding_x = 60
        frame_padding_y = 100
        layer_spacing_y = 200
        item_width = 240
        item_height = 100
        padding = 60
        gap = 20
        header_height = 40

        if isinstance(layers, dict):
            layers = [{"name": k, "items": v} for k, v in layers.items()]
        elif not isinstance(layers, list):
            return [], [], ""

        # Track cumulative Y position
        current_y = frame_padding_y

        # Generate nodes with LayerFrame backgrounds
        for layer_idx, layer in enumerate(layers):
            layer_name = layer.get("name") if isinstance(layer, dict) else f"layer-{layer_idx}"
            items = layer.get("items", []) if isinstance(layer, dict) else []
            color = layer_colors.get(layer_name.lower(), "#64748b")

            # Get layout configuration for this layer
            layer_layout = layer.get("layout", {}) if isinstance(layer, dict) else {}
            columns = layer_layout.get("columns", default_columns)

            # Calculate dynamic frame size based on items count
            frame_size = self._calculate_frame_size(len(items), columns)

            # Add LayerFrame background node with dynamic sizing
            layer_frame_id = f"{layer_name}-frame"
            nodes.append({
                "id": layer_frame_id,
                "type": "layerFrame",
                "position": {"x": frame_padding_x, "y": current_y},
                "data": {
                    "label": layer_name.capitalize(),
                    "color": color,
                    "width": frame_size["width"],
                    "height": frame_size["height"],
                    "layout": "grid",  # NEW: Indicate grid layout mode
                    "columns": columns,  # NEW: Number of columns for grid
                    "itemsCount": len(items),  # NEW: Track item count
                },
                "draggable": False,
                # CRITICAL: Set style to define the draggable area for child nodes
                "style": {
                    "width": frame_size["width"],
                    "height": frame_size["height"],
                },
            })

            # Position component nodes in grid layout RELATIVE to parent
            for item_idx, item in enumerate(items):
                if isinstance(item, dict):
                    label = item.get("label") or item.get("name") or f"{layer_name}-{item_idx}"
                    tech_stack = item.get("tech_stack", []) or []
                    note = item.get("note") or (", ".join(tech_stack) if tech_stack else "")
                    category = item.get("category", "service")  # NEW: Category for icons
                else:
                    label = str(item)
                    note = ""
                    tech_stack = []
                    category = "service"

                # Calculate grid position
                row = item_idx // columns
                col = item_idx % columns

                # Calculate RELATIVE position (relative to parent LayerFrame)
                # Start from padding, not absolute coordinates
                item_x_relative = padding + col * (item_width + gap)
                item_y_relative = header_height + padding + row * (item_height + gap)

                nodes.append({
                    "id": f"{layer_name}-{item_idx}",
                    "type": "frame",
                    "position": {"x": item_x_relative, "y": item_y_relative},  # RELATIVE position
                    "parentNode": layer_frame_id,  # CRITICAL: Set parent relationship
                    "extent": "parent",  # CRITICAL: Constrain dragging within parent
                    "data": {
                        "label": label,
                        "shape": "task",
                        "color": color,
                        "layer": layer_name,
                        "note": note,
                        "layerColor": color,
                        "tech_stack": tech_stack if isinstance(tech_stack, list) else [],
                        "category": category,  # NEW: For visual enhancements
                    },
                })

            # Update current_y for next layer (with spacing)
            current_y += frame_size["height"] + layer_spacing_y

        # Process edges if provided (for technical/deployment architectures)
        for edge_idx, edge_data in enumerate(ai_edges):
            if isinstance(edge_data, dict):
                source = edge_data.get("source")
                target = edge_data.get("target")
                if source and target:
                    edges.append({
                        "id": edge_data.get("id") or f"e-{edge_idx}",
                        "source": source,
                        "target": target,
                        "label": edge_data.get("label", ""),
                        "type": edge_data.get("type", "dependency"),
                    })

        # Generate mermaid code
        mermaid_lines = [f"# {template['name']} ({template['name_en']})"]
        for layer in layers:
            lname = layer.get("name") if isinstance(layer, dict) else str(layer)
            mermaid_lines.append(f"## {lname.capitalize()}")
            items = layer.get("items", []) if isinstance(layer, dict) else []
            for item in items:
                if isinstance(item, dict):
                    label = item.get("label") or item.get("name") or "component"
                    tech_stack = item.get("tech_stack", []) or []
                    note = item.get("note") or ", ".join(tech_stack)
                    mermaid_lines.append(f"- **{label}**: {note}")
                else:
                    mermaid_lines.append(f"- {item}")
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

    # ============================================================
    # 增量生成辅助方法 (Incremental Generation Helpers)
    # ============================================================

    def _build_architecture_description(
        self,
        nodes: List[Node],
        edges: List[Edge]
    ) -> str:
        """将现有架构转换为自然语言描述（参考 Prompter 模式）"""

        desc = f"### Current Architecture Overview\n\n"
        desc += f"**Total**: {len(nodes)} components, {len(edges)} connections\n\n"

        # 1. 按类型分组节点
        nodes_by_type = {}
        for node in nodes:
            node_type = node.type or "default"
            if node_type not in nodes_by_type:
                nodes_by_type[node_type] = []
            nodes_by_type[node_type].append(node)

        # 2. 描述各类型节点
        desc += "**Components by Type**:\n"
        for node_type, type_nodes in sorted(nodes_by_type.items()):
            desc += f"\n{node_type.upper()} ({len(type_nodes)}):\n"
            for node in type_nodes:
                desc += f"  - {node.data.label} (id: {node.id})\n"

        # 3. 描述连接关系
        desc += f"\n**Connections** ({len(edges)} total):\n"
        for edge in edges:
            # 查找 source 和 target 的 label
            source_node = next((n for n in nodes if n.id == edge.source), None)
            target_node = next((n for n in nodes if n.id == edge.target), None)

            source_label = source_node.data.label if source_node else edge.source
            target_label = target_node.data.label if target_node else edge.target
            edge_label = f" ({edge.label})" if edge.label else ""

            desc += f"  - {source_label} → {target_label}{edge_label}\n"

        # 4. 分析架构特征
        desc += "\n**Architecture Characteristics**:\n"

        # 检测分层结构（基于 y 坐标）
        y_coords = sorted(set(n.position.y for n in nodes))
        if len(y_coords) > 1:
            desc += f"  - Layered structure with {len(y_coords)} distinct layers\n"

        # 检测关键节点（入度/出度高的）
        in_degree = {n.id: 0 for n in nodes}
        out_degree = {n.id: 0 for n in nodes}
        for edge in edges:
            out_degree[edge.source] = out_degree.get(edge.source, 0) + 1
            in_degree[edge.target] = in_degree.get(edge.target, 0) + 1

        hubs = [n for n in nodes if in_degree[n.id] + out_degree[n.id] > 2]
        if hubs:
            desc += f"  - {len(hubs)} hub components with multiple connections\n"
            for hub in hubs[:3]:  # 只显示前 3 个
                desc += f"    * {hub.data.label} ({in_degree[hub.id]} in, {out_degree[hub.id]} out)\n"

        return desc

    def _build_incremental_prompt(
        self,
        request: ChatGenerationRequest,
        existing_nodes: List[Node],
        existing_edges: List[Edge]
    ) -> str:
        """构建增量生成的 Prompt"""

        # 提取现有节点信息
        existing_ids = [n.id for n in existing_nodes]
        max_x = max((n.position.x for n in existing_nodes), default=0)
        max_y = max((n.position.y for n in existing_nodes), default=0)
        min_y = min((n.position.y for n in existing_nodes), default=0)
        node_count = len(existing_nodes)
        edge_count = len(existing_edges)

        # 按类型分组节点
        nodes_by_type = {}
        for node in existing_nodes:
            node_type = node.type or "default"
            if node_type not in nodes_by_type:
                nodes_by_type[node_type] = []
            nodes_by_type[node_type].append(node.data.label)

        # 生成时间戳用于新节点 ID
        timestamp = int(time.time())

        # 构建系统 Prompt
        system_prompt = f"""You are an expert systems architect tasked with INCREMENTALLY enhancing an existing {"architecture" if request.diagram_type == "architecture" else "flowchart"}.

**CRITICAL CONSTRAINT: DO NOT SIMPLIFY THE EXISTING ARCHITECTURE**

This is an ENHANCEMENT task, NOT a REFACTORING task.

ABSOLUTE RULES:
1. PRESERVE COMPLEXITY: Keep all existing nodes with their EXACT labels, types, and properties
2. NO DELETION: Do NOT delete any existing nodes or edges
3. NO MODIFICATION: Do NOT change existing node labels, types, positions, or colors
4. NO MERGE: Do NOT merge or consolidate existing nodes
5. NO REARRANGEMENT: Do NOT change the existing layout or structure
6. ONLY ADD: You may ONLY add new nodes and new edges

The user wants to ENHANCE (add new features), not REFACTOR (restructure existing).
Treat the existing architecture as IMMUTABLE except for adding new nodes/edges.

If the user request seems to require modifying existing nodes, interpret it as
"add new nodes that complement the existing ones" instead.

---

**CRITICAL RULES FOR INCREMENTAL GENERATION:**
1. **PRESERVE ALL EXISTING NODES**: Keep all {node_count} nodes UNCHANGED (IDs: {', '.join(existing_ids[:10])}{', ...' if len(existing_ids) > 10 else ''})
2. **UNIQUE NEW IDs**: New nodes must use format `{{type}}-{timestamp}-{{sequence}}` (e.g., "service-{timestamp}-1")
3. **SMART POSITIONING**:
   - Existing bounds: x=[0, {max_x}], y=[{min_y}, {max_y}]
   - Place new nodes starting at x={max_x + 300}, y within [{min_y}, {max_y}]
   - Maintain spacing: 300px horizontal, 200px vertical
4. **PRESERVE EDGES**: Keep all {edge_count} existing connections unless explicitly removing
5. **TYPE CONSISTENCY**: Use existing node types where appropriate ({', '.join(nodes_by_type.keys())})

**EXISTING ARCHITECTURE SUMMARY:**
- Total: {node_count} nodes, {edge_count} edges
- Node types:
{chr(10).join(f'  - {t}: {len(nodes)} nodes ({", ".join(nodes[:3])}{"..." if len(nodes) > 3 else ""})' for t, nodes in nodes_by_type.items())}

**EXISTING ARCHITECTURE (NATURAL LANGUAGE)**:
{self._build_architecture_description(existing_nodes, existing_edges)}

**COMPLETE EXISTING STRUCTURE (JSON FORMAT)**:
```json
{json.dumps({
    "nodes": [n.model_dump() for n in existing_nodes],
    "edges": [e.model_dump() for e in existing_edges]
}, indent=2, ensure_ascii=False)}
```

**USER ENHANCEMENT REQUEST:**
"{request.user_input}"

**DIAGRAM TYPE:** {request.diagram_type}
**ARCHITECTURE TYPE:** {request.architecture_type if request.diagram_type == "architecture" else "N/A"}

**OUTPUT FORMAT:**
Return ONLY valid JSON (no markdown, no code blocks) with the COMPLETE architecture (existing + new):
{{
  "nodes": [
    ...ALL existing nodes UNCHANGED...,
    ...NEW nodes with unique IDs and proper positioning...
  ],
  "edges": [
    ...ALL existing edges...,
    ...NEW edges connecting new nodes...
  ]
}}

**VALIDATION CHECKLIST:**
- [ ] All {node_count} existing node IDs are present
- [ ] New node IDs use timestamp format ({timestamp})
- [ ] New nodes positioned at x >= {max_x + 300}
- [ ] All edges reference valid node IDs
- [ ] No duplicate node IDs

Generate the enhanced architecture now."""

        return system_prompt

    def _extract_semantic_keywords(self, label: str) -> set:
        """从节点label提取关键语义词"""
        import re

        # 移除常见修饰词
        noise_words = {'service', 'module', 'layer', 'system', 'component',
                       '服务', '模块', '层', '系统', '组件', 'api', 'db', 'database', 'server'}

        words = set()

        # 英文分词
        for word in re.findall(r'[A-Za-z]+', label.lower()):
            if word not in noise_words and len(word) > 2:
                words.add(word)

        # 中文分词（提取连续中文字符）
        for word in re.findall(r'[\u4e00-\u9fff]+', label):
            if word not in noise_words and len(word) >= 2:
                words.add(word)

        return words

    def _validate_semantic_coverage(self, original_nodes: List[Node], final_nodes: List[Node]) -> bool:
        """验证语义覆盖率 - 确保原有概念没有丢失"""

        # 提取原始节点的所有语义关键词
        original_keywords = set()
        original_node_keywords = {}  # {node_id: keywords}

        for node in original_nodes:
            keywords = self._extract_semantic_keywords(node.data.label)
            if keywords:  # 只考虑有实际语义的节点
                original_keywords.update(keywords)
                original_node_keywords[node.id] = {
                    'label': node.data.label,
                    'keywords': keywords
                }

        # 提取最终节点的所有语义关键词
        final_keywords = set()
        for node in final_nodes:
            keywords = self._extract_semantic_keywords(node.data.label)
            final_keywords.update(keywords)

        # 检查丢失的关键词
        lost_keywords = original_keywords - final_keywords

        if lost_keywords:
            logger.warning(
                f"Semantic content lost: keywords {lost_keywords} are missing in final architecture"
            )

            # 找出哪些节点的语义完全丢失了
            lost_semantic_nodes = []
            for node_id, info in original_node_keywords.items():
                # 如果这个节点的所有关键词都不在最终架构中，说明这个概念完全丢失了
                if info['keywords'] and not info['keywords'].intersection(final_keywords):
                    lost_semantic_nodes.append(info['label'])

            if lost_semantic_nodes:
                logger.error(
                    f"CRITICAL: {len(lost_semantic_nodes)} nodes lost semantic content: {lost_semantic_nodes}"
                )
                logger.error(
                    "This means AI simplified the architecture instead of appending to it!"
                )
                return False

        # 计算语义覆盖率
        if original_keywords:
            coverage = len(final_keywords.intersection(original_keywords)) / len(original_keywords)
            logger.info(f"Semantic coverage: {coverage * 100:.1f}%")

            if coverage < 0.8:
                logger.error(
                    f"Semantic coverage too low ({coverage * 100:.1f}%), "
                    "significant content loss detected"
                )
                return False

        return True

    def _validate_incremental_result(
        self,
        original_nodes: List[Node],
        ai_nodes: List[Node]
    ) -> List[Node]:
        """更严格的验证和修复 AI 的增量生成结果"""
        original_id_map = {n.id: n for n in original_nodes}
        ai_id_map = {n.id: n for n in ai_nodes}

        # 1. 检查缺失节点（AI 误删）
        missing_ids = set(original_id_map.keys()) - set(ai_id_map.keys())
        if missing_ids:
            logger.warning(f"AI deleted {len(missing_ids)} nodes: {missing_ids}, restoring them")
            # 恢复缺失节点
            for node_id in missing_ids:
                ai_nodes.append(original_id_map[node_id])
            # 重建 ai_id_map
            ai_id_map = {n.id: n for n in ai_nodes}

        # 2. 检查现有节点的属性是否被修改
        position_modified_count = 0
        for node_id in original_id_map.keys():
            if node_id in ai_id_map:
                original_node = original_id_map[node_id]
                ai_node = ai_id_map[node_id]

                # 检查关键属性
                if ai_node.data.label != original_node.data.label:
                    logger.warning(
                        f"Node label changed: {node_id} "
                        f"({original_node.data.label} → {ai_node.data.label}), "
                        f"reverting to original"
                    )
                    ai_node.data.label = original_node.data.label

                if ai_node.type != original_node.type:
                    logger.warning(
                        f"Node type changed: {node_id} "
                        f"({original_node.type} → {ai_node.type}), "
                        f"reverting to original"
                    )
                    ai_node.type = original_node.type

                # 🔧 在增量模式下，原始节点位置不应该变化（除非非常小的偏移 ±5px）
                pos_diff = abs(ai_node.position.x - original_node.position.x) + \
                           abs(ai_node.position.y - original_node.position.y)
                if pos_diff > 5:  # 严格限制：超过 5px 就认为是移动了
                    logger.warning(
                        f"Node position changed: {node_id} "
                        f"({original_node.position.x}, {original_node.position.y}) → "
                        f"({ai_node.position.x}, {ai_node.position.y}), diff={pos_diff:.0f}px, "
                        f"reverting to original"
                    )
                    ai_node.position = original_node.position
                    position_modified_count += 1

        # 如果大量节点位置被修改，说明 AI 重新排列了整个架构
        if position_modified_count > len(original_nodes) * 0.3:  # 超过 30% 的节点被移动
            logger.error(
                f"⚠️ {position_modified_count}/{len(original_nodes)} nodes had positions changed! "
                f"AI appears to have reorganized the entire architecture instead of appending."
            )

        # 3. 检查重复 ID
        seen_ids = set()
        deduplicated = []
        for node in ai_nodes:
            if node.id in seen_ids:
                # 重命名重复节点
                original_id = node.id
                node.id = f"{node.id}-dup-{int(time.time())}"
                logger.warning(f"Duplicate node ID: {original_id} → {node.id}")
            seen_ids.add(node.id)
            deduplicated.append(node)

        # 4. 检查位置重叠
        deduplicated = self._resolve_position_overlaps(deduplicated)

        # 5. 🆕 语义完整性检查 - 确保原有概念没有丢失
        semantic_ok = self._validate_semantic_coverage(original_nodes, deduplicated)
        if not semantic_ok:
            logger.error(
                "Semantic validation failed! AI simplified architecture. "
                "Keeping ALL original nodes to preserve content."
            )
            # 如果语义丢失严重，保留所有原始节点，只添加新节点
            final_node_ids = {n.id for n in deduplicated}
            original_node_ids = {n.id for n in original_nodes}
            new_nodes = [n for n in deduplicated if n.id not in original_node_ids]

            logger.warning(
                f"Falling back to safe mode: keeping all {len(original_nodes)} original nodes + "
                f"{len(new_nodes)} new nodes"
            )
            deduplicated = list(original_nodes) + new_nodes

        # 6. 🆕 检查是否真的新增了节点 - 关键验证！
        original_node_ids = set(original_id_map.keys())
        final_node_ids = {n.id for n in deduplicated}
        new_node_ids = final_node_ids - original_node_ids

        if len(new_node_ids) == 0:
            logger.error(
                f"❌ CRITICAL: No new nodes were added! "
                f"AI just rearranged existing {len(original_nodes)} nodes without adding requested content."
            )
            logger.error(
                "This is a failed incremental generation - user requested to ADD something, "
                "but AI only reorganized what already exists."
            )
        else:
            logger.info(f"✓ Successfully added {len(new_node_ids)} new nodes: {list(new_node_ids)[:5]}...")

        return deduplicated

    def _resolve_position_overlaps(self, nodes: List[Node]) -> List[Node]:
        """解决节点位置重叠"""
        overlap_threshold = 100  # 100px 以内视为重叠

        for i, node in enumerate(nodes):
            for other in nodes[:i]:
                distance = math.sqrt(
                    (node.position.x - other.position.x)**2 +
                    (node.position.y - other.position.y)**2
                )
                if distance < overlap_threshold:
                    # 向右偏移
                    node.position.x += 300
                    logger.info(f"Position overlap: shifted {node.id} to x={node.position.x}")

        return nodes

    def _merge_edges(self, original_edges: List[Edge], ai_edges: List[Edge]) -> List[Edge]:
        """智能合并边，确保原始边不丢失"""

        # 1. 为原始边建立索引（使用 source→target 作为签名）
        original_edge_map = {}
        for edge in original_edges:
            sig = (edge.source, edge.target)
            original_edge_map[sig] = edge

        # 2. 检查 AI 是否删除了原始边
        ai_edge_sigs = {(e.source, e.target) for e in ai_edges}
        original_edge_sigs = set(original_edge_map.keys())

        missing_edge_sigs = original_edge_sigs - ai_edge_sigs
        if missing_edge_sigs:
            logger.warning(
                f"AI deleted {len(missing_edge_sigs)} edges: {missing_edge_sigs}, "
                f"restoring them"
            )

        # 3. 合并：原始边 + AI 新增的边
        merged = list(original_edges)  # 确保所有原始边都保留

        for edge in ai_edges:
            sig = (edge.source, edge.target)
            if sig not in original_edge_map:
                # 这是 AI 新增的边
                merged.append(edge)
            else:
                # 这是原始边，检查 AI 是否修改了 label
                original_edge = original_edge_map[sig]
                if edge.label != original_edge.label and original_edge.label:
                    logger.warning(
                        f"Edge label changed: {sig} "
                        f"({original_edge.label} → {edge.label}), "
                        f"keeping original"
                    )
                    # 已经在 merged 中保留了原始边，不需要额外操作

        return merged

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

            # 获取有效配置（优先使用传入参数，否则使用默认预设）
            presets_service = get_model_presets_service()
            config = presets_service.get_active_config(
                provider=selected_provider,
                api_key=api_key or request.api_key,
                base_url=base_url or request.base_url,
                model_name=model_name or request.model_name
            )

            if not config:
                return ChatGenerationResponse(
                    success=False,
                    nodes=[],
                    edges=[],
                    mermaid_code="",
                    message="No AI configuration found. Please configure AI model in settings or provide API key."
                )

            vision_service = create_vision_service(
                provider=config["provider"],
                api_key=config["api_key"],
                base_url=config.get("base_url"),
                model_name=config.get("model_name"),
            )

            # 🔧 Fix: 使用配置中的实际 provider，而不是请求中的 provider
            # 这样可以确保 _call_ai_text_generation 使用正确的方法
            selected_provider = config["provider"]

            # 🆕 增量生成模式：检查并获取现有架构
            existing_nodes = []
            existing_edges = []
            session_id = request.session_id

            if request.incremental_mode and request.session_id:
                logger.info(f"[INCREMENTAL] Incremental mode enabled, loading session: {request.session_id}")
                session_manager = get_session_manager()
                session_data = session_manager.get_session(request.session_id)

                if session_data:
                    existing_nodes = [Node(**n) for n in session_data["nodes"]]
                    existing_edges = [Edge(**e) for e in session_data["edges"]]
                    logger.info(
                        f"[INCREMENTAL] Loaded {len(existing_nodes)} nodes, {len(existing_edges)} edges"
                    )
                else:
                    logger.warning(
                        f"[INCREMENTAL] Session {request.session_id} not found or expired, "
                        "falling back to full generation"
                    )
                    request.incremental_mode = False

            # 构建 Prompt（增量或全新）
            prompt_request = request.model_copy(update={"diagram_type": effective_diagram_type})
            if request.incremental_mode and existing_nodes:
                logger.info("[INCREMENTAL] Building incremental prompt")
                prompt = self._build_incremental_prompt(prompt_request, existing_nodes, existing_edges)
            else:
                prompt = self._build_generation_prompt(prompt_request)

            logger.info(f"[CHAT-GEN] Calling AI with provider: {selected_provider}")
            logger.info(f"[CHAT-GEN] Prompt (first 200 chars): {prompt[:200]}...")
            ai_raw = await self._call_ai_text_generation(vision_service, prompt, selected_provider)
            logger.info(f"[CHAT-GEN] AI raw response type: {type(ai_raw)}, keys: {list(ai_raw.keys()) if isinstance(ai_raw, dict) else 'N/A'}")
            ai_data = self._safe_json(ai_raw)
            logger.info(f"[CHAT-GEN] Parsed AI data keys: {list(ai_data.keys())}")

            if effective_diagram_type == "architecture":
                # Pass architecture_type to normalization
                arch_type = request.architecture_type or "layered"
                nodes, edges, mermaid_code = self._normalize_architecture_graph(ai_data, arch_type)

                # Only suppress edges if template says not to show them
                template = ARCHITECTURE_TEMPLATES.get(arch_type, ARCHITECTURE_TEMPLATES["layered"])
                if not template.get("show_edges", False):
                    edges = []  # Business and layered architectures don't show edges
                # Technical and deployment architectures will keep their edges
            else:
                nodes, edges, mermaid_code = self._normalize_ai_graph(ai_data)

            logger.info(f"[CHAT-GEN] After normalization: {len(nodes)} nodes, {len(edges)} edges")

            # 🆕 增量模式验证和合并
            if request.incremental_mode and existing_nodes:
                logger.info("[INCREMENTAL] Validating and merging incremental results")
                nodes = self._validate_incremental_result(existing_nodes, nodes)
                edges = self._merge_edges(existing_edges, edges)
                logger.info(
                    f"[INCREMENTAL] After merge: {len(nodes)} nodes (+{len(nodes) - len(existing_nodes)} new), "
                    f"{len(edges)} edges (+{len(edges) - len(existing_edges)} new)"
                )

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

            # 🆕 更新会话（增量模式或首次保存）
            if request.incremental_mode or session_id:
                session_manager = get_session_manager()
                session_id = session_manager.create_or_update_session(
                    session_id=session_id,
                    nodes=nodes,
                    edges=edges
                )
                logger.info(f"[SESSION] Updated session: {session_id}")

            return ChatGenerationResponse(
                nodes=nodes,
                edges=edges,
                mermaid_code=mermaid_code,
                success=True,
                message=message,
                session_id=session_id  # 🆕 返回 session_id
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
