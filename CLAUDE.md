# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SmartArchitect AI is a full-stack AI-powered architecture design platform that converts visual architecture diagrams into editable code. The system consists of a Next.js frontend with React Flow canvas and a FastAPI backend with multi-provider AI integration, RAG knowledge base, and export capabilities.

**Current Version:** 0.4.0 (Phase 4 Complete)
**Status:** Production Ready with 97% test coverage

## Development Commands

### Backend (FastAPI)

```bash
# Setup
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt

# Run development server
python -m app.main
# Server runs on http://localhost:8000
# API docs available at http://localhost:8000/docs

# Run all tests
"venv\Scripts\python.exe" -m pytest tests/ -v --tb=short

# Run specific test file
"venv\Scripts\python.exe" -m pytest tests/test_api.py -v

# Run single test
"venv\Scripts\python.exe" -m pytest tests/test_api.py::test_rag_workflow -v

# Run with coverage
"venv\Scripts\python.exe" -m pytest tests/ --cov=app --cov-report=html

# Install test dependencies
"venv\Scripts\python.exe" -m pip install -r test-requirements.txt
```

### Frontend (Next.js)

```bash
# Setup
cd frontend
npm install

# Run development server
npm run dev
# Server runs on http://localhost:3000

# Build for production
npm run build

# Start production server
npm start

# Lint code
npm run lint
```

### Full Stack Launch

```bash
# Windows
start-dev.bat

# Linux/Mac
./start-dev.sh
```

## Architecture Deep Dive

### Monorepo Structure

```
SmartArchitect/
├── backend/           # FastAPI backend (Python 3.12.5)
│   ├── app/
│   │   ├── api/       # API route handlers (7 modules)
│   │   ├── core/      # Configuration (settings via pydantic-settings)
│   │   ├── models/    # Pydantic schemas for request/response
│   │   ├── services/  # Business logic (RAG, AI, exporters)
│   │   └── main.py    # FastAPI app with CORS middleware
│   └── tests/         # pytest test suite (31 tests, 97% passing)
│
└── frontend/          # Next.js 14 App Router (React 19)
    ├── app/           # Page routes
    ├── components/    # React components
    └── public/        # Static assets
```

### Backend API Architecture

**27 Endpoints Across 7 Modules:**

1. **Health API** (`/api/health`) - Service health checks
2. **Mermaid API** (`/api/mermaid/parse`, `/api/graph/to-mermaid`) - Bidirectional Mermaid ↔ JSON conversion
3. **Models API** (`/api/models/config`) - AI provider configuration (Gemini, OpenAI, Claude, Custom)
4. **Vision API** (`/api/vision/analyze`) - Image-to-architecture AI analysis
5. **Prompter API** (`/api/prompter/*`) - Architecture refactoring scenarios
6. **Export API** (`/api/export/ppt`, `/api/export/slidev`, `/api/export/script`) - PowerPoint, Slidev, speech script generation
7. **RAG API** (`/api/rag/*`) - Document upload, semantic search, ChromaDB vector database

**Key Services:**

- **RAG Service** (`services/rag.py`) - ChromaDB integration with sentence-transformers embeddings (all-MiniLM-L6-v2), chunking strategy: 1000 chars with 200 overlap
- **AI Vision Service** (`services/ai_vision.py`) - Multi-provider abstraction layer for Gemini/OpenAI/Claude
- **PPT Exporter** (`services/ppt_exporter.py`) - python-pptx based presentation generator
- **Slidev Exporter** (`services/slidev_exporter.py`) - Markdown slide deck generator
- **Prompter Service** (`services/prompter.py`) - Scenario-based architecture refactoring

### Frontend Architecture

**State Management:** Zustand (implicit, no central store file found - state likely colocated in components)

**Key Components:**
- `ArchitectCanvas` - React Flow canvas with custom node types (API, Service, Database)
- `CodeEditor` - Monaco Editor for Mermaid code with bidirectional sync
- `Sidebar` - Tool controls and configuration
- `ThemeSwitcher` - 12+ theme system with CSS variables

**React Flow Integration:**
- Custom node components with developer-focused icons (Lucide React)
- Bidirectional sync: Canvas changes → Mermaid code, Code changes → Canvas redraw
- Auto-layout via dagre algorithm

### Data Flow & Schemas

**Critical Pydantic Models** (`backend/app/models/schemas.py`):

```python
# Node structure - ALWAYS include position field
class Node(BaseModel):
    id: str
    type: Optional[str] = "default"
    position: Position  # REQUIRED: {x: float, y: float}
    data: NodeData      # {label: str}

class Edge(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None

# Mermaid parsing - note field name
class MermaidParseRequest(BaseModel):
    code: str  # NOT "mermaid_code"

# Model configuration
class ModelConfig(BaseModel):
    provider: str
    api_key: str
    model_name: str  # NOT "model"
    base_url: Optional[str] = ""
```

**Common Schema Pitfalls:**
- Mermaid endpoints expect `{"code": "..."}` NOT `{"mermaid_code": "..."}`
- Models API POST expects `model_name` NOT `model`
- Models API GET requires path parameter: `/api/models/config/{provider}` NOT `/api/models/config`
- All Node objects MUST include `position: {x: float, y: float}` even if `{x: 0, y: 0}`

### AI Integration Pattern

**Multi-Provider Support:**
```python
# API keys configured via:
# 1. Environment variables (GEMINI_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY)
# 2. Runtime POST /api/models/config
# 3. Query parameters on vision/prompter endpoints

# Provider selection flow:
POST /api/vision/analyze?provider=gemini&api_key=xxx
```

