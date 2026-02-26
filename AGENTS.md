# AGENTS.md

This repository is a Python app for asset allocation awareness and anti-FOMO
portfolio monitoring. The guidance below is for agentic coding tools working
in this repo.

## Product Context

Anti-FOMO is a **cognitive awareness tool**, not a trading assistant or robo-advisor.
The core insight: most users lack a global view of their own asset allocation.
"Seeing" their portfolio clearly — and comparing it against proven templates —
is more valuable than any real-time alert or AI trading suggestion.

**v2** (complete): `serve.py` + `web/` — Web configuration UI with template library,
1v1 comparison, personality matching, and AI migration advice (F1–F5 shipped).

**v3 focus** (active): replace hard-coded template metrics with real historical data.
Scripts in `scripts/` pull proxy-index history via akshare, compute annualised return /
volatility / max drawdown / Sharpe, persist to `base_datas/`, and feed
`src/template_engine/` at startup. The v1 backend pipeline (`run.py`) is kept
functional but is not the development priority.

## Architecture

The project has two entry points:

1. **`run.py`** -- CLI for portfolio monitoring (single check, weekly report, or daily scheduler). v1, stable.
2. **`serve.py`** -- HTTP server for the Web-based asset configuration UI. v2 active development.

`serve.py` generates `config.asset.yaml`, which is the **sole source** of
portfolio holdings (stock names, codes, ratios). `config.yaml` only holds
operational settings (thresholds, AI analysis, data fetch, market engine,
cache, notification, scheduler, decision engine, report).

Core module dependency (simplified):

```
run.py -> src/main.py (AntiFOMO)
              |- src/portfolio_engine/   (Portfolio, Holding, DataFetcher,
              |                           VolatilityCalculator, ThresholdManager)
              |- src/market_engine/      (MarketScorer, MarketStatus -> akshare)
              |- src/decision_engine/    (PaceController, RebalanceChecker)
              |- src/report_engine/      (DailyDigest, WeeklyReport)
              |- src/ai_engine/          (AIAnalyzer -> OpenAI SDK)
              +- src/notification/       (NotificationManager)

serve.py -> web/ (static SPA) -> config.asset.yaml (generated)
         -> src/template_engine/ (v2 new: TemplateLibrary, TemplateComparator)
         -> src/ai_engine/template_advisor.py (v2 new: personality match + migration advice)

scripts/fetch_index_data.py    -> base_datas/index_weekly.csv  (v3 new)
scripts/calc_template_metrics.py -> base_datas/template_metrics.json (v3 new)
                                 -> base_datas/index_metrics.json    (v3 new)
```

Notes:
- `run.py` inserts `src/` into `sys.path` at runtime, so imports within
  `src/` use bare package names (e.g., `from portfolio_engine import Portfolio`).
  Sub-packages use relative imports internally (e.g., `from .cache import DataCache`).
- `serve.py` uses Python's stdlib `http.server.SimpleHTTPRequestHandler` +
  `socketserver.TCPServer`. No third-party web framework (Flask, FastAPI, etc.) is
  present or should be introduced.
- Each sub-package `__init__.py` re-exports its public symbols with an explicit
  `__all__` list. Follow this pattern when adding new packages.

## Quick Start Commands

```bash
pip3 install -r requirements.txt       # install deps (use pip3 on macOS system Python)
python3 serve.py                       # web UI at http://localhost:8080
python3 run.py                         # single daily check (v1)
python3 run.py weekly                  # generate weekly report immediately (v1)
python3 run.py schedule                # daily scheduler + weekly report on Fridays (v1)
python3 scripts/fetch_index_data.py    # pull proxy-index history via akshare (v3)
python3 scripts/calc_template_metrics.py  # compute real metrics, write base_datas/ (v3)
```

## Build / Lint / Test

### Linting and Formatting
```bash
# Format code with ruff
ruff format .

# Check linting issues
ruff check .

# Fix auto-fixable linting issues
ruff check --fix .

# Type checking with mypy (if installed)
mypy src/ --ignore-missing-imports
```

