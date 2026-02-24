"""
Anti-FOMO Main Application
对抗 FOMO 主程序
"""
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional

from portfolio_engine import (
    Portfolio,
    DataFetcher,
    VolatilityCalculator,
    VolatilityResult,
    ThresholdManager,
    ThresholdConfig,
)
from market_engine import MarketScorer, MarketStatus
from ai_engine import AIAnalyzer
from notification import NotificationManager


class AntiFOMO:
    """Anti-FOMO 应用主类"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """
        初始化应用
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = self._load_config(config_path)
        self.asset_allocation = self.config.get("asset_allocation", {})
        
        # 初始化各个模块
        self.portfolio = Portfolio.from_config(self.config)
        self.data_fetcher = DataFetcher(
            period=self.config['data_fetch']['period'],
            start_date=self.config['data_fetch'].get('start_date')
        )
        self.threshold_manager = ThresholdManager(
            ThresholdConfig.from_config(self.config)
        )
        self.ai_config = self.config.get('ai_analysis', {})
        self.ai_analyzer = AIAnalyzer(self.ai_config)
        self.ai_always_analyze = bool(self.ai_config.get('always_analyze', False))
        self.notification_manager = NotificationManager(
            self.config.get('notification', {})
        )

        # 初始化市场估值引擎 (v1)
        self.market_scorer = None
        market_config = self.config.get("market_engine", {})
        if market_config.get("enabled", False):
            market_config["_cache_config"] = self.config.get("cache", {})
            self.market_scorer = MarketScorer(market_config)
        
        print("Anti-FOMO 系统初始化完成")
        print(f"监控组合: {len(self.portfolio.holdings)} 个持仓")
        if self.market_scorer:
            print("市场估值引擎已启用")
        if self.asset_allocation:
            print("已加载资产配置起始文件")
    
    def _load_config(self, config_path: str) -> Dict:
        """加载配置文件"""
        with open(config_path, 'r', encoding='utf-8') as f:
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
    
    def run_check(self):
        """执行一次波动检查"""
        print(f"\n{'='*60}")
        print(f"Anti-FOMO 检查 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        # 1. 获取数据并计算波动率
        print("正在获取持仓数据...")
        individual_results = []
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
                weight=weights[holding.symbol]
            )
            individual_results.append(result)
        
        if not individual_results:
            print("无有效数据，检查终止")
            return
        
        # 2. 计算组合波动
        print("\n计算组合波动率...")
        portfolio_result = VolatilityCalculator.calculate_portfolio_volatility(
            individual_results
        )
        
        # 3. 评估阈值
        print("评估波动阈值...")
        alert_result = self.threshold_manager.evaluate(portfolio_result)

        if self.asset_allocation:
            self._print_allocation_summary()
        
        if alert_result.should_notify:
            print("\n波动明细（仅在触发阈值时展示）:")
            for result in individual_results:
                print(f"  - {result.name}({result.symbol}) 当前价: {result.current_price:.2f}, 涨跌: {result.change_pct:+.2f}%")
        else:
            print("\n波动正常，建议把注意力放回生活与长期计划。")

        # 4. 市场估值评估 (v1)
        market_status = None
        if self.market_scorer:
            print("\n正在评估市场估值...")
            market_status = self.market_scorer.evaluate()
            if market_status:
                print(f"\n{market_status}")

        # 5. AI 分析（如果启用）
        ai_analysis = None
        if self.ai_analyzer.enabled and (alert_result.should_notify or self.ai_always_analyze):
            print("正在进行 AI 分析...")
            ai_analysis = self.ai_analyzer.analyze(portfolio_result, alert_result)
        
        # 6. 发送通知
        print("发送通知...")
        self.notification_manager.send(
            portfolio_result,
            alert_result,
            ai_analysis
        )
        
        print(f"\n{'='*60}")
        print("检查完成")
        print(f"{'='*60}\n")
    
    def run_continuous(self):
        """持续运行（配合调度器）"""
        import schedule
        import time
        
        check_time = self.config['scheduler']['check_time']
        
        # 设置定时任务
        schedule.every().day.at(check_time).do(self.run_check)
        
        print(f"调度器已启动，将在每天 {check_time} 执行检查")
        print("按 Ctrl+C 停止\n")
        
        # 持续运行
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次
        except KeyboardInterrupt:
            print("\n\n调度器已停止")

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


def main():
    """主函数"""
    import sys
    
    # 创建应用实例
    app = AntiFOMO()
    
    # 根据命令行参数决定运行模式
    if len(sys.argv) > 1 and sys.argv[1] == 'schedule':
        # 调度模式
        app.run_continuous()
    else:
        # 单次运行模式
        app.run_check()


if __name__ == '__main__':
    main()
