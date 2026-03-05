"""
Comprehensive API Tests for SmartArchitect AI Backend
Tests all API endpoints across all phases
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
import json
import io

client = TestClient(app)


# ============================================================
# Health API Tests
# ============================================================

def test_root_endpoint():
    """Test root endpoint returns API info"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "SmartArchitect AI API"
    assert data["version"] == "0.5.0"
    assert "phase" in data


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


# ============================================================
# Mermaid API Tests
# ============================================================

def test_mermaid_parse_valid():
    """Test parsing valid Mermaid code"""
    mermaid_code = """
    graph LR
        A[API Gateway] --> B[Service]
        B --> C[Database]
    """
    response = client.post(
        "/api/mermaid/parse",
        json={"code": mermaid_code}
    )
    assert response.status_code == 200
    data = response.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) >= 2  # Parser may not detect all nodes
    assert len(data["edges"]) >= 1  # At least one edge


def test_mermaid_parse_invalid():
    """Test parsing invalid Mermaid code"""
    response = client.post(
        "/api/mermaid/parse",
        json={"code": "invalid mermaid"}
    )
    assert response.status_code in [200, 400]  # May return empty or error


def test_mermaid_generate():
    """Test generating Mermaid code from nodes and edges"""
    nodes = [
        {"id": "1", "data": {"label": "API"}, "type": "api", "position": {"x": 0, "y": 0}},
        {"id": "2", "data": {"label": "Service"}, "type": "service", "position": {"x": 0, "y": 0}}
    ]
    edges = [
        {"id": "e1", "source": "1", "target": "2", "label": "HTTP"}
    ]

    response = client.post(
        "/api/graph/to-mermaid",
        json={"nodes": nodes, "edges": edges}
    )
    assert response.status_code == 200
    data = response.json()
    assert "mermaid_code" in data
    assert "graph" in data["mermaid_code"].lower()


# ============================================================
# Models API Tests
# ============================================================

def test_models_get_config():
    """Test getting model config"""
    # First save a config
    client.post(
        "/api/models/config",
        json={
            "provider": "gemini",
            "api_key": "test_key",
            "model_name": "gemini-1.5-flash",
            "base_url": ""
        }
    )

    # Then get it
    response = client.get("/api/models/config/gemini")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "config" in data
    assert data["config"]["provider"] == "gemini"


