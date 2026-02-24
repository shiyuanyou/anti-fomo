"""
Percentile Calculator
百分位计算 -- 计算当前值在历史序列中的百分位排名
"""
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional


class PercentileCalculator:
    """历史百分位计算器"""

    @staticmethod
    def calculate(series: pd.Series, current_value: float) -> float:
        """
        计算 current_value 在 series 中的百分位 (0-100)

        使用排名百分位: 历史上有多少比例的值 <= current_value.

        Args:
            series: 历史数值序列
            current_value: 当前值

        Returns:
            百分位 (0-100), 序列为空则返回 50.0
        """
        valid = series.dropna()
        if valid.empty:
            return 50.0
        count_le = (valid <= current_value).sum()
        return float(count_le / len(valid) * 100)

    @staticmethod
    def calculate_with_window(
        df: pd.DataFrame,
        date_col: str,
        value_col: str,
        current_value: float,
        years: int = 10,
        as_of: Optional[datetime] = None,
    ) -> float:
        """
        只用近 N 年数据计算百分位

        Args:
            df: 含日期列和数值列的 DataFrame
            date_col: 日期列名
            value_col: 数值列名
            current_value: 当前值
            years: 回看窗口 (年), 默认 10
            as_of: 计算截止日期, 默认今天

        Returns:
            百分位 (0-100)
        """
        if df.empty:
            return 50.0

        if as_of is None:
            as_of = datetime.now()

        cutoff = as_of - timedelta(days=years * 365)
        dates = pd.to_datetime(df[date_col])
        mask = dates >= cutoff
        windowed = df.loc[mask, value_col]

        return PercentileCalculator.calculate(windowed, current_value)
