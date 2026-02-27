"""
Migrate hardcoded templates from src/template_engine/templates.py to SQLite database.
This is a one-time migration script for v3.3+.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import yaml
from src.template_engine.templates import TemplateLibrary
from api.models import create_tables, get_database_url
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def convert_template_to_allocation(tmpl) -> dict:
    """Convert PortfolioTemplate allocations to allocation dict"""
    allocation = {}
    for alloc in tmpl.allocations:
        # Create symbol from category and region
        symbol = f"{alloc.category}-{alloc.region}"
        symbol = symbol.lower().replace(" ", "_").replace("/", "_")
        allocation[symbol] = int(alloc.weight * 100)  # Convert to percentage
    return allocation


def convert_template_to_metrics(tmpl) -> dict:
    """Convert TemplateMetrics to metrics dict"""
    metrics = tmpl.metrics
    return {
        "expected_return": metrics.annualized_return / 100,  # Convert to decimal
        "volatility": metrics.annualized_volatility / 100,
        "max_drawdown": metrics.max_drawdown / 100,
        "sharpe_ratio": metrics.sharpe_ratio,
        "data_period": metrics.data_period
    }


def migrate_templates():
    """Migrate all templates to SQLite database"""
    print("Starting template migration...")

    # Import here to avoid circular import
    from api import models, schemas, crud

    # Create database tables
    create_tables()
    print(f"Created database at: {get_database_url()}")

    # Create session
    engine = create_engine(get_database_url())
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Clear existing templates
        db.query(models.Template).delete()
        db.commit()
        print("Cleared existing templates")

        # Get all templates
        templates = TemplateLibrary.all()
        print(f"Found {len(templates)} templates to migrate")

        for i, tpl in enumerate(templates, 1):
            print(f"\nMigrating template {i}/{len(templates)}: {tpl.name} ({tpl.id})")

            # Convert to allocation dict
            allocation = convert_template_to_allocation(tpl)
            print(f"  - Allocation: {allocation}")

            # Convert metrics
            metrics = convert_template_to_metrics(tpl)
            print(f"  - Metrics: {metrics}")

            # Convert tags
            tags = tpl.personality_tags
            print(f"  - Tags: {tags}")

            # Create template schema
            template_create = schemas.TemplateCreate(
                id=f"AF-T{i:03d}",  # Generate new ID format
                name=tpl.name,
                description=tpl.personality_description,
                allocation=allocation,
                metrics=metrics,
                tags=tags
            )

            # Create in database
            crud.create_template(db, template_create)
            print(f"  ✓ Migrated successfully")

        db.commit()
        print(f"\n✅ Migration completed! Migrated {len(templates)} templates")

        # Verify by reading back
        count = db.query(models.Template).count()
        print(f"✅ Verified: {count} templates in database")

    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    migrate_templates()