### Testing
There is no formal unit test suite yet. When adding tests:

1. Place tests in a `tests/` folder
2. Use pytest as test runner
3. Mock external dependencies (akshare, OpenAI API)

```bash
# Run all tests
pytest

# Run a specific test file
pytest tests/test_portfolio.py

# Run a single test
pytest tests/test_portfolio.py::test_portfolio_creation

# Run with coverage
pytest --cov=src --cov-report=html
```

### Development Commands
```bash
# Install development dependencies
pip install ruff pytest pytest-cov mypy

# Run all checks before committing
ruff format . && ruff check . && mypy src/ --ignore-missing-imports
```

## Configuration Files

| File | Purpose |
|------|---------|
| `config.yaml` | Operational config (thresholds, AI, data fetch, market engine, decision engine, report, cache, notification, scheduler). No portfolio holdings. No secrets. |
| `config.asset.yaml` | Generated by `serve.py`. Sole source of holdings for `run.py`. Gitignored. |
| `config.example.yaml` | Example config for new users. |
| `docs/v1-dev-wiki.md` | v1 implementation status, data structures, tech debt. |
| `docs/v2-dev-wiki.md` | v2 development plan, new module contracts, build order. Read this before starting v2 features. |
| `docs/v3-dev-wiki.md` | v3 development plan: real historical metrics, proxy-index mapping, data pipeline. Read this before starting v3 features. |

Environment variables (preferred for secrets):
- `OPENAI_API_KEY` or `AI_API_KEY`
- `OPENAI_BASE_URL` (for compatible providers)

### Symbol field disambiguation

- `config.asset.yaml portfolio.holdings[].symbol` -- akshare **market data** code (e.g. `000510`)
- `config.yaml market_engine.indices[].symbol` -- akshare **valuation** API Chinese name (e.g. `沪深300`)

These are different fields used by different APIs. Do not conflate them.

## Engine Responsibilities

### v1 Engines (stable, do not modify during v2 work)

| Engine | Input | Output |
|--------|-------|--------|
| `portfolio_engine` | `config.asset.yaml` holdings | `PortfolioVolatilityResult`, `AlertResult` |
| `market_engine` | `config.yaml market_engine` | `MarketStatus` (composite score, per-index PE/PB percentiles) |
| `decision_engine` | `PortfolioVolatilityResult` + `MarketStatus` | `Decision` (should_check, action_suggestion, rebalance details) |
| `report_engine` | all of the above | formatted string (daily digest or Markdown weekly report) |
| `ai_engine/analyzer.py` | `PortfolioVolatilityResult` + `AlertResult` | `Optional[str]` analysis text |
| `notification` | report string + alert | console / file / email dispatch |

`src/main.py:AntiFOMO` is the sole orchestrator for the v1 pipeline. New v1 features
should be added as engine methods and wired up in `run_check()` or `run_weekly_report()`.

### v2 Engines (complete, do not modify core logic)

| Engine | Input | Output |
|--------|-------|--------|
| `template_engine/templates.py` | static data + optional `base_datas/template_metrics.json` | `List[PortfolioTemplate]` |
| `template_engine/comparator.py` | user holdings + `PortfolioTemplate` | `ComparisonResult` (diffs, metrics delta) |
| `ai_engine/template_advisor.py` | user holdings + template | `str` (personality match or migration advice) |

New `serve.py` API endpoints (v2):
- `GET /api/templates` — template list with metrics and personality tags
- `GET /api/templates/{id}` — single template detail
- `POST /api/compare` — user config vs. template comparison
- `POST /api/ai/profile-match` — AI personality matching (optional)
- `POST /api/ai/migrate` — AI migration advice

### v3 Data Pipeline (new, active development)

