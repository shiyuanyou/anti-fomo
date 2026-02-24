"""
Pace Controller
决策节奏控制器 -- 融合 portfolio 和 market 信号, 输出行为建议
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from portfolio_engine import PortfolioVolatilityResult, AlertResult
    from market_engine import MarketStatus, MarketState

from .rebalance_checker import RebalanceChecker, RebalanceItem


@dataclass
class Decision:
    """决策结果"""
    should_check: bool                  # 是否需要看盘
    should_check_reason: str            # 原因
    action_suggestion: str              # 行动建议
    rebalance_needed: bool              # 是否需要再平衡
    rebalance_details: List[RebalanceItem] = field(default_factory=list)
    confidence: str = "高"              # 判断置信度: 高/中/低

    def __str__(self) -> str:
        lines = [
            f"是否需要看盘: {'是' if self.should_check else '否'}",
        ]
        if self.should_check_reason:
            lines.append(f"  原因: {self.should_check_reason}")
        lines.append(f"行动建议: {self.action_suggestion}")
        if self.rebalance_needed:
            lines.append(f"再平衡提示: 以下持仓偏离目标超过阈值")
            for item in self.rebalance_details:
                lines.append(f"  - {item}")
        lines.append(f"置信度: {self.confidence}")
        return "\n".join(lines)


class PaceController:
    """
    决策节奏控制器

    规则:
      1. 是否需要看盘:
         - 资产波动触发警报 AND 市场处于极端状态 (过热/便宜) -> 需要关注
         - 仅波动触发警报 -> 建议关注
         - 仅市场极端 -> 可选关注
         - 均正常 -> 忽略市场

      2. 是否需要再平衡: 由 RebalanceChecker 判断

      3. 行动建议: 基于市场状态给出定性建议
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Args:
            config: decision_engine 配置字典
                check_market_volatility: bool (默认 True)
                rebalance_threshold: float (默认 5.0)
        """
        cfg = config or {}
        self.check_market_volatility = cfg.get("check_market_volatility", True)
        rebalance_threshold = cfg.get("rebalance_threshold", 5.0)
        self.rebalance_checker = RebalanceChecker(threshold=rebalance_threshold)

    def decide(
        self,
        portfolio_result: "PortfolioVolatilityResult",
        alert_result: "AlertResult",
        market_status: Optional["MarketStatus"],
        current_weights: Optional[Dict[str, float]] = None,
        target_weights: Optional[Dict[str, float]] = None,
        symbol_names: Optional[Dict[str, str]] = None,
    ) -> Decision:
        """
        生成决策.

        Args:
            portfolio_result: 组合波动结果
            alert_result: 阈值告警结果
            market_status: 市场估值状态 (可为 None, 表示未启用)
            current_weights: 当前持仓权重 (用于再平衡检测)
            target_weights: 目标持仓权重 (用于再平衡检测)
            symbol_names: 代码->名称映射 (用于再平衡输出)

        Returns:
            Decision
        """
        # 延迟导入避免循环依赖
        from portfolio_engine.threshold import AlertLevel
        from market_engine.market_scorer import MarketState

        has_alert = alert_result.should_notify
        market_extreme = False
        market_cheap = False
        market_expensive = False

        if market_status is not None:
            market_extreme = market_status.market_state in (
                MarketState.CHEAP, MarketState.EXPENSIVE
            )
            market_cheap = market_status.market_state == MarketState.CHEAP
            market_expensive = market_status.market_state == MarketState.EXPENSIVE

        # --- 1. 是否需要看盘 ---
        should_check, check_reason = self._decide_check(
            has_alert, market_extreme, market_cheap, market_expensive,
            alert_result, market_status
        )

        # --- 2. 行动建议 ---
        action = self._build_action_suggestion(
            has_alert, market_cheap, market_expensive, market_status
        )

        # --- 3. 再平衡检测 ---
        rebalance_needed = False
        rebalance_details: List[RebalanceItem] = []
        if current_weights and target_weights:
            rebalance_needed, rebalance_details = self.rebalance_checker.check(
                current_weights, target_weights, symbol_names
            )

        # --- 4. 置信度 ---
        confidence = self._assess_confidence(market_status)

        return Decision(
            should_check=should_check,
            should_check_reason=check_reason,
            action_suggestion=action,
            rebalance_needed=rebalance_needed,
            rebalance_details=rebalance_details,
            confidence=confidence,
        )

    def _decide_check(
        self,
        has_alert: bool,
        market_extreme: bool,
        market_cheap: bool,
        market_expensive: bool,
        alert_result: "AlertResult",
        market_status: Optional["MarketStatus"],
    ):
        if has_alert and market_extreme:
            state_label = "便宜" if market_cheap else "过热"
            return True, f"资产波动触发告警, 且市场估值{state_label}"
        if has_alert:
            return True, "资产波动超出阈值"
        if market_extreme and self.check_market_volatility:
            state_label = "便宜" if market_cheap else "过热"
            return True, f"市场估值处于{state_label}区间, 可关注配置机会"
        return False, "市场与资产均处于正常区间"

    def _build_action_suggestion(
        self,
        has_alert: bool,
        market_cheap: bool,
        market_expensive: bool,
        market_status: Optional["MarketStatus"],
    ) -> str:
        if market_status is None:
            if has_alert:
                return "资产波动较大, 注意风险, 避免冲动操作"
            return "无需操作, 忽略市场"

        if market_cheap and not has_alert:
            return "市场估值偏低, 可考虑按计划定投"
        if market_cheap and has_alert:
            return "市场估值偏低但资产波动大, 可小幅定投, 注意仓位控制"
        if market_expensive and not has_alert:
            return "市场估值偏高, 注意控制权益仓位, 不宜追涨"
        if market_expensive and has_alert:
            return "市场过热且资产波动大, 注意风险, 考虑适度减仓"
        if has_alert:
            return "资产波动较大, 关注持仓但避免冲动操作"
        return "无需操作, 忽略市场"

    def _assess_confidence(self, market_status: Optional["MarketStatus"]) -> str:
        """根据是否有市场数据评估置信度"""
        if market_status is None:
            return "低"   # 缺少市场估值信号, 仅凭波动判断
        return "高"
