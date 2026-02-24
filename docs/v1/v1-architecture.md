# Anti-FOMO v1 -- 架构设计

## 设计原则

1. 融合而非重写 -- 在 v0 基础上新增模块, 不破坏已有功能.
2. Engine 模块制 -- 按业务职责划分为独立 engine, 各自负责明确的输入/输出.
3. 配置驱动 -- 新增功能通过扩展 config.yaml 配置, 不硬编码业务参数.
4. 渐进式扩展 -- MVP 只做核心, 但目录结构和接口设计为 P1 预留空间.
5. 单一数据源 -- PE/PB 数据统一通过 akshare 获取, 不引入新依赖.

## 目录结构 (重构后)

    anti-fomo/
    |-- run.py                         # CLI 入口 (不变)
    |-- serve.py                       # Web UI 入口 (不变)
    |-- config.yaml                    # 统一运行配置 (扩展)
    |-- config.example.yaml            # 示例配置 (扩展)
    |-- config.asset.yaml              # 持仓配置, serve.py 生成 (不变)
    |-- requirements.txt               # 依赖 (不变)
    |
    |-- src/
    |   |-- __init__.py
    |   |-- main.py                    # 主编排器 AntiFOMO (扩展)
    |   |
    |   |-- portfolio_engine/          # Layer 1: 个人资产状态 (v0 代码重组)
    |   |   |-- __init__.py
    |   |   |-- portfolio.py           # Portfolio, Holding 数据模型
    |   |   |-- data_fetcher.py        # 行情数据获取 (akshare)
    |   |   |-- volatility.py          # 波动率计算
    |   |   |-- threshold.py           # 阈值判断
    |   |   +-- mock_data.py           # Mock 数据生成
    |   |
    |   |-- market_engine/             # Layer 2: 市场估值状态 (v1 新增)
    |   |   |-- __init__.py
    |   |   |-- valuation_fetcher.py   # PE/PB 数据获取
    |   |   |-- percentile.py          # 百分位计算
    |   |   |-- market_scorer.py       # 市场状态评分
    |   |   +-- cache.py               # 数据缓存
    |   |
    |   |-- decision_engine/           # 决策节奏控制 (v1 新增)
    |   |   |-- __init__.py
    |   |   |-- pace_controller.py     # 看盘/忽略判断
    |   |   +-- rebalance_checker.py   # 再平衡检测
    |   |
    |   |-- report_engine/             # 报告生成 (v1 新增)
    |   |   |-- __init__.py
    |   |   |-- daily_digest.py        # 日度简报
    |   |   +-- weekly_report.py       # 周度报告
    |   |
    |   |-- ai_engine/                 # AI 分析 (v0 代码重组)
    |   |   |-- __init__.py
    |   |   +-- analyzer.py            # LLM 分析 (原 ai_analyzer.py)
    |   |
    |   |-- notification/              # 通知输出 (v0 代码重组)
    |   |   |-- __init__.py
    |   |   +-- manager.py             # 多渠道通知 (原 notification.py)
    |   |
    |   +-- asset_configurator.py      # Legacy CLI 配置向导 (保留, 不扩展)
    |
    |-- web/                           # Web SPA (保留, 后续扩展)
    |   |-- index.html
    |   |-- app.js
    |   +-- style.css
    |
    |-- docs/                          # 项目文档
    |-- logs/                          # 日志输出
    +-- cache/                         # 数据缓存 (v1 新增, gitignored)

### 与 v0 的映射关系

    v0 文件                    -> v1 位置
    -------------------------------------------------------
    src/portfolio.py           -> src/portfolio_engine/portfolio.py
    src/data_fetcher.py        -> src/portfolio_engine/data_fetcher.py
    src/volatility_calculator.py -> src/portfolio_engine/volatility.py
    src/threshold_manager.py   -> src/portfolio_engine/threshold.py
    src/mock_data.py           -> src/portfolio_engine/mock_data.py
    src/ai_analyzer.py         -> src/ai_engine/analyzer.py
    src/notification.py        -> src/notification/manager.py
    src/main.py                -> src/main.py (扩展)
    src/asset_configurator.py  -> src/asset_configurator.py (不动)