| Script | Input | Output |
|--------|-------|--------|
| `scripts/fetch_index_data.py` | akshare APIs | `base_datas/index_weekly.csv` |
| `scripts/calc_template_metrics.py` | `index_weekly.csv` | `base_datas/template_metrics.json`, `base_datas/index_metrics.json` |

`templates.py` loads `template_metrics.json` at startup to override hard-coded values.
`comparator.py` loads `index_metrics.json` to replace hard-coded `_CATEGORY_RETURN` / `_CATEGORY_VOL` dicts.
Both fall back gracefully to hard-coded values if `base_datas/` files are absent.

## Code Style Guidelines

### General

- Language: Python 3.x.
- **No emoji anywhere** -- logs, code, comments, commit messages, docs.
  Keep all output concise, professional, and clear.
- Favor small, readable functions over deep abstraction.
- Avoid unnecessary comments; explain only non-obvious behavior.

### Imports

- Standard library first, then third-party, then local imports.
- Keep imports at top of file. Lazy imports inside functions are acceptable
  for heavy or optional deps (e.g., `import schedule`, `import akshare`).
- Use explicit imports; no wildcards.
- `TYPE_CHECKING` guards are acceptable for cross-engine type hints to avoid
  circular imports (see `pace_controller.py` for the pattern).

### Formatting

- Indentation: 4 spaces.
- Use double quotes for string literals and `dict.get()` defaults.
  Dict key subscript access (`data['key']`) may use single quotes; this is an
  existing minor inconsistency — prefer double quotes for new code.
- Keep line length reasonable (100-120 chars).
- Prefer f-strings for formatting.
- Do not auto-format or reorder YAML keys unless necessary.

### Types

- Use type hints for public functions and dataclass fields.
- Prefer `Optional[T]` for nullable values.
- Dataclasses (`@dataclass`) are the standard for data containers.
  Implement `__str__` on dataclasses when human-readable output is useful.
- LSP errors for `pandas`, `openai`, `schedule` are environment false-positives
  (sys.path injection). Do not add type: ignore comments just to silence them.

### Naming Conventions

- Classes: `CamelCase` (e.g., `AntiFOMO`, `DataFetcher`, `PaceController`).
- Functions / variables: `snake_case`.
- Private helpers: prefix with `_` (e.g., `_load_config`, `_make_decision`).
- Constants: `UPPER_SNAKE_CASE` (e.g., `PORT`, `BASE_DIR`).
- Enums: `CamelCase` class, `UPPER_SNAKE_CASE` members
  (e.g., `AlertLevel.WARNING`, `MarketState.CHEAP`).
- File names: `snake_case.py`.

### Error Handling

- Prefer graceful failure with clear console messages.
- For external calls (network / API), wrap in try/except and return safe
  defaults (empty DataFrame, `None`) where appropriate.
- `_evaluate_index` in `market_scorer.py` wraps the entire body in try/except
  to handle both akshare failures and column-name changes gracefully -- follow
  this pattern for any new external-data processing function.
- Use `raise SystemExit(1)` only for truly fatal config errors (missing
  `config.asset.yaml`, empty holdings).
- Use `ValueError` only for programmer errors (invalid arguments).
- Avoid raising exceptions for user-supplied config unless the system
  cannot proceed; print an error and return a safe default instead.

### IO and Side Effects

- Configuration parsing lives in `src/main.py:_load_config`.
- Portfolio data fetching is centralized in `src/portfolio_engine/data_fetcher.py`.
- Market valuation fetching is centralized in `src/market_engine/valuation_fetcher.py`.
- Notification output is centralized in `src/notification/manager.py`.
- Weekly reports are written to `logs/weekly_YYYYMMDD.md` by `main.py:_save_weekly_report`.
- Avoid writing files outside `logs/` and `cache/`.

### Caching

- Market PE/PB data is cached in `cache/` as pickle + JSON meta files.
- Cache key format: `pe_{symbol}` / `pb_{symbol}` (Chinese names; known tech
  debt on Windows/NAS paths -- do not change the format without also fixing the
  path-safety issue).
