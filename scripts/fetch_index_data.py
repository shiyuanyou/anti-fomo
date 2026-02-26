"""
scripts/fetch_index_data.py — v3 D2

Pull proxy-index weekly OHLC history from akshare for all asset categories
defined in the D1 mapping table.

Output: base_datas/index_weekly.csv
Columns: date, index_code, open, high, low, close

Run:
    python3 scripts/fetch_index_data.py

On first run, pulls 2010-01-01 to today (~2-5 min depending on network).
On subsequent runs, only fetches new data since the last stored date (incremental).

Each akshare call is wrapped in try/except; failures print a warning and skip
without interrupting the overall fetch.
"""

from __future__ import annotations

import sys
import os
from pathlib import Path
from datetime import date, timedelta

# Ensure project root is importable (not strictly needed here but keeps pattern consistent)
ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

import pandas as pd

BASE_DATAS_DIR = ROOT / "base_datas"
OUTPUT_CSV = BASE_DATAS_DIR / "index_weekly.csv"
START_DATE = "20100101"

# ---------------------------------------------------------------------------
#  D1 Proxy-index mapping table
#  Each entry: (index_code, fetch_func_name, fetch_kwargs, close_col)
#  close_col: name of the closing-price column returned by the akshare API
# ---------------------------------------------------------------------------


# We define fetchers as callables so we can lazy-import akshare per call
def _fetch_zh_a(code: str, start: str, end: str) -> pd.DataFrame:
    """A-share domestic index via index_zh_a_hist (weekly)."""
    import akshare as ak

    df = ak.index_zh_a_hist(
        symbol=code, period="weekly", start_date=start, end_date=end
    )
    return df


def _fetch_hk_sina(code: str, start: str, end: str) -> pd.DataFrame:
    """HK index via stock_hk_index_daily_sina (daily, will resample to weekly)."""
    import akshare as ak

    df = ak.stock_hk_index_daily_sina(symbol=code)
    return df


def _fetch_us_sina(code: str, start: str, end: str) -> pd.DataFrame:
    """US index via index_us_stock_sina (daily, will resample to weekly)."""
    import akshare as ak

    df = ak.index_us_stock_sina(symbol=code)
    return df


def _fetch_global_em(name: str, start: str, end: str) -> pd.DataFrame:
    """Global index via index_global_hist_em (daily, will resample to weekly).
    Returns column '最新价' for closing price.
    """
    import akshare as ak

    df = ak.index_global_hist_em(symbol=name)
    return df


def _fetch_gold_sge(start: str, end: str) -> pd.DataFrame:
    """Gold spot price via spot_hist_sge (AU9999, daily)."""
    import akshare as ak

    df = ak.spot_hist_sge(symbol="Au99.99")
    return df


def _fetch_gold_futures(start: str, end: str) -> pd.DataFrame:
    """Gold futures spot via futures_zh_spot (fallback)."""
    import akshare as ak

    df = ak.futures_zh_spot(symbol="AU0", market="CF")
    return df


# ---------------------------------------------------------------------------
#  Index definitions
#
#  Each entry is a dict with:
#    index_code  : unique key used in the CSV and as identifier
#    name        : human-readable label (for logging)
#    fetch       : callable(start_str, end_str) -> raw DataFrame
#    date_col    : name of the date column in raw df
#    close_col   : name of the close/price column in raw df
#    is_daily    : True if raw data is daily (needs weekly resampling)
# ---------------------------------------------------------------------------

