"""
Demo Mode with Mock Data
演示模式 - 使用模拟数据展示系统功能
"""
import pandas as pd
from datetime import datetime, timedelta
import random


def generate_mock_data(symbol: str, days: int = 30) -> pd.DataFrame:
    """
    生成模拟的股票数据
    
    Args:
        symbol: 股票代码
        days: 天数
        
    Returns:
        模拟的DataFrame
    """
    # 基础价格
    base_prices = {
        '000510': 1200,  # 中证A500
        '930050': 5500,  # 中证A50
        '932000': 2900,  # 中证2000
    }
    
    base_price = base_prices.get(symbol, 3000)
    
    dates = []
    opens = []
    closes = []
    highs = []
    lows = []
    
    current_price = base_price
    
    for i in range(days):
        date = (datetime.now() - timedelta(days=days-i)).strftime('%Y-%m-%d')
        dates.append(date)
        
        # 随机波动 -2% 到 +2%
        change = random.uniform(-0.02, 0.02)
        # 今天加大波动，制造一个警报场景
        if i == days - 1:
            if symbol == '932000':  # 中证2000 今天大涨
                change = 0.045
            else:
                change = random.uniform(0.01, 0.025)
        
        open_price = current_price
        close_price = current_price * (1 + change)
        high_price = max(open_price, close_price) * 1.01
        low_price = min(open_price, close_price) * 0.99
        
        opens.append(round(open_price, 2))
        closes.append(round(close_price, 2))
        highs.append(round(high_price, 2))
        lows.append(round(low_price, 2))
        
        current_price = close_price
    
    df = pd.DataFrame({
        '日期': dates,
        '开盘': opens,
        '收盘': closes,
        '最高': highs,
        '最低': lows,
        '成交量': [random.randint(1000000, 5000000) for _ in range(days)],
        '成交额': [random.randint(1000000000, 5000000000) for _ in range(days)],
        '振幅': [random.uniform(1, 3) for _ in range(days)],
        '涨跌幅': [(closes[i] - closes[i-1]) / closes[i-1] * 100 if i > 0 else 0 for i in range(days)],
        '涨跌额': [closes[i] - closes[i-1] if i > 0 else 0 for i in range(days)],
        '换手率': [random.uniform(0.5, 2.0) for _ in range(days)]
    })
    
    return df
