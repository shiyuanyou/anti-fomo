"""
Market Scorer
市场状态评分 -- 综合指数 PE/PB 百分位, 输出市场估值状态
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from .cache import DataCache
from .valuation_fetcher import ValuationFetcher
from .percentile import PercentileCalculator


class MarketState(Enum):
    """市场估值状态"""
    CHEAP = "cheap"
    NORMAL = "normal"
    EXPENSIVE = "expensive"


@dataclass
class IndexValuation:
    """单个指数的估值数据"""
    symbol: str
    name: str
    pe_ttm: float
    pb: float
    pe_percentile: float
    pb_percentile: float
    score: float

    def __str__(self) -> str:
        return (
            f"{self.name}({self.symbol}): "
            f"PE={self.pe_ttm:.2f} (百分位 {self.pe_percentile:.1f}%), "
            f"PB={self.pb:.2f} (百分位 {self.pb_percentile:.1f}%), "
            f"评分={self.score:.1f}"
        )


@dataclass
class MarketStatus:
    """市场整体状态"""
    indices: Dict[str, IndexValuation]
    composite_score: float
    market_state: MarketState
    updated_at: datetime

    def __str__(self) -> str:
        state_labels = {
            MarketState.CHEAP: "便宜",
            MarketState.NORMAL: "正常",
            MarketState.EXPENSIVE: "过热",
        }
        lines = [
            f"市场状态: {state_labels[self.market_state]} (综合评分 {self.composite_score:.1f})",
            f"更新时间: {self.updated_at.strftime('%Y-%m-%d %H:%M')}",
            "",
        ]
        for valuation in self.indices.values():
            lines.append(f"  {valuation}")
        return "\n".join(lines)


@dataclass
class IndexConfig:
    """单个指数的配置"""
    symbol: str
    code: str
    weight: float


class MarketScorer:
    """市场估值评分器"""

    def __init__(self, config: Dict):
        """
        Args:
            config: market_engine 配置字典, 结构:
                indices: [{symbol, code, weight}, ...]
                percentile_window_years: int
                thresholds: {cheap: int, expensive: int}
                cache: {enabled: bool, dir: str, ttl_hours: int}  (可选, 来自顶层)
        """
        self.indices = self._parse_indices(config.get("indices", []))
        self.window_years = config.get("percentile_window_years", 10)
        thresholds = config.get("thresholds", {})
        self.cheap_threshold = thresholds.get("cheap", 20)
        self.expensive_threshold = thresholds.get("expensive", 80)

        cache_config = config.get("_cache_config")
        cache = None
        if cache_config and cache_config.get("enabled", True):
            cache = DataCache(
                cache_dir=cache_config.get("dir", "cache/"),
                ttl_hours=cache_config.get("ttl_hours", 24),
            )

        self.fetcher = ValuationFetcher(cache=cache)
        self.percentile = PercentileCalculator()

    def _parse_indices(self, raw: List[Dict]) -> List[IndexConfig]:
        result = []
        for item in raw:
            result.append(IndexConfig(
                symbol=item["symbol"],
                code=item.get("code", ""),
                weight=item.get("weight", 1.0),
            ))
        return result

    def evaluate(self) -> Optional[MarketStatus]:
        """
        获取数据, 计算百分位, 打分, 判断状态.

        Returns:
            MarketStatus, 如果所有指数都获取失败则返回 None
        """
        if not self.indices:
            print("market_engine: 未配置指数")
            return None

        valuations: Dict[str, IndexValuation] = {}

        for idx_cfg in self.indices:
            valuation = self._evaluate_index(idx_cfg)
            if valuation is not None:
                valuations[idx_cfg.symbol] = valuation

        if not valuations:
            print("market_engine: 所有指数数据获取失败")
            return None

        composite = self._compute_composite(valuations)
        state = self._determine_state(composite)

        return MarketStatus(
            indices=valuations,
            composite_score=composite,
            market_state=state,
            updated_at=datetime.now(),
        )

    def _evaluate_index(self, idx_cfg: IndexConfig) -> Optional[IndexValuation]:
        """评估单个指数"""
        try:
            pe_df = self.fetcher.fetch_pe(idx_cfg.symbol)
            pb_df = self.fetcher.fetch_pb(idx_cfg.symbol)

            if pe_df.empty or pb_df.empty:
                print(f"  {idx_cfg.symbol}: 数据不完整, 跳过")
                return None

            pe_series = pe_df["滚动市盈率"].dropna()
            pb_series = pb_df["市净率"].dropna()

            if pe_series.empty or pb_series.empty:
                print(f"  {idx_cfg.symbol}: 有效数据为空 (全为 NaN), 跳过")
                return None

            pe_current = float(pe_series.iloc[-1])
            pb_current = float(pb_series.iloc[-1])

            pe_pct = self.percentile.calculate_with_window(
                pe_df, "日期", "滚动市盈率", pe_current, years=self.window_years
            )
            pb_pct = self.percentile.calculate_with_window(
                pb_df, "日期", "市净率", pb_current, years=self.window_years
            )

            score = (pe_pct + pb_pct) / 2

            return IndexValuation(
                symbol=idx_cfg.symbol,
                name=idx_cfg.symbol,
                pe_ttm=pe_current,
                pb=pb_current,
                pe_percentile=pe_pct,
                pb_percentile=pb_pct,
                score=score,
            )
        except Exception as e:
            print(f"  {idx_cfg.symbol}: 评估失败 ({e}), 跳过")
            return None

    def _compute_composite(self, valuations: Dict[str, IndexValuation]) -> float:
        """加权平均计算综合评分"""
        total_weight = 0.0
        weighted_sum = 0.0

        for idx_cfg in self.indices:
            if idx_cfg.symbol in valuations:
                v = valuations[idx_cfg.symbol]
                weighted_sum += v.score * idx_cfg.weight
                total_weight += idx_cfg.weight

        if total_weight == 0:
            return 50.0
        return weighted_sum / total_weight

    def _determine_state(self, score: float) -> MarketState:
        """根据综合评分判断市场状态"""
        if score < self.cheap_threshold:
            return MarketState.CHEAP
        if score > self.expensive_threshold:
            return MarketState.EXPENSIVE
        return MarketState.NORMAL
