# AGENTS.md

This repository is a Python app for asset allocation awareness and anti-FOMO portfolio monitoring. The guidance below is for agentic coding tools working in this repo.

## 1. Product & Architecture Context

Anti-FOMO is a **cognitive awareness tool**, not an auto-trading bot.

### Core Entry Points
1. **`run.py`** -- CLI for portfolio monitoring (v1). Stable.
2. **`api/`** -- **NEW in v3.3**: FastAPI backend with layered architecture.
   - `api/app/main.py` -- Application factory
   - `api/routers/` -- API route handlers (templates, shares, assets)
   - `api/models/` -- SQLAlchemy database models
   - `api/schemas/` -- Pydantic request/response schemas
   - `api/crud/` -- Database CRUD operations
3. **`scripts/`** -- Offline data pipelines and database initialization.

### Legacy Code (v2/v3 - Backup Only)
- `serve_legacy.py.bak` -- Old HTTP server (backed up, do not use)
- `src/template_engine/templates_legacy.py.bak` -- Old hardcoded templates (backed up)
- `scripts/migrate_templates_legacy.py.bak` -- Old migration script (backed up)

**v3.3 Refactor**: All template data now lives in database, matching `templates.json` format.

### Frontend Context (v3+)
The `web/` directory uses **Vue 3 + Vite + TypeScript**. It operates in two modes:
- **Local Mode** (`.env.local`): Reads/writes to backend `config.asset.yaml` via `/api/assets`
- **Cloud Mode** (`.env.cloud`): Reads/writes browser `localStorage`, uses `/api/templates` and `/api/shares` for sharing

**v3.3 Architecture Change**: Frontend is now pure static files served by Nginx. Backend is separate FastAPI service on port 8000. Frontend calls `https://anti-fomo.yoyoostone.cn/api/*` in production.

### Database Context (v3.3+)
- **SQLite** for official templates (`templates` table) and user shares (`shares` table)
- **SQLAlchemy ORM** for database operations, **Alembic** for migrations
- Single file: `anti-fomo.db` in project root
- **Migration path**: Can switch to PostgreSQL by changing DB URL in `api/database.py` with zero code changes

---

## 2. Build, Lint, and Test Commands

### Python Backend (src/ and api/)
We use `ruff` for linting/formatting, `mypy` for typing, and `pytest` for testing.

```bash
# Install dependencies (v3.3+)
pip install -r requirements.txt

# Format and lint code
ruff format .
ruff check --fix .

# Type checking
mypy src/ --ignore-missing-imports
mypy api/ --ignore-missing-imports

# Testing (Mock external dependencies like akshare/OpenAI)
pytest                                                   # Run all tests
pytest tests/test_portfolio.py                           # Run a specific test file
pytest tests/test_portfolio.py::test_portfolio_creation  # Run a single test
pytest --cov=src --cov=src --cov-report=html           # Run with coverage

# Database migrations (v3.3+)
alembic revision --autogenerate -m "description"         # Create migration
alembic upgrade head                                     # Apply migrations

# Run FastAPI backend (development)
cd api
python3 -m uvicorn api.main:app --reload --port 8000   # Auto-reload on code changes

# Run FastAPI backend (production)
python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000  # Bind to all interfaces
```

### Vue 3 Frontend (`web/` directory)
```bash
cd web
npm install

# Run local development server (with API proxy to localhost:8000)
npm run dev

# Build for Local Mode (reads/writes to backend config.asset.yaml)
npm run build:local

# Build for Cloud Mode (reads/writes localStorage, for Nginx/Share deployments)
npm run build:cloud

# Preview production build
npm run preview
```

### Deployment Commands (v3.3+)
```bash
# 1. Build frontend for cloud deployment
cd web && npm run build:cloud

# 2. Initialize database (first time only)
python3 scripts/init_db.py                             # Import templates from templates.json to SQLite

# 3. Configure Nginx (copy template from docs/v3.3-architecture-lite.md)
sudo ln -s /path/to/nginx.conf /etc/nginx/sites-enabled/anti-fomo
sudo certbot --nginx -d anti-fomo.yoyoostone.cn       # SSL certificate

# 4. Setup systemd service for FastAPI
cp docs/anti-fomo-api.service /etc/systemd/system/
sudo systemctl enable anti-fomo-api
sudo systemctl start anti-fomo-api
```

