"""
Demo Script - 使用模拟数据演示系统功能
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

import yaml
from portfolio import Portfolio
from volatility_calculator import VolatilityCalculator
from threshold_manager import ThresholdManager, ThresholdConfig
from notification import NotificationManager
from mock_data import generate_mock_data


def main():
    print("="*60)
    print("Anti-FOMO 演示模式（使用模拟数据）")
    print("="*60)
    print()
    
    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 初始化组件
    portfolio = Portfolio.from_config(config)
    threshold_manager = ThresholdManager(ThresholdConfig.from_config(config))
    notification_manager = NotificationManager(config.get('notification', {}))
    
    print(f"✅ 系统初始化完成")
    print(f"📊 监控组合: {len(portfolio.holdings)} 个持仓\n")
    
    print("📥 生成模拟数据（演示用）...\n")
    
    # 获取权重
    weights = portfolio.get_holding_weights()
    
    # 计算每个持仓的波动率
    individual_results = []
    
    for holding in portfolio.holdings:
        print(f"  处理 {holding.name}({holding.symbol})...")
        
        # 生成模拟数据
        df = generate_mock_data(holding.symbol, days=30)
        
        # 计算波动率
        result = VolatilityCalculator.calculate_individual_volatility(
            df=df,
            symbol=holding.symbol,
            name=holding.name,
            weight=weights[holding.symbol]
        )
        
        individual_results.append(result)
        print(f"    当前价: {result.current_price:.2f}, 涨跌: {result.change_pct:+.2f}%")
    
    print()
    
    # 计算组合波动
    print("📊 计算组合波动率...")
    portfolio_result = VolatilityCalculator.calculate_portfolio_volatility(
        individual_results
    )
    
    # 评估阈值
    print("🔍 评估波动阈值...")
    alert_result = threshold_manager.evaluate(portfolio_result)
    
    print()
    
    # 显示结果
    print("="*60)
    print("波动监控报告")
    print("="*60)
    print()
    print(str(alert_result))
    print()
    print("组合波动详情:")
    print("-"*60)
    print(str(portfolio_result))
    print()
    
    if alert_result.should_notify:
        print("💡 提示: 检测到异常波动，建议关注")
        print()
        print("在真实环境中，系统会:")
        print("  1. 调用 AI 分析波动原因")
        print("  2. 提供专业投资建议")
        print("  3. 发送通知到配置的渠道")
        print("  4. 记录日志供后续查看")
    else:
        print("✅ 波动在正常范围内，无需特别关注")
    
    print()
    print("="*60)
    print("演示完成！")
    print()
    print("下一步:")
    print("  1. 修改 config.yaml 配置您的真实持仓")
    print("  2. 在网络正常时运行: python run.py")
    print("  3. （可选）配置 OpenAI API Key 启用 AI 分析")
    print("="*60)


if __name__ == '__main__':
    main()