重组策略: 文件内容基本不变, 只调整目录位置和 import 路径.
每个 engine 的 __init__.py 导出核心类, 保持对外接口简洁.

## Engine 职责与接口

### portfolio_engine -- 个人资产状态

职责: 管理持仓数据, 获取行情, 计算波动, 判断阈值.
这是 v0 已有功能的打包, 逻辑不变.

    输入: config.asset.yaml (持仓配置)
    输出: PortfolioStatus
      - holdings: List[Holding]          # 持仓列表
      - weights: Dict[str, float]        # 当前权重
      - volatility: PortfolioVolatilityResult  # 波动结果
      - alert: AlertResult               # 告警结果

核心类:
- Portfolio / Holding (数据模型, 来自 portfolio.py)
- DataFetcher (行情获取, 来自 data_fetcher.py)
- VolatilityCalculator (波动计算, 来自 volatility_calculator.py)
- ThresholdManager (阈值判断, 来自 threshold_manager.py)

### market_engine -- 市场估值状态

职责: 获取指数 PE/PB 数据, 计算百分位, 输出市场评分.
这是 v1 核心新增模块.

    输入: config.yaml 中的 market_engine 配置
    输出: MarketStatus
      - indices: Dict[str, IndexValuation]  # 各指数估值
      - composite_score: float              # 综合评分 (0-100)
      - market_state: MarketState           # 便宜/正常/过热
      - updated_at: datetime                # 数据时间

#### 子模块说明

valuation_fetcher.py:

    class ValuationFetcher:
        def fetch_pe(symbol: str) -> pd.DataFrame
            # akshare stock_index_pe_lg(symbol)
            # 返回历史 PE 序列

        def fetch_pb(symbol: str) -> pd.DataFrame
            # akshare stock_index_pb_lg(symbol)
            # 返回历史 PB 序列

percentile.py:

    class PercentileCalculator:
        def calculate(series: pd.Series, current_value: float) -> float
            # 返回 current_value 在 series 中的百分位 (0-100)

        def calculate_with_window(series, value, years=10) -> float
            # 可选: 只用近 N 年数据计算百分位

market_scorer.py:

    @dataclass
    class IndexValuation:
        symbol: str
        name: str
        pe_ttm: float
        pb: float
        pe_percentile: float        # 0-100
        pb_percentile: float        # 0-100
        score: float                # (pe_pct + pb_pct) / 2

    class MarketState(Enum):
        CHEAP = "cheap"             # < 20
        NORMAL = "normal"           # 20-80
        EXPENSIVE = "expensive"     # > 80

    @dataclass
    class MarketStatus:
        indices: Dict[str, IndexValuation]
        composite_score: float
        market_state: MarketState
        updated_at: datetime

    class MarketScorer:
        def __init__(config):
            # 从 config 读取指数列表, 权重, 阈值

        def evaluate() -> MarketStatus:
            # 获取数据 -> 计算百分位 -> 打分 -> 判断状态

cache.py:

    class DataCache:
        def __init__(cache_dir="cache/"):
            # 文件缓存, 按日期+指数 key 存储

        def get(key: str) -> Optional[pd.DataFrame]:
            # 命中返回缓存, 否则 None

        def set(key: str, data: pd.DataFrame, ttl_hours=24):
            # 写入缓存

        def is_valid(key: str) -> bool:
            # 检查缓存是否过期

### decision_engine -- 决策节奏控制

职责: 融合 portfolio 和 market 信号, 输出行为建议.

    输入:
      - PortfolioStatus (from portfolio_engine)
      - MarketStatus (from market_engine)
    输出: Decision
      - should_check: bool                # 是否需要看盘
      - should_check_reason: str          # 原因
      - action_suggestion: str            # 行动建议
      - rebalance_needed: bool            # 是否需要再平衡
      - rebalance_details: List[str]      # 偏离详情
      - confidence: str                   # 判断置信度: 高/中/低

