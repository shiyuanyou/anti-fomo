"""
Scheduled jobs for Anti-FOMO Backend
"""
import os
import sys
import yaml
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from apps.backend.engines.portfolio_engine import (
    Portfolio,
    DataFetcher,
    VolatilityCalculator,
    VolatilityResult,
    ThresholdManager,
    ThresholdConfig,
)
from apps.backend.engines.market_engine import MarketScorer, MarketStatus
from apps.backend.engines.decision_engine import PaceController
from apps.backend.engines.report_engine import DailyDigest, WeeklyReport
from apps.backend.engines.ai_engine import AIAnalyzer
from apps.backend.engines.notification import NotificationManager


class JobRunner:
    """Execute scheduled jobs"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.getenv("CONFIG_PATH", "/app/configs/config.yaml")
        
        self.config_path = config_path
        self.config = None
        self.portfolio = None
        self.ai_analyzer = None
        self.notification_manager = None
        self.market_scorer = None
        self.pace_controller = None

    def load_config(self):
        """Load configuration"""
        if not Path(self.config_path).exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        asset_config_path = self.config.get("asset_config_path", "/app/configs/config.asset.yaml")
        asset_path = Path(asset_config_path)
        
        if not asset_path.exists():
            raise FileNotFoundError(f"Asset config not found: {asset_config_path}")

        with open(asset_path, "r", encoding="utf-8") as f:
            asset_config = yaml.safe_load(f)

        holdings = asset_config.get("portfolio", {}).get("holdings")
        if not holdings:
            raise ValueError("No holdings found in asset config")

        self.config["portfolio"] = asset_config["portfolio"]
        if asset_config.get("asset_allocation"):
            self.config["asset_allocation"] = asset_config["asset_allocation"]

    def initialize(self):
        """Initialize engines"""
        self.portfolio = Portfolio.from_config(self.config)
        
        self.data_fetcher = DataFetcher(
            period=self.config["data_fetch"]["period"],
            start_date=self.config["data_fetch"].get("start_date"),
        )
        
        self.threshold_manager = ThresholdManager(
            ThresholdConfig.from_config(self.config)
        )

        ai_config = self.config.get("ai_analysis", {})
        self.ai_analyzer = AIAnalyzer(ai_config)

        self.notification_manager = NotificationManager(
            self.config.get("notification", {})
        )

        raw_market_config = self.config.get("market_engine", {})
        if raw_market_config.get("enabled", False):
            market_config = dict(raw_market_config)
            market_config["_cache_config"] = self.config.get("cache", {})
            self.market_scorer = MarketScorer(market_config)

        decision_cfg = self.config.get("decision_engine", {})
        if decision_cfg.get("enabled", True):
            self.pace_controller = PaceController(decision_cfg)

    def run_daily_check(self) -> dict:
        """Execute daily check job"""
        job_id = f"daily_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"
        
        try:
            if not self.config:
                self.load_config()
                self.initialize()

            print(f"Running daily check: {job_id}")

            weights = self.portfolio.get_holding_weights()
            results = []

            for holding in self.portfolio.holdings:
                df = self.data_fetcher.fetch_index_data(holding.symbol)
                if df.empty:
                    continue
                result = VolatilityCalculator.calculate_individual_volatility(
                    df=df,
                    symbol=holding.symbol,
                    name=holding.name,
                    weight=weights[holding.symbol],
                )
                results.append(result)

            if not results:
                return {"job_id": job_id, "status": "completed", "message": "No data fetched"}

            portfolio_result = VolatilityCalculator.calculate_portfolio_volatility(results)
            alert_result = self.threshold_manager.evaluate(portfolio_result)

            market_status = None
            if self.market_scorer:
                market_status = self.market_scorer.evaluate()

            decision = None
            if self.pace_controller:
                current_weights = self.portfolio.get_holding_weights()
                target_weights = self.config.get("asset_allocation", {}).get("calculable_weights") or current_weights
                symbol_names = {h.symbol: h.name for h in self.portfolio.holdings}
                decision = self.pace_controller.decide(
                    portfolio_result=portfolio_result,
                    alert_result=alert_result,
                    market_status=market_status,
                    current_weights=current_weights,
                    target_weights=target_weights,
                    symbol_names=symbol_names,
                )

            if self.ai_analyzer.enabled and (alert_result.should_notify or self.config.get("ai_analysis", {}).get("always_analyze", False)):
                ai_analysis = self.ai_analyzer.analyze(portfolio_result, alert_result)
            else:
                ai_analysis = None

            self.notification_manager.send(portfolio_result, alert_result, ai_analysis)

            return {
                "job_id": job_id,
                "status": "completed",
                "message": f"Daily check completed. Alert: {alert_result.should_notify}"
            }

        except Exception as e:
            return {
                "job_id": job_id,
                "status": "failed",
                "message": str(e)
            }

    def run_weekly_report(self) -> dict:
        """Execute weekly report job"""
        job_id = f"weekly_{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"
        
        try:
            if not self.config:
                self.load_config()
                self.initialize()

            print(f"Running weekly report: {job_id}")

            weights = self.portfolio.get_holding_weights()
            results = []

            for holding in self.portfolio.holdings:
                df = self.data_fetcher.fetch_index_data(holding.symbol)
                if df.empty:
                    continue
                result = VolatilityCalculator.calculate_individual_volatility(
                    df=df,
                    symbol=holding.symbol,
                    name=holding.name,
                    weight=weights[holding.symbol],
                )
                results.append(result)

            if not results:
                return {"job_id": job_id, "status": "completed", "message": "No data fetched"}

            portfolio_result = VolatilityCalculator.calculate_portfolio_volatility(results)
            alert_result = self.threshold_manager.evaluate(portfolio_result)

            market_status = None
            if self.market_scorer:
                market_status = self.market_scorer.evaluate()

            decision = None
            if self.pace_controller:
                current_weights = self.portfolio.get_holding_weights()
                target_weights = self.config.get("asset_allocation", {}).get("calculable_weights") or current_weights
                symbol_names = {h.symbol: h.name for h in self.portfolio.holdings}
                decision = self.pace_controller.decide(
                    portfolio_result=portfolio_result,
                    alert_result=alert_result,
                    market_status=market_status,
                    current_weights=current_weights,
                    target_weights=target_weights,
                    symbol_names=symbol_names,
                )

            ai_analysis = None
            if self.ai_analyzer.enabled and self.config.get("report", {}).get("weekly", {}).get("include_ai", True):
                ai_analysis = self.ai_analyzer.analyze(portfolio_result, alert_result)

            report = WeeklyReport().generate(
                portfolio_result=portfolio_result,
                alert_result=alert_result,
                market_status=market_status,
                decision=decision,
                ai_analysis=ai_analysis,
            )

            log_dir = Path("/app/logs")
            log_dir.mkdir(exist_ok=True)
            filename = log_dir / f"weekly_{datetime.now().strftime('%Y%m%d')}.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(report)

            return {
                "job_id": job_id,
                "report_id": filename.name,
                "status": "completed",
                "message": f"Report saved to {filename}"
            }

        except Exception as e:
            return {
                "job_id": job_id,
                "status": "failed",
                "message": str(e)
            }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("job", choices=["daily", "weekly"], help="Job type")
    parser.add_argument("--config", default="/app/configs/config.yaml", help="Config path")
    args = parser.parse_args()

    runner = JobRunner(config_path=args.config)
    
    if args.job == "daily":
        result = runner.run_daily_check()
    else:
        result = runner.run_weekly_report()
    
    print(result)


if __name__ == "__main__":
    main()
