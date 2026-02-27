#!/usr/bin/env python3
import http.server
import socketserver
import json
import os
import sys
import yaml
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Ensure src/ is in the python path to satisfy bare package imports like `from portfolio_engine import ...`
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# v2 engines
from src.template_engine.templates import TemplateLibrary
from src.template_engine.comparator import TemplateComparator
from src.ai_engine.template_advisor import TemplateAdvisor

PORT = 8080
BASE_DIR = Path(__file__).resolve().parent
# Modified to serve the Vue dist directory
WEB_DIR = BASE_DIR / "web" / "dist"
CONFIG_FILE = BASE_DIR / "config.asset.yaml"

class AntiFOMOHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        
        # API: Get current portfolio config
        if parsed.path == "/api/assets":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    try:
                        data = yaml.safe_load(f)
                        if not data:
                            data = {"portfolio": {"total_amount": 0, "holdings": []}}
                        self.wfile.write(json.dumps(data).encode())
                    except yaml.YAMLError:
                        self.wfile.write(json.dumps({"portfolio": {"total_amount": 0, "holdings": []}}).encode())
            else:
                self.wfile.write(json.dumps({"portfolio": {"total_amount": 0, "holdings": []}}).encode())
            return
            
        # API: Get templates list
        elif parsed.path == "/api/templates":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            library = TemplateLibrary()
            templates = library.get_all_templates()
            # Convert dataclass objects to dicts
            result = [
                {
                    "id": t.id,
                    "name": t.name,
                    "description": t.description,
                    "metrics": {
                        "expected_return": t.metrics.expected_return,
                        "volatility": t.metrics.volatility,
                        "max_drawdown": t.metrics.max_drawdown,
                        "sharpe_ratio": t.metrics.sharpe_ratio
                    },
                    "allocation": t.allocation,
                    "personality_tags": t.personality_tags
                }
                for t in templates
            ]
            self.wfile.write(json.dumps(result).encode())
            return
            
        # Add fallback for Vue router history mode
        # If it's not an API route and not a static file, serve index.html
        if not parsed.path.startswith("/api/"):
            file_path = WEB_DIR / parsed.path.lstrip("/")
            if not file_path.exists() or not file_path.is_file():
                self.path = "/"
                
        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        
        # API: Save portfolio config
        if parsed.path == "/api/save":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                # Cleanup _localId if it exists from frontend
                if 'portfolio' in data and 'holdings' in data['portfolio']:
                    for holding in data['portfolio']['holdings']:
                        if '_localId' in holding:
                            del holding['_localId']
                
                with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
                    
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
            return
            
        # API: Compare portfolio vs template
        elif parsed.path == "/api/compare":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                portfolio_data = data.get('portfolio', {})
                template_id = data.get('template_id')
                
                if not template_id:
                    raise ValueError("Missing template_id")
                    
                # Convert frontend portfolio payload to src/models/portfolio.py structure
                # Simplified for the comparator
                
                library = TemplateLibrary()
                template = library.get_template(template_id)
                if not template:
                    raise ValueError(f"Template {template_id} not found")
                    
                comparator = TemplateComparator()
                result = comparator.compare(portfolio_data, template)
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                
                # Convert dataclass to dict
                response_data = {
                    "dimensions": result.dimensions,
                    "metrics_delta": result.metrics_delta
                }
                self.wfile.write(json.dumps(response_data).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
            return
            
        # API: AI Personality Match
        elif parsed.path == "/api/ai/profile-match":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                portfolio_data = data.get('portfolio', {})
                
                advisor = TemplateAdvisor()
                advice = advisor.analyze_personality(portfolio_data)
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"advice": advice}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
            return
            
        # API: AI Migration Advice
        elif parsed.path == "/api/ai/migrate":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                portfolio_data = data.get('portfolio', {})
                template_id = data.get('template_id')
                
                library = TemplateLibrary()
                template = library.get_template(template_id)
                
                advisor = TemplateAdvisor()
                advice = advisor.get_migration_advice(portfolio_data, template)
                
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"advice": advice}).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode())
            return
            
        self.send_response(404)
        self.end_headers()

if __name__ == "__main__":
    import sys
    
    # Check if web/dist exists
    if not WEB_DIR.exists() or not (WEB_DIR / "index.html").exists():
        print(f"Error: Could not find web frontend build at {WEB_DIR}")
        print("Please build the frontend first:")
        print("  cd web && npm install && npm run build:local")
        sys.exit(1)
        
    with socketserver.TCPServer(("", PORT), AntiFOMOHandler) as httpd:
        print(f"Anti-FOMO Web UI serving at http://localhost:{PORT}")
        print(f"Serving static files from: {WEB_DIR}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
