# Anti-FOMO v1 开发 Wiki

> 本文档是 v1 开发的短期记忆, 供后续开发者(含 AI agent)快速定位当前实现状态、接口约定和待办事项.
> 不是用户手册, 不是设计文档.

---

## 当前状态 (feat/v1-dev)

| Engine | 状态 | 备注 |
|--------|------|------|
| portfolio_engine | 完成 (v0) | 数据获取 / 波动计算 / 阈值告警 |
| market_engine | 完成 (v1) | PE/PB 百分位 / 市场评分 / 文件缓存 |
| decision_engine | 完成 (v1) | 看盘判断 / 再平衡检测 |
| report_engine | 完成 (v1) | 日度简报 / 周度报告 |
| ai_engine | 部分 (v0 接口) | 仅接受 portfolio 信号, 未纳入 market/decision |
| notification | 完成 (v0) | console / file / email, 接口未变 |

`python run.py` 完整跑通, 输出日度判断。`python run.py weekly` 手动生成周报。
`python run.py schedule` 每日定时检查 + 每周五定时周报。

---

## 目录结构 (实际)

```
src/
  main.py                        # 编排器 AntiFOMO
  portfolio_engine/
    portfolio.py                 # Portfolio, Holding, AllocationType, HoldingType
    data_fetcher.py              # DataFetcher (akshare)
    volatility.py                # VolatilityCalculator, VolatilityResult, PortfolioVolatilityResult
    threshold.py                 # ThresholdManager, ThresholdConfig, AlertLevel, AlertResult
    mock_data.py
  market_engine/
    valuation_fetcher.py         # ValuationFetcher.fetch_pe / fetch_pb
    percentile.py                # PercentileCalculator.calculate / calculate_with_window
    market_scorer.py             # MarketScorer, MarketStatus, MarketState, IndexValuation
    cache.py                     # DataCache (pickle + json meta, TTL)
  decision_engine/
    rebalance_checker.py         # RebalanceChecker, RebalanceItem
    pace_controller.py           # PaceController, Decision
  report_engine/
    daily_digest.py              # DailyDigest.generate
    weekly_report.py             # WeeklyReport.generate
  ai_engine/
    analyzer.py                  # AIAnalyzer (OpenAI-compatible, v0 接口未扩展)
  notification/
    manager.py                   # NotificationManager
  asset_configurator.py          # Legacy CLI 向导, 不扩展
```

---

## 核心数据结构

### portfolio_engine

```python
# volatility.py
@dataclass
class VolatilityResult:
    symbol: str
    name: str
    current_price: float
    previous_price: float
    change_pct: float        # 日涨跌幅 (%)
    volatility: float        # 历史波动率 (20日标准差 %)
    weight: float            # 持仓权重 (0-1)
    month_return_pct: float  # 近一月涨跌幅 (%)

@dataclass
class PortfolioVolatilityResult:
    total_volatility: float              # abs(加权日涨跌幅)
    individual_results: List[VolatilityResult]
    weighted_volatility: float
    max_volatility_holding: VolatilityResult

# threshold.py
class AlertLevel(Enum):
    NONE = "none"
    WARNING = "warning"
    ALERT = "alert"

@dataclass
class AlertResult:
    level: AlertLevel
    portfolio_level: AlertLevel
    individual_alerts: List[tuple]  # (symbol, name, level)
    message: str
    should_notify: bool
```

### market_engine

```python
# market_scorer.py
class MarketState(Enum):
    CHEAP = "cheap"        # 综合评分 < 20
    NORMAL = "normal"      # 20 <= 评分 <= 80
    EXPENSIVE = "expensive"  # 评分 > 80

@dataclass
class IndexValuation:
    symbol: str            # 中文名 (如 "沪深300")
    name: str
    pe_ttm: float
    pb: float
    pe_percentile: float   # 0-100
    pb_percentile: float
    score: float           # (pe_pct + pb_pct) / 2

@dataclass
class MarketStatus:
    indices: Dict[str, IndexValuation]
    composite_score: float
    market_state: MarketState
    updated_at: datetime
```

### decision_engine

