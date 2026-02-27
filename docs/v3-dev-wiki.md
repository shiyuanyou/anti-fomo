# Anti-FOMO v3 开发 Wiki

> 本文档是 v3 的开发记忆，供 AI agent 和开发者在 v3 迭代期间快速定位目标、边界约定和分阶段任务。
> v1 历史实现见 `docs/v1-dev-wiki.md`，v2 历史实现见 `docs/v2-dev-wiki.md`。

---

## 战略背景

v1 建立了后端监控管道（波动率、市场估值、AI 建议、调度）。
v2 将产品重心转向"认知启蒙型配置工具"，实现了模板库、1v1 对比可视化、AI 迁移建议（F1–F5）。

v2 遗留的核心问题：

> **模板指标数据不可信。** 6 个模板的年化收益、最大回撤、波动率、夏普比率全部是手工填写的经验估算值。
> `comparator.py` 的用户指标估算同样依赖手工系数字典（`_CATEGORY_RETURN` / `_CATEGORY_VOL`）。

这个问题在当前 F1–F5 的"认知对比"场景下已造成可信度缺失，并且是后续扩展（DIY 模板、多模板对比、用户权重微调）的根本障碍：

- DIY 模板：用户调整权重后需要看到实时重算的真实指标
- 多模板对比：指标不可信则横向对比无意义
- 用户配置估算：`comparator.py` 的线性加权近似误差过大

v3 的核心目标：

> **用 akshare 拉取各类资产代理指数的真实历史行情，建立本地金融数据层，
> 用真实数据计算并替换模板硬编码指标，同时使用户配置的指标估算变得可信。**

v3 不是"建数据库"，是"让现有指标数字说真话"。

---

## v3 功能范围

### 已确定要做（MVP）

#### D1 — 资产类别代理指数映射表

为 `templates.py` 和 `comparator.py` 中出现的每个资产类别，确定一个 akshare 可拉取的代理指数，
形成静态映射表。

| 资产类别 | 代理指数 | akshare 接口 | 代码 |
|---------|---------|-------------|------|
| A股大盘 | 沪深300 | `index_zh_a_hist` | `000300` |
| A股中盘 | 中证500 | `index_zh_a_hist` | `000905` |
| A股小盘 | 中证1000 | `index_zh_a_hist` | `000852` |
| A股成长 | 创业板指 | `index_zh_a_hist` | `399006` |
| 港股 | 恒生指数 | `stock_hk_index_daily_sina` | `HSI` |
| 港股科技 | 恒生科技 | `stock_hk_index_daily_sina` | `HSTECH` |
| 美股大盘 | 标普500 | `index_us_stock_sina` | `.INX` |
| 美股科技 | 纳斯达克100 | `index_us_stock_sina` | `.NDX` |
| 欧洲股票 | 欧洲斯托克50 | `index_global_hist_em` | `欧洲斯托克50` |
| 日本股票 | 日经225 | `index_global_hist_em` | `日经225` |
| 新兴市场股票 | MSCI新兴市场 | `index_global_hist_em` | `MSCI新兴市场` |
| 发达市场股票 | MSCI世界 | `index_global_hist_em` | `MSCI全球` |
| 债券（中国） | 中证全债 | `index_zh_a_hist` | `000012` |
| 短期债券 | 固定年化 2.5%（常数，无指数） | — | — |
| 黄金 | 沪金期货主力 / AU9999 | `futures_zh_spot` / `spot_hist_sge` | — |
| 大宗商品 | 南华商品指数 | `index_zh_a_hist` | `000978` |
| 货币基金 | 固定年化 2.0%（常数，无指数） | — | — |

注：
- `index_global_hist_em` 返回列名 `最新价` 而非 `收盘`，需特殊处理。
- `短期债券` 和 `货币基金` 无对应指数，用固定常数模拟（年化收益固定，波动率=0，回撤=0）。
- 黄金接口待验证，优先尝试 `spot_hist_sge`（上海黄金交易所 AU9999），备用 `futures_zh_spot`。

#### D2 — 历史行情拉取脚本

新建 `scripts/fetch_index_data.py`：