---

## 3. Code Style Guidelines

### Python General
- **Language**: Python 3.8+
- **No Emoji**: No emojis in logs, code, comments, or commit messages. Keep output concise.
- **Simplicity**: Favor small, readable functions over deep abstraction. Avoid unnecessary comments.

### Python Imports
- Order: Standard library -> Third-party -> Local imports.
- Use explicit imports; no wildcards (`from module import *`).
- Use absolute imports for cross-package references: `from portfolio_engine import Portfolio`
- Use relative imports within same package: `from .cache import DataCache`
- **v3.3+**: In `api/`, use `from models import Template` (no relative imports needed)

### Python Formatting
- **Indentation**: 4 spaces.
- **Quotes**: Use double quotes (`"`) for string literals and dictionary defaults.
- **Line Length**: Max 100-120 characters.
- **Strings**: Prefer f-strings for formatting.
- Do not auto-format YAML keys.

### Python Types & Data Structures
- Use type hints for all public functions and dataclass fields.
- Prefer `Optional[T]` for nullable values.
- Standardize on `@dataclass` for data containers; implement `__str__` if human-readable output is helpful.
- Use Pydantic models for API request/response schemas (v3.3+, in `api/schemas.py`)

### Python Naming Conventions
- **Classes**: `CamelCase` (e.g., `AntiFOMO`, `DataFetcher`).
- **Functions/Variables**: `snake_case`.
- **Private Helpers**: Prefix with `_` (e.g., `_load_config`).
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `PORT`, `BASE_DIR`).
- **Enums**: `CamelCase` class, `UPPER_SNAKE_CASE` members.
- **Database Models**: Singular noun (e.g., `class Template(Base)`, `class Share(Base)`)

### Python Error Handling
- Prefer graceful failure. Wrap external network/API calls (like akshare or OpenAI) in `try/except` and return safe defaults (e.g., empty DataFrame, `None`).
- Log warnings on failure rather than crashing.
- Use `raise SystemExit(1)` only for truly fatal config errors (e.g., missing `config.asset.yaml`).
- Use `ValueError` strictly for programmer errors (invalid arguments).
- **FastAPI errors**: Use HTTPException for API errors: `raise HTTPException(status_code=404, detail="Template not found")`

### State & Side Effects
- **Config**: Only parse in `src/main.py:_load_config`. `config.asset.yaml` is the sole source of truth for holdings in Local Mode.
- **Cache**: PE/PB data is cached in `cache/` as pickle/JSON. TTL is 24h. Always go through `ValuationFetcher`.
- **IO**: Do not write files outside of `logs/`, `cache/`, or `base_datas/`.
- **Database**: Only write to SQLite through SQLAlchemy ORM in `api/crud.py`. Never use raw SQL in route handlers.

### Frontend Guidelines (Vue 3 + TS)
- **Composition API**: Use Vue 3 Composition API (`<script setup lang="ts">`).
- **State Management**: Use Pinia or abstracted composables to handle the Local vs. Cloud dual-mode logic cleanly.
- **Styling**: Scoped CSS within Vue components. Maintain the existing visual aesthetic (dark/light theme, Chart.js).
- **Network**: Use standard `fetch` API. Do not introduce Axios unless absolutely necessary.
- **Environment Variables**: Use `import.meta.env.VITE_API_BASE_URL` for API base URL (differs between local/cloud modes)

---

## 4. Repository Conventions

- No Cursor or Copilot rule files are present. Do not look for them.
- Keep `config.yaml` free of secrets and free of portfolio holdings.
- **v3.3+**: Keep `anti-fomo.db` in `.gitignore` (SQLite database should not be committed)
- Several files in `src/` have iCloud conflict duplicates named `"<name> 2.py"`. These are never imported and should be ignored; do not edit or create files with space-and-number suffixes.
- **Migration scripts**: Place in `scripts/` directory, single-run utilities for data migration
- **API documentation**: FastAPI auto-generates docs at `/docs` (Swagger UI) and `/redoc` (ReDoc)
