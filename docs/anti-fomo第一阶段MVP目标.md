你目前的 Anti-FOMO v0 是一个**个股/组合波动监控工具**，核心功能是波动提醒 + AI 情绪安抚，属于“事后反应型”工具。而你现在想转向的是一个**低频、宏观导向的投资环境导航系统**，强调“事前判断、减少决策、透明依据”[1]。

两者在目标、节奏、数据维度和输出形式上存在本质差异。直接在现有架构上堆叠新功能，确实会导致结构混乱。你需要一次有目的的重构 —— 不是为了重写代码，而是为了**预留扩展路径**，让 MVP 能平滑演进到完整产品。

---

## ✅ 重构核心原则（来自你的需求共识）[1]

1. **极度收缩 MVP**：初期只聚焦 **1 个指数**（如沪深300），不碰个股组合。
2. **不是投顾，是环境判断器**：输出“当前状态 / 是否行动 / 为什么”，而非买卖建议。
3. **分层架构清晰**：数据 → 信号 → 决策 → 输出，各层职责分离。
4. **低频输出节奏**：周报、月报、季报、年报，避免日级干扰。
5. **可解释性优先**：用户必须能看懂系统为什么给出这个判断。

---

## 🧱 推荐重构后的项目结构

```
anti-fomo/
├── core/                     # 核心逻辑层（与 UI / 调度解耦）
│   ├── data_layer/           # 数据获取与缓存
│   │   ├── market_fetcher.py     # 获取PE/PB等估值数据
│   │   ├── macro_fetcher.py      # 获取宏观政策/统计
│   │   └── data_cache.py         # 本地缓存机制（避免重复请求）
│   │
│   ├── signal_layer/         # 状态判断引擎
│   │   ├── valuation_analyzer.py # 估值百分位判断
│   │   ├── macro_analyzer.py     # 宏观环境打分
│   │   └── event_detector.py     # 重大事件识别（可选）
│   │
│   ├── decision_layer/       # 行动建议生成
│   │   ├── action_advisor.py     # 是否需要调仓/再平衡
│   │   └── rationale_builder.py  # 生成“为什么”的解释文本
│   │
│   └── report_generator.py   # 报告模板引擎（支持周/月/季/年）
│
├── config/
│   ├── system.yaml           # 系统参数（阈值、频率、指数选择）
│   ├── macro_sources.yaml    # 宏观数据源配置
│   └── report_templates/     # 各周期报告模板（Markdown/HTML）
│
├── scheduler/                # 低频调度器（非每日！）
│   ├── weekly_scheduler.py
│   ├── monthly_scheduler.py
│   └── on_event_trigger.py   # 重大事件时手动/自动触发
│
├── output/
│   ├── console.py            # 控制台输出
│   ├── email_sender.py       # 邮件推送
│   └── file_exporter.py      # 保存为 PDF/Markdown
│
├── web/                      # （可选）轻量 Web 查看器
│   └── status_dashboard/     # 展示当前环境状态 + 历史报告
│
├── docs/
│   └── architecture.md       # 记录架构设计与演进思路
│
└── main.py                   # 入口：支持 run / schedule / init
```

---

## 🔄 如何从 v0 平滑过渡？

1. **保留但隔离旧模块**  
   将 `src/` 下的旧文件（如 `portfolio.py`, `volatility_calculator.py`）移入 `legacy/` 目录，标记为“v0 功能，暂不维护”。这样不影响新架构，也保留回退能力。

2. **新增 `core/` 作为新大脑**  
   所有新功能围绕“环境判断”展开，不碰个股波动计算。

3. **配置文件拆分**  
   将 `config.yaml` 拆分为：
   - `system.yaml`：控制运行逻辑（用哪个指数、报告频率）
   - `macro_sources.yaml`：配置商务部/国务院等数据源 URL 或 API
   - 保留 `config.asset.yaml` 仅用于 legacy 模块

4. **调度器重写**  
   放弃 `schedule` 库的日级调度，改用 `weekly_scheduler.py` 等按需触发，符合“低频”原则。

5. **输出层抽象化**  
   报告内容由 `report_generator.py` 生成标准结构，再由 `output/` 中不同模块渲染成邮件/文件/Web，便于未来扩展渠道。

---

## 🚀 MVP 第一阶段开发建议

1. 实现 `data_layer/market_fetcher.py` → 只拉取 **沪深300 的 PE/PB 百分位**
2. 实现 `signal_layer/valuation_analyzer.py` → 判断当前处于“低估 / 中性 / 高估”
3. 实现 `decision_layer/action_advisor.py` → 输出“无需操作 / 可考虑定投 / 建议再平衡”
4. 实现 `report_generator.py` → 生成周报 Markdown
5. 实现 `scheduler/weekly_scheduler.py` → 每周五收盘后运行

> ✅ 这样你就有了一个最小闭环：**每周告诉用户“现在市场贵不贵，要不要动”** —— 完全符合你“降低焦虑、避免频繁决策”的初衷 [1]。

---

## 📌 后续扩展路径（Roadmap）

```
v1: 单指数环境判断（沪深300）→ 已重构架构支持
v2: 加入宏观政策解读（五年规划匹配度）
v3: 支持多指数（中证500、恒生等）
v4: 增量资金配置建议（月薪如何投）
v5: 季度再平衡提醒 + 年度安全检查
```

你现在做的重构，就是在为这条路径铺路 —— **让每一步扩展都只需要加模块，而不是改架构**。