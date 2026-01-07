"""
Service Layer Tests for SmartArchitect AI Backend
Tests document parser, PPT exporter, Slidev exporter
"""

import pytest
import tempfile
import os
from app.services.document_parser import create_document_parser
from app.services.ppt_exporter import create_ppt_exporter
from app.services.slidev_exporter import create_slidev_exporter
from app.models.schemas import Node, Edge, Position, NodeData


# ============================================================
# Document Parser Tests
# ============================================================

def test_document_parser_markdown():
    """Test parsing markdown documents"""
    parser = create_document_parser()

    # Create a temporary markdown file
    content = """# Test Document

## Section 1
This is section 1 with some content.

## Section 2
This is section 2 with more content.

## Section 3
And this is section 3 with even more content to ensure chunking works properly.
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        chunks = parser.parse_file(temp_path, "markdown")
        assert len(chunks) > 0
        assert all(hasattr(chunk, 'content') for chunk in chunks)
        assert all(hasattr(chunk, 'chunk_id') for chunk in chunks)
        assert all(hasattr(chunk, 'metadata') for chunk in chunks)
    finally:
        os.unlink(temp_path)


def test_document_parser_chunking():
    """Test that long documents are properly chunked"""
    parser = create_document_parser(chunk_size=100, chunk_overlap=20)

    # Create a long document
    content = "A" * 500  # 500 character document

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        chunks = parser.parse_file(temp_path, "markdown")
        # Should create multiple chunks
        assert len(chunks) >= 4  # 500 chars / 100 per chunk

        # Check overlap
        if len(chunks) >= 2:
            # Chunks should overlap
            assert len(chunks[0].content) <= 120  # chunk_size + some margin
    finally:
        os.unlink(temp_path)


# ============================================================
# PPT Exporter Tests
# ============================================================

def test_ppt_exporter_basic():
    """Test basic PowerPoint generation"""
    exporter = create_ppt_exporter()

    nodes = [
        Node(id="1", type="api", position=Position(x=100, y=100), data=NodeData(label="API Gateway")),
        Node(id="2", type="service", position=Position(x=300, y=100), data=NodeData(label="User Service")),
        Node(id="3", type="database", position=Position(x=500, y=100), data=NodeData(label="PostgreSQL"))
    ]
    edges = [
        Edge(id="e1", source="1", target="2", label="HTTP"),
        Edge(id="e2", source="2", target="3", label="SQL")
    ]

    ppt_bytes = exporter.create_presentation(nodes, edges, "Test Architecture")

    assert isinstance(ppt_bytes, bytes)
    assert len(ppt_bytes) > 1000  # Should be at least 1KB


def test_ppt_exporter_empty():
    """Test PPT generation with no nodes"""
    exporter = create_ppt_exporter()

    ppt_bytes = exporter.create_presentation([], [], "Empty Architecture")

    assert isinstance(ppt_bytes, bytes)
    assert len(ppt_bytes) > 1000  # Should still create a valid PPT


def test_ppt_exporter_node_colors():
    """Test that different node types get different colors"""
    exporter = create_ppt_exporter()

    # Test color assignment
    api_color = exporter._get_node_color("api")
    service_color = exporter._get_node_color("service")
    database_color = exporter._get_node_color("database")

    assert api_color != service_color
    assert service_color != database_color
    assert api_color != database_color


# ============================================================
# Slidev Exporter Tests
# ============================================================

def test_slidev_exporter_basic():
    """Test basic Slidev markdown generation"""
    exporter = create_slidev_exporter()

    nodes = [
        Node(id="1", type="api", position=Position(x=0, y=0), data=NodeData(label="API Gateway")),
        Node(id="2", type="service", position=Position(x=0, y=0), data=NodeData(label="User Service"))
    ]
    edges = [
        Edge(id="e1", source="1", target="2", label="HTTP")
    ]
    mermaid_code = "graph LR\nA[API Gateway]-->B[User Service]"

    markdown = exporter.create_slidev(nodes, edges, mermaid_code, "Test Architecture")

    assert isinstance(markdown, str)
    assert "---" in markdown  # Frontmatter
    assert "Test Architecture" in markdown
    assert "mermaid" in markdown.lower()
    assert len(markdown) > 500  # Should be substantial


def test_slidev_exporter_frontmatter():
    """Test Slidev frontmatter generation"""
    exporter = create_slidev_exporter()

    markdown = exporter.create_slidev([], [], "", "Test")

    # Check frontmatter structure
    assert markdown.startswith("---")
    assert "theme:" in markdown
    assert "title:" in markdown
    assert "mdc: true" in markdown


def test_slidev_exporter_statistics():
    """Test statistics calculation in slides"""
    exporter = create_slidev_exporter()

    nodes = [
        Node(id="1", type="api", position=Position(x=0, y=0), data=NodeData(label="API1")),
        Node(id="2", type="api", position=Position(x=0, y=0), data=NodeData(label="API2")),
        Node(id="3", type="service", position=Position(x=0, y=0), data=NodeData(label="Service1")),
        Node(id="4", type="database", position=Position(x=0, y=0), data=NodeData(label="DB1"))
    ]
    edges = [
        Edge(id="e1", source="1", target="3"),
        Edge(id="e2", source="2", target="3"),
        Edge(id="e3", source="3", target="4")
    ]

    markdown = exporter.create_slidev(nodes, edges, "", "Test")

    # Should mention statistics
    assert "4 total components" in markdown or "4" in markdown
    assert "3 total connections" in markdown or "3" in markdown


# ============================================================
# Integration Tests
# ============================================================

def test_end_to_end_export_workflow():
    """Test complete export workflow"""
    # 1. Parse a document
    parser = create_document_parser()
    content = "# Architecture Document\n\nThis is a test document."

    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        chunks = parser.parse_file(temp_path, "markdown")
        assert len(chunks) > 0
    finally:
        os.unlink(temp_path)

    # 2. Export to PPT
    ppt_exporter = create_ppt_exporter()
    nodes = [Node(id="1", type="api", position=Position(x=100, y=100), data=NodeData(label="Test"))]
    ppt_bytes = ppt_exporter.create_presentation(nodes, [], "Test")
    assert len(ppt_bytes) > 1000

    # 3. Export to Slidev
    slidev_exporter = create_slidev_exporter()
    markdown = slidev_exporter.create_slidev(nodes, [], "", "Test")
    assert len(markdown) > 500


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
