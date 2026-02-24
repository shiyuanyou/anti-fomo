"""
HTTP server for the Anti-FOMO visualization frontend with asset configuration API.

Endpoints:
    GET  /api/assets              — Return current web assets from config.asset.yaml (or []).
    POST /api/save                — Accept JSON asset list, generate config.asset.yaml.
    GET  /api/templates           — Return all portfolio templates (v2).
    GET  /api/templates/{id}      — Return single template by ID (v2).
    POST /api/compare             — Compare user config vs. a template (v2).
    POST /api/ai/profile-match    — AI personality matching (v2).
    POST /api/ai/migrate          — AI migration advice (v2).
    *    /*                        — Static files from web/ directory.

Usage: python serve.py [port]
Then open http://localhost:8080 in your browser.
"""

import http.server
import socketserver
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

import yaml

PORT = 8080
BASE_DIR = Path(__file__).parent.resolve()
WEB_DIR = BASE_DIR / "web"
CONFIG_ASSET_PATH = BASE_DIR / "config.asset.yaml"
SRC_DIR = BASE_DIR / "src"

# Add src/ to path so template_engine and ai_engine can be imported.
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


# ------------------------------------------------------------------
#  Lazy imports for v2 engines (imported on first request)
# ------------------------------------------------------------------

def _get_template_library():
    from template_engine import TemplateLibrary
    return TemplateLibrary


def _get_comparator():
    from template_engine import TemplateComparator
    return TemplateComparator


def _get_template_advisor():
    from ai_engine.template_advisor import TemplateAdvisor
    return TemplateAdvisor


# ------------------------------------------------------------------
#  Config generation helpers
# ------------------------------------------------------------------

def _build_categories(web_assets):
    """Build a two-level category tree from flat web assets.

    Level 1 = type (股票 / 大宗商品 / 货币基金 / …)
    Level 2 = region (中国大陆 / 美国 / …)
    Items are placed under their region sub-category.
    """
    total_amount = sum(a.get("amount", 0) for a in web_assets)

    # type -> region -> [asset, …]
    type_map: dict = {}
    for a in web_assets:
        t = a.get("type", "其他")
        r = a.get("region", "其他")
        type_map.setdefault(t, {}).setdefault(r, []).append(a)

    categories = []
    for type_name, regions in type_map.items():
        children = []
        for region_name, items in regions.items():
            region_items = []
            for item in items:
                ratio = (item["amount"] / total_amount * 100) if total_amount > 0 else 0
                region_items.append({
                    "name": item["name"],
                    "code": item.get("code", ""),
                    "ratio": round(ratio, 2),
                    "auto_calculate": bool(item.get("code")),
                    "start_price": None,
                })
            children.append({
                "name": region_name,
                "items": region_items,
                "children": [],
            })
        categories.append({
            "name": type_name,
            "items": [],
            "children": children,
        })

    return categories


def _collect_items_from_tree(cat):
    """Recursively collect all items from a serialized category dict."""
    items = list(cat.get("items", []))
    for child in cat.get("children", []):
        items.extend(_collect_items_from_tree(child))
    return items


def _generate_config(web_assets):
    """Generate the full config dict to be written as config.asset.yaml."""
    categories = _build_categories(web_assets)

    all_items = []
    for cat in categories:
        all_items.extend(_collect_items_from_tree(cat))

    total_ratio = sum(item["ratio"] for item in all_items)
    calculable_items = [
        item for item in all_items
        if item.get("auto_calculate") and item.get("code")
    ]
    calculable_ratio = sum(item["ratio"] for item in calculable_items)
    calculable_weights = {}
    if calculable_ratio > 0:
        calculable_weights = {
            item["code"]: round(item["ratio"] / calculable_ratio, 6)
            for item in calculable_items
        }
    equity_start = {
        item["code"]: item["start_price"]
        for item in calculable_items
        if item.get("start_price") is not None
    }

    holdings = []
    for item in all_items:
        if not item.get("code"):
            continue
        holdings.append({
            "symbol": item["code"],
            "name": item["name"],
            "type": "index",
            "allocation_type": "ratio",
            "value": item["ratio"],
        })

    config = {
        "portfolio": {"holdings": holdings},
        "asset_allocation": {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "categories": categories,
            "total_ratio": round(total_ratio, 2),
            "calculable_ratio": round(calculable_ratio, 2),
            "calculable_weights": calculable_weights,
            "equity_start": equity_start,
        },
        "web_assets": web_assets,
    }
    return config


