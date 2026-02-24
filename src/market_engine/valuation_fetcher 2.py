"""
Valuation Fetcher
指数估值数据获取 -- 通过 akshare 获取 PE/PB 历史序列
"""
import pandas as pd
from typing import Optional

from .cache import DataCache


class ValuationFetcher:
    """获取指数 PE/PB 历史数据"""

    def __init__(self, cache: Optional[DataCache] = None):
        """
        Args:
            cache: 可选的数据缓存实例, None 则不缓存
        """
        self.cache = cache

    def fetch_pe(self, symbol: str) -> pd.DataFrame:
        """
        获取指数历史 PE 数据

        Args:
            symbol: 指数中文名 (如 "沪深300", "中证500", "上证50")

        Returns:
            DataFrame, 列: [日期, 滚动市盈率], 按日期升序.
            失败返回空 DataFrame.
        """
        cache_key = f"pe_{symbol}"
        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        try:
            import akshare as ak
            df = ak.stock_index_pe_lg(symbol=symbol)
        except Exception as e:
            print(f"获取 {symbol} PE 数据失败: {e}")
            return pd.DataFrame()

        if df.empty:
            print(f"{symbol} PE 数据为空")
            return df

        df = df[["日期", "滚动市盈率"]].copy()
        df["日期"] = pd.to_datetime(df["日期"])
        df = df.sort_values("日期").reset_index(drop=True)

        if self.cache is not None:
            self.cache.set(cache_key, df)

        return df

    def fetch_pb(self, symbol: str) -> pd.DataFrame:
        """
        获取指数历史 PB 数据

        Args:
            symbol: 指数中文名 (如 "沪深300", "中证500", "上证50")

        Returns:
            DataFrame, 列: [日期, 市净率], 按日期升序.
            失败返回空 DataFrame.
        """
        cache_key = f"pb_{symbol}"
        if self.cache is not None:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        try:
            import akshare as ak
            df = ak.stock_index_pb_lg(symbol=symbol)
        except Exception as e:
            print(f"获取 {symbol} PB 数据失败: {e}")
            return pd.DataFrame()

        if df.empty:
            print(f"{symbol} PB 数据为空")
            return df

        df = df[["日期", "市净率"]].copy()
        df["日期"] = pd.to_datetime(df["日期"])
        df = df.sort_values("日期").reset_index(drop=True)

        if self.cache is not None:
            self.cache.set(cache_key, df)

        return df
