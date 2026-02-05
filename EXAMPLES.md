# 示例：如何扩展和自定义

## 添加新的指数或个股

编辑 `config.yaml`：

```yaml
portfolio:
  holdings:
    # 添加沪深300
    - symbol: "000300"
      name: "沪深300"
      type: "index"
      allocation_type: "ratio"
      value: 25
    
    # 添加个股（示例）
    - symbol: "600519"
      name: "贵州茅台"
      type: "stock"
      allocation_type: "amount"
      value: 100000
```

## 自定义 AI 提示词

在 `config.yaml` 中修改 `prompt_template`，可以调整 AI 分析的角度和风格。

如果你使用 OpenAI 兼容接口，建议配置 `base_url` 并使用环境变量提供密钥。

## 添加其他数据源

扩展 `src/data_fetcher.py`，添加新的数据获取方法：

```python
def fetch_us_stock_data(self, symbol: str) -> pd.DataFrame:
    # 添加美股数据获取逻辑
    pass
```

## 自定义通知方式

扩展 `src/notification.py`，添加新的通知渠道：

```python
def _send_wechat(self, content: str, method: Dict):
    # 添加微信通知逻辑
    pass
```