# ------------------------------------------------------------------
#  HTTP Handler
# ------------------------------------------------------------------

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    # --- GET -----------------------------------------------------------

    def do_GET(self):
        if self.path == "/api/assets":
            self._handle_get_assets()
        elif self.path == "/api/templates":
            self._handle_get_templates()
        elif re.match(r"^/api/templates/[^/]+$", self.path):
            template_id = self.path.split("/")[-1]
            self._handle_get_template(template_id)
        else:
            super().do_GET()

    def _handle_get_assets(self):
        """Return web_assets from config.asset.yaml, or [] if not found."""
        assets = []
        if CONFIG_ASSET_PATH.exists():
            try:
                with open(CONFIG_ASSET_PATH, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                if config and isinstance(config.get("web_assets"), list):
                    assets = config["web_assets"]
            except Exception:
                pass  # return empty list on any parse failure
        self._json_response(200, assets)

    def _handle_get_templates(self):
        """Return all portfolio templates as a JSON array."""
        try:
            lib = _get_template_library()
            templates = [t.to_dict() for t in lib.all()]
            self._json_response(200, templates)
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_get_template(self, template_id: str):
        """Return a single template by ID."""
        try:
            lib = _get_template_library()
            template = lib.get(template_id)
            if template is None:
                self._json_response(404, {"error": f"Template '{template_id}' not found"})
                return
            self._json_response(200, template.to_dict())
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    # --- POST ----------------------------------------------------------

    def do_POST(self):
        if self.path == "/api/save":
            self._handle_save()
        elif self.path == "/api/compare":
            self._handle_compare()
        elif self.path == "/api/ai/profile-match":
            self._handle_ai_profile_match()
        elif self.path == "/api/ai/migrate":
            self._handle_ai_migrate()
        else:
            self.send_error(404)

    def _read_json_body(self):
        """Read and parse the request body as JSON. Returns (data, error_str)."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)
        try:
            return json.loads(body), None
        except (json.JSONDecodeError, ValueError) as e:
            return None, str(e)

    def _handle_save(self):
        """Accept JSON asset list, generate config.asset.yaml."""
        web_assets, err = self._read_json_body()
        if err:
            self._json_response(400, {"ok": False, "error": "Invalid JSON"})
            return

        if not isinstance(web_assets, list):
            self._json_response(400, {"ok": False, "error": "Expected a JSON array"})
            return

        try:
            config = _generate_config(web_assets)
            with open(CONFIG_ASSET_PATH, "w", encoding="utf-8") as f:
                yaml.safe_dump(config, f, allow_unicode=True, sort_keys=False)
            print(f"  config saved -> {CONFIG_ASSET_PATH}")
            self._json_response(200, {"ok": True})
        except Exception as e:
            self._json_response(500, {"ok": False, "error": str(e)})

    def _handle_compare(self):
        """Compare user config vs. a template. Body: {template_id, web_assets?}."""
        body, err = self._read_json_body()
        if err or not isinstance(body, dict):
            self._json_response(400, {"error": "Invalid JSON body"})
            return

        template_id = body.get("template_id")
        if not template_id:
            self._json_response(400, {"error": "Missing template_id"})
            return

        try:
            lib = _get_template_library()
            template = lib.get(template_id)
            if template is None:
                self._json_response(404, {"error": f"Template '{template_id}' not found"})
                return

            Comparator = _get_comparator()
            comparator = Comparator()
            web_assets = body.get("web_assets")  # optional; if absent, load from file
            result = comparator.compare(template, web_assets=web_assets)

            response = {
                "template_id": result.template_id,
                "template_name": result.template_name,
                "user_total_amount": result.user_total_amount,
                "diffs": [
                    {
                        "category": d.category,
                        "region": d.region,
                        "user_weight": d.user_weight,
                        "template_weight": d.template_weight,
                        "deviation": d.deviation,
                    }
                    for d in result.diffs
                ],
                "user_metrics": {
                    "annualized_return": result.user_metrics.annualized_return,
                    "annualized_volatility": result.user_metrics.annualized_volatility,
                    "max_drawdown": result.user_metrics.max_drawdown,
                    "sharpe_ratio": result.user_metrics.sharpe_ratio,
                    "data_period": result.user_metrics.data_period,
                },
                "summary": result.summary,
            }
            self._json_response(200, response)
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_ai_profile_match(self):
        """AI personality matching. Body: {web_assets?}."""
        body, err = self._read_json_body()
        if err or not isinstance(body, dict):
            self._json_response(400, {"error": "Invalid JSON body"})
            return

        try:
            web_assets = body.get("web_assets")
            if not web_assets:
                Comparator = _get_comparator()
                web_assets = Comparator().load_web_assets()

            if not web_assets:
                self._json_response(400, {"error": "No asset configuration found"})
                return

            Advisor = _get_template_advisor()
            advisor = Advisor()
            result = advisor.match_personality(web_assets)
            self._json_response(200, {"result": result})
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    def _handle_ai_migrate(self):
        """AI migration advice. Body: {template_id, web_assets?}."""
        body, err = self._read_json_body()
        if err or not isinstance(body, dict):
            self._json_response(400, {"error": "Invalid JSON body"})
            return

        template_id = body.get("template_id")
        if not template_id:
            self._json_response(400, {"error": "Missing template_id"})
            return

        try:
            lib = _get_template_library()
            template = lib.get(template_id)
            if template is None:
                self._json_response(404, {"error": f"Template '{template_id}' not found"})
                return

            web_assets = body.get("web_assets")
            if not web_assets:
                Comparator = _get_comparator()
                web_assets = Comparator().load_web_assets()

            if not web_assets:
                self._json_response(400, {"error": "No asset configuration found"})
                return

            Advisor = _get_template_advisor()
            advisor = Advisor()
            result = advisor.suggest_migration(web_assets, template)
            self._json_response(200, {"result": result})
        except Exception as e:
            self._json_response(500, {"error": str(e)})

    # --- Helpers -------------------------------------------------------

    def _json_response(self, code, data):
        payload = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, format, *args):
        print(f"  {args[0]}")


# ------------------------------------------------------------------
#  Main
# ------------------------------------------------------------------

def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    with socketserver.TCPServer(("", port), Handler) as httpd:
        print(f"\n  Anti-FOMO Visualization")
        print(f"  http://localhost:{port}")
        print(f"  API: GET /api/assets  POST /api/save")
        print(f"       GET /api/templates  GET /api/templates/{{id}}")
        print(f"       POST /api/compare  POST /api/ai/profile-match  POST /api/ai/migrate\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.")


if __name__ == "__main__":
    main()
