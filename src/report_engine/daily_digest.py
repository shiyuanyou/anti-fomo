"""
Daily Digest
日度简报生成器 -- 将 decision + market 信号汇总为 3-5 行可读输出
"""
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from market_engine import MarketStatus
    from decision_engine import Decision


class DailyDigest:
    """日度简报生成器"""

    def generate(
        self,
        market_status: Optional["MarketStatus"],
        decision: "Decision",
        date: Optional[datetime] = None,
    ) -> str:
        """
        生成日度简报.

        Args:
            market_status: 市场估值状态 (可为 None)
            decision: 决策结果
            date: 报告日期 (默认今日)

        Returns:
            格式化的简报字符串
        """
        from market_engine.market_scorer import MarketState

        today = (date or datetime.now()).strftime("%Y-%m-%d")
        lines = [
            f"[{today}] Anti-FOMO 判断",
            "-" * 40,
        ]

        # 市场状态
        if market_status is not None:
            state_labels = {
                MarketState.CHEAP: "便宜",
                MarketState.NORMAL: "正常",
                MarketState.EXPENSIVE: "过热",
            }
            state_label = state_labels.get(market_status.market_state, "未知")
            lines.append(
                f"市场状态: {state_label} "
                f"(综合评分 {market_status.composite_score:.1f})"
            )
        else:
            lines.append("市场状态: 未获取")

        # 看盘建议
        check_label = "需要关注" if decision.should_check else "无需关注"
        lines.append(f"看盘建议: {check_label}")

        # 行动建议
        lines.append(f"建议: {decision.action_suggestion}")

        # 再平衡提示
        if decision.rebalance_needed:
            lines.append(f"再平衡: 有持仓偏离超出阈值, 建议检查配置")

        lines.append("-" * 40)
        return "\n".join(lines)