INDEX_DEFS: list[dict] = [
    # ---- A-share domestic ----
    {
        "index_code": "000300",
        "name": "沪深300",
        "fetch": lambda s, e: _fetch_zh_a("000300", s, e),
        "date_col": "日期",
        "close_col": "收盘",
        "is_daily": False,  # already weekly from akshare
    },
    {
        "index_code": "000905",
        "name": "中证500",
        "fetch": lambda s, e: _fetch_zh_a("000905", s, e),
        "date_col": "日期",
        "close_col": "收盘",
        "is_daily": False,
    },
    {
        "index_code": "000852",
        "name": "中证1000",
        "fetch": lambda s, e: _fetch_zh_a("000852", s, e),
        "date_col": "日期",
        "close_col": "收盘",
        "is_daily": False,
    },
    {
        "index_code": "399006",
        "name": "创业板指",
        "fetch": lambda s, e: _fetch_zh_a("399006", s, e),
        "date_col": "日期",
        "close_col": "收盘",
        "is_daily": False,
    },
    {
        "index_code": "000012",
        "name": "中证全债",
        "fetch": lambda s, e: _fetch_zh_a("000012", s, e),
        "date_col": "日期",
        "close_col": "收盘",
        "is_daily": False,
    },
    {
        "index_code": "000978",
        "name": "南华商品",
        "fetch": lambda s, e: _fetch_zh_a("000978", s, e),
        "date_col": "日期",
        "close_col": "收盘",
        "is_daily": False,
    },
    # ---- HK ----
    {
        "index_code": "HSI",
        "name": "恒生指数",
        "fetch": lambda s, e: _fetch_hk_sina("HSI", s, e),
        "date_col": "date",
        "close_col": "close",
        "is_daily": True,
    },
    {
        "index_code": "HSTECH",
        "name": "恒生科技",
        "fetch": lambda s, e: _fetch_hk_sina("HSTECH", s, e),
        "date_col": "date",
        "close_col": "close",
        "is_daily": True,
    },
    # ---- US ----
    {
        "index_code": ".INX",
        "name": "标普500",
        "fetch": lambda s, e: _fetch_us_sina(".INX", s, e),
        "date_col": "date",
        "close_col": "close",
        "is_daily": True,
    },
    {
        "index_code": ".NDX",
        "name": "纳斯达克100",
        "fetch": lambda s, e: _fetch_us_sina(".NDX", s, e),
        "date_col": "date",
        "close_col": "close",
        "is_daily": True,
    },
    # ---- Global (index_global_hist_em) ----
    {
        "index_code": "EU50",
        "name": "欧洲斯托克50",
        "fetch": lambda s, e: _fetch_global_em("欧洲斯托克50", s, e),
        "date_col": "日期",
        "close_col": "最新价",
        "is_daily": True,
    },
    {
        "index_code": "N225",
        "name": "日经225",
        "fetch": lambda s, e: _fetch_global_em("日经225", s, e),
        "date_col": "日期",
        "close_col": "最新价",
        "is_daily": True,
    },
    {
        "index_code": "MSCIEM",
        "name": "MSCI新兴市场",
        "fetch": lambda s, e: _fetch_global_em("MSCI新兴市场", s, e),
        "date_col": "日期",
        "close_col": "最新价",
        "is_daily": True,
    },
    {
        "index_code": "MSCIWORLD",
        "name": "MSCI全球",
        "fetch": lambda s, e: _fetch_global_em("MSCI全球", s, e),
        "date_col": "日期",
        "close_col": "最新价",
        "is_daily": True,
    },
    # ---- Gold ----
    {
        "index_code": "AU9999",
        "name": "黄金AU9999",
        "fetch": lambda s, e: _fetch_gold_sge(s, e),
        "date_col": "date",
        "close_col": "close",
        "is_daily": True,
        "gold_fallback": True,  # mark for special handling
    },
]


# ---------------------------------------------------------------------------
#  Helper utilities
# ---------------------------------------------------------------------------


def _to_date_str(d: date) -> str:
    return d.strftime("%Y%m%d")


def _load_existing() -> pd.DataFrame:
    """Load existing index_weekly.csv if present, return empty DataFrame otherwise."""
    if OUTPUT_CSV.exists():
        try:
            df = pd.read_csv(OUTPUT_CSV, parse_dates=["date"])
            df["date"] = pd.to_datetime(df["date"]).dt.date
            return df
        except Exception as exc:
            print(f"Warning: could not read existing {OUTPUT_CSV}: {exc}")
    return pd.DataFrame(columns=["date", "index_code", "open", "high", "low", "close"])


