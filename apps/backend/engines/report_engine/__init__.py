"""
report_engine -- 报告生成

将各 engine 输出组装为人类可读的报告.
"""
from .daily_digest import DailyDigest
from .weekly_report import WeeklyReport

__all__ = [
    "DailyDigest",
    "WeeklyReport",
]
