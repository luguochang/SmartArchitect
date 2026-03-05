import json
import logging
import math
import time
from pathlib import Path
from typing import List, Optional, Tuple, Any, Dict

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
        "name": "Layered Architecture",
        "name_en": "Layered Architecture",
        "layers": ["frontend", "backend", "middleware", "data", "infrastructure"],
        "default_columns": 5,
        "show_edges": False,
        "description": "General multi-tier architecture for web applications and services.",
    },
    "business": {
        "name": "Business Architecture",
        "name_en": "Business Architecture",
        "layers": ["capability", "service", "process", "organization"],
        "default_columns": 6,
        "show_edges": False,
        "description": "Business capability map focused on value streams and organizational processes.",
    },
    "technical": {
        "name": "Technical Architecture",
        "name_en": "Technical Architecture",
        "layers": ["presentation", "application", "integration", "data", "infrastructure"],
        "default_columns": 5,
        "show_edges": True,
        "edge_type": "data-flow",
        "description": "Technical component architecture with dependencies and data flow.",
    },
    "deployment": {
        "name": "Deployment Architecture",
        "name_en": "Deployment Architecture",
        "layers": ["dmz", "app-tier", "data-tier", "monitoring"],
        "default_columns": 4,
        "show_edges": True,
        "edge_type": "network",
        "description": "Infrastructure and network deployment topology.",
    },
    "domain": {
        "name": "Domain Architecture",
        "name_en": "Domain-Driven Architecture",
        "layers": ["domain-services", "shared-kernel", "anti-corruption", "infrastructure"],
        "default_columns": 4,
        "show_edges": True,
        "edge_type": "dependency",
        "description": "DDD-oriented architecture showing bounded contexts and domain relationships.",
    },
}


class ChatGeneratorService:
    """Chat-based flowchart generation service (mock-first)."""

    _ALLOWED_NODE_SHAPES = {
        "rectangle",
        "circle",
        "diamond",
        "start-event",
        "end-event",
        "intermediate-event",
        "task",
    }

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
**棣冨綒 BUSINESS ARCHITECTURE - Focus on BUSINESS CAPABILITIES:**
CRITICAL: This is a BUSINESS view, NOT technical implementation!

