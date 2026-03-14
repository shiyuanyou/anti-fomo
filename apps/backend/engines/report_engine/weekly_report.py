"""
Weekly Report
周度报告生成器 -- 生成完整的 Markdown 格式周报
"""
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from portfolio_engine import PortfolioVolatilityResult, AlertResult
    from market_engine import MarketStatus
    from decision_engine import Decision


class WeeklyReport:
    """周度报告生成器"""

    def generate(
        self,
        portfolio_result: "PortfolioVolatilityResult",
        alert_result: "AlertResult",
        market_status: Optional["MarketStatus"],
        decision: "Decision",
        ai_analysis: Optional[str] = None,
        date: Optional[datetime] = None,
    ) -> str:
        """
        生成周度报告.

        Args:
            portfolio_result: 组合波动结果
            alert_result: 告警结果
            market_status: 市场估值状态
            decision: 决策结果
            ai_analysis: AI 分析文本 (可选)
            date: 报告日期 (默认今日)

        Returns:
            Markdown 格式的报告字符串
        """
        today = (date or datetime.now()).strftime("%Y-%m-%d")
        sections = [
            f"# Anti-FOMO 周度报告 {today}",
            "",
            self._section_market(market_status),
            self._section_portfolio(portfolio_result, alert_result),
            self._section_decision(decision),
        ]

        if ai_analysis:
            sections.append(self._section_ai(ai_analysis))

        return "\n".join(sections)

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _section_market(self, market_status: Optional["MarketStatus"]) -> str:
        from market_engine.market_scorer import MarketState

        lines = ["## 一. 市场估值概览", ""]

        if market_status is None:
            lines.append("市场估值数据未获取。")
            return "\n".join(lines)

        state_labels = {
            MarketState.CHEAP: "便宜",
            MarketState.NORMAL: "正常",
            MarketState.EXPENSIVE: "过热",
        }
        state_label = state_labels.get(market_status.market_state, "未知")

        lines.append(
            f"综合评分: **{market_status.composite_score:.1f}**  "
            f"市场状态: **{state_label}**"
        )
        lines.append("")
        lines.append("| 指数 | PE(TTM) | PE 百分位 | PB | PB 百分位 | 综合评分 |")
        lines.append("|------|---------|-----------|-----|-----------|---------|")

        for val in market_status.indices.values():
            lines.append(
                f"| {val.name} "
                f"| {val.pe_ttm:.2f} "
                f"| {val.pe_percentile:.1f}% "
                f"| {val.pb:.2f} "
                f"| {val.pb_percentile:.1f}% "
                f"| {val.score:.1f} |"
            )

        lines.append("")
        lines.append(
            f"_数据更新时间: {market_status.updated_at.strftime('%Y-%m-%d %H:%M')}_"
        )
        return "\n".join(lines)

    def _section_portfolio(
        self,
        portfolio_result: "PortfolioVolatilityResult",
        alert_result: "AlertResult",
    ) -> str:
        from portfolio_engine.threshold import AlertLevel

        lines = ["", "## 二. 资产状态摘要", ""]

        level_labels = {
            AlertLevel.NONE: "正常",
            AlertLevel.WARNING: "警告",
            AlertLevel.ALERT: "警报",
        }
        level_label = level_labels.get(alert_result.level, "未知")
        lines.append(
            f"组合波动: **{portfolio_result.total_volatility:.2f}%**  "
            f"告警级别: **{level_label}**"
        )
        lines.append("")
        lines.append("| 持仓 | 当前价 | 日涨跌 | 近一月 | 权重 |")
        lines.append("|------|--------|--------|--------|------|")

        for r in portfolio_result.individual_results:
            lines.append(
                f"| {r.name}({r.symbol}) "
                f"| {r.current_price:.2f} "
                f"| {r.change_pct:+.2f}% "
                f"| {r.month_return_pct:+.2f}% "
                f"| {r.weight:.1%} |"
            )

        return "\n".join(lines)

    def _section_decision(self, decision: "Decision") -> str:
        lines = ["", "## 三. 行为建议", ""]

        check_label = "需要关注" if decision.should_check else "无需关注"
        lines.append(f"- 看盘建议: {check_label} ({decision.should_check_reason})")
        lines.append(f"- 行动建议: {decision.action_suggestion}")
        lines.append(f"- 判断置信度: {decision.confidence}")

        if decision.rebalance_needed:
            lines.append("")
            lines.append("**再平衡提示** (以下持仓偏离目标超过阈值):")
            for item in decision.rebalance_details:
                lines.append(f"  - {item}")

        return "\n".join(lines)

    def _section_ai(self, ai_analysis: str) -> str:
        lines = ["", "## 四. AI 分析", "", ai_analysis]
        return "\n".join(lines)
