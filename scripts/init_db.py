#!/usr/bin/env python3
"""
Initialize database from web/public/templates.json
This replaces the old migrate_templates.py
"""
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.models import create_tables, SessionLocal
from api.schemas import TemplateCreate, TemplateMetrics, AllocationItem
from api.crud import create_template, delete_all_templates


def load_templates_from_json() -> list:
    """Load templates from web/public/templates.json"""
    json_path = project_root / "web" / "public" / "templates.json"
    
    if not json_path.exists():
        print(f"❌ Error: {json_path} not found")
        sys.exit(1)
    
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("templates", [])


def convert_to_schema(template_data: dict) -> TemplateCreate:
    """Convert JSON template to TemplateCreate schema"""
    original = template_data.get("original_data", template_data)
    
    # Convert allocations
    allocations = []
    for alloc in original.get("allocations", []):
        allocations.append(AllocationItem(
            category=alloc["category"],
            region=alloc["region"],
            weight=alloc["weight"]
        ))
    
    # Convert metrics
    metrics_data = template_data.get("metrics", {})
    metrics = TemplateMetrics(
        expected_return=metrics_data.get("expected_return", 0),
        volatility=metrics_data.get("volatility", 0),
        max_drawdown=metrics_data.get("max_drawdown", 0),
        sharpe_ratio=metrics_data.get("sharpe_ratio", 0),
        data_period=metrics_data.get("data_period", "")
    )
    
    # Build allocation dict (simple format)
    allocation = template_data.get("allocation", {})
    
    return TemplateCreate(
        id=template_data["id"],
        name=template_data["name"],
        tagline=original.get("tagline", ""),
        description=template_data["description"],
        target_audience=original.get("target_audience", ""),
        risk_level=original.get("risk_level", "中"),
        allocations=allocations,
        allocation=allocation,
        metrics=metrics,
        personality_tags=template_data.get("personality_tags", []),
        original_data=original,
    )


def init_database():
    """Initialize database from templates.json"""
    print("=" * 60)
    print("Anti-FOMO Database Initialization")
    print("=" * 60)
    
    # Create tables
    print("\n📦 Creating database tables...")
    create_tables()
    print("✅ Tables created")
    
    # Load templates
    print("\n📂 Loading templates from web/public/templates.json...")
    templates_data = load_templates_from_json()
    print(f"✅ Found {len(templates_data)} templates")
    
    # Initialize database
    db = SessionLocal()
    try:
        # Clear existing
        print("\n🗑️  Clearing existing templates...")
        count = delete_all_templates(db)
        print(f"✅ Deleted {count} old templates")
        
        # Import templates
        print(f"\n📥 Importing {len(templates_data)} templates...")
        for i, template_data in enumerate(templates_data, 1):
            print(f"\n  {i}/{len(templates_data)}: {template_data['id']}")
            
            # Convert and create
            template_create = convert_to_schema(template_data)
            created = create_template(db, template_create)
            
            print(f"    ✅ {created.name}")
            print(f"       Risk: {created.risk_level} | Return: {template_create.metrics.expected_return}%")
        
        print(f"\n{'=' * 60}")
        print(f"✅ Successfully imported {len(templates_data)} templates!")
        print(f"{'=' * 60}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    init_database()