**Required Layers (use EXACTLY these names):**
1. "capability" (閼宠棄濮忕仦? - 10-15 business capabilities
   - Examples: 鐠佸灝缁狅紕鎮? 鏉烇箒绶犵粻锛勬倞, 鐎瑰妲婚惄鎴炲付, 閼宠姤绨粻锛勬倞, 閻椻晙绗熼張宥呭, 閺呴缚鍏樺Δ鐓庣暏, 閻滈惄鎴炵ゴ, 鐠у嫪楠囩粻锛勬倞, 鎼存梹鈧儲瀵氶幐? 閺佺増宓侀崚鍡樼€? 缂佺喍绔寸拋銈堢槈, 濞戝牊浼呴柅姘辩叀
   - Use category: "service" for all capability items
   - NO tech stack - focus on WHAT the business does

2. "service" (閺堝秴濮熺仦? - 5-8 business service systems
   - Examples: 鐠佸灝妫板嫮瀹崇化鑽ょ埠, 鏉烇箒绶犵拠鍡楀焼缁崵绮? 鐟欏棝閻╂垶甯堕獮鍐插酱, 閼冲€熲偓妤€鍨庨弸鎰挬閸? 閻椻晙绗熷銉ュ礋缁崵绮?
   - Use category: "platform"
   - Add tech_stack ONLY if relevant to business stakeholders

3. "process" (濞翠胶鈻肩仦? - 3-5 key business processes
   - Examples: 鐠佸灝閸忋儱娲ù浣衡柤, 鏉烇箒绶犳潻娑樺毉濞翠胶鈻? 鎼存梹鈧儱鎼锋惔鏃€绁︾粙?
   - Use category: "default"

4. "organization" (缂佸嫮绮愮仦? - 3-5 organizational units
   - Examples: 鏉╂劘鎯€娑撶妇, 鐎瑰绻氶柈銊╂，, 閻椻晙绗熼柈銊╂，, IT闁劑妫?
   - Use category: "default"

**STRICT RULES:**
- NO database/cache/queue components (those are technical!)
- NO infrastructure components (K8s, Docker, etc.)
- Focus on BUSINESS VALUE and CAPABILITIES
- Use business-friendly language (Chinese preferred)
"""
            elif arch_type == "technical":
                layer_examples = """
**閳挎瑱绗?TECHNICAL ARCHITECTURE - Focus on TECHNICAL COMPONENTS:**
CRITICAL: This is a TECHNICAL view showing HOW systems are built!

**Required Layers (use EXACTLY these names):**
1. "presentation" (鐞涖劎骞囩仦? - 3-5 UI components
   - Examples: React閸撳秶, Vue缁狅紕鎮婇崥搴″酱, 缁夎濮╃粩鐤塸p, 鐏忓繒鈻兼惔?
   - Use category: "api"
   - tech_stack: ["React", "TypeScript"], ["Vue", "Element UI"], etc.

2. "application" (鎼存梻鏁ょ仦? - 6-10 application services
   - Examples: 閻劍鍩涢張宥呭, 鐠併垹宕熼張宥呭, 閺€绮張宥呭, 闁氨鐓￠張宥呭, 鐠併倛鐦夐張宥呭
   - Use category: "service"
   - tech_stack: ["Spring Boot", "Java"], ["FastAPI", "Python"], etc.

3. "integration" (闂嗗棙鍨氱仦? - 4-6 integration components
   - Examples: API Gateway, 濞戝牊浼呴梼鐔峰灙, ESB閹崵鍤? 閺堝秴濮熺純鎴炵壐
   - Use category: "network"
   - tech_stack: ["Kong"], ["Kafka"], ["Istio"], etc.

4. "data" (閺佺増宓佺仦? - 4-6 data storage systems
   - Examples: MySQL娑撹绨? Redis缂傛挸鐡? MongoDB閺傚洦銆傛惔? Elasticsearch閹兼粎鍌?
   - Use category: "database"
   - tech_stack: ["MySQL 8.0"], ["Redis Cluster"], etc.

5. "infrastructure" (閸╄櫣鐠佺偓鏌︾仦? - 3-5 infrastructure components
   - Examples: Kubernetes闂嗗棛鍏? Docker鐎圭懓娅? Nginx鐠愮喕娴囬崸鍥€€, 娴滄垶婀囬崝鈥虫珤
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
**棣冩畬 DEPLOYMENT ARCHITECTURE - Focus on INFRASTRUCTURE TOPOLOGY:**
CRITICAL: This is a DEPLOYMENT view showing WHERE systems run!

**Required Layers (use EXACTLY these names):**
1. "dmz" (DMZ閸? - 3-4 edge components
   - Examples: Nginx鐠愮喕娴囬崸鍥€€, WAF闂冭尙浼€婢? CDN閼哄倻鍋? SSL缂佸牏绮?
   - Use category: "network"
   - tech_stack: ["Nginx", "HAProxy"], ["ModSecurity"], etc.
   - note: Include IP ranges or network segments

2. "app-tier" (鎼存梻鏁ょ仦? - 5-8 application deployment units
   - Examples: K8s Pod (鐠併垹宕熼張宥呭), Docker鐎圭懓娅?(閻劍鍩涢張宥呭), Tomcat鐎圭偘绶?
   - Use category: "compute"
   - tech_stack: ["K8s Deployment"], ["Docker Compose"], etc.
   - note: Include replica counts (e.g., "3閸撴拱")

3. "data-tier" (閺佺増宓佺仦? - 3-5 data storage deployments
   - Examples: MySQL娑撹绮犻梿鍡欏參, Redis閸濄劌鍙洪梿鍡欏參, MinIO鐎电钖勭€涙ê鍋?
   - Use category: "storage"
   - tech_stack: ["MySQL 8.0 娑撹绮?], ["Redis Sentinel"], etc.
   - note: Include HA configuration

4. "monitoring" (閻╂垶甯剁仦? - 3-4 monitoring/logging systems
   - Examples: Prometheus閻╂垶甯? Grafana閸欓崠? ELK閺冦儱绻? Jaeger闁炬崘鐭炬潻鍊熼嚋
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
**棣冨箚 DOMAIN-DRIVEN ARCHITECTURE - Focus on BOUNDED CONTEXTS:**
CRITICAL: This is a DDD view showing domain boundaries!

**Required Layers (use EXACTLY these names):**
1. "domain-services" (妫板棗鐓欓張宥呭鐏? - 5-8 bounded contexts
   - Examples: 鐠併垹宕熼崺? 閻劍鍩涢崺? 閺€绮崺? 鎼存挸鐡ㄩ崺? 閻椻晜绁﹂崺?
   - Use category: "service"
   - note: Include domain responsibilities

2. "shared-kernel" (閸忓彉闊╅崘鍛壋鐏? - 2-4 shared components
   - Examples: 闁氨鏁ゅ銉ュ徔缁? 妫板棗鐓欐禍瀣╂閹崵鍤? 閸忓彉闊╅崐鐓庣挒?
   - Use category: "platform"

3. "anti-corruption" (闂冭尪鍘仦? - 2-3 integration adapters
   - Examples: 婢舵牠鍎撮弨绮柅鍌炲帳閸? 缁楃瑏閺傚湱澧垮ù渚€鈧倿鍘ら崳?
   - Use category: "network"

4. "infrastructure" (閸╄櫣鐠佺偓鏌︾仦? - 3-4 infrastructure services
   - Examples: 閺佺増宓侀幐浣风畽閸? 濞戝牊浼呴崣鎴濈, 缂傛挸鐡ㄩ張宥呭
   - Use category: "infrastructure"

**STRICT RULES:**
- Use DDD terminology (Bounded Context, Aggregate, etc.)
- Show domain boundaries clearly
- Include edges for domain events
"""
            else:  # layered (default/generic)
                layer_examples = """
**棣冨綒 LAYERED ARCHITECTURE - Generic multi-tier structure:**

**Required Layers (use EXACTLY these names):**
1. "frontend" (閸撳秶鐏? - 2-4 client applications
2. "backend" (閸氬海鐏? - 4-6 backend services
3. "middleware" (娑撴？娴犺泛鐪? - 3-5 middleware components
4. "data" (閺佺増宓佺仦? - 3-4 data storage systems
5. "infrastructure" (閸╄櫣鐠佺偓鏌︾仦? - 2-3 infrastructure components

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
- Example: {{"source": "application-0", "target": "integration-0", "label": "API鐠嬪啰鏁?}}
- Keep edge labels concise (API鐠嬪啰鏁? 閺佺増宓佸ù? 缂冩垹绮舵潻鐐村复, etc.)
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
        {{"label": "鐠佸灝缁狅紕鎮?, "category": "service", "note": "鐠佸灝妫板嫮瀹虫稉搴ｆ鐠?}},
        {{"label": "鏉烇箒绶犵粻锛勬倞", "category": "service", "note": "鏉烇箒绶犵拠鍡楀焼娑撳骸浠犳潪?}},
        {{"label": "鐎瑰妲婚惄鎴炲付", "category": "service", "note": "鐟欏棝閻╂垶甯舵稉搴ㄧ拃?}},
        {{"label": "閼宠姤绨粻锛勬倞", "category": "service", "note": "閼冲€熲偓妤€鍨庨弸鎰瑢娴兼ê瀵?}},
        {{"label": "閻椻晙绗熼張宥呭", "category": "service", "note": "瀹搞儱宕熸稉搴㈠鐠囧閻?}},
        {{"label": "閺呴缚鍏樺Δ鐓庣暏", "category": "service", "note": "濡ょ厧鐣ら懛甯舵稉搴ょ殶閼?}},
        {{"label": "閻滈惄鎴炵ゴ", "category": "service", "note": "缁岀儤鐨电拹銊╁櫤娑撳孩淇﹢鍨"}},
        {{"label": "鐠у嫪楠囩粻锛勬倞", "category": "service", "note": "鐠у嫪楠囬惄妯煎仯娑撳氦鎷烽煪?}},
        {{"label": "鎼存梹鈧儲瀵氶幐?, "category": "service", "note": "鎼存梹鈧儱鎼锋惔鏂剧瑢鐠嬪啫瀹?}},
        {{"label": "閺佺増宓侀崚鍡樼€?, "category": "platform", "note": "閺佺増宓侀崣閸栨牔绗岄幎銉ㄣ€?}},
        {{"label": "缂佺喍绔寸拋銈堢槈", "category": "platform", "note": "閸楁洜鍋ｉ惂璇茬秿娑撳孩娼堥梽?}},
        {{"label": "濞戝牊浼呴柅姘辩叀", "category": "platform", "note": "濞戝牊浼呴幒銊┾偓浣风瑢閹绘劙鍟?}}
      ]
    }},
    {{
      "name": "application",
      "layout": {{ "columns": 5 }},
      "items": [
        {{"label": "鐠佸灝妫板嫮瀹崇化鑽ょ埠", "tech_stack": ["Vue", "Spring Boot"], "note": "鐠佸灝妫板嫮瀹虫稉搴￠幍?}},
        {{"label": "鏉烇箒绶犵拠鍡楀焼缁崵绮?, "tech_stack": ["TensorFlow", "FastAPI"], "note": "鏉烇妇澧濈拠鍡楀焼娑撳孩濮勯幏?}},
        {{"label": "鐟欏棝閻╂垶甯堕獮鍐插酱", "tech_stack": ["WebRTC", "Node.js"], "note": "鐟欏棝濞翠礁閻?}},
        {{"label": "閼冲€熲偓妤€鍨庨弸鎰挬閸?, "tech_stack": ["Grafana", "InfluxDB"], "note": "閼冲€熲偓妤佹殶閹瑰瀻閺?}},
        {{"label": "閻椻晙绗熷銉ュ礋缁崵绮?, "tech_stack": ["React", "Django"], "note": "瀹搞儱宕熷ù浣芥祮婢跺嫮鎮?}}
      ]
    }},
    {{
      "name": "integration",
      "layout": {{ "columns": 4 }},
      "items": [
        {{"label": "API Gateway", "tech_stack": ["Kong"], "note": "缂佺喍绔寸純鎴濆彠"}},
        {{"label": "ESB閹崵鍤?, "tech_stack": ["Kafka"], "note": "濞戝牊浼呴幀鑽ゅ殠"}},
        {{"label": "IoT楠炲啿褰?, "tech_stack": ["EMQ X"], "note": "鐠佹儳閹恒儱鍙?}},
        {{"label": "閺佺増宓佹禍銈嗗床", "tech_stack": ["DataX"], "note": "閺佺増宓侀崥灞?}}
      ]
    }},
    {{
      "name": "data",
      "layout": {{ "columns": 5 }},
      "items": [
        {{"label": "娑撴艾濮熼弫鐗堝祦鎼?, "tech_stack": ["PostgreSQL"], "note": "娑撶粯鏆熼幑绨?}},
        {{"label": "閺冭泛绨弫鐗堝祦鎼?, "tech_stack": ["InfluxDB"], "note": "IoT閺佺増宓?}},
        {{"label": "閸ョ偓鏆熼幑绨?, "tech_stack": ["Neo4j"], "note": "閸忓磭閮撮崶鎹愭皑"}},
        {{"label": "缂傛挸鐡ㄧ仦?, "tech_stack": ["Redis Cluster"], "note": "閸掑棗绔峰蹇曠处鐎?}},
        {{"label": "閺佺増宓佸﹢?, "tech_stack": ["MinIO"], "note": "鐎电钖勭€涙ê鍋?}}
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
4. **Parallel processes**: Keep siblings aligned horizontally on the same y. Use even spacing (鍗?40/鍗?80 from center) so the layout feels balanced.
5. **Long flows**: After every 3-4 steps, gently shift the spine to an adjacent column (x=+200 or -200) to avoid a single vertical line while keeping flow mostly downward.
6. **Edge directions**:
   - Sequential: Vertical (top to bottom)
   - Branches: Diagonal or horizontal
   - Avoid all edges exiting from the same side; balance entry/exit points.

**LAYOUT EXAMPLE (Decision Flow):**
{{
  "nodes": [
    {{"id": "start", "type": "default", "position": {{"x": 400, "y": 100}},
      "data": {{"label": "瀵偓婵?, "shape": "start-event", "color": "#16a34a"}}}},
    {{"id": "step1", "type": "default", "position": {{"x": 400, "y": 280}},
      "data": {{"label": "閹绘劒姘﹂悽瀹?, "shape": "task", "color": "#2563eb"}}}},
    {{"id": "decision1", "type": "gateway", "position": {{"x": 400, "y": 460}},
      "data": {{"label": "鐎光剝澹掗柅姘崇箖?", "shape": "diamond"}}}},
    {{"id": "yes-branch", "type": "default", "position": {{"x": 400, "y": 640}},
      "data": {{"label": "閸欐垶鏂侀柅姘辩叀", "shape": "task", "color": "#2563eb"}}}},
    {{"id": "no-branch", "type": "default", "position": {{"x": 50, "y": 640}},
      "data": {{"label": "妞瑰啿娲栭獮鎯伴弰搴″斧閸?, "shape": "task", "color": "#dc2626"}}}},
    {{"id": "end", "type": "default", "position": {{"x": 400, "y": 820}},
      "data": {{"label": "缂佹挻娼?, "shape": "end-event", "color": "#dc2626"}}}}
  ],
  "edges": [
    {{"id": "e1", "source": "start", "target": "step1"}},
    {{"id": "e2", "source": "step1", "target": "decision1"}},
    {{"id": "e3", "source": "decision1", "target": "yes-branch", "label": "閺?}},
    {{"id": "e4", "source": "decision1", "target": "no-branch", "label": "閸?}},
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
2. Complexity targets (adaptive by request size):
   - Simple request: 10-14 nodes, 12-22 edges
   - Medium request: 14-24 nodes, 20-40 edges
   - Complex/system-level request: 24-45 nodes, 36-72 edges
   - If user explicitly asks for "complex/detailed/production" diagrams, prefer 32-50 nodes
3. For complex flows:
   - Include at least 3 decision hubs, 2 loop-back paths, and 1 explicit merge node
   - Include main path + exception path + compensation/recovery path + observability/monitoring path
   - Use horizontal space and multi-column distribution to keep readability
   - Build 3-6 logical clusters, each with 4-10 nodes
4. Avoid cluttered layouts:
   - Max 5 parallel branches per decision hub
   - Keep branch lanes visually separated
   - Ensure every non-start node has at least one incoming edge
5. Prevent truncation/incomplete output:
   - Output complete "nodes" array first, then complete "edges" array
   - Do not omit closing brackets/braces
   - Do not output explanatory prose
   - Use compact JSON (minimal whitespace) to reduce latency

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

    @staticmethod
    def _classify_provider_error(error: Exception) -> tuple[int, str]:
        text = str(error).lower()
        if "usage_limit" in text or "rate limit" in text or "quota" in text or " 429" in text or "429 " in text:
            return 429, "usage_limit_reached"
        if "unauthorized" in text or "invalid api key" in text or "authentication" in text or "401" in text:
            return 401, "authentication_failed"
        if "timeout" in text or "timed out" in text:
            return 504, "upstream_timeout"
        if "bad gateway" in text or "502" in text or "503" in text or "service unavailable" in text:
            return 503, "upstream_unavailable"
        return 500, "provider_error"

    @classmethod
    def _is_retryable_provider_error(cls, error: Exception) -> bool:
        status_code, _ = cls._classify_provider_error(error)
        return status_code in {429, 503, 504}

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
        allowed_node_types = {
            "default": "default",
            "database": "database",
            "api": "api",
            "service": "service",
            "gateway": "gateway",
            "cache": "cache",
            "queue": "queue",
            "storage": "storage",
            "client": "client",
            "frame": "frame",
            "layerframe": "layerFrame",
        }

        def normalize_node_type(raw_node_type: Any) -> str:
            node_type = str(raw_node_type or "").strip().lower()
            if node_type in allowed_node_types:
                return allowed_node_types[node_type]
            if node_type in {"decision", "gateway"}:
                return "gateway"
            return "default"

        def normalize_shape(raw_shape: Any, node_type: Any) -> str:
            shape = str(raw_shape or "").strip().lower()
            node_type = str(node_type or "").strip().lower()

            if shape in self._ALLOWED_NODE_SHAPES:
                return shape

            alias_map = {
                "start": "start-event",
                "start_event": "start-event",
                "startevent": "start-event",
                "begin": "start-event",
                "end": "end-event",
                "end_event": "end-event",
                "endevent": "end-event",
                "stop": "end-event",
                "decision": "diamond",
                "gateway": "diamond",
                "rhombus": "diamond",
                "process": "task",
                "activity": "task",
                "service": "task",
                "rounded-rectangle": "task",
                "rounded_rectangle": "task",
                "hexagon": "rectangle",
                "parallelogram": "rectangle",
                "trapezoid": "rectangle",
                "cloud": "rectangle",
                "document": "rectangle",
                "cylinder": "rectangle",
                "square": "rectangle",
            }
            if shape in alias_map:
                return alias_map[shape]

            if node_type in {"start", "start-event"}:
                return "start-event"
            if node_type in {"end", "end-event"}:
                return "end-event"
            if node_type in {"gateway", "decision"}:
                return "diamond"
            return "task"

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

            original_node_type = n.get("type")
            n["type"] = normalize_node_type(original_node_type)
            if "data" not in n or not isinstance(n["data"], dict):
                n["data"] = {}
            if label_value is not None:
                n["data"].setdefault("label", label_value)
            n["data"].setdefault("label", n.get("id", "node"))
            if "shape" not in n["data"]:
                raw_type = str(original_node_type or "").strip().lower()
                if raw_type in {"start", "start-event"}:
                    n["data"]["shape"] = "start-event"
                elif raw_type in {"end", "end-event"}:
                    n["data"]["shape"] = "end-event"
                elif raw_type in {"decision", "gateway"}:
                    n["data"]["shape"] = "diamond"
                elif raw_type in {"task", "process", "subprocess"}:
                    n["data"]["shape"] = "task"
            n["data"]["shape"] = normalize_shape(n["data"].get("shape"), n.get("type"))
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
             "data": {"label": "Start", "shape": "start-event", "iconType": "play-circle", "color": c["start"]}},
            {"id": "client-1", "type": "client", "position": {"x": 240, "y": 200},
             "data": {"label": "Web Client"}},
            {"id": "gateway-1", "type": "gateway", "position": {"x": 460, "y": 200},
             "data": {"label": "API Gateway", "shape": "diamond"}},
            {"id": "service-1", "type": "service", "position": {"x": 720, "y": 120},
             "data": {"label": "Auth Service", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "cache-1", "type": "cache", "position": {"x": 720, "y": 300},
             "data": {"label": "Redis Cache"}},
            {"id": "service-2", "type": "service", "position": {"x": 980, "y": 200},
             "data": {"label": "Order Service", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "queue-1", "type": "queue", "position": {"x": 1240, "y": 200},
             "data": {"label": "Message Queue"}},
            {"id": "service-3", "type": "service", "position": {"x": 1500, "y": 200},
             "data": {"label": "Inventory Service", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "database-1", "type": "database", "position": {"x": 1760, "y": 200},
             "data": {"label": "MySQL"}},
            {"id": "end-1", "type": "default", "position": {"x": 2000, "y": 200},
             "data": {"label": "Done", "shape": "end-event", "iconType": "stop-circle", "color": c["end"]}},
        ]
        edges = [
            {"id": "e0", "source": "start-1", "target": "client-1", "label": "request"},
            {"id": "e1", "source": "client-1", "target": "gateway-1", "label": "HTTPS"},
            {"id": "e2", "source": "gateway-1", "target": "service-1", "label": "auth"},
            {"id": "e3", "source": "gateway-1", "target": "cache-1", "label": "cache"},
            {"id": "e4", "source": "service-1", "target": "service-2", "label": "ok"},
            {"id": "e5", "source": "cache-1", "target": "service-2", "label": "miss"},
            {"id": "e6", "source": "service-2", "target": "queue-1", "label": "enqueue"},
            {"id": "e7", "source": "queue-1", "target": "service-3", "label": "consume"},
            {"id": "e8", "source": "service-3", "target": "database-1", "label": "update"},
            {"id": "e9", "source": "database-1", "target": "end-1", "label": "response"},
        ]
        mermaid_code = """graph LR
    start-1((Start))
    client-1[Web Client]
    gateway-1{API Gateway}
    service-1[Auth Service]
    cache-1[Redis Cache]
    service-2[Order Service]
    queue-1[Message Queue]
    service-3[Inventory Service]
    database-1[(MySQL)]
    end-1((Done))
    start-1 --> client-1
    client-1 --> gateway-1
    gateway-1 --> service-1
    gateway-1 --> cache-1
    service-1 --> service-2
    cache-1 --> service-2
    service-2 --> queue-1
    queue-1 --> service-3
    service-3 --> database-1
    database-1 --> end-1"""
        return {"nodes": nodes, "edges": edges, "mermaid_code": mermaid_code}

    def _mock_high_concurrency(self):
        c = self._bpmn_colors()
        nodes = [
            {"id": "start-1", "type": "default", "position": {"x": 0, "y": 200},
             "data": {"label": "Start", "shape": "start-event", "iconType": "play-circle", "color": c["start"]}},
            {"id": "client-1", "type": "client", "position": {"x": 220, "y": 200},
             "data": {"label": "Mobile App"}},
            {"id": "gateway-1", "type": "gateway", "position": {"x": 460, "y": 200},
             "data": {"label": "Rate Limit?", "shape": "diamond"}},
            {"id": "cache-1", "type": "cache", "position": {"x": 700, "y": 120},
             "data": {"label": "Redis"}},
            {"id": "queue-1", "type": "queue", "position": {"x": 700, "y": 300},
             "data": {"label": "Kafka"}},
            {"id": "service-1", "type": "service", "position": {"x": 960, "y": 200},
             "data": {"label": "Order Service", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "database-1", "type": "database", "position": {"x": 1220, "y": 200},
             "data": {"label": "MySQL"}},
            {"id": "end-1", "type": "default", "position": {"x": 1460, "y": 200},
             "data": {"label": "Done", "shape": "end-event", "iconType": "stop-circle", "color": c["end"]}},
        ]
        edges = [
            {"id": "e0", "source": "start-1", "target": "client-1"},
            {"id": "e1", "source": "client-1", "target": "gateway-1", "label": "burst"},
            {"id": "e2", "source": "gateway-1", "target": "cache-1", "label": "hit"},
            {"id": "e3", "source": "gateway-1", "target": "queue-1", "label": "miss"},
            {"id": "e4", "source": "cache-1", "target": "service-1"},
            {"id": "e5", "source": "queue-1", "target": "service-1"},
            {"id": "e6", "source": "service-1", "target": "database-1"},
            {"id": "e7", "source": "database-1", "target": "end-1"},
        ]
        mermaid_code = """graph LR
    start-1((Start))
    client-1[Mobile App]
    gateway-1{Rate Limit?}
    cache-1[Redis]
    queue-1[Kafka]
    service-1[Order Service]
    database-1[(MySQL)]
    end-1((Done))
    start-1 --> client-1
    client-1 --> gateway-1
    gateway-1 -->|hit| cache-1
    gateway-1 -->|miss| queue-1
    cache-1 --> service-1
    queue-1 --> service-1
    service-1 --> database-1
    database-1 --> end-1"""
        return {"nodes": nodes, "edges": edges, "mermaid_code": mermaid_code}

    def _mock_oom_investigation(self):
        c = self._bpmn_colors()
        nodes = [
            {"id": "start-1", "type": "default", "position": {"x": 220, "y": 60},
             "data": {"label": "OOM Alert", "shape": "start-event", "iconType": "alert-circle", "color": c["start"]}},
            {"id": "step-1", "type": "default", "position": {"x": 220, "y": 180},
             "data": {"label": "Check heap usage", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "decision-1", "type": "gateway", "position": {"x": 220, "y": 300},
             "data": {"label": "Heap > 90%?", "shape": "diamond"}},
            {"id": "step-2", "type": "default", "position": {"x": 80, "y": 430},
             "data": {"label": "Create heap dump", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "step-3", "type": "default", "position": {"x": 360, "y": 430},
             "data": {"label": "Check direct memory", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "step-4", "type": "default", "position": {"x": 220, "y": 560},
             "data": {"label": "Analyze dump/threads", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "decision-2", "type": "gateway", "position": {"x": 220, "y": 690},
             "data": {"label": "Memory leak found?", "shape": "diamond"}},
            {"id": "step-5", "type": "default", "position": {"x": 80, "y": 820},
             "data": {"label": "Fix leak and rollback", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "step-6", "type": "default", "position": {"x": 360, "y": 820},
             "data": {"label": "Tune JVM and throttle", "shape": "task", "iconType": "box", "color": c["task"]}},
            {"id": "end-1", "type": "default", "position": {"x": 220, "y": 950},
             "data": {"label": "Verify recovery", "shape": "end-event", "iconType": "stop-circle", "color": c["end"]}},
        ]
        edges = [
            {"id": "e1", "source": "start-1", "target": "step-1"},
            {"id": "e2", "source": "step-1", "target": "decision-1"},
            {"id": "e3", "source": "decision-1", "target": "step-2", "label": "yes"},
            {"id": "e4", "source": "decision-1", "target": "step-3", "label": "no"},
            {"id": "e5", "source": "step-2", "target": "step-4"},
            {"id": "e6", "source": "step-3", "target": "step-4"},
            {"id": "e7", "source": "step-4", "target": "decision-2"},
            {"id": "e8", "source": "decision-2", "target": "step-5", "label": "yes"},
            {"id": "e9", "source": "decision-2", "target": "step-6", "label": "no"},
            {"id": "e10", "source": "step-5", "target": "end-1"},
            {"id": "e11", "source": "step-6", "target": "end-1"},
        ]
        mermaid_code = """graph TD
    start-1((OOM Alert))
    step-1[Check heap usage]
    decision-1{Heap > 90%?}
    step-2[Create heap dump]
    step-3[Check direct memory]
    step-4[Analyze dump/threads]
    decision-2{Memory leak found?}
    step-5[Fix leak and rollback]
    step-6[Tune JVM and throttle]
    end-1((Verify recovery))
    start-1 --> step-1
    step-1 --> decision-1
    decision-1 -->|yes| step-2
    decision-1 -->|no| step-3
    step-2 --> step-4
    step-3 --> step-4
    step-4 --> decision-2
    decision-2 -->|yes| step-5
    decision-2 -->|no| step-6
    step-5 --> end-1
    step-6 --> end-1"""
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
    # 婢х偤鍣洪悽鐔稿灇鏉堝懎濮弬瑙勭《 (Incremental Generation Helpers)
    # ============================================================

    def _build_architecture_description(
        self,
        nodes: List[Node],
        edges: List[Edge]
    ) -> str:
        node_count = len(nodes)
        edge_count = len(edges)
        type_counts: Dict[str, int] = {}
        for node in nodes:
            node_type = node.type or "default"
            type_counts[node_type] = type_counts.get(node_type, 0) + 1

        lines = [
            f"Total nodes: {node_count}",
            f"Total edges: {edge_count}",
            "Node type distribution:",
        ]
        for key in sorted(type_counts.keys()):
            lines.append(f"- {key}: {type_counts[key]}")

        return "\n".join(lines)

    def _build_incremental_prompt(
        self,
        request: ChatGenerationRequest,
        existing_nodes: List[Node],
        existing_edges: List[Edge]
    ) -> str:
        existing_ids = [n.id for n in existing_nodes]
        max_x = max((n.position.x for n in existing_nodes), default=0)
        max_y = max((n.position.y for n in existing_nodes), default=0)
        min_y = min((n.position.y for n in existing_nodes), default=0)
        node_count = len(existing_nodes)
        edge_count = len(existing_edges)
        timestamp = int(time.time())

        node_type_summary: Dict[str, int] = {}
        for node in existing_nodes:
            node_type = node.type or "default"
            node_type_summary[node_type] = node_type_summary.get(node_type, 0) + 1

        type_lines = "\n".join([f"- {k}: {v}" for k, v in sorted(node_type_summary.items())])
        existing_json = json.dumps(
            {
                "nodes": [n.model_dump() for n in existing_nodes],
                "edges": [e.model_dump() for e in existing_edges],
            },
            ensure_ascii=False,
            indent=2,
        )

        return (
            f"You are an expert systems architect doing incremental updates.\n"
            f"Keep all existing nodes/edges unchanged and add only new content.\n"
            f"Existing node IDs: {', '.join(existing_ids[:15])}{'...' if len(existing_ids) > 15 else ''}\n"
            f"Existing bounds: x=[0,{max_x}], y=[{min_y},{max_y}]\n"
            f"New nodes should be placed at x >= {max_x + 280}.\n"
            f"Current graph stats: nodes={node_count}, edges={edge_count}\n"
            f"Node types:\n{type_lines}\n\n"
            f"Current graph JSON:\n{existing_json}\n\n"
            f"User request: {request.user_input}\n"
            f"New node IDs must follow <type>-{timestamp}-<n>.\n"
            f"Return only valid JSON with full nodes and edges arrays."
        )

    def _extract_semantic_keywords(self, label: str) -> set:
        import re

        noise_words = {
            "service", "module", "layer", "system", "component",
            "api", "db", "database", "server", "with", "from", "into",
        }

        words = set()
        for word in re.findall(r"[A-Za-z]+", (label or "").lower()):
            if len(word) > 2 and word not in noise_words:
                words.add(word)

        for chunk in re.findall(r"[\u4e00-\u9fff]+", label or ""):
            if len(chunk) >= 2:
                words.add(chunk)

        return words

    def _validate_semantic_coverage(self, original_nodes: List[Node], final_nodes: List[Node]) -> bool:
        original_keywords = set()
        final_keywords = set()

        for node in original_nodes:
            original_keywords.update(self._extract_semantic_keywords(node.data.label))

        for node in final_nodes:
            final_keywords.update(self._extract_semantic_keywords(node.data.label))

        if not original_keywords:
            return True

        coverage = len(original_keywords.intersection(final_keywords)) / max(len(original_keywords), 1)
        logger.info("Semantic coverage: %.2f", coverage)
        return coverage >= 0.8

    def _validate_incremental_result(
        self,
        original_nodes: List[Node],
        ai_nodes: List[Node]
    ) -> List[Node]:
        original_map = {n.id: n for n in original_nodes}
        ai_map = {n.id: n for n in ai_nodes}

        for node_id, node in original_map.items():
            if node_id not in ai_map:
                ai_nodes.append(node)

        ai_map = {n.id: n for n in ai_nodes}
        for node_id, original in original_map.items():
            if node_id not in ai_map:
                continue
            current = ai_map[node_id]
            current.type = original.type
            current.data.label = original.data.label
            current.position = original.position

        seen_ids = set()
        deduped = []
        for idx, node in enumerate(ai_nodes):
            if node.id in seen_ids:
                node.id = f"{node.id}-dup-{idx}"
            seen_ids.add(node.id)
            deduped.append(node)

        return self._resolve_position_overlaps(deduped)

    def _resolve_position_overlaps(self, nodes: List[Node]) -> List[Node]:
        overlap_threshold = 100
        for i, node in enumerate(nodes):
            for other in nodes[:i]:
                distance = math.sqrt(
                    (node.position.x - other.position.x) ** 2 +
                    (node.position.y - other.position.y) ** 2
                )
                if distance < overlap_threshold:
                    node.position.x += 260
                    node.position.y += 30
        return nodes

    def _merge_edges(self, original_edges: List[Edge], ai_edges: List[Edge]) -> List[Edge]:
        merged = list(original_edges)
        existing_signatures = {(e.source, e.target) for e in original_edges}
        for edge in ai_edges:
            sig = (edge.source, edge.target)
            if sig not in existing_signatures:
                merged.append(edge)
                existing_signatures.add(sig)
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

            # 閼惧嘲褰囬張澶嬫櫏闁板秶鐤嗛敍鍫滅喘閸忓牅濞囬悽銊ょ炊閸忋儱寮弫甯礉閸氾箑鍨担璺ㄦ暏姒涙妫板嫯閿?
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

            config_candidates = [config]
            config_candidates.extend(
                presets_service.get_failover_configs(primary_config=config, max_candidates=3)
            )
            logger.info(
                "[CHAT-GEN] Config candidates prepared: %s",
                [
                    f"{item.get('provider')}:{item.get('model_name')}@{item.get('base_url') or '-'}"
                    for item in config_candidates
                ],
            )
            # 棣冨晭 婢х偤鍣洪悽鐔稿灇濡€崇础閿涙碍閺屻儱鑻熼懢宄板絿閻滅増婀侀弸鑸电€?
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

            # 閺嬪嫬缂?Prompt閿涘牆闁插繑鍨ㄩ崗銊︽煀閿?
            prompt_request = request.model_copy(update={"diagram_type": effective_diagram_type})
            if request.incremental_mode and existing_nodes:
                logger.info("[INCREMENTAL] Building incremental prompt")
                prompt = self._build_incremental_prompt(prompt_request, existing_nodes, existing_edges)
            else:
                prompt = self._build_generation_prompt(prompt_request)

            logger.info(f"[CHAT-GEN] Calling AI with provider: {selected_provider}")
            logger.info(f"[CHAT-GEN] Prompt (first 200 chars): {prompt[:200]}...")

            ai_raw: Any = None
            attempt_errors: List[Dict[str, Any]] = []

            for attempt_index, attempt_config in enumerate(config_candidates, start=1):
                attempt_provider = attempt_config.get("provider") or selected_provider
                attempt_model = attempt_config.get("model_name") or ""
                attempt_base = attempt_config.get("base_url") or ""
                try:
                    logger.info(
                        "[CHAT-GEN] Attempt %s/%s via provider=%s model=%s base=%s",
                        attempt_index,
                        len(config_candidates),
                        attempt_provider,
                        attempt_model,
                        attempt_base or "-",
                    )
                    vision_service = create_vision_service(
                        provider=attempt_provider,
                        api_key=attempt_config.get("api_key"),
                        base_url=attempt_config.get("base_url"),
                        model_name=attempt_config.get("model_name"),
                    )
                    ai_raw = await self._call_ai_text_generation(vision_service, prompt, attempt_provider)
                    selected_provider = attempt_provider
                    config = attempt_config
                    if attempt_index > 1:
                        logger.warning(
                            "[CHAT-GEN] Provider failover succeeded on attempt %s (%s/%s)",
                            attempt_index,
                            attempt_provider,
                            attempt_model,
                        )
                    break
                except Exception as provider_error:
                    status_code, error_code = self._classify_provider_error(provider_error)
                    attempt_errors.append({
                        "provider": attempt_provider,
                        "model_name": attempt_model,
                        "status_code": status_code,
                        "error_code": error_code,
                        "detail": str(provider_error),
                    })
                    logger.warning(
                        "[CHAT-GEN] Attempt %s failed (%s/%s): %s",
                        attempt_index,
                        status_code,
                        error_code,
                        provider_error,
                    )
                    if (
                        attempt_index < len(config_candidates)
                        and self._is_retryable_provider_error(provider_error)
                    ):
                        continue

            if ai_raw is None:
                status_priority = [429, 401, 503, 504, 500]
                chosen_status = 500
                for status in status_priority:
                    if any(err.get("status_code") == status for err in attempt_errors):
                        chosen_status = status
                        break

                summary = "; ".join(
                    f"{err['provider']}/{err['model_name']} -> {err['status_code']}:{err['error_code']}"
                    for err in attempt_errors
                )[:600]
                last_detail = attempt_errors[-1]["detail"][:240] if attempt_errors else "unknown upstream error"
                raise HTTPException(
                    status_code=chosen_status,
                    detail=(
                        f"AI generation failed after {len(attempt_errors)} attempts. "
                        f"Summary: {summary}. Last error: {last_detail}"
                    ),
                )

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

            # 棣冨晭 婢х偤鍣哄Ο鈥崇础妤犲矁鐦夐崪灞芥値楠?
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

            # 棣冨晭 閺囧瓨鏌婃导姘崇樈閿涘牆闁插繑膩瀵繑鍨ㄦ＃鏍ㄦ穱婵嗙摠閿?
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
                session_id=session_id  # 棣冨晭 鏉╂柨娲?session_id
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Flowchart generation failed: {e}", exc_info=True)
            status_code, error_code = self._classify_provider_error(e)
            raise HTTPException(
                status_code=status_code,
                detail=f"AI generation failed ({error_code}): {str(e)}. Please check model configuration and retry."
            )


def create_chat_generator_service() -> ChatGeneratorService:
    """Create service instance."""
    return ChatGeneratorService()







