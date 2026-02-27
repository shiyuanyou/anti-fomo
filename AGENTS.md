# AGENTS.md

This repository is a Python + Vue 3 app for asset allocation awareness and anti-FOMO portfolio monitoring. The guidance below is for agentic coding tools working in this repo.

## 1. Product & Architecture Context

Anti-FOMO is a **cognitive awareness tool**, not an auto-trading bot.

### Core Entry Points
1. **`run.py`** — CLI for portfolio monitoring (v1). Stable, do not break.
2. **`api/`** — FastAPI backend (v3.3+) with layered architecture:
   - `api/app/main.py` — Application factory (`create_app()`)
   - `api/main.py` — Uvicorn entry point
   - `api/routers/` — Route handlers: `assets.py`, `templates.py`, `shares.py`
   - `api/models/` — SQLAlchemy ORM models (`Template`, `Share`)
   - `api/schemas/` — Pydantic request/response schemas
   - `api/crud/` — Database CRUD operations (only place that touches SQLite)
   - `api/services/` — Business logic layer (compare, AI, shares)
3. **`web/`** — Vue 3 + Vite + TypeScript frontend (v3.3+)
4. **`web-legacy/`** — Original vanilla JS demo. Read-only reference; do not modify.
5. **`scripts/`** — Offline data pipelines and one-shot DB initialization utilities.

### Legacy / Backup Files (do not use or modify)
- `serve_legacy.py.bak`, `src/template_engine/templates_legacy.py.bak` — backed-up old code

### Frontend Dual-Mode Architecture
`web/` builds in two modes controlled by `VITE_APP_MODE`:
- **Local Mode** (`npm run build:local`, `.env.local`): Pinia store uses `LocalStorageStrategy` — reads `GET /api/assets`, writes `POST /api/save` to backend YAML.
- **Cloud Mode** (`npm run build:cloud`, `.env.cloud`): Pinia store uses `CloudStorageStrategy` — reads/writes `localStorage`. Templates and shares via `/api/templates` and `/api/shares`.

### Database (v3.3+)
- **SQLite** (`anti-fomo.db` in project root) — do not commit this file.
- Tables: `templates` (official allocations), `shares` (user-exported configs).
- ORM only: never write raw SQL in route handlers. All DB access via `api/crud/`.
- Migration path to PostgreSQL: change `DATABASE_URL` in `api/models/database.py` — zero code changes needed.

---

## 2. Build, Lint, and Test Commands

### Python Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Format and lint
ruff format .
ruff check --fix .

# Type checking
mypy src/ --ignore-missing-imports
mypy api/ --ignore-missing-imports

# Run all tests
pytest

# Run a single test file
pytest tests/test_portfolio.py

# Run a single test by name
pytest tests/test_portfolio.py::test_portfolio_creation

# Run with coverage
pytest --cov=src --cov=api --cov-report=html

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Initialize DB from templates.json (first-time setup only)
python3 scripts/init_db.py

# Run FastAPI dev server (from repo root)
python3 -m uvicorn api.main:app --reload --port 8000
```

### Vue 3 Frontend (`web/`)

```bash
cd web
npm install

npm run dev            # Dev server with proxy to localhost:8000
npm run build:local    # Production build — Local Mode
npm run build:cloud    # Production build — Cloud Mode
npm run preview        # Preview the last build
```

There is **no separate test command** for the frontend; use the Vite build (`build:local`) as the compile/type-check gate. A clean build with zero errors is the acceptance criterion.

---

## 3. Code Style Guidelines

### Python — General
- **Python 3.8+** throughout.
- No emojis in code, comments, logs, or commit messages.
- Favor small, readable functions. Avoid deep abstraction or unnecessary wrapper classes.
- Do not add comments that merely restate what the code does.

### Python — Imports
- Order: standard library → third-party → local. One blank line between groups.
- Explicit imports only; no `from module import *`.
- Absolute imports for cross-package: `from api.schemas import TemplateResponse`
- Relative imports within the same package: `from .cache import DataCache`

### Python — Formatting
- 4-space indentation. Max line length 100–120 characters.
- Double quotes `"` for string literals and dict defaults.
- f-strings for all string interpolation; no `%` or `.format()`.
- Do not auto-format YAML keys.

### Python — Types
- Type hints on all public functions and dataclass fields.
- Use `Optional[T]` for nullable values (not `T | None` — keep 3.8 compat).
- `@dataclass` for data containers; add `__str__` when human-readable output helps.
- Pydantic `BaseModel` for all API request/response schemas (in `api/schemas/`).
- SQLAlchemy models use singular nouns: `class Template(Base)`, `class Share(Base)`.

