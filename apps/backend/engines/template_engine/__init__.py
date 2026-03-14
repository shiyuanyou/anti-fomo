"""
Template engine for v2 portfolio template library and comparison.

Public API:
    TemplateLibrary     - access all built-in portfolio templates
    TemplateComparator  - compare user holdings against a template
    PortfolioTemplate   - template data container
    TemplateMetrics     - quantitative metrics container
    AssetAllocation     - single allocation entry
    ComparisonResult    - result of a user vs. template comparison
    AllocationDiff      - per-category deviation
"""

from .templates import (
    AssetAllocation,
    TemplateMetrics,
    PortfolioTemplate,
    TemplateLibrary,
)
from .comparator import (
    AllocationDiff,
    ComparisonResult,
    TemplateComparator,
)

__all__ = [
    "AssetAllocation",
    "TemplateMetrics",
    "PortfolioTemplate",
    "TemplateLibrary",
    "AllocationDiff",
    "ComparisonResult",
    "TemplateComparator",
]
