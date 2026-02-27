"""
CRUD package initialization
"""
from .template import (
    get_template,
    get_templates,
    create_template,
    delete_template,
    delete_all_templates,
)
from .share import (
    get_share,
    get_shares,
    create_share,
    delete_share,
    generate_share_id,
)

__all__ = [
    # Template
    "get_template",
    "get_templates",
    "create_template",
    "delete_template",
    "delete_all_templates",
    # Share
    "get_share",
    "get_shares",
    "create_share",
    "delete_share",
    "generate_share_id",
]