- 拉取 D1 映射表中所有可用指数，时间范围 **2010-01-01 至今**
- 统一输出为**周度 OHLC 数据**（周五收盘价聚合，开/高/低/收）
- 存储至 `base_datas/index_weekly.csv`，列格式：`date, index_code, open, high, low, close`
- 对每个接口做 try/except，拉取失败时打印警告、跳过，不中断整体流程
- 本地已有数据时，支持增量更新（只拉取 max(date)+1 至今）

#### D3 — 模板指标计算脚本

新建 `scripts/calc_template_metrics.py`：

- 读取 `base_datas/index_weekly.csv`
- 对每个模板，按其 `allocations` 权重加权各代理指数的周度收益率，合成组合收益率序列
- 计算以下指标（2010-01-01 至数据截止日）：
  - 年化收益率（几何平均）
  - 年化波动率（周度收益率标准差 × √52）
  - 最大回撤（基于净值曲线）
  - 夏普比率（年化收益 - 2.0% 无风险利率）/ 年化波动率
- 输出 `base_datas/template_metrics.json`，结构：
  ```json
  {
    "calculated_at": "2025-XX-XX",
    "data_period": "2010-01-01 至 2025-XX-XX",
    "templates": {
      "global_balanced": {
        "annualized_return": 7.4,
        "annualized_volatility": 9.8,
        "max_drawdown": -19.3,
        "sharpe_ratio": 0.55
      },
      ...
    }
  }
  ```
- 同时更新 `comparator.py` 的 `_CATEGORY_RETURN` / `_CATEGORY_VOL` 字典（用单一指数的真实数据替换手工系数）

#### D4 — 模板数据层接入真实指标

修改 `src/template_engine/templates.py`：

- 启动时尝试从 `base_datas/template_metrics.json` 加载指标，覆盖硬编码值
- 若文件不存在，退回硬编码值（保持向后兼容，打印一次警告）
- `data_period` 字段从文件中读取（如 `"2010-2024 真实历史数据"`），不再写死

修改 `src/template_engine/comparator.py`：

- `_CATEGORY_RETURN` / `_CATEGORY_VOL` 字典改为从 `base_datas/index_metrics.json` 加载（由 D3 脚本生成）
- 文件不存在时退回现有硬编码字典

#### D5 — 数据有效性标注

前端展示层更新（`web/templates.js`、`web/compare.js`）：

- 模板指标卡片增加数据来源标注：真实数据显示 `"2010-XXXX 真实历史回测"`，经验值显示 `"经验估算"`
- 无需改动后端 API 结构，`data_period` 字段已承载这个信息

### 列为 TODO（后续迭代）

- **F6 — DIY 模板**：用户自定义权重，实时调用 D3 的计算逻辑重算指标，展示真实历史模拟结果
- **F7 — 多模板横向对比**：多个模板的指标并排展示，依赖 D3 的可信数据
- **F8 — 用户配置历史回测**：用用户实际持仓权重 × 代理指数历史数据，生成个人组合的真实历史净值曲线

---

## v3 架构变化

### 新增文件

```
scripts/
  fetch_index_data.py      # D2: akshare 拉取各代理指数历史行情，输出周度 OHLC CSV
  calc_template_metrics.py # D3: 读取 CSV，计算模板加权组合指标，输出 JSON

base_datas/
  index_weekly.csv         # 各代理指数周度 OHLC 数据（由 D2 生成）
  template_metrics.json    # 6个模板的真实计算指标（由 D3 生成）
  index_metrics.json       # 各资产类别单一指数指标（由 D3 生成，供 comparator 使用）
```

### 修改文件

```
src/template_engine/templates.py    # D4: 启动时加载 template_metrics.json
src/template_engine/comparator.py   # D4: 加载 index_metrics.json 替换手工系数
web/templates.js                    # D5: 数据来源标注
web/compare.js                      # D5: 数据来源标注
```

### 不修改的文件

v1 后端全部文件（`run.py`、`src/main.py`、`portfolio_engine`、`market_engine`、
`decision_engine`、`report_engine`、`notification`、`src/ai_engine/analyzer.py`）。

`serve.py` 的 API 结构不变（`TemplateMetrics` 的 JSON 输出结构不变）。