#### 子模块说明

pace_controller.py:

    @dataclass
    class Decision:
        should_check: bool
        should_check_reason: str
        action_suggestion: str
        rebalance_needed: bool
        rebalance_details: List[str]
        confidence: str

    class PaceController:
        def __init__(config):
            # 从 config 读取判断阈值

        def decide(portfolio_status, market_status) -> Decision:
            # 核心决策逻辑

rebalance_checker.py:

    class RebalanceChecker:
        def __init__(target_weights, threshold=5.0):
            # 目标权重和偏离阈值

        def check(current_weights) -> Tuple[bool, List[str]]:
            # 对比当前权重和目标权重
            # 返回 (是否需要再平衡, 偏离详情列表)

### report_engine -- 报告生成

职责: 将各 engine 输出组装为人类可读的报告.

    输入: PortfolioStatus, MarketStatus, Decision, Optional[AI分析]
    输出: str (格式化的文本报告)

#### 子模块说明

daily_digest.py:

    class DailyDigest:
        def generate(market_status, decision) -> str:
            # 生成 3-5 行的日度简报

weekly_report.py:

    class WeeklyReport:
        def generate(portfolio_status, market_status, decision,
                     ai_analysis=None) -> str:
            # 生成完整周度报告 (Markdown 格式)

### ai_engine -- AI 分析

职责: 调用 LLM API 进行定性分析. 与 v0 的 AIAnalyzer 功能相同,
重组为独立 engine 并扩展 prompt 以包含市场估值信息.

    输入: PortfolioStatus, MarketStatus, Decision
    输出: Optional[str] (AI 分析文本)

接口:

    class AIAnalyzer:
        def analyze(portfolio_status, market_status, decision) -> Optional[str]:
            # 构建 prompt, 调用 LLM, 返回分析文本

### notification -- 通知输出

职责: 多渠道消息分发. 与 v0 功能相同, 调整输入接口以适应新数据结构.

    输入: 报告内容 (str), 告警级别
    输出: 发送到 console / file / email

## 主编排器 (src/main.py)

AntiFOMO 类作为所有 engine 的编排器, 控制整体执行流程:

    class AntiFOMO:

        def run_check():
            # 日度检查 (完整流程):
            # 1. portfolio_engine -> PortfolioStatus
            # 2. market_engine -> MarketStatus
            # 3. decision_engine -> Decision
            # 4. report_engine -> DailyDigest
            # 5. (可选) ai_engine -> AI分析
            # 6. notification -> 输出

        def run_weekly_report():
            # 周度报告:
            # 1-3 同上
            # 4. report_engine -> WeeklyReport
            # 5. ai_engine -> AI分析
            # 6. notification -> 输出

        def run_continuous():
            # 定时调度:
            # - 每日 check_time 运行 run_check
            # - 每周五 report_time 运行 run_weekly_report

## 数据流

    config.yaml ----+
                    |
    config.asset.yaml --+--> AntiFOMO (main.py)
                              |
                    +---------+---------+
                    |                   |
                    v                   v
          portfolio_engine        market_engine
            |                       |
            v                       v
       PortfolioStatus          MarketStatus
            |                       |
            +-----------+-----------+
                        |
                        v
                 decision_engine
                        |
                        v
                    Decision
                        |
            +-----------+-----------+
            |           |           |
            v           v           v
      report_engine  ai_engine  notification
            |           |
            v           v
        Report       AI Analysis
            |           |
            +-----+-----+
                  |
                  v
            notification
                  |
                  v
        console / file / email

## 配置文件扩展

