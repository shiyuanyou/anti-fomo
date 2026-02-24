# Anti-FOMO v2 开发 Wiki

> 本文档是 v2 的开发记忆，供 AI agent 和开发者在 v2 迭代期间快速定位目标、边界约定和分阶段任务。
> v1 的历史实现状态见 `docs/v1-dev-wiki.md`。

---

## 战略背景

v1 的重心在后端监控管道（波动率计算、市场估值、AI 建议、每日调度）。
用户研究发现，更根本的问题是：**大多数用户缺乏对自身资产配置的全局认知**，
在看清自己持有什么之前，任何波动提醒或 AI 建议都缺乏认知基础。

v2 的核心转向：

> **Anti-FOMO 是一个"认知启蒙型工具"，而非"智能投顾"或"交易辅助系统"。**
> 让用户在不看盘的情况下，依然能清晰知道"我的钱在哪里、为什么在那里、是否合理"。

v2 的主战场：**`serve.py` + `web/`** — Web 配置 UI 的全面升级。
v1 后端引擎（`run.py` 管道）保持可用，暂不扩展。

---

## v2 功能范围

### 已确定要做（MVP + 迭代一）

#### F1 — 配置模板库（Templates）

提供 4-6 个经典资产配置模板，以不同指数基金 + 债基 + 商品基金 + 货币基金的不同比例
体现不同投资思路。每个模板需包含：

- 名称与一句话定位（目标人群、风险偏好）
- 资产类别权重分布（可用饼图/条形图展示）
- 量化指标（见 F2）
- 性格标签（见 F3）

候选模板方向（最终数量/内容可在开发时调整）：

| 模板名 | 思路 | 大致比例方向 |
|--------|------|-------------|
| 全球均衡型 | 本外均配，股债平衡 | 全球股票 60% + 债券 40% |
| A股核心型 | 本国优先，A股大比重 | 沪深300+中证500 70%+，少量海外+债 |
| 全天候防御型 | 风险平价，多资产对冲 | 股+债+商品+黄金均衡分散 |
| 成长进取型 | 高风险高预期，偏科技/新兴 | 科技+新兴市场 80%+ |
| 无国界对冲型 | 全球充分对冲，弱化本国偏好 | 全球多区域+多资产类别均衡 |
| 现金稳健型 | 保守，流动性优先 | 货币基金+短债 80%+ |

模板数据以静态 JSON 形式内置在前端或通过 `serve.py` 的 `/api/templates` 接口提供。

#### F2 — 模板量化指标展示

每个模板展示以下指标，用于横向对比和用户决策参考。
数据来源优先使用历史模拟回测（静态预计算），不依赖实时接口。

| 指标 | 说明 |
|------|------|
| 预计年化收益率 | 历史回测均值，标注时间段 |
| 内涵波动率 | 历史年化波动率 |
| 最大回撤率 | 历史最大回撤 |
| 夏普比率 | (年化收益 - 无风险利率) / 波动率 |

数据精度：近似值即可，用于认知对比，不作为精确投资建议。

#### F3 — 模板性格分析（AI 辅助）

每个模板附带"性格画像"，帮助用户找到与自身认知和风险偏好匹配的模板。
示例维度：

- 本国优先 vs. 无国界思维
- 接受大幅波动 vs. 追求平稳
- 相信长期成长 vs. 偏好防御
- 是否认可黄金/商品作为对冲工具

实现方式：
- 静态文案 + AI 辅助生成描述（`ai_engine` 扩展，或独立的 `template_engine`）
- 可选：用户完成简短问卷，AI 匹配推荐模板

#### F4 — 配置对比（用户配置 vs. 模板 1v1）

用户当前配置（来自 `config.asset.yaml`）与选定模板进行一对一可视化对比：

- 雷达图 / 条形图：用户配置 vs. 模板目标权重
- 偏离度标注（如"科技股超配 40%"、"缺少海外分散"）
- 关键指标对比表（年化、波动率、最大回撤、夏普比）

#### F5 — 资产配置迁移方案建议（AI）

在对比结果的基础上，调用 AI 生成迁移建议：
- "如果你想向 X 模板靠拢，可以考虑……"
- 不给出买卖指令，只提供方向性思路
- 接口：新增 `ai_engine` 方法 `suggest_migration(user_config, template) -> str`

### 列为 TODO（后续迭代）

- **F6 — 多配置多模板横向对比**：支持用户保存多套配置，批量与多个模板对比
- **F7 — 知识库 + AI 对话**：将所有模板+用户配置作为上下文知识库，支持自然语言问答和 Deep Research 风格的深度分析

---

## v2 架构变化

### 主要新增模块