def _last_date_for(existing: pd.DataFrame, index_code: str) -> str:
    """Return the day after the last stored date for a given index (YYYYMMDD)."""
    subset = existing[existing["index_code"] == index_code]
    if subset.empty:
        return START_DATE
    last = pd.to_datetime(subset["date"]).max().date()
    next_day = last + timedelta(days=1)
    return _to_date_str(next_day)


def _resample_to_weekly(
    df: pd.DataFrame, date_col: str, close_col: str
) -> pd.DataFrame:
    """
    Resample daily OHLC (or close-only) data to weekly (Friday close).
    Returns DataFrame with columns: date, open, high, low, close.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col).sort_index()

    # Normalize column names for possible OHLC columns
    col_map = {}
    lower_cols = {c.lower(): c for c in df.columns}

    # Try to find open/high/low columns; they may not exist in all APIs
    for std, candidates in [
        ("open", ["open", "开盘"]),
        ("high", ["high", "最高"]),
        ("low", ["low", "最低"]),
    ]:
        for cand in candidates:
            if cand in lower_cols:
                col_map[std] = lower_cols[cand]
                break
            if cand in df.columns:
                col_map[std] = cand
                break

    close_series = df[close_col].apply(pd.to_numeric, errors="coerce")

    agg_dict: dict = {"close": ("W-FRI", close_series, "last")}

    # Build resampled frame
    resampled = close_series.resample("W-FRI").last().rename("close")
    result = resampled.to_frame()

    for std, orig_col in col_map.items():
        s = df[orig_col].apply(pd.to_numeric, errors="coerce")
        if std == "open":
            result[std] = s.resample("W-FRI").first()
        elif std == "high":
            result[std] = s.resample("W-FRI").max()
        elif std == "low":
            result[std] = s.resample("W-FRI").min()

    # Fill missing OHLC with close
    for col in ["open", "high", "low"]:
        if col not in result.columns:
            result[col] = result["close"]

    result = result[["open", "high", "low", "close"]].dropna(subset=["close"])
    result.index.name = "date"
    result = result.reset_index()
    result["date"] = result["date"].dt.date
    return result


def _normalize_zh_a_weekly(
    df: pd.DataFrame, date_col: str, close_col: str
) -> pd.DataFrame:
    """
    Normalize A-share weekly data from index_zh_a_hist.
    The API already returns weekly bars; just standardise column names.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col]).dt.date

    col_map = {
        "date": date_col,
        "close": close_col,
    }
    for std, candidates in [
        ("open", ["开盘", "open"]),
        ("high", ["最高", "high"]),
        ("low", ["最低", "low"]),
    ]:
        for cand in candidates:
            if cand in df.columns:
                col_map[std] = cand
                break

    rename = {v: k for k, v in col_map.items() if v in df.columns}
    df = df.rename(columns=rename)

    for col in ["open", "high", "low", "close"]:
        if col not in df.columns:
            df[col] = df.get("close", float("nan"))
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df[["date", "open", "high", "low", "close"]].dropna(subset=["close"])


# ---------------------------------------------------------------------------
#  Gold-specific fetch with fallback
# ---------------------------------------------------------------------------


def _fetch_gold(start: str, end: str) -> tuple:
    """Try spot_hist_sge first; fall back to futures_zh_spot on failure."""
    try:
        df = _fetch_gold_sge(start, end)
        if df is not None and not df.empty:
            print("  Gold: using spot_hist_sge (Au99.99)")
            return df, "date", "close"
    except Exception as exc:
        print(f"  Gold spot_hist_sge failed: {exc}, trying futures fallback...")

    try:
        df = _fetch_gold_futures(start, end)
        if df is not None and not df.empty:
            print("  Gold: using futures_zh_spot fallback")
            return df, "date", "close"
    except Exception as exc:
        print(f"  Gold futures fallback also failed: {exc}")
    return None, None, None


# ---------------------------------------------------------------------------
#  Main fetch loop
# ---------------------------------------------------------------------------


