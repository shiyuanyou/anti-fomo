# 快速开始指南

## 1. 安装依赖

```bash
pip install -r requirements.txt
```

## 2. 配置您的投资组合

编辑 `config.yaml` 中的 `portfolio` 部分：

```yaml
portfolio:
  holdings:
    - symbol: "000510"  # 修改为您持有的指数/股票代码
      name: "中证A500"   # 修改为名称
      type: "index"      # index 或 stock
      allocation_type: "amount"  # amount(金额) 或 ratio(比例)
      value: 50000       # 填入金额或比例
```

### 常见指数代码

- 000510: 中证A500
- 930050: 中证A50
- 932000: 中证2000
- 000300: 沪深300
- 000001: 上证指数
- 000688: 科创50

## 3. 调整波动阈值（可选）

根据您的风险偏好调整：

```yaml
thresholds:
  portfolio_volatility:
    warning: 3.0   # 降低此值会更敏感
    alert: 5.0
```

## 4. 运行测试

```bash
python run.py
```

第一次运行会：
- 下载市场数据
- 计算波动率
- 输出报告到控制台

## 5. 启用 AI 分析（可选）

如果您有 OpenAI API Key：

1. 在 `config.yaml` 中配置：
```yaml
ai_analysis:
  enabled: true
  api_key: "sk-..."  # 填入您的 API Key
```

2. 重新运行即可看到 AI 分析建议

## 6. 设置定时任务

```bash
# 每天自动运行
python run.py schedule
```

程序会在每天 15:30（可在配置中修改）自动检查并生成报告。

## 常见问题

### Q: 报错 "获取数据失败"
A: 检查网络连接，akshare 需要访问外部数据源

### Q: 如何添加个股？
A: 在 config.yaml 中添加：
```yaml
- symbol: "600519"  # 股票代码
  name: "贵州茅台"
  type: "stock"     # 注意这里是 stock
  allocation_type: "amount"
  value: 100000
```

### Q: 波动率为 0？
A: 可能是数据不足，默认需要至少 2 天的数据

### Q: 想要周报而非日报？
A: 修改 config.yaml 中的 `period: "weekly"`

## 下一步

- 查看 `README.md` 了解完整功能
- 查看 `EXAMPLES.md` 了解更多配置示例
- 检查 `logs/alerts.log` 查看历史记录