**Providers:**
- `gemini` - Google Gemini 2.5 Flash (default, multimodal)
- `openai` - OpenAI GPT-4 Vision
- `claude` - Anthropic Claude
- `custom` - Custom API endpoint (requires base_url)

### RAG System Details

**ChromaDB Configuration:**
- Persistent storage in `backend/chroma_data/`
- Collection: `architecture_docs`
- Embedding model: `all-MiniLM-L6-v2` (384 dimensions)
- First query latency: ~26s (model loading), subsequent: 100-200ms

**Supported Document Types:**
- PDF (PyPDF2)
- Markdown (.md)
- DOCX (python-docx)

**Chunking Strategy:**
```python
# Default settings (configurable)
chunk_size = 1000      # characters per chunk
chunk_overlap = 200    # character overlap between chunks
```

### Testing Strategy

**Test Files:**
- `tests/test_api.py` - 22 API endpoint tests (integration)
- `tests/test_services.py` - 9 service layer tests (unit)

**Test Coverage:**
- Overall: 97% (30/31 passing)
- RAG System: 100% (7/7)
- Service Layer: 100% (9/9)
- Export APIs: 75% (3/4)

**Running Subset of Tests:**
```bash
# By marker/pattern
"venv\Scripts\python.exe" -m pytest tests/ -k "rag"

# By file
"venv\Scripts\python.exe" -m pytest tests/test_services.py

# Specific test
"venv\Scripts\python.exe" -m pytest tests/test_api.py::test_models_get_config -v
```

**Test Patterns:**
```python
# API tests use FastAPI TestClient
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
response = client.post("/api/endpoint", json={...})

# Service tests use Pydantic models directly
from app.models.schemas import Node, Edge, Position, NodeData

nodes = [
    Node(id="1", type="api", position=Position(x=100, y=100),
         data=NodeData(label="API Gateway"))
]
```

## Configuration & Environment

**Backend Configuration** (`backend/app/core/config.py`):
```python
# Uses pydantic-settings with .env support
API_HOST = "0.0.0.0"
API_PORT = 8000
API_RELOAD = True
CORS_ORIGINS = ["http://localhost:3000", "http://127.0.0.1:3000"]

# Optional AI keys (can be set at runtime via API)
GEMINI_API_KEY = ""
OPENAI_API_KEY = ""
ANTHROPIC_API_KEY = ""
```

**Frontend Port:** 3000 (configurable, auto-discovery in production)
**Backend Port:** 8000

## Phase History & Features

**Phase 1 (Complete):** Core Canvas & Mermaid
- React Flow interactive canvas
- Bidirectional Mermaid code sync
- Custom node types (API, Service, Database)

**Phase 2 (Complete):** AI Vision Analysis
- Multi-provider AI integration (Gemini, OpenAI, Claude, Custom)
- Image upload → architecture diagram conversion
- Architecture component detection

**Phase 3 (Complete):** Prompter + Theme System
- 3 scenario-based refactoring prompts (+ custom)
- 12+ professional themes
- Dynamic CSS variable styling

**Phase 4 (Complete):** RAG + Export
- ChromaDB vector database with semantic search
- Document upload (PDF, Markdown, DOCX)
- PowerPoint export (4-slide presentation)
- Slidev export (markdown slide deck)
- Speech script generation (30s, 2min, 5min)

## Known Issues & Limitations

1. **First RAG Query Latency:** ~26 seconds for embedding model initialization (subsequent queries: 100-200ms)
2. **Auto Layout:** Basic fitView implementation, no advanced algorithms (dagre/elk planned but not integrated)
3. **Test Timeout:** `test_export_script_no_api_key` hangs on invalid AI API key (expected behavior for error path test)
4. **Security Gaps:** No authentication, no rate limiting (documented in SYSTEM_REVIEW.md for production deployment)

## Code Patterns & Conventions

### Backend

**Service Factory Pattern:**
```python
# Services use factory functions, not classes
def create_rag_service():
    return RAGService(...)

# Lazy initialization for heavy services
_rag_service = None
def get_rag_service():
    global _rag_service
    if _rag_service is None:
        _rag_service = create_rag_service()
    return _rag_service
```

**Error Handling:**
```python
from fastapi import HTTPException

try:
    result = service.process()
except Exception as e:
    raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
```

**Response Models:**
```python
# All responses use Pydantic BaseModel
class ExportResponse(BaseModel):
    success: bool
    message: str
    # Additional fields...

@router.post("/export/ppt", response_model=ExportResponse)
async def export_ppt(request: ExportRequest):
    # ...
```

### Frontend

**Component Organization:**
- Client components: `"use client"` directive at top
- Server components: Default (no directive)
- Styling: Tailwind CSS with dark mode support (`dark:` prefix)

**API Communication:**
```typescript
// Fetch pattern used throughout
const response = await fetch('http://localhost:8000/api/endpoint', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(data)
});
```

## Performance Characteristics

**Backend Response Times:**
- Health checks: <10ms
- Mermaid parse/generate: 50-100ms
- RAG search: 1-2s (first), 100-200ms (cached)
- PPT export: 200-500ms
- AI vision analysis: 3-8s (provider-dependent)

**Frontend Bundle Size:**
- Total: ~2.5MB uncompressed
- Main: ~800KB
- React Flow: ~600KB

## Related Documentation

- `SYSTEM_REVIEW.md` - Comprehensive production readiness assessment
- `TEST_COVERAGE_REPORT.md` - Detailed test results and recommendations
- `README.md` - Project overview and quick start (Chinese)
- `http://localhost:8000/docs` - Interactive OpenAPI documentation (when backend running)