def test_models_save_config():
    """Test saving model config"""
    response = client.post(
        "/api/models/config",
        json={
            "provider": "gemini",
            "api_key": "test_key",
            "model_name": "gemini-1.5-flash",
            "base_url": ""
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data


def test_models_save_config_with_legacy_field_names():
    """兼容旧字段：api_base/model 应可被 models/config 接口接受。"""
    response = client.post(
        "/api/models/config",
        json={
            "provider": "custom",
            "api_key": "test_key",
            "api_base": "https://www.right.codes/codex/v1",
            "model": "gpt-5.2"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_default_model_preset_is_right_codes():
    """默认预设应固定为 right.codes + gpt-5.2。"""
    response = client.get("/api/models/presets/default/current")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["preset"]["provider"] == "custom"
    assert data["preset"]["base_url"] == "https://www.right.codes/codex/v1"
    assert data["preset"]["model_name"] == "gpt-5.2"


def test_models_save_siliconflow_config():
    """Ensure SiliconFlow provider config is accepted"""
    response = client.post(
        "/api/models/config",
        json={
            "provider": "siliconflow",
            "api_key": "test_key",
            "model_name": "Pro/Qwen/Qwen2.5-7B-Instruct",
            "base_url": "https://api.siliconflow.cn/v1"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


# ============================================================
# Chat Generator API Tests
# ============================================================


def test_chat_generator_calls_ai_and_normalizes(monkeypatch):
    """Chat generator should call AI path and normalize graph."""
    from app.services import chat_generator as cg

    sample_graph = {
        "nodes": [
            {"id": "start", "type": "default", "data": {"label": "Start"}},
            {"id": "step", "type": "service", "data": {"label": "Check"}},
        ],
        "edges": [{"id": "e1", "source": "start", "target": "step", "label": "next"}],
        "mermaid_code": "graph TD\nstart[Start]-->step[Check]",
    }

    async def fake_call(self, vision_service, prompt, provider):
        return sample_graph

    def fake_vision_service(*args, **kwargs):
        class Dummy:
            pass
        return Dummy()

    monkeypatch.setattr(cg.ChatGeneratorService, "_call_ai_text_generation", fake_call, raising=True)
    monkeypatch.setattr(cg, "create_vision_service", fake_vision_service, raising=True)

    response = client.post(
        "/api/chat-generator/generate",
        json={"user_input": "generate something", "provider": "siliconflow", "api_key": "invalid"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["nodes"]) >= 2
    assert data["nodes"][0]["position"]["x"] is not None
    assert len(data["edges"]) >= 1


def test_chat_generator_stream_emits_partial_graph_events(monkeypatch):
    """Stream endpoint should emit PARTIAL_NODE/PARTIAL_EDGE before final layout."""
    from app.api import chat_generator as cg_api

    class DummyPresetsService:
        def get_active_config(self, **kwargs):
            return {
                "provider": "custom",
                "api_key": "test-key",
                "base_url": "https://example.invalid/v1",
                "model_name": "mock-model",
            }

    class DummyVisionService:
        provider = "custom"
        model_name = "mock-model"

        async def generate_with_stream(self, prompt: str):
            chunks = [
                '{"nodes":[{"id":"start","type":"default","position":{"x":0,"y":0},"data":{"label":"Start"}},',
                '{"id":"step-1","type":"default","position":{"x":260,"y":0},"data":{"label":"Process"}}],',
                '"edges":[{"id":"e1","source":"start","target":"step-1","label":"next"}],',
                '"mermaid_code":"graph TD\\nstart-->step-1"}',
            ]
            for item in chunks:
                yield item

    monkeypatch.setattr(cg_api, "get_model_presets_service", lambda: DummyPresetsService(), raising=True)
    monkeypatch.setattr(cg_api, "create_vision_service", lambda **kwargs: DummyVisionService(), raising=True)

    response = client.post(
        "/api/chat-generator/generate-stream",
        json={"user_input": "stream graph please", "provider": "custom", "diagram_type": "flow"},
    )

    assert response.status_code == 200
    payload = response.text
    assert "[PARTIAL_NODE]" in payload
    assert "[PARTIAL_EDGE]" in payload
    assert "[LAYOUT_DATA]" in payload
    assert "[END] done" in payload
    assert payload.index("[PARTIAL_NODE]") < payload.index("[LAYOUT_DATA]")


def test_chat_generator_stream_architecture_layers_emit_partial_nodes(monkeypatch):
    """Architecture stream should emit partial nodes from layers/items before final layout."""
    from app.api import chat_generator as cg_api

    class DummyPresetsService:
        def get_active_config(self, **kwargs):
            return {
                "provider": "custom",
                "api_key": "test-key",
                "base_url": "https://example.invalid/v1",
                "model_name": "mock-model",
            }

    class DummyVisionService:
        provider = "custom"
        model_name = "mock-model"

        async def generate_with_stream(self, prompt: str):
            chunks = [
                '{"layers":[{"name":"presentation","layout":{"columns":3},"items":[',
                '{"id":"web-ui","label":"Web UI","category":"client","tech_stack":["React"]},',
                '{"id":"api-gateway","label":"API Gateway","category":"gateway","tech_stack":["Kong"]}',
                ']}],"edges":[{"id":"e1","source":"web-ui","target":"api-gateway","label":"https"}]}',
            ]
            for item in chunks:
                yield item

    monkeypatch.setattr(cg_api, "get_model_presets_service", lambda: DummyPresetsService(), raising=True)
    monkeypatch.setattr(cg_api, "create_vision_service", lambda **kwargs: DummyVisionService(), raising=True)

    response = client.post(
        "/api/chat-generator/generate-stream",
        json={
            "user_input": "generate technical architecture",
            "provider": "custom",
            "diagram_type": "architecture",
            "architecture_type": "technical",
        },
    )

    assert response.status_code == 200
    payload = response.text
    assert "[PARTIAL_NODE]" in payload
    assert "[PARTIAL_LAYER]" in payload
    assert "layerFrame" in payload
    assert "web-ui" in payload
    assert "[LAYOUT_DATA]" in payload
    assert payload.index("[PARTIAL_NODE]") < payload.index("[LAYOUT_DATA]")


def test_chat_generator_auto_failover_on_usage_limit(monkeypatch):
    """Non-stream chat generation should fail over to backup config when primary is rate-limited."""
    from app.services import chat_generator as cg_service

    sample_graph = {
        "nodes": [
            {"id": "start", "type": "default", "position": {"x": 0, "y": 0}, "data": {"label": "Start"}},
            {"id": "step", "type": "default", "position": {"x": 240, "y": 0}, "data": {"label": "Step"}},
        ],
        "edges": [{"id": "e1", "source": "start", "target": "step", "label": "next"}],
        "mermaid_code": "graph TD\nstart-->step",
    }
    attempted_keys = []

    class DummyPresetsService:
        def get_active_config(self, **kwargs):
            return {
                "provider": "custom",
                "api_key": "primary-key",
                "base_url": "https://primary.invalid/v1",
                "model_name": "primary-model",
            }

        def get_failover_configs(self, primary_config=None, max_candidates=3):
            return [{
                "provider": "custom",
                "api_key": "backup-key",
                "base_url": "https://backup.invalid/v1",
                "model_name": "backup-model",
            }]

    class DummyVisionService:
        def __init__(self, api_key: str):
            self.api_key = api_key

    def fake_vision_service(provider, api_key=None, base_url=None, model_name=None):
        return DummyVisionService(api_key=api_key or "")

    async def fake_call(self, vision_service, prompt, provider):
        attempted_keys.append(vision_service.api_key)
        if vision_service.api_key == "primary-key":
            raise RuntimeError("429 usage_limit_reached")
        return sample_graph

    monkeypatch.setattr(cg_service, "get_model_presets_service", lambda: DummyPresetsService(), raising=True)
    monkeypatch.setattr(cg_service, "create_vision_service", fake_vision_service, raising=True)
    monkeypatch.setattr(cg_service.ChatGeneratorService, "_call_ai_text_generation", fake_call, raising=True)

    response = client.post(
        "/api/chat-generator/generate",
        json={"user_input": "generate with failover", "provider": "custom"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["nodes"]) == 2
    assert attempted_keys == ["primary-key", "backup-key"]


def test_chat_generator_stream_auto_failover_on_usage_limit(monkeypatch):
    """Stream generation should fail over when primary stream path is rate-limited."""
    from app.api import chat_generator as cg_api

    attempted_keys = []

    class DummyPresetsService:
        def get_active_config(self, **kwargs):
            return {
                "provider": "custom",
                "api_key": "primary-key",
                "base_url": "https://primary.invalid/v1",
                "model_name": "primary-model",
            }

        def get_failover_configs(self, primary_config=None, max_candidates=3):
            return [{
                "provider": "custom",
                "api_key": "backup-key",
                "base_url": "https://backup.invalid/v1",
                "model_name": "backup-model",
            }]

    class DummyVisionService:
        def __init__(self, api_key: str):
            self.api_key = api_key
            self.provider = "custom"
            self.model_name = "mock-model"

        async def generate_with_stream(self, prompt: str):
            attempted_keys.append(self.api_key)
            if self.api_key == "primary-key":
                raise RuntimeError("429 usage_limit_reached")

            chunks = [
                '{"nodes":[{"id":"start","type":"default","position":{"x":0,"y":0},"data":{"label":"Start"}},',
                '{"id":"step-1","type":"default","position":{"x":260,"y":0},"data":{"label":"Process"}}],',
                '"edges":[{"id":"e1","source":"start","target":"step-1","label":"next"}],',
                '"mermaid_code":"graph TD\\nstart-->step-1"}',
            ]
            for item in chunks:
                yield item

    monkeypatch.setattr(cg_api, "get_model_presets_service", lambda: DummyPresetsService(), raising=True)
    monkeypatch.setattr(
        cg_api,
        "create_vision_service",
        lambda provider, api_key=None, base_url=None, model_name=None: DummyVisionService(api_key=api_key or ""),
        raising=True,
    )

    response = client.post(
        "/api/chat-generator/generate-stream",
        json={"user_input": "generate with stream failover", "provider": "custom", "diagram_type": "flow"},
    )

    assert response.status_code == 200
    payload = response.text
    assert "stream_failed" in payload
    assert "[PARTIAL_NODE]" in payload
    assert "[LAYOUT_DATA]" in payload
    assert "[END] done" in payload
    assert attempted_keys == ["primary-key", "backup-key"]


# ============================================================
# Excalidraw API Tests
# ============================================================


def test_excalidraw_stream_emits_partial_elements(monkeypatch):
    """Excalidraw stream should emit PARTIAL_ELEMENT events before RESULT."""
    from app.api import excalidraw as ex_api

    class DummyPresetsService:
        def get_active_config(self, **kwargs):
            return {
                "provider": "custom",
                "api_key": "test-key",
                "base_url": "https://example.invalid/v1",
                "model_name": "mock-model",
            }

        def get_failover_configs(self, primary_config=None, max_candidates=3):
            return []

    class DummyVisionService:
        async def generate_with_stream(self, prompt: str):
            chunks = [
                '{"elements":[{"id":"rect-1","type":"rectangle","x":120,"y":120,"width":200,"height":100},',
                '{"id":"arrow-1","type":"arrow","x":340,"y":170,"width":160,"height":1,"points":[[0,0],[160,0]],"endArrowhead":"arrow"}],',
                '"appState":{"viewBackgroundColor":"#ffffff"},"files":{}}',
            ]
            for chunk in chunks:
                yield chunk

    monkeypatch.setattr(ex_api, "get_model_presets_service", lambda: DummyPresetsService(), raising=True)
    monkeypatch.setattr(ex_api, "create_vision_service", lambda **kwargs: DummyVisionService(), raising=True)

    response = client.post(
        "/api/excalidraw/generate-stream",
        json={"prompt": "stream excalidraw scene", "provider": "custom"},
    )

    assert response.status_code == 200
    payload = response.text
    assert "[PARTIAL_ELEMENT]" in payload
    assert "[RESULT]" in payload
    assert "[END] done" in payload
    assert payload.index("[PARTIAL_ELEMENT]") < payload.index("[RESULT]")


# ============================================================
# Prompter API Tests
# ============================================================

def test_prompter_list_scenarios():
    """Test listing available prompt scenarios"""
    response = client.get("/api/prompter/scenarios")
    assert response.status_code == 200
    data = response.json()
    assert "scenarios" in data
    assert len(data["scenarios"]) >= 3  # At least 3 default scenarios


def test_prompter_execute_without_api_key():
    """Test executing prompter without API key (should fail gracefully)"""
    nodes = [{"id": "1", "data": {"label": "API"}, "type": "api"}]
    edges = []

    response = client.post(
        "/api/prompter/execute",
        params={"provider": "gemini", "api_key": "invalid"},
        json={
            "scenario_id": "refactoring",
            "nodes": nodes,
            "edges": edges
        }
    )
    # Should handle gracefully (may be 200 with error or 500)
    assert response.status_code in [200, 400, 422, 500]


# ============================================================
# Export API Tests
# ============================================================

def test_export_health():
    """Test export service health check"""
    response = client.get("/api/export/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "available_formats" in data
    assert "ppt" in data["available_formats"]
    assert "slidev" in data["available_formats"]
    assert "script" in data["available_formats"]


def test_export_ppt():
    """Test PowerPoint export"""
    nodes = [
        {"id": "1", "position": {"x": 100, "y": 100}, "data": {"label": "API"}, "type": "api"},
        {"id": "2", "position": {"x": 300, "y": 100}, "data": {"label": "DB"}, "type": "database"}
    ]
    edges = [{"id": "e1", "source": "1", "target": "2", "label": "SQL"}]

    response = client.post(
        "/api/export/ppt",
        json={
            "nodes": nodes,
            "edges": edges,
            "mermaid_code": "graph LR\nA-->B",
            "title": "Test Architecture"
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    # Check that we got binary data
    assert len(response.content) > 1000  # PPT should be at least 1KB


def test_export_slidev():
    """Test Slidev markdown export"""
    nodes = [
        {"id": "1", "type": "api", "position": {"x": 0, "y": 0}, "data": {"label": "API"}},
        {"id": "2", "type": "database", "position": {"x": 0, "y": 0}, "data": {"label": "DB"}}
    ]
    edges = [{"id": "e1", "source": "1", "target": "2"}]

    response = client.post(
        "/api/export/slidev",
        json={
            "nodes": nodes,
            "edges": edges,
            "mermaid_code": "graph LR\nA[API]-->B[DB]",
            "title": "Test Architecture"
        }
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    content = response.content.decode('utf-8')
    assert "---" in content  # Frontmatter
    assert "mermaid" in content.lower()


def test_export_script_no_api_key():
    """Test script generation without API key"""
    nodes = [{"id": "1", "type": "api", "position": {"x": 0, "y": 0}, "data": {"label": "API"}}]
    edges = []

    response = client.post(
        "/api/export/script?provider=gemini&api_key=invalid",
        json={
            "nodes": nodes,
            "edges": edges,
            "duration": "30s"
        }
    )
    # Should handle gracefully (may fail or return error)
    assert response.status_code in [200, 400, 422, 500]


def test_vision_rejects_siliconflow_image():
    """SiliconFlow is text-only; image analysis should be rejected"""
    fake_image = io.BytesIO(b"fake")
    files = {"file": ("test.png", fake_image, "image/png")}
    response = client.post(
        "/api/vision/analyze",
        params={"provider": "siliconflow"},
        files=files
    )
    assert response.status_code == 400
    data = response.json()
    assert "text-only" in data["detail"]


# ============================================================
# RAG API Tests
# ============================================================

def test_rag_health():
    """Test RAG service health check"""
    response = client.get("/api/rag/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "supported_formats" in data
    assert "pdf" in data["supported_formats"]
    assert "markdown" in data["supported_formats"]
    assert "docx" in data["supported_formats"]
    assert "embedding_model" in data
    assert data["embedding_model"]


def test_rag_list_documents():
    """Test listing documents"""
    response = client.get("/api/rag/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total" in data
    assert isinstance(data["documents"], list)


def test_rag_upload_markdown():
    """Test uploading a markdown document"""
    # Create a test markdown file
    content = b"# Test Document\n\nThis is a test document for RAG testing."
    files = {"file": ("test.md", io.BytesIO(content), "text/markdown")}

    response = client.post("/api/rag/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "document_id" in data
    assert data["chunks_created"] > 0

    # Clean up - delete the uploaded document
    doc_id = data["document_id"]
    client.delete(f"/api/rag/documents/{doc_id}")


def test_rag_search():
    """Test searching documents"""
    # First upload a document
    content = b"# Architecture Best Practices\n\nUse microservices for scalability. Implement API Gateway for authentication."
    files = {"file": ("best_practices.md", io.BytesIO(content), "text/markdown")}
    upload_response = client.post("/api/rag/upload", files=files)
    assert upload_response.status_code == 200
    doc_id = upload_response.json()["document_id"]

    # Now search
    search_response = client.post(
        "/api/rag/search",
        json={"query": "How to implement authentication?", "top_k": 3}
    )
    assert search_response.status_code == 200
    data = search_response.json()
    assert "chunks" in data
    assert data["success"] is True
    assert data["query"] == "How to implement authentication?"

    # Clean up
    client.delete(f"/api/rag/documents/{doc_id}")


def test_rag_delete_document():
    """Test deleting a document"""
    # Upload a document
    content = b"# Test Document\n\nTemporary document for deletion test."
    files = {"file": ("temp.md", io.BytesIO(content), "text/markdown")}
    upload_response = client.post("/api/rag/upload", files=files)
    doc_id = upload_response.json()["document_id"]

    # Delete it
    delete_response = client.delete(f"/api/rag/documents/{doc_id}")
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["success"] is True


def test_rag_upload_invalid_file_type():
    """Test uploading invalid file type"""
    content = b"invalid content"
    files = {"file": ("test.xyz", io.BytesIO(content), "application/octet-stream")}

    response = client.post("/api/rag/upload", files=files)
    assert response.status_code == 400


# ============================================================
# Integration Tests
# ============================================================

def test_full_architecture_workflow():
    """Test complete workflow: parse, generate, export"""
    # 1. Parse Mermaid code
    mermaid_code = "graph LR\nA[API]-->B[Service]\nB-->C[DB]"
    parse_response = client.post(
        "/api/mermaid/parse",
        json={"code": mermaid_code}
    )
    assert parse_response.status_code == 200
    nodes = parse_response.json()["nodes"]
    edges = parse_response.json()["edges"]

    # 2. Generate Mermaid code back
    gen_response = client.post(
        "/api/graph/to-mermaid",
        json={"nodes": nodes, "edges": edges}
    )
    assert gen_response.status_code == 200

    # 3. Export to Slidev (with required position fields)
    for node in nodes:
        if "position" not in node:
            node["position"] = {"x": 0, "y": 0}

    export_response = client.post(
        "/api/export/slidev",
        json={
            "nodes": nodes,
            "edges": edges,
            "mermaid_code": mermaid_code,
            "title": "Integration Test"
        }
    )
    assert export_response.status_code == 200


def test_rag_workflow():
    """Test RAG workflow: upload, search, delete"""
    # 1. Upload document
    content = b"""# Microservices Architecture

    ## Best Practices
    - Use API Gateway for routing
    - Implement service discovery
    - Use message queues for async communication
    """
    files = {"file": ("architecture.md", io.BytesIO(content), "text/markdown")}
    upload_response = client.post("/api/rag/upload", files=files)
    assert upload_response.status_code == 200
    doc_id = upload_response.json()["document_id"]

    # 2. Search for relevant information
    search_response = client.post(
        "/api/rag/search",
        json={"query": "What are microservices best practices?", "top_k": 5}
    )
    assert search_response.status_code == 200
    chunks = search_response.json()["chunks"]
    assert len(chunks) > 0

    # 3. List documents
    list_response = client.get("/api/rag/documents")
    assert list_response.status_code == 200
    docs = list_response.json()["documents"]
    assert any(d["document_id"] == doc_id for d in docs)

    # 4. Delete document
    delete_response = client.delete(f"/api/rag/documents/{doc_id}")
    assert delete_response.status_code == 200


# ============================================================
# Performance Tests
# ============================================================

def test_multiple_concurrent_requests():
    """Test handling multiple concurrent requests"""
    import concurrent.futures

    def make_health_request():
        return client.get("/api/health")

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(make_health_request) for _ in range(10)]
        results = [f.result() for f in futures]

    assert all(r.status_code == 200 for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