### Python — Naming
- Classes: `CamelCase` — `AntiFOMO`, `DataFetcher`
- Functions/variables: `snake_case`
- Private helpers: `_leading_underscore`
- Constants: `UPPER_SNAKE_CASE`
- Enums: `CamelCase` class, `UPPER_SNAKE_CASE` members

### Python — Error Handling
- Wrap all external calls (akshare, OpenAI, network) in `try/except`; return safe defaults (`None`, empty list/DataFrame) and log a warning. Never crash on external failure.
- `raise SystemExit(1)` only for fatal startup errors (missing required config file).
- `ValueError` only for programmer errors (invalid arguments passed to a function).
- FastAPI route errors: `raise HTTPException(status_code=404, detail="Template not found")`

### Python — State & Side Effects
- `config.asset.yaml` is the sole source of truth for holdings in Local Mode. Only read/write via `api/routers/assets.py`.
- Cache files live in `cache/` (pickle/JSON, 24 h TTL). Always go through `ValuationFetcher`.
- File IO: only write inside `logs/`, `cache/`, or `base_datas/`.
- Database: all writes through SQLAlchemy ORM in `api/crud/`. No raw SQL anywhere.

---

## 4. Frontend Guidelines (Vue 3 + TypeScript)

### Component Authoring
- Use `<script setup lang="ts">` (Composition API). No Options API.
- Scoped CSS inside `.vue` files for component-specific styles. Global styles in `web/src/assets/style.css`.
- Do **not** duplicate CSS classes from `style.css` in scoped blocks — check the global file first.
- All CSS variables are defined in `style.css :root`. Use those names (`--bg-primary`, `--accent`, `--text-secondary`, etc.). Never invent new variable names like `--panel-bg` or `--bg-color`.

### State Management (Pinia — `configStore`)
- The single store (`web/src/store/configStore.ts`) uses a **strategy pattern** for dual-mode storage.
- `loadConfig()` has a `_loaded` guard — it executes only once per session. Calling it again is a no-op.
- `setAssets()` sets `_loaded = true` to prevent subsequent `loadConfig()` calls (e.g., on route navigation) from overwriting freshly set in-memory state. This is intentional — preserve it.
- `saveStatus` values are `'idle' | 'success' | 'error'`. CSS expects `save-ok` / `save-err` class names; map with a computed property, do not change the store's internal values.

### Shared Utilities
- `web/src/utils/index.ts` exports: `formatAmount()`, `PALETTE`, `ALLOC_PALETTE`, `RISK_COLORS`.
- **Never copy-paste these into components.** Import from `@/utils`.
- `PALETTE` and `ALLOC_PALETTE` must stay identical across treemap blocks and detail chips — both sort by value descending, so color indices match automatically.

### Types (`web/src/types/index.ts`)
- `Template` has **both** `allocations: AllocationItem[]` (detailed, with `region` per item) and `allocation: Record<string, number> | null` (simplified dict, values in %). Prefer `allocations` when `region` data is needed (e.g., `copyTemplate`).
- Do not use `any` for API responses that have known shapes — extend the type interfaces instead.

### Chart.js Usage
- `ChartBar.vue` uses `chartjs-plugin-datalabels` via **local registration** (`plugins: [ChartDataLabels]` inside `new Chart()`). Do not call `Chart.register(ChartDataLabels)` globally — it pollutes all chart instances.
- Always `destroy()` a chart instance before re-creating it.

### Networking
- Use the standard `fetch` API. Do not introduce Axios.
- All API paths are relative (`/api/...`). The Vite dev proxy forwards them to `localhost:8000`.

---

## 5. Repository Conventions

- **No Cursor or Copilot rule files** — do not look for `.cursor/` or `.github/copilot-instructions.md`.
- `anti-fomo.db` is in `.gitignore`. Do not commit it.
- `web-legacy/` is read-only reference code (original vanilla JS demo). It is the design authority for UI interactions and visual style. When in doubt about intended UX, check the corresponding file there.
- Files in `src/` named `"<name> 2.py"` are iCloud sync duplicates. Ignore them; never import or edit them.
- Migration/init scripts go in `scripts/`. They are one-shot utilities, not part of the regular server.
- FastAPI auto-generates docs at `http://localhost:8000/docs` (Swagger) and `/redoc` (ReDoc).
- Commit messages: lowercase imperative, no emoji, no period. Example: `fix template copy missing region field`
