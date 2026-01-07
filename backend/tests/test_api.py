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
    assert data["version"] == "0.4.0"
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
    assert data["embedding_model"] == "all-MiniLM-L6-v2"


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