---

## 数据流

```
akshare
  |
  v
scripts/fetch_index_data.py
  |-- base_datas/index_weekly.csv
  |
  v
scripts/calc_template_metrics.py
  |-- base_datas/template_metrics.json   --> src/template_engine/templates.py
  |-- base_datas/index_metrics.json      --> src/template_engine/comparator.py
```

脚本运行是**离线、按需**的，不在 `serve.py` 或 `run.py` 启动时自动触发。
运行一次后结果持久化在 `base_datas/`，应用读取文件即可。

---

## 关键设计决策

### 为什么不用 aktools

aktools 是面向多语言/多服务的 HTTP 部署方案。本项目是单机 Python 应用，
直接 `import akshare` 即可，引入 aktools 只增加运维复杂度，无收益。

### 为什么选周度而非日度

- 日度数据量大（15年 × 17个指数 × 250交易日 ≈ 63,000行），拉取时间长
- 模板指标（年化收益、最大回撤、夏普）用周度数据计算与日度结果差异在 1% 以内
- 周度数据拉取和计算均在秒级完成，适合脚本离线运行

### 为什么保留硬编码作为 fallback

`base_datas/` 文件由脚本生成，新用户 clone 仓库后不存在这些文件。
保留硬编码 fallback 确保 `python3 serve.py` 在任何环境下都能正常启动，
不因缺少数据文件而报错。

### 短期债券和货币基金的处理

这两类资产无法用指数代理（货币基金净值平滑，没有公开指数序列）。
用固定常数（货币基金 2.0%，短期债券 2.5%）模拟，误差极小，且在所有模板中权重较低。
计算时直接在合成组合收益率中加入该比例的固定日收益。

### 数据校验方式

SBBI-China-2024 PDF 数据作为**人工校验参照**，不进入代码。
计算结果生成后，与 PDF 中对应资产类别的长期历史数字做目测比对。
如差异超过合理范围（如 A 股年化收益差异 > 3%），排查代理指数选择是否合适。

---

## 开发顺序

1. **D2 脚本**：先验证各 akshare 接口可用性，逐一拉取代理指数数据，写入 CSV
2. **D3 脚本**：读取 CSV，计算加权组合指标，写入 JSON；命令行打印结果供人工校验
3. **D4 接入**：修改 `templates.py` 和 `comparator.py` 加载 JSON
4. **D5 标注**：前端 `data_period` 标注更新，区分真实数据和经验估算

---

## 已知约束与注意事项

- `index_global_hist_em` 返回列名 `最新价` 而非 `收盘`，合并时需重命名
- akshare 部分境外接口（港股、美股）有时返回数据不完整或时区不对齐，需在 D2 中做对齐处理
- `000852`（中证1000）上市于 2014 年，2010-2014 区间无数据；缺失区间用 `000905`（中证500）近似填充
- 计算最大回撤时基于**周度净值序列**而非日度，极端回撤可能被低估约 5-10%，在 `data_period` 备注中说明
- `base_datas/` 目录加入 `.gitignore`（生成文件不纳入版本控制），但 `scripts/` 纳入版本控制

---

## 运行方式

```bash
# 1. 拉取历史行情（首次约 2-5 分钟，增量更新约 30 秒）
python3 scripts/fetch_index_data.py

# 2. 计算模板指标（约 5 秒）
python3 scripts/calc_template_metrics.py

# 3. 启动 Web UI，验证模板指标已更新
python3 serve.py

# 4. 确认 v1 未受影响
python3 run.py
```

---

## 技术债（v3 新增）

| 位置 | 问题 | 优先级 |
|------|------|--------|
| `base_datas/index_weekly.csv` | 港股、美股数据时区不对齐，周度聚合可能差一天 | 中 |
| `comparator.py:_estimate_user_metrics` | 当前线性加权忽略相关性，v3 D4 后用真实指数数据改善，但仍是近似 | 低 |
| `scripts/fetch_index_data.py` | 境外指数接口稳定性未经长期验证，需监控 | 中 |
| `000852` 中证1000 | 2010-2014 用中证500近似填充，影响小盘相关模板指标精度 | 低 |
