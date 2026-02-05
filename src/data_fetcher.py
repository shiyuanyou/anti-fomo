"""
Market Data Fetcher
市场数据获取模块
"""
import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, List


class DataFetcher:
    """数据获取器"""
    
    def __init__(self, period: str = "daily", start_date: Optional[str] = None):
        """
        初始化数据获取器
        
        Args:
            period: 数据周期 (daily/weekly)
            start_date: 开始日期 (格式: YYYYMMDD)
        """
        self.period = period
        self.start_date = start_date or self._get_default_start_date()
    
    def _get_default_start_date(self) -> str:
        """获取默认开始日期（30天前）"""
        date = datetime.now() - timedelta(days=30)
        return date.strftime("%Y%m%d")
    
    def fetch_index_data(self, symbol: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取指数数据
        
        Args:
            symbol: 指数代码
            end_date: 结束日期 (格式: YYYYMMDD)，默认为今天
            
        Returns:
            包含指数数据的DataFrame
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")

        errors = []

        try:
            df = ak.index_zh_a_hist(
                symbol=symbol,
                period=self.period,
                start_date=self.start_date,
                end_date=end_date,
            )
            if not df.empty:
                return df
        except Exception as e:
            errors.append(f"index_zh_a_hist: {e}")

        candidates = self._index_symbol_candidates(symbol)

        for cand in candidates:
            try:
                df = ak.stock_zh_index_daily_em(
                    symbol=cand,
                    start_date=self.start_date,
                    end_date=end_date,
                )
                if not df.empty:
                    df = self._normalize_index_df(df)
                    df = self._resample_if_needed(df)
                    return df
            except Exception as e:
                errors.append(f"stock_zh_index_daily_em({cand}): {e}")

        for cand in candidates:
            try:
                df = ak.stock_zh_index_daily(symbol=cand)
                if not df.empty:
                    df = self._normalize_index_df(df)
                    df = self._filter_by_date(df)
                    df = self._resample_if_needed(df)
                    return df
            except Exception as e:
                errors.append(f"stock_zh_index_daily({cand}): {e}")

        for cand in candidates:
            try:
                df = ak.stock_zh_index_daily_tx(symbol=cand)
                if not df.empty:
                    df = self._normalize_index_df(df)
                    df = self._filter_by_date(df)
                    df = self._resample_if_needed(df)
                    return df
            except Exception as e:
                errors.append(f"stock_zh_index_daily_tx({cand}): {e}")

        print(f"获取指数 {symbol} 数据失败: {', '.join(errors)}")
        return pd.DataFrame()
    
    def fetch_stock_data(self, symbol: str, end_date: Optional[str] = None) -> pd.DataFrame:
        """
        获取个股数据
        
        Args:
            symbol: 股票代码
            end_date: 结束日期
            
        Returns:
            包含股票数据的DataFrame
        """
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        
        try:
            # 根据代码判断市场
            if symbol.startswith('6'):
                adjust = 'qfq'  # 前复权
            else:
                adjust = 'qfq'
            
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=self.period,
                start_date=self.start_date,
                end_date=end_date,
                adjust=adjust
            )
            return df
        except Exception as e:
            print(f"获取股票 {symbol} 数据失败: {str(e)}")
            return pd.DataFrame()

    def _index_symbol_candidates(self, symbol: str) -> List[str]:
        if symbol.startswith(("sh", "sz", "bj", "csi")):
            return [symbol]

        if symbol.startswith("399"):
            return [f"sz{symbol}", f"sh{symbol}", f"csi{symbol}"]

        if symbol.startswith(("93", "94", "95", "96", "97", "98")):
            return [f"csi{symbol}", f"sh{symbol}", f"sz{symbol}"]

        return [f"sh{symbol}", f"sz{symbol}", f"csi{symbol}"]

    def _normalize_index_df(self, df: pd.DataFrame) -> pd.DataFrame:
        if "日期" in df.columns:
            return df

        rename_map = {
            "date": "日期",
            "open": "开盘",
            "close": "收盘",
            "high": "最高",
            "low": "最低",
            "volume": "成交量",
            "amount": "成交额",
            "latest": "收盘",
        }
        cols = {k: v for k, v in rename_map.items() if k in df.columns}
        return df.rename(columns=cols)

    def _filter_by_date(self, df: pd.DataFrame) -> pd.DataFrame:
        if "日期" not in df.columns:
            return df

        start = self.start_date
        end = datetime.now().strftime("%Y%m%d")
        df = df.copy()
        df["日期"] = pd.to_datetime(df["日期"])
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end)
        return df[(df["日期"] >= start_dt) & (df["日期"] <= end_dt)]

    def _resample_if_needed(self, df: pd.DataFrame) -> pd.DataFrame:
        if self.period == "daily" or "日期" not in df.columns:
            return df

        df = df.copy()
        df["日期"] = pd.to_datetime(df["日期"])
        df = df.sort_values("日期")
        df = df.set_index("日期")

        rule = "W-FRI" if self.period == "weekly" else "M"

        agg = {
            "开盘": "first",
            "收盘": "last",
            "最高": "max",
            "最低": "min",
        }

        if "成交量" in df.columns:
            agg["成交量"] = "sum"
        if "成交额" in df.columns:
            agg["成交额"] = "sum"

        resampled = df.resample(rule).agg(agg).dropna().reset_index()
        return resampled
    
    def get_latest_close_price(self, df: pd.DataFrame) -> Optional[float]:
        """获取最新收盘价"""
        if df.empty:
            return None
        return float(df.iloc[-1]['收盘'])
    
    def get_previous_close_price(self, df: pd.DataFrame) -> Optional[float]:
        """获取前一日收盘价"""
        if len(df) < 2:
            return None
        return float(df.iloc[-2]['收盘'])