- TTL default: 24 hours (configurable via `config.yaml cache.ttl_hours`).
- Do not bypass the cache in production paths; always go through `ValuationFetcher`.

### AI Analysis

- `src/ai_engine/analyzer.py` is the only module that calls LLM APIs for v1 monitoring.
- v2 adds `src/ai_engine/template_advisor.py` for template personality matching and
  migration advice. Keep these two files separate; do not mix concerns.
- Current v1 interface: `analyze(portfolio_result, alert_result) -> Optional[str]`.
- Do not hardcode API keys; use environment variables or config.

### Asset Configuration

- `serve.py` serves `web/` and provides the config generation API.
- `config.asset.yaml` is the sole source of holdings for `run.py`.
- Keep the web asset schema simple: name, code, amount, type, region, style.
- `src/asset_configurator.py` is the legacy interactive CLI wizard
  (superseded by `serve.py`). Keep it functional but do not expand it.

### Template Engine (v2)

- Template data (allocations, metrics, personality tags) is initially static JSON
  baked into `src/template_engine/templates.py`. Do not fetch live data for templates.
- Quantitative metrics (annualized return, Sharpe ratio, max drawdown) are
  historical simulation approximations. Always surface the data period (e.g.,
  "2010-2024 historical simulation") to avoid misleading users.
- `TemplateComparator` reads user holdings from `config.asset.yaml`; it must not
  call akshare or any live data source.

### v3 Data Pipeline

- `scripts/fetch_index_data.py` and `scripts/calc_template_metrics.py` are offline,
  on-demand scripts. They are never imported by `serve.py` or `run.py`.
- Output files live in `base_datas/` (gitignored). Both `templates.py` and
  `comparator.py` fall back to hard-coded values when these files are absent.
- `index_global_hist_em` returns a column named `最新价` (not `收盘`); rename it
  before merging with domestic index data.
- Wrap every akshare call in try/except; print a warning and skip on failure.
- `短期债券` and `货币基金` have no index proxy — simulate with fixed annual
  constants (2.5% and 2.0% respectively); vol = 0, drawdown = 0.
- Use weekly (Friday close) aggregation for all index series. Daily granularity
  is not needed for template-level metrics.

### Frontend (v2)

- `web/` remains a zero-build-tool vanilla HTML/CSS/JS SPA. No React, Vue, or
  bundlers.
- The current `web/app.js` contains a hand-implemented squarified treemap renderer
  and a modal-based asset edit/delete flow. Do not replace these with library
  components unless explicitly instructed.
- Charts: use **Chart.js** via CDN (pie, radar, bar). No other charting libraries.
- New JS files are split by feature: `templates.js`, `compare.js`, `charts.js`.
- All API calls use `fetch`; do not introduce axios or other HTTP clients.

## Repository Conventions

- No Cursor or Copilot rule files are present.
- Keep `config.yaml` free of secrets and free of portfolio holdings.
- Documentation: `README.md` (user-facing), `AGENTS.md` (agent guidance).
  Do not create additional top-level markdown docs.
- `docs/` holds short-term dev memory between sessions. Not for user-facing docs.
- `web/` is a vanilla HTML/CSS/JS SPA with no build tools or frameworks.
- Several files in `src/` have iCloud conflict duplicates named `"<name> 2.py"`
  (e.g., `portfolio 2.py`, `data_fetcher 2.py`). These are never imported and
  should be ignored; do not edit or create files with space-and-number suffixes.

## Suggested Manual Verification

```bash
python3 serve.py          # open browser, verify template library and compare views
python3 run.py            # confirm v1 daily check still completes with DailyDigest output
python3 run.py weekly     # confirm weekly report generates and saves to logs/
python3 scripts/fetch_index_data.py        # verify akshare interfaces are reachable
python3 scripts/calc_template_metrics.py   # verify metrics output to base_datas/
```
