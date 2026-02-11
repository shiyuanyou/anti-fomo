# Anti-FOMO - 股票组合波动监控工具

帮助投资者对抗 FOMO（Fear Of Missing Out）情绪的智能股票组合监控工具。

## 功能特性

- **Web 资产配置** — 通过浏览器可视化配置持仓，生成 `config.asset.yaml`
- **智能波动监控** — 计算组合和个股波动率，双层阈值（警告/警报）自动判定
- **AI 分析** — 可选接入 OpenAI 兼容 API，提供理性投资建议
- **多渠道通知** — 控制台、文件日志、邮件（可配置）
- **自动化调度** — 每日收盘后定时检查，支持跳过周末和节假日

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 配置资产（Web UI）

```bash
python serve.py
```

打开 `http://localhost:8080`，在界面中添加持仓并保存。这会生成 `config.asset.yaml`，
作为持仓的唯一数据来源。

### 2. 运行波动检查

```bash
python run.py            # 单次检查
python run.py schedule   # 每日定时检查（默认 15:30）
```

## 配置说明

项目使用两个配置文件：

| 文件 | 用途 | 编辑方式 |
|------|------|----------|
| `config.yaml` | 运营配置（阈值、AI、通知、调度） | 手动编辑 |
| `config.asset.yaml` | 持仓配置（股票名称、代码、比例） | 通过 `serve.py` Web UI 生成 |

`config.yaml` **不包含** 持仓数据。所有股票名称、代码、比例均来自 `config.asset.yaml`。

### 波动阈值

```yaml
thresholds:
  portfolio_volatility:
    warning: 3.0   # 组合日波动超过 3% 警告
    alert: 5.0     # 组合日波动超过 5% 警报
  individual_volatility:
    warning: 5.0   # 个股日波动超过 5% 警告
    alert: 8.0     # 个股日波动超过 8% 警报
```

### AI 分析（可选）

```yaml
ai_analysis:
  enabled: true
  model: "qwen-plus"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  api_key: ""  # 建议使用环境变量 OPENAI_API_KEY
```

支持任何 OpenAI 兼容 API。API Key 推荐通过环境变量 `OPENAI_API_KEY` 或 `AI_API_KEY` 传入。

## 项目结构

```
anti-fomo/
├── run.py                       # CLI 入口：波动检查 / 定时调度
├── serve.py                     # HTTP 服务：Web 资产配置 UI
├── config.yaml                  # 运营配置（阈值、AI、通知、调度）
├── config.asset.yaml            # 持仓配置（由 serve.py 生成，gitignore）
├── config.example.yaml          # 示例配置
├── requirements.txt             # Python 依赖
├── src/
│   ├── main.py                  # 主程序 AntiFOMO 类
│   ├── portfolio.py             # 组合管理
│   ├── data_fetcher.py          # 市场数据获取（akshare）
│   ├── volatility_calculator.py # 波动率计算
│   ├── threshold_manager.py     # 阈值判断与警报
│   ├── ai_analyzer.py           # AI 分析（OpenAI 兼容）
│   ├── notification.py          # 多渠道通知
│   ├── asset_configurator.py    # 资产配置向导（legacy CLI）
│   └── mock_data.py             # 模拟数据生成
├── web/                         # Web 前端（serve.py 提供）
│   ├── index.html
│   ├── app.js
│   └── style.css
├── docs/                        # 文档 / AI 对话记忆
└── logs/                        # 日志目录
```

## 依赖项

- `akshare` — A 股市场数据
- `pandas` / `numpy` — 数据处理
- `pyyaml` — 配置解析
- `schedule` — 定时调度
- `openai` — AI 分析（可选）

## 注意事项

- 数据来源为 akshare，需要网络连接
- 建议在交易日收盘后运行，以获取最新数据
- AI 建议仅供参考，不构成投资建议
- `config.asset.yaml` 已在 `.gitignore` 中，不会提交到仓库

## License

MIT License
