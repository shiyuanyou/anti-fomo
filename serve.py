"""
HTTP server for the Anti-FOMO visualization frontend with asset configuration API.

Endpoints:
    GET  /api/assets  — Return current web assets from config.asset.yaml (or []).
    POST /api/save    — Accept JSON asset list, generate config.asset.yaml.
    *    /*            — Static files from web/ directory.

Usage: python serve.py [port]
Then open http://localhost:8080 in your browser.
"""

import http.server
import socketserver
import os
import sys
import json
from pathlib import Path
from datetime import datetime

import yaml

PORT = 8080
BASE_DIR = Path(__file__).parent.resolve()
WEB_DIR = BASE_DIR / "web"
CONFIG_ASSET_PATH = BASE_DIR / "config.asset.yaml"


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

    # --- POST ----------------------------------------------------------

    def do_POST(self):
        if self.path == "/api/save":
            self._handle_save()
        else:
            self.send_error(404)

    def _handle_save(self):
        """Accept JSON asset list, generate config.asset.yaml."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            web_assets = json.loads(body)
        except (json.JSONDecodeError, ValueError):
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
        print(f"  API: GET /api/assets  POST /api/save\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.")


if __name__ == "__main__":
    main()
