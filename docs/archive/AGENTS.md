# Repository Guidelines

## Project Structure & Module Organization
- `frontend/` (Next.js 14) holds the UI: `app/` routes, `components/` (canvas, modals, node components), `lib/store` (Zustand state), `lib/themes`, `lib/utils` (node shape helpers), and `public/` assets.
- `backend/` (FastAPI) contains `app/api` routes, `app/services` for AI/RAG/export logic, `app/models/schemas.py` for Pydantic contracts, `app/core/config.py` for env settings, and `app/data` prompt/flow templates. Runtime artifacts land in `backend/logs` and `backend/data/uploads`.
- `docs/` keeps architecture and onboarding notes; `start-dev.(bat|sh)` launches both tiers for local work.

## Build, Test, and Development Commands
- Full stack: `start-dev.bat` (Windows) or `./start-dev.sh` (Unix) -> frontend on http://localhost:3000, backend on http://localhost:8000.
- Frontend: `cd frontend && npm install && npm run dev`; production build via `npm run build && npm start`; lint with `npm run lint`.
- Backend: `cd backend && python -m venv venv && venv\Scripts\activate` (or `source venv/bin/activate`), install deps `pip install -r requirements.txt -r test-requirements.txt`, run `python -m app.main` or `uvicorn app.main:app --reload --port 8000`; tests with `pytest -q`.

## Coding Style & Naming Conventions
- React/TypeScript: functional components, PascalCase file names in `components/`, hooks prefixed with `use` (e.g., `useArchitectStore`), props/state in camelCase, Tailwind classes for styling. Keep imports ordered (lib/react/local) and favor 2-space indents consistent with current files.
- Python: 4-space indents, type hints required, snake_case modules and functions, Pydantic models centralized in `app/models/schemas.py`, and configuration pulled from `app/core/config.py`. Use `logging` setup in `app/core/logging.py` instead of ad-hoc prints.

## Testing Guidelines
- Backend tests live in `backend/tests`; name files `test_*.py` and scenarios `test_*`. Run `pytest -q`; keep tests offline and rely on fixtures/templates in `app/data`. Align request bodies with Pydantic schemas to avoid 422s noted in `TEST_COVERAGE_REPORT.md`. Add or adjust tests whenever you change an endpoint or service.
- Frontend tests are not yet present; if you add UI features, prefer React Testing Library or Playwright and mirror component names.

## Commit & Pull Request Guidelines
- Follow conventional commits (e.g., `feat: add-bpmn-nodes`, `fix: validate-mermaid-request`, `docs: update-readme`) as seen in history; keep messages imperative and under ~72 chars.
- PRs should include: what changed, why, and risk notes; linked issue or ticket; screenshots or recordings for UI tweaks; commands run (e.g., `pytest -q`, `npm run lint`); and any env/config updates (`.env` keys, ports).

## Security & Configuration Tips
- Copy `.env.example` to `.env` locally; never commit secrets or API keys. Check that generated logs/exports/uploads stay out of Git.
- Default ports are 3000 (frontend) and 8000 (backend); update `app/core/config.py` if you must change them and mirror proxy settings in `frontend/next.config.js`.
