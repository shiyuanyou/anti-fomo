# AGENTS.md

This repository is a Python app for asset allocation awareness and anti-FOMO portfolio monitoring. The guidance below is for agentic coding tools working in this repo.

## 1. Product & Architecture Context

Anti-FOMO is a **cognitive awareness tool**, not an auto-trading bot.

### Core Entry Points
1. **`run.py`** -- CLI for portfolio monitoring (v1). Stable.
2. **`serve.py`** -- HTTP server for the web UI (v2/v3). In v3.5+, it serves the `web/dist` directory.
3. **`scripts/`** -- v3 offline data pipelines (pulling index history via akshare).

### Frontend Context (v3.5+)
The `web/` directory uses **Vue 3 + Vite + TypeScript**. It operates in two modes:
- **Local Mode** (`.env.local`): Reads/writes to the backend `config.asset.yaml`. Used when running `serve.py` locally.
- **Cloud Mode** (`.env.cloud`): Reads/writes purely to browser `localStorage` (used for Nginx deployments and sharing).

---

## 2. Build, Lint, and Test Commands

### Python Backend
We use `ruff` for linting/formatting, `mypy` for typing, and `pytest` for testing.

```bash
# Format and lint code
ruff format .
ruff check --fix .

# Type checking
mypy src/ --ignore-missing-imports

# Testing (Mock external dependencies like akshare/OpenAI)
pytest                                                   # Run all tests
pytest tests/test_portfolio.py                           # Run a specific test file
pytest tests/test_portfolio.py::test_portfolio_creation  # Run a single test
pytest --cov=src --cov-report=html                       # Run with coverage
```

### Vue 3 Frontend (`web/` directory)
```bash
cd web
npm install

# Run local development server
npm run dev

# Build for Local Mode (reads/writes to backend config.asset.yaml)
npm run build:local

# Build for Cloud Mode (reads/writes to localStorage, for Nginx/Share deployments)
npm run build:cloud
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
- Internal module imports should use bare package names if injected into `sys.path` (e.g., `from portfolio_engine import Portfolio`), but prefer relative imports within the same sub-package (`from .cache import DataCache`).

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

### Python Naming Conventions
- **Classes**: `CamelCase` (e.g., `AntiFOMO`, `DataFetcher`).
- **Functions/Variables**: `snake_case`.
- **Private Helpers**: Prefix with `_` (e.g., `_load_config`).
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `PORT`, `BASE_DIR`).
- **Enums**: `CamelCase` class, `UPPER_SNAKE_CASE` members.

### Python Error Handling
- Prefer graceful failure. Wrap external network/API calls (like akshare or OpenAI) in `try/except` and return safe defaults (e.g., empty DataFrame, `None`).
- Log warnings on failure rather than crashing.
- Use `raise SystemExit(1)` only for truly fatal config errors (e.g., missing `config.asset.yaml`).
- Use `ValueError` strictly for programmer errors (invalid arguments).

### State & Side Effects
- **Config**: Only parse in `src/main.py:_load_config`. `config.asset.yaml` is the sole source of truth for holdings in Local Mode.
- **Cache**: PE/PB data is cached in `cache/` as pickle/JSON. TTL is 24h. Always go through `ValuationFetcher`.
- **IO**: Do not write files outside of `logs/`, `cache/`, or `base_datas/`.

### Frontend Guidelines (Vue 3 + TS)
- **Composition API**: Use Vue 3 Composition API (`<script setup lang="ts">`).
- **State Management**: Use Pinia or abstracted composables to handle the Local vs. Cloud dual-mode logic cleanly.
- **Styling**: Scoped CSS within Vue components. Maintain the existing visual aesthetic (dark/light theme, Chart.js).
- **Network**: Use standard `fetch` API. Do not introduce Axios unless absolutely necessary.

## 4. Repository Conventions
- No Cursor or Copilot rule files are present. Do not look for them.
- Keep `config.yaml` free of secrets and free of portfolio holdings.
- Several files in `src/` have iCloud conflict duplicates named `"<name> 2.py"`. These are never imported and should be ignored; do not edit or create files with space-and-number suffixes.
