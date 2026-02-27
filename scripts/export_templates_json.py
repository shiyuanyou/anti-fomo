#!/usr/bin/env python3
"""
scripts/export_templates_json.py — v3.3

Export templates.py data + template_metrics.json into a single JSON file
for frontend static consumption. This enables pure frontend deployment
without Python backend runtime.

This script should be run after calc_template_metrics.py to ensure
real historical metrics are included.

Output: web/public/templates.json (gets copied to dist/ by Vite during build)
"""

import json
import sys
from pathlib import Path

# Add project root to path to import src modules
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

# Paths
BASE_DATAS_DIR = ROOT / "base_datas"
TEMPLATE_METRICS_PATH = BASE_DATAS_DIR / "template_metrics.json"
OUTPUT_PATH = ROOT / "web" / "public" / "templates.json"

def export_templates():
    """Export template data to JSON file."""
    print("Exporting templates to JSON for frontend...")
    
    # Import template library
    try:
        from src.template_engine.templates import TemplateLibrary
    except Exception as e:
        print(f"Error importing TemplateLibrary: {e}")
        sys.exit(1)
    
    # Load real metrics if available
    real_metrics = {}
    if TEMPLATE_METRICS_PATH.exists():
        try:
            with open(TEMPLATE_METRICS_PATH, "r", encoding="utf-8") as f:
                metrics_data = json.load(f)
                real_metrics = metrics_data.get("templates", {})
            print(f"  Loaded real metrics for {len(real_metrics)} templates")
        except Exception as e:
            print(f"  Warning: Could not load template_metrics.json ({e}), using defaults")
    else:
        print("  Warning: template_metrics.json not found, using default metrics")
    
    # Export all templates
    library = TemplateLibrary()
    templates = library.all()
    
    output_data = {
        "exported_at": TEMPLATE_METRICS_PATH.exists() and metrics_data.get("calculated_at")
                     or "unknown",
        "data_period": TEMPLATE_METRICS_PATH.exists() and metrics_data.get("data_period")
                     or "default estimates",
        "templates": []
    }
    
    for template in templates:
        # Use base template data
        template_dict = template.to_dict()
        
        # Convert allocations to simpler format for frontend
        allocation_dict = {}
        for alloc in template.allocations:
            key = f"{alloc.category} ({alloc.region})" if alloc.region != "中国" else alloc.category
            allocation_dict[key] = round(alloc.weight * 100, 1)
        
        # Apply real metrics if available
        if template.id in real_metrics:
            real = real_metrics[template.id]
            template_dict["metrics"] = {
                "expected_return": round(real["annualized_return"], 2),
                "volatility": round(real["annualized_volatility"], 2),
                "max_drawdown": round(real["max_drawdown"], 2),
                "sharpe_ratio": round(real["sharpe_ratio"], 3),
                "data_period": template_dict.get("metrics", {}).get("data_period", "")
            }
        
        # Simplify for frontend consumption
        output_template = {
            "id": template.id,
            "name": template.name,
            "description": template.personality_description,
            "metrics": template_dict["metrics"],
            "allocation": allocation_dict,
            "personality_tags": template.personality_tags,
            "original_data": template_dict  # Keep full data for future extensibility
        }
        
        output_data["templates"].append(output_template)
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Write JSON file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Exported {len(templates)} templates to {OUTPUT_PATH}")
    print("  File will be served as /templates.json (static file)")
    
    return True

if __name__ == "__main__":
    success = export_templates()
    sys.exit(0 if success else 1)
