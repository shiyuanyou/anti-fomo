"""
Volatility Calculator
波动率计算模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class VolatilityResult:
    """波动率计算结果"""
    symbol: str          # 代码
    name: str           # 名称
    current_price: float # 当前价格
    previous_price: float # 前一日价格
    change_pct: float   # 涨跌幅(%)
    volatility: float   # 波动率
    weight: float       # 权重
    month_return_pct: float  # 近一月涨跌幅(%)
    
    def __str__(self) -> str:
        return (f"{self.name}({self.symbol}): "
                f"当前价 {self.current_price:.2f}, "
                f"涨跌幅 {self.change_pct:+.2f}%, "
                f"波动率 {self.volatility:.2f}%, "
                f"权重 {self.weight:.2%}")


@dataclass
class PortfolioVolatilityResult:
    """组合波动率结果"""
    total_volatility: float              # 总体波动率
    individual_results: List[VolatilityResult]  # 个股波动率
    weighted_volatility: float           # 加权波动率
    max_volatility_holding: VolatilityResult   # 波动最大的持仓
    
    def __str__(self) -> str:
        lines = [
            f"组合总波动: {self.total_volatility:.2f}%",
            f"加权波动: {self.weighted_volatility:.2f}%",
            f"最大波动持仓: {self.max_volatility_holding.name} ({self.max_volatility_holding.volatility:.2f}%)",
            "\n个股明细:"
        ]
        for result in self.individual_results:
            lines.append(f"  {str(result)}")
        return "\n".join(lines)


class VolatilityCalculator:
    """波动率计算器"""
    
    @staticmethod
    def calculate_daily_return(current: float, previous: float) -> float:
        """
        计算日收益率
        
        Args:
            current: 当前价格
            previous: 前一日价格
            
        Returns:
            收益率(百分比)
        """
        if previous == 0:
            return 0.0
        return ((current - previous) / previous) * 100
    
    @staticmethod
    def calculate_volatility(prices: pd.Series, window: int = 20) -> float:
        """
        计算历史波动率（标准差）
        
        Args:
            prices: 价格序列
            window: 计算窗口
            
        Returns:
            波动率(百分比)
        """
        if len(prices) < 2:
            return 0.0
        
        returns = prices.pct_change().dropna()
        if len(returns) < window:
            window = len(returns)
        
        volatility = returns.tail(window).std() * 100
        return float(volatility)
    
    @staticmethod
    def calculate_individual_volatility(
        df: pd.DataFrame,
        symbol: str,
        name: str,
        weight: float
    ) -> VolatilityResult:
        """
        计算单个持仓的波动率
        
        Args:
            df: 价格数据
            symbol: 代码
            name: 名称
            weight: 权重
            
        Returns:
            波动率结果
        """
        if df.empty or len(df) < 2:
            return VolatilityResult(
                symbol=symbol,
                name=name,
                current_price=0,
                previous_price=0,
                change_pct=0,
                volatility=0,
                weight=weight,
                month_return_pct=0
            )
        
        current_price = float(df.iloc[-1]['收盘'])
        previous_price = float(df.iloc[-2]['收盘'])
        change_pct = VolatilityCalculator.calculate_daily_return(current_price, previous_price)
        volatility = VolatilityCalculator.calculate_volatility(df['收盘'])
        month_return_pct = VolatilityCalculator.calculate_month_return(df['收盘'])
        
        return VolatilityResult(
            symbol=symbol,
            name=name,
            current_price=current_price,
            previous_price=previous_price,
            change_pct=change_pct,
            volatility=volatility,
            weight=weight,
            month_return_pct=month_return_pct
        )

    @staticmethod
    def calculate_month_return(prices: pd.Series, window: int = 21) -> float:
        """
        计算近一月涨跌幅（默认 21 个交易日）

        Args:
            prices: 价格序列
            window: 交易日窗口

        Returns:
            近一月涨跌幅(百分比)
        """
        if len(prices) < 2:
            return 0.0

        current = float(prices.iloc[-1])
        base_index = -window - 1 if len(prices) > window else 0
        base = float(prices.iloc[base_index])
        if base == 0:
            return 0.0
        return ((current - base) / base) * 100
    
    @staticmethod
    def calculate_portfolio_volatility(
        individual_results: List[VolatilityResult]
    ) -> PortfolioVolatilityResult:
        """
        计算组合整体波动率
        
        Args:
            individual_results: 个股波动率结果列表
            
        Returns:
            组合波动率结果
        """
        if not individual_results:
            raise ValueError("个股结果列表不能为空")
        
        # 加权波动率
        weighted_volatility = sum(
            r.volatility * r.weight for r in individual_results
        )
        
        # 总体收益率（加权）
        total_return = sum(
            r.change_pct * r.weight for r in individual_results
        )
        
        # 找出波动最大的持仓
        max_vol_holding = max(individual_results, key=lambda x: abs(x.volatility))
        
        return PortfolioVolatilityResult(
            total_volatility=abs(total_return),
            individual_results=individual_results,
            weighted_volatility=weighted_volatility,
            max_volatility_holding=max_vol_holding
        )
