"""
Anti-FOMO Main Application
对抗 FOMO 主程序
"""
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

from portfolio_engine import (
    Portfolio,
    DataFetcher,
    VolatilityCalculator,
    VolatilityResult,
    ThresholdManager,
    ThresholdConfig,
)
from market_engine import MarketScorer, MarketStatus
from decision_engine import PaceController, Decision
from report_engine import DailyDigest, WeeklyReport
from ai_engine import AIAnalyzer
from notification import NotificationManager


class AntiFOMO:
    """Anti-FOMO 应用主类"""

    def __init__(self, config_path: str = "config.yaml"):
        self.config = self._load_config(config_path)
        self.asset_allocation = self.config.get("asset_allocation", {})

        # portfolio_engine
        self.portfolio = Portfolio.from_config(self.config)
        self.data_fetcher = DataFetcher(
            period=self.config["data_fetch"]["period"],
            start_date=self.config["data_fetch"].get("start_date"),
        )
        self.threshold_manager = ThresholdManager(
            ThresholdConfig.from_config(self.config)
        )

        # ai_engine
        self.ai_config = self.config.get("ai_analysis", {})
        self.ai_analyzer = AIAnalyzer(self.ai_config)
        self.ai_always_analyze = bool(self.ai_config.get("always_analyze", False))

        # notification
        self.notification_manager = NotificationManager(
            self.config.get("notification", {})
        )

        # market_engine
        self.market_scorer: Optional[MarketScorer] = None
        raw_market_config = self.config.get("market_engine", {})
        if raw_market_config.get("enabled", False):
            market_config = dict(raw_market_config)
            market_config["_cache_config"] = self.config.get("cache", {})
            self.market_scorer = MarketScorer(market_config)

        # decision_engine
        self.pace_controller: Optional[PaceController] = None
        decision_cfg = self.config.get("decision_engine", {})
        if decision_cfg.get("enabled", True):
            self.pace_controller = PaceController(decision_cfg)

        # report_engine
        self.daily_digest = DailyDigest()
        self.weekly_report = WeeklyReport()

        print("Anti-FOMO 系统初始化完成")
        print(f"监控组合: {len(self.portfolio.holdings)} 个持仓")
        if self.market_scorer:
            print("市场估值引擎已启用")
        if self.pace_controller:
            print("决策节奏引擎已启用")

    # -------------------------------------------------------------------------
    # Config loading
    # -------------------------------------------------------------------------

    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        asset_config_path = config.get("asset_config_path", "config.asset.yaml")
        asset_path = Path(asset_config_path)
        if not asset_path.exists():
            print(f"资产配置文件 {asset_config_path} 不存在")
            print("  请先运行 python serve.py 并在 Web 界面中配置资产")
            raise SystemExit(1)

        with open(asset_path, "r", encoding="utf-8") as f:
            asset_config = yaml.safe_load(f)

        holdings = asset_config.get("portfolio", {}).get("holdings")
        if not holdings:
            print(f"资产配置文件 {asset_config_path} 中没有持仓数据")
            print("  请先运行 python serve.py 并在 Web 界面中配置资产")
            raise SystemExit(1)

        config["portfolio"] = asset_config["portfolio"]
        if asset_config.get("asset_allocation"):
            config["asset_allocation"] = asset_config["asset_allocation"]

        return config

    # -------------------------------------------------------------------------
    # Core data collection helpers
    # -------------------------------------------------------------------------

    def _collect_portfolio_data(self):
        """获取持仓数据并计算波动, 返回 (individual_results, portfolio_result, alert_result)"""
        print("正在获取持仓数据...")
        individual_results: List[VolatilityResult] = []
        weights = self.portfolio.get_holding_weights()

        for holding in self.portfolio.holdings:
            print(f"  - 获取 {holding.name}({holding.symbol}) 数据...")
            df = self.data_fetcher.fetch_index_data(holding.symbol)
            if df.empty:
                print(f"    数据获取失败")
                continue
            result = VolatilityCalculator.calculate_individual_volatility(
                df=df,
                symbol=holding.symbol,
                name=holding.name,
                weight=weights[holding.symbol],
            )
            individual_results.append(result)

        if not individual_results:
            return None, None, None

        print("\n计算组合波动率...")
        portfolio_result = VolatilityCalculator.calculate_portfolio_volatility(
            individual_results
        )

        print("评估波动阈值...")
        alert_result = self.threshold_manager.evaluate(portfolio_result)

        return individual_results, portfolio_result, alert_result

    def _make_decision(self, portfolio_result, alert_result, market_status) -> Optional[Decision]:
        """生成决策"""
        if self.pace_controller is None:
            return None

        current_weights = self.portfolio.get_holding_weights()
        # 目标权重: 当前只用当前权重作为目标 (无独立目标配置时退化为无偏离)
        # 如果 asset_allocation 中有 calculable_weights, 则使用它作为目标
        target_weights = self.asset_allocation.get("calculable_weights") or current_weights
        symbol_names = {h.symbol: h.name for h in self.portfolio.holdings}

        return self.pace_controller.decide(
            portfolio_result=portfolio_result,
            alert_result=alert_result,
            market_status=market_status,
            current_weights=current_weights,
            target_weights=target_weights,
            symbol_names=symbol_names,
        )

    # -------------------------------------------------------------------------
    # Public run methods
    # -------------------------------------------------------------------------

    def run_check(self):
        """执行一次日度检查"""
        print(f"\n{'='*60}")
        print(f"Anti-FOMO 检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        # 1. portfolio_engine
        individual_results, portfolio_result, alert_result = self._collect_portfolio_data()
        if portfolio_result is None:
            print("无有效持仓数据，检查终止")
            return

        if self.asset_allocation:
            self._print_allocation_summary()

        if alert_result.should_notify:
            print("\n波动明细 (触发阈值):")
            for result in individual_results:
                print(
                    f"  - {result.name}({result.symbol}) "
                    f"当前价: {result.current_price:.2f}, "
                    f"涨跌: {result.change_pct:+.2f}%"
                )
        else:
            print("\n波动正常，建议把注意力放回生活与长期计划。")

        # 2. market_engine
        market_status: Optional[MarketStatus] = None
        if self.market_scorer:
            print("\n正在评估市场估值...")
            market_status = self.market_scorer.evaluate()

        # 3. decision_engine
        decision: Optional[Decision] = self._make_decision(
            portfolio_result, alert_result, market_status
        )

        # 4. report_engine -- 日度简报
        if decision is not None:
            digest = self.daily_digest.generate(market_status, decision)
            print(f"\n{digest}")
        elif market_status is not None:
            print(f"\n{market_status}")

        # 5. AI 分析
        ai_analysis = None
        if self.ai_analyzer.enabled and (alert_result.should_notify or self.ai_always_analyze):
            print("正在进行 AI 分析...")
            ai_analysis = self.ai_analyzer.analyze(portfolio_result, alert_result)

        # 6. 通知
        print("发送通知...")
        self.notification_manager.send(portfolio_result, alert_result, ai_analysis)

        print(f"\n{'='*60}")
        print("检查完成")
        print(f"{'='*60}\n")

    def run_weekly_report(self):
        """生成周度报告"""
        print(f"\n{'='*60}")
        print(f"Anti-FOMO 周报 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

        # 1. portfolio_engine
        individual_results, portfolio_result, alert_result = self._collect_portfolio_data()
        if portfolio_result is None:
            print("无有效持仓数据，周报生成终止")
            return

        # 2. market_engine
        market_status = None
        if self.market_scorer:
            print("\n正在评估市场估值...")
            market_status = self.market_scorer.evaluate()

        # 3. decision_engine
        decision = self._make_decision(portfolio_result, alert_result, market_status)
        if decision is None:
            # 没有决策引擎时, 构造一个占位 Decision
            from decision_engine import Decision as DecisionClass
            decision = DecisionClass(
                should_check=alert_result.should_notify,
                should_check_reason="基于波动告警",
                action_suggestion="请参考市场状态人工判断",
                rebalance_needed=False,
            )

        # 4. AI 分析
        ai_analysis = None
        report_cfg = self.config.get("report", {})
        include_ai = report_cfg.get("weekly", {}).get("include_ai", True)
        if include_ai and self.ai_analyzer.enabled:
            print("正在进行 AI 分析...")
            ai_analysis = self.ai_analyzer.analyze(portfolio_result, alert_result)

        # 5. 生成周报
        report = self.weekly_report.generate(
            portfolio_result=portfolio_result,
            alert_result=alert_result,
            market_status=market_status,
            decision=decision,
            ai_analysis=ai_analysis,
        )

        print(report)

        # 6. 持久化到日志
        self._save_weekly_report(report)

        # 7. 通知
        print("发送通知...")
        self.notification_manager.send(portfolio_result, alert_result, ai_analysis)

        print(f"\n{'='*60}")
        print("周报生成完成")
        print(f"{'='*60}\n")

    def _save_weekly_report(self, report: str):
        """将周报保存到 logs/ 目录"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        filename = log_dir / f"weekly_{datetime.now().strftime('%Y%m%d')}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n周报已保存至 {filename}")

    def run_continuous(self):
        """持续运行 (配合调度器)"""
        import schedule
        import time

        check_time = self.config["scheduler"]["check_time"]
        report_cfg = self.config.get("report", {})
        weekly_cfg = report_cfg.get("weekly", {})
        weekly_enabled = weekly_cfg.get("enabled", True)
        weekly_day = weekly_cfg.get("day", "friday").lower()
        weekly_time = weekly_cfg.get("time", "16:00")

        # 每日检查
        schedule.every().day.at(check_time).do(self.run_check)

        # 周报调度
        if weekly_enabled:
            day_schedulers = {
                "monday": schedule.every().monday,
                "tuesday": schedule.every().tuesday,
                "wednesday": schedule.every().wednesday,
                "thursday": schedule.every().thursday,
                "friday": schedule.every().friday,
                "saturday": schedule.every().saturday,
                "sunday": schedule.every().sunday,
            }
            day_scheduler = day_schedulers.get(weekly_day, schedule.every().friday)
            day_scheduler.at(weekly_time).do(self.run_weekly_report)
            print(f"周报调度: 每{_day_label(weekly_day)} {weekly_time}")

        print(f"调度器已启动，将在每天 {check_time} 执行日度检查")
        print("按 Ctrl+C 停止\n")

        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n\n调度器已停止")

    # -------------------------------------------------------------------------
    # Misc helpers
    # -------------------------------------------------------------------------

    def _print_allocation_summary(self):
        """输出资产配置概览"""
        total_ratio = self.asset_allocation.get("total_ratio")
        calculable_ratio = self.asset_allocation.get("calculable_ratio")
        calculable_weights = self.asset_allocation.get("calculable_weights", {})
        equity_start = self.asset_allocation.get("equity_start", {})

        print("\n资产配置概览")
        if total_ratio is not None:
            print(f"  - 配置总比例: {total_ratio:.2f}%")
        if calculable_ratio is not None:
            print(f"  - 可计算比例: {calculable_ratio:.2f}%")
        if calculable_weights:
            print("  - 可计算资产权重:")
            for symbol, weight in calculable_weights.items():
                print(f"    * {symbol}: {weight:.2%}")
        if equity_start:
            print("  - 起始价格/成本:")
            for symbol, price in equity_start.items():
                print(f"    * {symbol}: {price}")


def _day_label(day: str) -> str:
    labels = {
        "monday": "周一", "tuesday": "周二", "wednesday": "周三",
        "thursday": "周四", "friday": "周五", "saturday": "周六", "sunday": "周日",
    }
    return labels.get(day, day)


def main():
    """主函数"""
    import sys

    app = AntiFOMO()

    if len(sys.argv) > 1 and sys.argv[1] == "schedule":
        app.run_continuous()
    elif len(sys.argv) > 1 and sys.argv[1] == "weekly":
        app.run_weekly_report()
    else:
        app.run_check()


if __name__ == "__main__":
    main()