def fetch_all(force_full: bool = False) -> None:
    """Fetch all proxy indices and write/update base_datas/index_weekly.csv."""
    BASE_DATAS_DIR.mkdir(parents=True, exist_ok=True)

    existing = _load_existing()
    today_str = _to_date_str(date.today())
    all_frames: list[pd.DataFrame] = []

    if not existing.empty and not force_full:
        # Keep all existing rows; we will append new rows below
        all_frames.append(existing)

    for idx_def in INDEX_DEFS:
        code = idx_def["index_code"]
        label = idx_def["name"]
        is_daily = idx_def.get("is_daily", False)
        date_col = idx_def["date_col"]
        close_col = idx_def["close_col"]
        is_gold = idx_def.get("gold_fallback", False)

        if force_full:
            start_str = START_DATE
        else:
            start_str = _last_date_for(existing, code)

        # Check if we already have up-to-date data
        if start_str > today_str:
            print(f"[skip]   {code:12s} {label} — already up to date")
            continue

        print(f"[fetch]  {code:12s} {label}  ({start_str} -> {today_str})")

        try:
            if is_gold:
                raw_df, date_col_actual, close_col_actual = _fetch_gold(
                    start_str, today_str
                )
                if raw_df is None:
                    print(f"  Warning: skipping {label} — all fetch attempts failed")
                    continue
                date_col = date_col_actual or date_col
                close_col = close_col_actual or close_col
                weekly = _resample_to_weekly(raw_df, date_col, close_col)
            elif is_daily:
                raw_df = idx_def["fetch"](start_str, today_str)
                if raw_df is None or raw_df.empty:
                    print(f"  Warning: empty result for {label}, skipping")
                    continue
                weekly = _resample_to_weekly(raw_df, date_col, close_col)
            else:
                # A-share weekly: already weekly bars from akshare
                raw_df = idx_def["fetch"](start_str, today_str)
                if raw_df is None or raw_df.empty:
                    print(f"  Warning: empty result for {label}, skipping")
                    continue
                weekly = _normalize_zh_a_weekly(raw_df, date_col, close_col)

            # Filter to start_date and beyond (incremental mode)
            if not force_full and not existing.empty:
                start_filter = pd.to_datetime(start_str).date()
                weekly = weekly[weekly["date"] >= start_filter]

            if weekly.empty:
                print(f"  No new rows for {label}")
                continue

            weekly.insert(1, "index_code", code)
            all_frames.append(weekly)
            print(f"  +{len(weekly)} rows")

        except Exception as exc:
            print(f"  Warning: failed to fetch {label} ({code}): {exc}")
            continue

    if not all_frames:
        print("No data fetched.")
        return

    combined = pd.concat(all_frames, ignore_index=True)
    combined["date"] = pd.to_datetime(combined["date"]).dt.date

    # Deduplicate (keep last occurrence per date+code, newer fetch wins)
    combined = combined.drop_duplicates(subset=["date", "index_code"], keep="last")
    combined = combined.sort_values(["index_code", "date"]).reset_index(drop=True)

    # Apply 000852 (CSI 1000) gap-fill: use 000905 (CSI 500) for dates before 2014-12-31
    combined = _fill_csi1000_gap(combined)

    combined.to_csv(OUTPUT_CSV, index=False)
    print(f"\nSaved {len(combined)} rows to {OUTPUT_CSV}")


def _fill_csi1000_gap(df: pd.DataFrame) -> pd.DataFrame:
    """
    000852 (CSI 1000) launched in 2014; backfill 2010-2014 with 000905 (CSI 500).
    Only fills if 000852 rows are missing for the gap period.
    """
    cutoff = date(2014, 12, 31)
    has_852 = df[(df["index_code"] == "000852") & (df["date"] <= cutoff)]
    if not has_852.empty:
        return df  # already have data, nothing to fill

    csi500_rows = df[(df["index_code"] == "000905") & (df["date"] <= cutoff)].copy()
    if csi500_rows.empty:
        return df

    csi500_rows["index_code"] = "000852"
    print(
        f"  000852 gap-fill: copying {len(csi500_rows)} rows from 000905 for 2010-2014"
    )
    return pd.concat([df, csi500_rows], ignore_index=True)


# ---------------------------------------------------------------------------
#  Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    force = "--full" in sys.argv
    if force:
        print("Mode: full refresh (ignoring existing data)")
    else:
        print("Mode: incremental update")

    fetch_all(force_full=force)
