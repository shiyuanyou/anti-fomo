# Anti-FOMO — 资产配置认知工具

帮助权益类投资者建立对自身资产配置的全局认知，通过对比经典模板，减少无意义盯盘和情绪化操作。

## 产品定位

Anti-FOMO 是一个**认知启蒙型工具**，而非智能投顾或交易辅助系统。

大多数普通投资者陷入 FOMO（Fear Of Missing Out）的根本原因，不是不会投资，而是**缺乏对自身资产配置的全局认知**：不知道自己持有什么、为什么持有、风险在哪。先"看见"，才能"理解"，之后才可能"不动摇"。

## 功能概览

### Web 资产配置 UI（v2 主战场）

- **配置模板库** — 提供多个经典资产配置模板（全球均衡、A股核心、全天候防御等），附带量化指标（预计年化、波动率、最大回撤、夏普比）和性格画像
- **模板性格匹配** — AI 辅助分析，帮助用户找到与自身认知和风险偏好匹配的模板
- **配置对比** — 用户当前持仓 vs. 选定模板的可视化 1v1 对比（雷达图/条形图），直观展示超配/低配偏离
- **迁移建议** — AI 提供方向性的资产配置调整思路（非买卖指令）

### 后端监控管道（v1，保持可用）

- **智能波动监控** — 计算组合和个股波动率，双层阈值（警告/警报）自动判定
- **市场估值** — PE/PB 百分位评分，判断市场整体冷热程度
- **AI 分析** — 接入 OpenAI 兼容 API，提供理性投资建议
- **自动化调度** — 每日收盘后定时检查，每周五生成周报

## 快速开始

### 安装依赖

```bash
pip3 install -r requirements.txt
```

### 启动 Web UI（主入口）

```bash
python3 serve.py
```

打开 `http://localhost:8080`，在界面中：
1. 浏览配置模板库，了解不同投资思路
2. 输入或导入自己的持仓
3. 与模板进行可视化对比
4. 获取 AI 迁移建议

这会生成 `config.asset.yaml`，作为持仓的唯一数据来源。

### 运行波动监控（可选，v1 功能）

```bash
python3 run.py            # 单次日度检查
python3 run.py weekly     # 手动生成周报
python3 run.py schedule   # 每日定时检查（默认 15:30）+ 每周五周报
```

## 配置说明

| 文件 | 用途 | 编辑方式 |
|------|------|----------|
| `config.yaml` | 运营配置（阈值、AI、通知、调度） | 手动编辑 |
| `config.asset.yaml` | 持仓配置（名称、代码、比例） | 通过 Web UI 生成，gitignored |

`config.yaml` 不包含持仓数据。所有持仓信息均来自 `config.asset.yaml`。

### AI 分析（可选）

```yaml
ai_analysis:
  enabled: true
  model: "qwen-plus"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  api_key: ""  # 推荐使用环境变量 OPENAI_API_KEY 或 AI_API_KEY
```

支持任何 OpenAI 兼容 API。

## 项目结构

```
anti-fomo/
├── run.py                        # CLI 入口：波动检查 / 定时调度
├── serve.py                      # HTTP 服务：Web 资产配置 UI
├── config.yaml                   # 运营配置（阈值、AI、通知、调度）
├── config.asset.yaml             # 持仓配置（由 serve.py 生成，gitignored）
├── config.example.yaml           # 示例配置
├── requirements.txt              # Python 依赖
├── src/
│   ├── main.py                   # 主程序 AntiFOMO 编排器
│   ├── template_engine/          # v2 新增：模板库、对比引擎、AI 顾问
│   ├── portfolio_engine/         # 持仓数据获取、波动率计算、阈值告警
│   ├── market_engine/            # PE/PB 估值、市场评分
│   ├── decision_engine/          # 看盘判断、再平衡检测
│   ├── report_engine/            # 日度简报、周度报告
│   ├── ai_engine/                # AI 分析（OpenAI 兼容）
│   ├── notification/             # 多渠道通知
│   └── asset_configurator.py     # Legacy CLI 向导（已由 serve.py 取代）
├── web/                          # Web 前端（零构建工具 SPA）
├── docs/                         # 开发文档
│   ├── v1-dev-wiki.md            # v1 实现状态记录
│   ├── v2-dev-wiki.md            # v2 开发计划与约定
│   └── anti-fomo核心.md          # 产品第一性原理讨论记录
└── logs/                         # 运行日志
```

## 依赖项

- `akshare` — A 股市场数据
- `pandas` / `numpy` — 数据处理
- `pyyaml` — 配置解析
- `schedule` — 定时调度
- `openai` — AI 分析（可选）

## 注意事项

- 数据来源为 akshare，需要网络连接
- 量化指标（年化收益、夏普比等）基于历史数据模拟，仅供认知参考，不构成投资建议
- AI 建议仅供参考，不构成投资建议
- 建议在交易日收盘后运行波动检查，以获取最新数据

## License

MIT License