```
serve.py（扩展）
  |- GET  /api/templates            # 返回模板列表（含指标和性格标签）
  |- GET  /api/templates/{id}       # 单个模板详情
  |- POST /api/compare              # 用户配置 vs. 模板，返回对比数据
  |- POST /api/ai/profile-match     # AI 性格匹配（可选）
  |- POST /api/ai/migrate           # AI 迁移建议

src/template_engine/（新建）
  templates.py        # TemplateLibrary, PortfolioTemplate dataclass
  comparator.py       # TemplateComparator (用户配置 vs. 模板，计算偏离度)
  metrics.py          # 指标计算：年化/波动率/最大回撤/夏普比（静态数据）

src/ai_engine/（扩展）
  analyzer.py         # 现有接口不动
  template_advisor.py # 新增：性格匹配 + 迁移建议

web/（大幅扩展）
  index.html          # 重构布局，增加模板库、对比视图
  templates.js        # 模板展示组件
  compare.js          # 对比可视化
  charts.js           # 雷达图/条形图/饼图（使用 Chart.js 或轻量替代）
```

### v1 后端保持不变

`run.py`、`src/main.py`、`portfolio_engine`、`market_engine`、`decision_engine`、
`report_engine`、`notification` — 暂不修改。

---

## 数据结构约定（v2 新增）

```python
# src/template_engine/templates.py

@dataclass
class AssetAllocation:
    category: str          # 资产类别，如 "A股大盘" / "美股科技" / "债券" / "黄金"
    region: str            # 地区，如 "中国" / "全球" / "美国"
    weight: float          # 0-1

@dataclass
class TemplateMetrics:
    annualized_return: float       # 预计年化收益率 (%)
    annualized_volatility: float   # 年化波动率 (%)
    max_drawdown: float            # 最大回撤 (%, 负数)
    sharpe_ratio: float            # 夏普比率
    data_period: str               # 数据区间说明，如 "2010-2024 历史模拟"

@dataclass
class PortfolioTemplate:
    id: str                        # 唯一标识，如 "global_balanced"
    name: str                      # 展示名称
    tagline: str                   # 一句话定位
    target_audience: str           # 目标人群描述
    risk_level: str                # "低" / "中" / "中高" / "高"
    allocations: List[AssetAllocation]
    metrics: TemplateMetrics
    personality_tags: List[str]    # 性格标签，如 ["本国优先", "接受大幅波动"]
    personality_description: str   # 性格画像文字描述
```

```python
# src/template_engine/comparator.py

@dataclass
class AllocationDiff:
    category: str
    user_weight: float             # 用户当前权重
    template_weight: float         # 模板目标权重
    deviation: float               # user - template，正=超配，负=低配

@dataclass
class ComparisonResult:
    user_config_name: str
    template: PortfolioTemplate
    diffs: List[AllocationDiff]
    user_metrics: TemplateMetrics  # 用用户配置估算的指标（近似）
    summary: str                   # 文字摘要，如 "整体偏A股集中，缺少海外分散"
```

---

## 前端技术约定（v2）

- 延续 `web/` 的零构建工具原则（vanilla HTML/CSS/JS）
- 图表库：优先使用 **Chart.js**（CDN 引入），满足饼图、雷达图、条形图需求
- 不引入 React/Vue 等框架
- 新增 JS 文件按功能拆分（`templates.js`, `compare.js`, `charts.js`）
- API 调用统一走 `fetch`，不引入 axios

---

## 开发顺序建议

1. **后端模板数据层**：定义 `PortfolioTemplate` 数据结构，内置 4-6 个模板的静态数据（含量化指标）
2. **`/api/templates` 接口**：`serve.py` 提供模板列表和详情 API
3. **前端模板库视图**：展示模板卡片、指标、性格标签
4. **对比引擎**：`TemplateComparator` 计算偏离度，`/api/compare` 接口
5. **前端对比可视化**：雷达图/条形图对比展示
6. **AI 性格匹配**：`template_advisor.py`，`/api/ai/profile-match`
7. **AI 迁移建议**：`suggest_migration()`，`/api/ai/migrate`
8. （后续）多配置对比、知识库对话

---

## 已知约束与注意事项

- 量化指标（年化收益、夏普比等）数据精度为近似值，明确标注数据来源和时间段，避免误导用户
- AI 接口仍使用 OpenAI 兼容 SDK，key 走环境变量，不硬编码
- 模板数据初始版本可以硬编码为静态 JSON；后续可迁移到独立数据文件或数据库
- `config.asset.yaml` 结构不变，`TemplateComparator` 读取其中的 `portfolio.holdings` 进行对比
- v1 后端不受 v2 开发影响，`run.py` 管道继续可用

---

## 运行验证

```bash
python3 serve.py          # 开启 Web UI，验证模板库和对比功能
python3 run.py            # v1 日度检查，确认未被 v2 改动破坏
```
