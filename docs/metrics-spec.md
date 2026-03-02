# anti-fomo 指数指标口径规范（V1/V2）

## 1. 文档目标

统一指数分析口径，确保：

- 后端计算一致
- 前端展示一致
- 云端版与本地版结果一致

本规范优先服务 `P0 数据预处理`、`指数展示页`、`模板对比`。

---

## 2. 数据对象与字段口径

## 2.1 指数基础信息

每个指数必须具备：

- `name`：指数名称
- `code`：指数代码
- `category`：类型（宽基/行业/主题/海外等）
- `region`：区域（中国/美国/欧洲/日本/其他）
- `style`：风格（价值/成长/红利/均衡/其他）

## 2.2 时间序列数据

主序列（必需）：

- 指数价值（价格指数）OHLC：`open`, `high`, `low`, `close`

扩展序列（可选）：

- 全收益指数 OHLC：`tr_open`, `tr_high`, `tr_low`, `tr_close`

时间粒度：

- 原始数据按日存储；聚合输出至少支持周、月、季、年

---

## 3. 聚合规则（OHLC）

设某周期内日线集合为 $D$：

- 周期开盘：首个交易日 `open`
- 周期收盘：最后一个交易日 `close`
- 周期最高：周期内 `high` 最大值
- 周期最低：周期内 `low` 最小值

适用到价格指数与全收益指数。

---

## 4. 收益与风险指标定义

## 4.1 周期收益率

对任意周期 $t$：

$$
r_t = \frac{close_t}{close_{t-1}} - 1
$$

## 4.2 综合年化收益（CAGR）

设起止净值分别为 $V_0, V_T$，总年数为 $Y$：

$$
\text{CAGR} = \left(\frac{V_T}{V_0}\right)^{\frac{1}{Y}} - 1
$$

说明：

- $Y$ 按交易日折算（例如交易日数 / 252）
- 周/月/季频统计时用相应频率折算年数

## 4.3 最大年化（滚动）

定义：在固定窗口（建议 1 年窗口）上滚动计算年化收益，取最大值。

窗口收益：

$$
r_{win} = \frac{V_{t+w}}{V_t} - 1
$$

窗口年化：

$$
r_{ann} = (1+r_{win})^{\frac{1}{Y_w}} - 1
$$

其中 $Y_w$ 为窗口对应年数。

## 4.4 最大涨幅（分周/月/季/年）

在指定频率序列中，计算每个周期收益率，取最大值：

$$
\max\{r_t\}
$$

## 4.5 最大回撤（分周/月/季/年）

设净值序列为 $V_t$，历史高点为 $P_t = \max(V_0,\dots,V_t)$：

$$
DD_t = \frac{V_t - P_t}{P_t}
$$

最大回撤：

$$
MDD = \min\{DD_t\}
$$

---

## 5. 连续状态时长口径（周频）

用于“最长连续增长/震荡/下跌”分析。

以周收益率 $r_t$ 为基础，设置阈值 $\epsilon = 0.5\%$（可配置）：

- 增长周：$r_t > \epsilon$
- 下跌周：$r_t < -\epsilon$
- 震荡周：$|r_t| \le \epsilon$

### 5.1 最长连续时长（最大）

- 对三种状态分别计算最长连续周数
- 同时记录起始周、结束周

### 5.2 平均连续时长

- 对每种状态的所有连续片段，计算长度平均值

---

## 6. 缺失数据与异常处理

1. 周期缺失：
   - 若某周期无交易数据，不生成该周期点
2. 单点异常：
   - 若出现非正价格（`<=0`），该点记为异常并剔除
3. 序列起点不足：
   - 年化、滚动窗口指标若样本不足，返回 `null`
4. 全收益缺失：
   - 允许仅展示价格指数；前端标记“全收益数据暂缺”

---

## 7. 输出字段建议（API）

示例结构（建议，不强制）：

- `annualized_return`
- `max_annualized_return`
- `max_gain_weekly`, `max_gain_monthly`, `max_gain_quarterly`, `max_gain_yearly`
- `max_drawdown_weekly`, `max_drawdown_monthly`, `max_drawdown_quarterly`, `max_drawdown_yearly`
- `streak_longest_up`, `streak_longest_flat`, `streak_longest_down`
- `streak_avg_up`, `streak_avg_flat`, `streak_avg_down`

其中 `streak_longest_*` 建议包含：

- `length_weeks`
- `start_date`
- `end_date`

---

## 8. 版本管理

- 当前版本：`metrics-spec v1.0`
- 生效范围：V1 首页/指数页/模板对比基础统计，V2 本地增强统计
- 变更原则：任何指标口径变更都需更新本文件并记录兼容说明
