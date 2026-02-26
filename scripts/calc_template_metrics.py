"""
scripts/calc_template_metrics.py — v3 D3

Read base_datas/index_weekly.csv and compute:
  1. Per-template weighted portfolio metrics -> base_datas/template_metrics.json
  2. Per-category single-index metrics       -> base_datas/index_metrics.json

Metrics computed (2010-01-01 to latest available data):
  - Annualized return (geometric mean)
  - Annualized volatility (weekly return std x sqrt(52))
  - Max drawdown (based on weekly NAV curve)
  - Sharpe ratio ((annualized return - risk_free_rate) / annualized_vol)

Run:
    python3 scripts/calc_template_metrics.py

Prints results to stdout for manual verification.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
import numpy as np

ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ROOT))

BASE_DATAS_DIR = ROOT / "base_datas"
INPUT_CSV = BASE_DATAS_DIR / "index_weekly.csv"
OUTPUT_TEMPLATE_METRICS = BASE_DATAS_DIR / "template_metrics.json"
OUTPUT_INDEX_METRICS = BASE_DATAS_DIR / "index_metrics.json"

RISK_FREE_RATE = 2.0  # % per year, approximate 2010-present average
WEEKS_PER_YEAR = 52.0

# ---------------------------------------------------------------------------
#  Category -> index_code mapping
#  Each asset category in templates.py maps to one proxy index.
#  "短期债券" and "货币基金" have no index proxy; use fixed annual constants.
# ---------------------------------------------------------------------------

CATEGORY_INDEX_MAP: dict[str, Optional[str]] = {
    "A股大盘": "000300",
    "A股中盘": "000905",
    "A股小盘": "000852",
    "A股成长": "399006",
    "港股": "HSI",
    "港股科技": "HSTECH",
    "美股大盘": ".INX",
    "美股科技": ".NDX",
    "欧洲股票": "EU50",
    "日本股票": "N225",
    "新兴市场股票": "MSCIEM",
    "发达市场股票": "MSCIWORLD",
    "债券": "000012",
    "大宗商品": "000978",
    "黄金": "AU9999",
    # Fixed constants (no index proxy):
    "短期债券": None,  # 2.5% fixed annual
    "货币基金": None,  # 2.0% fixed annual
}

# Fixed annual returns for constant-yield assets (%)
FIXED_RETURN: dict[str, float] = {
    "短期债券": 2.5,
    "货币基金": 2.0,
}

# ---------------------------------------------------------------------------
#  Template definitions (allocations mirrored from templates.py)
#  category -> weight (0-1); must sum to 1.0
# ---------------------------------------------------------------------------

TEMPLATE_ALLOCATIONS: dict[str, dict[str, float]] = {
    "global_balanced": {
        "A股大盘": 0.20,
        "发达市场股票": 0.20,
        "新兴市场股票": 0.10,
        "美股大盘": 0.10,
        "债券": 0.25,
        "债券_全球": 0.10,  # special key; maps to 000012 as proxy
        "黄金": 0.05,
    },
    "a_share_core": {
        "A股大盘": 0.35,
        "A股中盘": 0.20,
        "A股小盘": 0.15,
        "港股": 0.10,
        "债券": 0.15,
        "货币基金": 0.05,
    },
    "all_weather": {
        "A股大盘": 0.12,
        "发达市场股票": 0.13,
        "债券": 0.30,
        "债券_全球": 0.15,
        "黄金": 0.15,
        "大宗商品": 0.10,
        "货币基金": 0.05,
    },
    "growth_aggressive": {
        "美股科技": 0.30,
        "A股成长": 0.20,
        "新兴市场股票": 0.20,
        "港股科技": 0.15,
        "债券": 0.10,
        "货币基金": 0.05,
    },
    "global_diversified": {
        "美股大盘": 0.20,
        "欧洲股票": 0.12,
        "日本股票": 0.08,
        "A股大盘": 0.10,
        "新兴市场股票": 0.10,
        "债券_全球": 0.20,
        "黄金": 0.10,
        "大宗商品": 0.05,
        "货币基金": 0.05,
    },
    "cash_conservative": {
        "货币基金": 0.40,
        "短期债券": 0.30,
        "债券": 0.15,
        "黄金": 0.10,
        "A股大盘": 0.05,
    },
}

# Resolve "债券_全球" to the same index as "债券" (000012 as best available proxy)
# This is noted explicitly so readers understand the approximation.
CATEGORY_INDEX_MAP["债券_全球"] = "000012"


# ---------------------------------------------------------------------------
#  Data loading
# ---------------------------------------------------------------------------


def load_weekly_data() -> pd.DataFrame:
    """Load index_weekly.csv and return a clean DataFrame indexed by date."""
    if not INPUT_CSV.exists():
        print(f"Error: {INPUT_CSV} not found.")
        print("Run python3 scripts/fetch_index_data.py first.")
        sys.exit(1)

    df = pd.read_csv(INPUT_CSV, parse_dates=["date"])
    df["date"] = df["date"].dt.date
    df["close"] = pd.to_numeric(df["close"], errors="coerce")
    return df


def get_close_series(df: pd.DataFrame, index_code: str) -> pd.Series:
    """Extract weekly close price series for a given index code."""
    subset = df[df["index_code"] == index_code][["date", "close"]].copy()
    subset = subset.dropna(subset=["close"])
    subset = subset.sort_values("date")
    s = pd.Series(subset["close"].values, index=pd.to_datetime(subset["date"]))
    return s


def build_fixed_return_series(
    annual_pct: float, ref_index: pd.DatetimeIndex
) -> pd.Series:
    """
    Build a synthetic weekly return series for fixed-yield assets (货币基金, 短期债券).
    Returns a constant weekly return series aligned to ref_index.
    """
    weekly_return = (1 + annual_pct / 100) ** (1 / WEEKS_PER_YEAR) - 1
    return pd.Series(weekly_return, index=ref_index)


# ---------------------------------------------------------------------------
#  Metric computations
# ---------------------------------------------------------------------------


def calc_returns(price_series: pd.Series) -> pd.Series:
    """Compute weekly percentage returns from price series."""
    return price_series.pct_change().dropna()


def calc_annualized_return(returns: pd.Series) -> float:
    """Geometric annualized return (%)."""
    if returns.empty:
        return 0.0
    cumulative = (1 + returns).prod()
    n_weeks = len(returns)
    if n_weeks < 2 or cumulative <= 0:
        return 0.0
    ann_return = (cumulative ** (WEEKS_PER_YEAR / n_weeks) - 1) * 100
    return round(float(ann_return), 2)


def calc_annualized_vol(returns: pd.Series) -> float:
    """Annualized volatility (%) = weekly std * sqrt(52)."""
    if returns.empty or len(returns) < 2:
        return 0.0
    vol = float(returns.std()) * (WEEKS_PER_YEAR**0.5) * 100
    return round(vol, 2)


def calc_max_drawdown(returns: pd.Series) -> float:
    """Max drawdown (%) from weekly NAV curve. Returns a negative value."""
    if returns.empty:
        return 0.0
    nav = (1 + returns).cumprod()
    rolling_max = nav.cummax()
    drawdown = (nav - rolling_max) / rolling_max
    mdd = float(drawdown.min()) * 100
    return round(mdd, 2)


def calc_sharpe(annualized_return: float, annualized_vol: float) -> float:
    """Sharpe ratio = (ann_return - risk_free) / ann_vol."""
    if annualized_vol == 0:
        return 0.0
    sharpe = (annualized_return - RISK_FREE_RATE) / annualized_vol
    return round(float(sharpe), 3)


def compute_single_index_metrics(returns: pd.Series) -> dict:
    """Compute all metrics for a single return series."""
    ann_return = calc_annualized_return(returns)
    ann_vol = calc_annualized_vol(returns)
    mdd = calc_max_drawdown(returns)
    sharpe = calc_sharpe(ann_return, ann_vol)
    return {
        "annualized_return": ann_return,
        "annualized_volatility": ann_vol,
        "max_drawdown": mdd,
        "sharpe_ratio": sharpe,
    }


# ---------------------------------------------------------------------------
#  Portfolio composition
# ---------------------------------------------------------------------------


def build_portfolio_returns(
    allocations: dict[str, float],
    df: pd.DataFrame,
) -> pd.Series:
    """
    Build weighted composite weekly return series from category allocations.

    For fixed-yield categories (货币基金, 短期债券), uses constant weekly return.
    For index-backed categories, uses actual price history.
    Returns are aligned to the common date range of all included indices.
    """
    # First pass: collect all index return series
    index_returns: dict[str, pd.Series] = {}
    fixed_series: dict[
        str, tuple[float, float]
    ] = {}  # cat -> (weight, fixed_ann_return)

    for cat, weight in allocations.items():
        idx_code = CATEGORY_INDEX_MAP.get(cat)
        if idx_code is None:
            # Fixed yield
            fixed_ann = FIXED_RETURN.get(cat, 2.0)
            fixed_series[cat] = (weight, fixed_ann)
            continue
        prices = get_close_series(df, idx_code)
        if prices.empty:
            print(
                f"  Warning: no price data for category '{cat}' (index={idx_code}), skipping"
            )
            continue
        returns = calc_returns(prices)
        if returns.empty:
            continue
        index_returns[cat] = returns

    # Find common date range for index-backed assets
    if not index_returns:
        # All fixed — just use a synthetic 10-year series
        ref_idx = pd.date_range("2010-01-01", periods=520, freq="W-FRI")
        combined = pd.Series(0.0, index=ref_idx)
        for cat, (w, fixed_ann) in fixed_series.items():
            fixed_r = build_fixed_return_series(fixed_ann, ref_idx)
            combined = combined + w * fixed_r
        return combined

    # Align all index return series to a common index
    all_series = list(index_returns.values())
    common_index = all_series[0].index
    for s in all_series[1:]:
        common_index = common_index.intersection(s.index)

    common_index = common_index.sort_values()

    # Weighted sum
    portfolio_returns = pd.Series(0.0, index=common_index)
    total_weight_used = 0.0

    for cat, returns in index_returns.items():
        aligned = returns.reindex(common_index).fillna(0)
        weight = allocations[cat]
        portfolio_returns += weight * aligned
        total_weight_used += weight

    # Add fixed-yield contributions
    for cat, (weight, fixed_ann) in fixed_series.items():
        fixed_r = build_fixed_return_series(fixed_ann, common_index)
        portfolio_returns += weight * fixed_r
        total_weight_used += weight

    # Normalise if weights don't sum exactly to 1 (due to missing indices)
    if total_weight_used > 0 and abs(total_weight_used - 1.0) > 0.01:
        print(
            f"  Note: total weight used = {total_weight_used:.2f} (some indices missing); normalising"
        )
        portfolio_returns /= total_weight_used

    return portfolio_returns


# ---------------------------------------------------------------------------
#  Main computation
# ---------------------------------------------------------------------------


def compute_template_metrics(df: pd.DataFrame) -> dict:
    """Compute metrics for all templates."""
    start_date = pd.Timestamp("2010-01-01")
    results = {}

    for tmpl_id, allocations in TEMPLATE_ALLOCATIONS.items():
        print(f"\nComputing: {tmpl_id}")
        port_returns = build_portfolio_returns(allocations, df)

        # Filter to 2010-01-01 onwards
        port_returns = port_returns[port_returns.index >= start_date]

        if port_returns.empty:
            print(f"  Warning: no data for {tmpl_id}, skipping")
            continue

        ann_return = calc_annualized_return(port_returns)
        ann_vol = calc_annualized_vol(port_returns)
        mdd = calc_max_drawdown(port_returns)
        sharpe = calc_sharpe(ann_return, ann_vol)

        data_end = port_returns.index.max().date().strftime("%Y-%m-%d")

        print(
            f"  Ann.Return={ann_return:.1f}%  Volatility={ann_vol:.1f}%  "
            f"MaxDD={mdd:.1f}%  Sharpe={sharpe:.3f}"
        )

        results[tmpl_id] = {
            "annualized_return": ann_return,
            "annualized_volatility": ann_vol,
            "max_drawdown": mdd,
            "sharpe_ratio": sharpe,
        }

    return results


def compute_index_metrics(df: pd.DataFrame) -> dict:
    """Compute single-index metrics for each category's proxy index."""
    start_date = pd.Timestamp("2010-01-01")
    results = {}

    seen_codes: dict[str, str] = {}  # index_code -> first category that used it

    for cat, idx_code in CATEGORY_INDEX_MAP.items():
        if idx_code is None:
            # Fixed yield asset
            fixed_ann = FIXED_RETURN.get(cat, 2.0)
            results[cat] = {
                "index_code": None,
                "annualized_return": fixed_ann,
                "annualized_volatility": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": round((fixed_ann - RISK_FREE_RATE) / 0.001, 3)
                if fixed_ann > RISK_FREE_RATE
                else 0.0,
                "note": "fixed annual constant (no index proxy)",
            }
            continue

        prices = get_close_series(df, idx_code)
        if prices.empty:
            print(f"  Warning: no data for {cat} ({idx_code})")
            results[cat] = {
                "index_code": idx_code,
                "annualized_return": None,
                "annualized_volatility": None,
                "max_drawdown": None,
                "sharpe_ratio": None,
                "note": "no data available",
            }
            continue

        returns = calc_returns(prices)
        returns = returns[returns.index >= start_date]

        metrics = compute_single_index_metrics(returns)
        data_end = (
            prices.index.max().date().strftime("%Y-%m-%d")
            if not prices.empty
            else "N/A"
        )

        results[cat] = {
            "index_code": idx_code,
            **metrics,
        }
        print(
            f"  {cat:20s} ({idx_code:10s})  Ann={metrics['annualized_return']:.1f}%  "
            f"Vol={metrics['annualized_volatility']:.1f}%  "
            f"MDD={metrics['max_drawdown']:.1f}%  "
            f"Sharpe={metrics['sharpe_ratio']:.3f}"
        )

    return results