```python
# rebalance_checker.py
@dataclass
class RebalanceItem:
    symbol: str
    name: str
    target_weight: float   # 0-1
    current_weight: float  # 0-1
    deviation: float       # 百分点, 正=超配, 负=低配

# pace_controller.py
@dataclass
class Decision:
    should_check: bool
    should_check_reason: str
    action_suggestion: str
    rebalance_needed: bool
    rebalance_details: List[RebalanceItem]
    confidence: str        # "高" / "中" / "低"
```

---

## 主编排器接口 (src/main.py)

```python
class AntiFOMO:
    def run_check()          # 日度检查, 输出 DailyDigest
    def run_weekly_report()  # 周报, 保存至 logs/weekly_YYYYMMDD.md
    def run_continuous()     # 调度: 每日 check_time + 每周五 weekly_time
```

内部调用顺序:

```
_collect_portfolio_data()  -> PortfolioVolatilityResult, AlertResult
market_scorer.evaluate()   -> MarketStatus
_make_decision()           -> Decision
daily_digest.generate()    -> str  (run_check)
weekly_report.generate()   -> str  (run_weekly_report)
ai_analyzer.analyze()      -> Optional[str]
notification_manager.send()
```

`_make_decision()` 的目标权重来源:

1. 优先使用 `asset_allocation.calculable_weights`（由 `serve.py` 生成写入 `config.asset.yaml`）
2. 不存在时退化为当前权重（再平衡检测结果恒为无偏离）

---

## 配置文件

`config.yaml` 关键 section（完整文件见项目根目录）:

```yaml
market_engine:
  enabled: true
  indices:
    - {symbol: "沪深300", code: "000300", weight: 0.5}
    - {symbol: "中证500", code: "000905", weight: 0.3}
    - {symbol: "上证50",  code: "000016", weight: 0.2}
  percentile_window_years: 10
  thresholds: {cheap: 20, expensive: 80}

decision_engine:
  enabled: true
  check_market_volatility: true   # 市场极端时也触发看盘提示
  rebalance_threshold: 5.0        # 百分点

report:
  weekly:
    enabled: true
    day: "friday"
    time: "16:00"
    include_ai: true

cache:
  enabled: true
  dir: "cache/"
  ttl_hours: 24
```

`config.asset.yaml` 由 `serve.py` 生成, 含 `portfolio.holdings` 和可选的 `asset_allocation`.
持仓的 `symbol` 字段是 akshare 行情代码 (如 `000510`), `market_engine.indices[].symbol` 是 akshare 估值接口的中文名 (如 `沪深300`), 两者用途不同, 不要混淆.

---

## 已知技术债

| 位置 | 问题 | 优先级 |
|------|------|--------|
| `cache.py:28-31` | cache key 含中文直接作为文件名, Windows/NAS 可能报错 | 低 |
| `ai_engine/analyzer.py` | `analyze()` 只接受 `portfolio_result + alert_result`, 未纳入 `MarketStatus` / `Decision` | 中 |
| `main.py:_make_decision` | 无独立目标权重配置时再平衡检测无意义 (当前=目标) | 低 |
| `run.py` | `python` 命令在 macOS 系统 Python 3.9 环境下需用 `python3` | 低 |

---

## 下一步开发重点 (P1 预留)

按 v1-goal.md 定义的 P1 范围:

1. **ai_engine 扩展** — 将 `MarketStatus` 和 `Decision` 纳入 prompt, 输出综合市场+资产的定性分析。接口改为 `analyze(portfolio_result, alert_result, market_status=None, decision=None)`

2. **目标权重配置** — 在 `config.asset.yaml` 或 `config.yaml` 中支持独立的目标权重字段, 使再平衡检测真正有意义

3. **notification 扩展** — 目前 `send()` 接口仍是 v0 签名 `(portfolio_result, alert_result, ai_analysis)`, 未传入周报内容; 周报通知需要新增发送路径或扩展 `send()` 接口

4. **Web 仪表盘** (`serve.py`) — `GET /api/market-status` 返回 `MarketStatus` JSON, 供前端展示

5. **宏观环境** (`src/macro_engine/`) — P1 预留目录未创建, 接口预留在 `PaceController.decide(macro_status=None)`

---

## 运行验证

```bash
# 单次日度检查
python3 run.py

# 手动生成周报
python3 run.py weekly

# 启动调度器 (每日 15:30 + 每周五 16:00)
python3 run.py schedule

# Web 资产配置 UI
python3 serve.py
```
