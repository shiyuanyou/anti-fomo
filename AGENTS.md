# AGENTS.md

This repository is a Python + Vue 3 app for asset allocation awareness and anti-FOMO portfolio monitoring.

## 1. Product & Architecture

Anti-FOMO is a **cognitive awareness tool**, not an auto-trading bot.

### Core Entry Points
- **`run.py`** — CLI for portfolio monitoring (v1)
- **`apps/bff/`** — FastAPI BFF backend (v3.5+)
- **`apps/backend/`** — FastAPI backend services with gRPC
- **`web/`** — Vue 3 + Vite + TypeScript frontend
- **`scripts/`** — Offline data pipelines and DB initialization

### Database
- **SQLite** in `data/bff/` and `data/jobs/`
- ORM only via `apps/*/crud/`. No raw SQL.

---

## 2. Build, Lint, and Test Commands

### Python Backend
```bash
pip install -r requirements.txt

# Format and lint
ruff format .
ruff check --fix .

# Type checking
mypy apps/ --ignore-missing-imports

# Run all tests
pytest

# Run a single test file
pytest tests/test_portfolio.py

# Run a single test by name
pytest tests/test_portfolio.py::test_portfolio_creation

# Run with coverage
pytest --cov=apps --cov-report=html

# Initialize DB
python3 scripts/init_db.py
```

### Vue 3 Frontend
```bash
cd web && npm install

npm run dev            # Dev server with proxy
npm run build:local    # Production build — Local Mode
npm run build:cloud    # Production build — Cloud Mode
```

---

## 3. Code Style Guidelines

### Python
- Python 3.8+, 4-space indent, max 120 chars per line
- Type hints on all public functions, use `Optional[T]`
- Double quotes for strings, f-strings for interpolation
- Order imports: stdlib → third-party → local
- Error handling: wrap external calls in try/except, return safe defaults

### Vue 3 + TypeScript
- Use `<script setup lang="ts">` (Composition API)
- Scoped CSS, global styles in `style.css`
- Use CSS variables (`--bg-primary`, `--accent`, etc.)
- Use `fetch` API, not Axios

---

## 4. Important Reminders

### Frontend: Browser API Compatibility
**NEVER use `crypto.randomUUID()` directly** — it requires secure context (HTTPS) and fails on Safari/older browsers.

```typescript
// WRONG
const id = crypto.randomUUID()

// CORRECT - use feature detection or uuid library
import { v4 as uuidv4 } from 'uuid'
const id = uuidv4()
```

### Backend: Data Structure Access
When accessing request data, verify the actual structure. Common mistake:
```python
# WRONG - double nesting
config.portfolio["portfolio"]["holdings"]

# CORRECT
config.portfolio["holdings"]
```

---

## 5. Documentation Guide

Read these docs before specific tasks:

| Task | Read This |
|------|-----------|
| Architecture overview | `docs/anti-fomo核心.md` |
| API contracts | `docs/api.md` |
| Product roadmap | `docs/product-roadmap.md` |
| MVP scope | `docs/mvp-scope-v1.md` |
| Refactoring plan | `docs/refactoring-plan.md` |
| Docker deployment | `docker/README.md` (if exists) or Makefile |
| Past bugs/accidents | `docs/accidents.md` |

---

## 6. Repository Conventions

- `anti-fomo.db` is in `.gitignore`. Do not commit.
- No Cursor/Copilot rules — do not look for them.
- Commit messages: lowercase imperative, no emoji. Example: `fix template copy missing region field`
