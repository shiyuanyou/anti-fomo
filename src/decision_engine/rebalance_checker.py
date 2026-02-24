"""
Rebalance Checker
再平衡检测 -- 对比当前持仓权重与目标权重, 判断是否需要再平衡
"""
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class RebalanceItem:
    """单个持仓的偏离情况"""
    symbol: str
    name: str
    target_weight: float    # 目标权重 (0-1)
    current_weight: float   # 当前权重 (0-1)
    deviation: float        # 偏离量 (百分点, 正为超配, 负为低配)

    def __str__(self) -> str:
        direction = "超配" if self.deviation > 0 else "低配"
        return (
            f"{self.name}({self.symbol}): "
            f"目标 {self.target_weight:.1%} -> 当前 {self.current_weight:.1%}, "
            f"{direction} {abs(self.deviation):.1f}pp"
        )


class RebalanceChecker:
    """
    再平衡检测器

    对比当前权重和目标权重, 当任一持仓偏离超过阈值时触发再平衡建议.
    """

    def __init__(self, threshold: float = 5.0):
        """
        Args:
            threshold: 偏离触发阈值, 单位百分点 (默认 5.0pp)
        """
        self.threshold = threshold

    def check(
        self,
        current_weights: Dict[str, float],
        target_weights: Dict[str, float],
        symbol_names: Optional[Dict[str, str]] = None,
    ) -> Tuple[bool, List[RebalanceItem]]:
        """
        检查是否需要再平衡.

        Args:
            current_weights: 当前权重 {symbol: weight}, weight 为 0-1 小数
            target_weights: 目标权重 {symbol: weight}, weight 为 0-1 小数
            symbol_names: 代码到名称的映射 (可选, 缺失时用代码代替)

        Returns:
            (需要再平衡: bool, 偏离明细列表)
        """
        if not target_weights:
            return False, []

        names = symbol_names or {}
        items: List[RebalanceItem] = []

        for symbol, target in target_weights.items():
            current = current_weights.get(symbol, 0.0)
            # 偏离量转换为百分点
            deviation_pp = (current - target) * 100.0
            if abs(deviation_pp) >= self.threshold:
                items.append(RebalanceItem(
                    symbol=symbol,
                    name=names.get(symbol, symbol),
                    target_weight=target,
                    current_weight=current,
                    deviation=deviation_pp,
                ))

        items.sort(key=lambda x: abs(x.deviation), reverse=True)
        return bool(items), items