config.yaml 新增以下 section (与现有配置并列):

    # === 新增: 市场估值配置 ===
    market_engine:
      enabled: true
      indices:
        - symbol: "沪深300"
          code: "000300"
          weight: 0.5
        - symbol: "中证500"
          code: "000905"
          weight: 0.3
        - symbol: "上证50"
          code: "000016"
          weight: 0.2
      percentile_window_years: 10    # 百分位计算窗口 (年)
      thresholds:
        cheap: 20                    # < 20 为便宜
        expensive: 80                # > 80 为过热

    # === 新增: 决策引擎配置 ===
    decision_engine:
      enabled: true
      check_market_volatility: true  # 是否结合资产波动判断
      rebalance_threshold: 5.0       # 再平衡偏离阈值 (%)

    # === 新增: 报告配置 ===
    report:
      weekly:
        enabled: true
        day: "friday"                # 周几生成
        time: "16:00"                # 生成时间
        include_ai: true             # 是否包含 AI 分析

    # === 新增: 缓存配置 ===
    cache:
      enabled: true
      dir: "cache/"
      ttl_hours: 24                  # 缓存有效期

config.asset.yaml 不变 -- 继续由 serve.py 生成, 仅存储持仓数据.

## Import 路径处理

v0 通过 run.py 将 src/ 加入 sys.path, 使用裸模块名导入 (如 from portfolio import Portfolio).

v1 重构为子包后, 有两种可选方案:

方案 A (推荐): 保持 sys.path 插入 src/, 子包内部使用相对导入.

    # src/portfolio_engine/__init__.py
    from .portfolio import Portfolio, Holding
    from .data_fetcher import DataFetcher

    # src/main.py
    from portfolio_engine import Portfolio, DataFetcher
    from market_engine import MarketScorer, MarketStatus

方案 B: 使用标准包结构, 从项目根目录 import.

    from src.portfolio_engine import Portfolio

方案 A 改动更小, 且与 v0 的 sys.path 策略一致, 推荐采用.

## 重构执行步骤

阶段一: 结构重组 (不改功能)
1. 创建子包目录结构 (portfolio_engine/, market_engine/ 等)
2. 将 v0 文件移入对应子包, 调整 import
3. 更新 main.py 的 import 路径
4. 验证: python run.py 和 python serve.py 功能不变

阶段二: 新增 market_engine
1. 实现 valuation_fetcher.py (akshare PE/PB 获取)
2. 实现 percentile.py (百分位计算)
3. 实现 market_scorer.py (评分和状态判断)
4. 实现 cache.py (数据缓存)
5. 扩展 config.yaml
6. 验证: 能独立输出三大指数的市场状态

阶段三: 新增 decision_engine
1. 实现 pace_controller.py (看盘/忽略判断)
2. 实现 rebalance_checker.py (再平衡检测)
3. 集成到 main.py 的 run_check 流程
4. 验证: run.py 输出包含行为建议

阶段四: 新增 report_engine
1. 实现 daily_digest.py (日度简报)
2. 实现 weekly_report.py (周度报告)
3. 扩展 main.py 的调度逻辑
4. 验证: 周五定时生成完整周报

阶段五: AI 集成 + 通知扩展
1. 重组 ai_analyzer -> ai_engine
2. 扩展 prompt 模板, 包含市场估值信息
3. 调整 notification 输入接口
4. 端到端测试

## 扩展预留 (P1 接口)

以下目录/接口在 MVP 中不实现, 但在设计中预留:

    src/macro_engine/           # P1: 宏观环境分析
        __init__.py
        macro_fetcher.py        # 宏观指标获取
        risk_scorer.py          # 风险等级评分

decision_engine.decide() 的签名预留 macro_status 参数:

    def decide(portfolio_status, market_status,
               macro_status=None) -> Decision:

report_engine 预留月报/季报模板:

    src/report_engine/
        monthly_report.py       # P1
        quarterly_review.py     # P1

Web UI 预留仪表盘路由:

    serve.py:
        GET /api/market-status  # P1: 返回市场状态 JSON
        GET /dashboard          # P1: 市场状态仪表盘页面

## 新增依赖

无. 所有新功能仅依赖 akshare (已有) 和 Python 标准库.
缓存使用 JSON + pickle, 不引入 Redis/SQLite 等外部存储.