def main() -> None:
    print("Loading index_weekly.csv ...")
    df = load_weekly_data()
    print(
        f"  {len(df)} rows, {df['index_code'].nunique()} indices, "
        f"date range: {df['date'].min()} – {df['date'].max()}"
    )

    # ---- Per-index metrics ----
    print("\n=== Single-index metrics ===")
    index_metrics = compute_index_metrics(df)

    # ---- Per-template metrics ----
    print("\n=== Template portfolio metrics ===")
    template_metrics = compute_template_metrics(df)

    # ---- Determine data period ----
    data_end_date = str(df["date"].max())
    data_period = f"2010-01-01 至 {data_end_date}"

    # ---- Write outputs ----
    BASE_DATAS_DIR.mkdir(parents=True, exist_ok=True)
    today_str = date.today().isoformat()

    template_output = {
        "calculated_at": today_str,
        "data_period": data_period,
        "risk_free_rate_pct": RISK_FREE_RATE,
        "note": "Max drawdown based on weekly NAV; may underestimate intraweek extremes by ~5-10%.",
        "templates": template_metrics,
    }

    with open(OUTPUT_TEMPLATE_METRICS, "w", encoding="utf-8") as f:
        json.dump(template_output, f, ensure_ascii=False, indent=2)
    print(f"\nWrote {OUTPUT_TEMPLATE_METRICS}")

    index_output = {
        "calculated_at": today_str,
        "data_period": data_period,
        "risk_free_rate_pct": RISK_FREE_RATE,
        "categories": index_metrics,
    }

    with open(OUTPUT_INDEX_METRICS, "w", encoding="utf-8") as f:
        json.dump(index_output, f, ensure_ascii=False, indent=2)
    print(f"Wrote {OUTPUT_INDEX_METRICS}")

    # ---- Summary table ----
    print("\n=== Template metrics summary ===")
    print(f"{'Template':<25} {'AnnRet':>8} {'Vol':>8} {'MaxDD':>8} {'Sharpe':>8}")
    print("-" * 62)
    for tid, m in template_metrics.items():
        print(
            f"{tid:<25} {m['annualized_return']:>7.1f}%  {m['annualized_volatility']:>7.1f}%  "
            f"{m['max_drawdown']:>7.1f}%  {m['sharpe_ratio']:>7.3f}"
        )


if __name__ == "__main__":
    main()
