# SiliconFlow Integration Notes (Text-Only, 2026-01-12)

## Current Status
- SiliconFlow added as text-only provider; default model `Pro/Qwen/Qwen2.5-7B-Instruct` (key set in code for current phase).
- Vision image analysis explicitly rejects SiliconFlow with 400 (text-only note).
- Frontend model picker/store includes SiliconFlow; backend validations and services updated.
- Chat Flowchart: SSE streaming with token-level logging, chat bubbles, and animated drawing of nodes/edges; falls back to non-stream if provider returns empty stream.
- Prompter: wired to real `/api/prompter/execute`; scenarios fetched from backend; results applied to canvas and chat log. New scenarios added (beautify-bpmn, cyberpunk-visual, handdrawn-sketch, swimlane-layout).
- Verified real API call with provided key (chat/completions) returns 200 and content.

## Dependencies / Environment
- Backend venv: `backend/venv`.
- Installed via Tsinghua mirror; RAG deps commented out to avoid build issues:
  - Commented: chromadb, sentence-transformers, pypdf2, python-docx, markdown.
- Installed `lxml==5.2.1` (mirror) to satisfy `python-pptx`.
- Key commands used:
  - Install deps (mirror): `backend/venv/Scripts/python -m pip install -r requirements.txt -r test-requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`
  - Install lxml (mirror): `backend/venv/Scripts/python -m pip install --timeout 180 -i https://pypi.tuna.tsinghua.edu.cn/simple lxml==5.2.1`

## Tests
- Ran in venv:
  - `backend/venv/Scripts/python -m pytest -q tests/test_api.py::test_models_save_siliconflow_config tests/test_api.py::test_vision_rejects_siliconflow_image`
  - Result: 2 passed (warnings only).

## Files Touched (key)
- Backend: `app/services/ai_vision.py`, `app/services/prompter.py`, `app/services/chat_generator.py`, `app/api/vision.py`, `app/api/export.py`, `app/api/chat_generator.py` (SSE), `app/api/prompter.py` (JSON body + query params), `app/core/config.py`, `app/models/schemas.py`, `app/data/prompt_presets.json` (new scenarios), `tests/test_api.py`, `requirements.txt`, `.env.example`.
- Frontend: `components/ModelConfigModal.tsx`, `components/ImageUploadModal.tsx`, `components/AiControlPanel.tsx` (chat + streaming log), `components/PrompterModal.tsx` (style/theme labels), `lib/store/useArchitectStore.ts`.
- Env: `backend/.env.example`.

## Next Steps
1) Decide on RAG: if needed, restore commented deps in `backend/requirements.txt` and install (may need build tools or wheels via mirror).
2) Run broader test suite as needed: `backend/venv/Scripts/python -m pytest`.
3) Keep using SiliconFlow for text flows (Prompter/Script); vision with SiliconFlow will return 400 by design.
4) Prompter UI: add diff/preview and apply flow; consider auto-layout/theme application from returned nodes/edges.
5) Refine streaming UI if needed (token pacing, error surfacing).

## Notes
- Provided SiliconFlow API key verified; not stored in code (.env/UI only).
- Vision endpoint now accepts provider from form or query; default remains gemini.
