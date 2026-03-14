# Anti-FOMO API 契约文档

## 概述

本文档定义了 Anti-FOMO 后端 API 接口规范，供前端开发和前后端联调使用。

**Base URL:** `http://localhost:8000`

**交互方式:** RESTful JSON API

---

## 目录

1. [资产配置 (Assets)](#1-资产配置-assets)
2. [模板 (Templates)](#2-模板-templates)
3. [分享 (Shares)](#3-分享-shares)
4. [对比 (Compare) - 前端实现](#4-对比-compare---前端实现)
5. [AI 分析 - 前端实现](#5-ai-分析---前端实现)

---

## 1. 资产配置 (Assets)

管理用户持仓配置。

| 方法 | 路径 | 说明 |
|-----|------|------|
| `GET` | `/api/assets` | 获取当前资产配置 |
| `POST` | `/api/save` | 保存资产配置 |

### GET /api/assets

获取当前用户的资产配置。

**响应示例 (200):**

```json
{
  "portfolio": {
    "total_amount": 100000,
    "holdings": [
      {
        "name": "沪深300",
        "code": "SH000300",
        "amount": 50000,
        "type": "指数",
        "region": "中国",
        "style": "大盘"
      },
      {
        "name": "标普500",
        "code": "SPX",
        "amount": 30000,
        "type": "指数",
        "region": "美国",
        "style": "大盘"
      }
    ]
  }
}
```

### POST /api/save

保存资产配置。

**请求体:**

```json
{
  "portfolio": {
    "total_amount": 100000,
    "holdings": [
      {
        "name": "沪深300",
        "code": "SH000300",
        "amount": 50000,
        "type": "指数",
        "region": "中国",
        "style": "大盘"
      }
    ]
  }
}
```

**响应示例 (200):**

```json
{
  "status": "success"
}
```

---

## 2. 模板 (Templates)

管理官方资产配置模板。

| 方法 | 路径 | 说明 |
|-----|------|------|
| `GET` | `/api/templates` | 获取模板列表 |
| `GET` | `/api/templates/{template_id}` | 获取单个模板详情 |

### GET /api/templates

获取所有官方模板列表。

**查询参数:**

| 参数 | 类型 | 默认值 | 说明 |
|-----|------|--------|------|
| `skip` | int | 0 | 跳过数量（分页） |
| `limit` | int | 100 | 返回数量（分页） |

**响应示例 (200):**

```json
[
  {
    "id": "global_balanced",
    "name": "全球均衡型",
    "tagline": "分散风险，全球布局",
    "description": "60%全球股票 + 40%债券的经典配置...",
    "target_audience": "寻求稳健增值的投资者",
    "risk_level": "中",
    "allocations": [
      {
        "category": "A股大盘",
        "region": "中国",
        "weight": 0.2
      },
      {
        "category": "美股科技",
        "region": "美国",
        "weight": 0.2
      }
    ],
    "allocation": {
      "A股大盘": 20,
      "美股科技": 20
    },
    "metrics": {
      "expected_return": 7.5,
      "volatility": 12.0,
      "max_drawdown": -18.0,
      "sharpe_ratio": 0.62,
      "data_period": "2010-2024"
    },
    "personality_tags": ["稳健", "分散风险", "长期持有"]
  }
]
```

### GET /api/templates/{template_id}

获取指定模板详情。

**路径参数:**

| 参数 | 类型 | 说明 |
|-----|------|------|
| `template_id` | string | 模板 ID，如 `global_balanced` |

**响应示例 (200):** 同上完整模板对象

**错误响应 (404):**

```json
{
  "detail": "Template 'xxx' not found"
}
```

---

## 3. 分享 (Shares)

管理用户分享的配置。

| 方法 | 路径 | 说明 |
|-----|------|------|
| `POST` | `/api/shares` | 创建分享 |
| `GET` | `/api/shares/{share_id}` | 获取分享 |

### POST /api/shares

创建一个新的配置分享。

**请求体:**

```json
{
  "name": "我的保守配置",
  "author": "张三",
  "description": "低风险配置，适合退休计划",
  "config_json": {
    "portfolio": {
      "total_amount": 500000,
      "holdings": [
        {
          "name": "国债ETF",
          "code": "511010",
          "amount": 400000,
          "type": "债券",
          "region": "中国",
          "style": "保守"
        }
      ]
    }
  }
}
```

**响应示例 (201):**

```json
{
  "id": "AF-SHARE-A1B2C3D4",
  "name": "我的保守配置",
  "author": "张三",
  "description": "低风险配置，适合退休计划",
  "config_json": { ... },
  "created_at": "2024-01-15T10:30:00"
}
```

### GET /api/shares/{share_id}

获取指定分享的配置。

**路径参数:**

| 参数 | 类型 | 说明 |
|-----|------|------|
| `share_id` | string | 分享 ID，如 `AF-SHARE-A1B2C3D4` |

**响应示例 (200):** 同上完整分享对象

**错误响应 (404):**

```json
{
  "detail": "Share 'xxx' not found"
}
```

---

## 4. 对比 (Compare) - 前端实现

**状态:** 前端已实现，不需要后端 API

用户持仓与模板的对比计算在前端完成：

```javascript
// 前端已有数据来源
const userHoldings = store.assets;           // 来自 /api/assets
const templates = await fetch('/api/templates');  // 来自 /api/templates

// 对比逻辑在前端计算
const diffs = compare(userHoldings, template);
```

---

## 5. AI 分析 - 前端实现

**状态:** 暂未实现，后续可能用 JS 直接调用外部 AI API

计划使用 JS 在前端直接调用通义千问等 AI 服务，不经过后端。

---

## 数据模型

### Asset (资产)

```typescript
interface Asset {
  name: string;      // 资产名称，如 "沪深300"
  code: string;     // 代码，如 "SH000300"
  amount: number;    // 金额，如 50000
  type: string;      // 类型，如 "指数"
  region: string;    // 地区，如 "中国"
  style: string;     // 风格，如 "大盘"
}
```

### Portfolio (组合)

```typescript
interface Portfolio {
  total_amount: number;  // 总金额
  holdings: Asset[];     // 持仓列表
}
```

### TemplateMetrics (模板指标)

```typescript
interface TemplateMetrics {
  expected_return: number;  // 预期年化收益 (%)
  volatility: number;        // 年化波动率 (%)
  max_drawdown: number;      // 最大回撤 (%)
  sharpe_ratio: number;      // 夏普比率
  data_period: string;       // 数据区间，如 "2010-2024"
}
```

### AllocationItem (配置项)

```typescript
interface AllocationItem {
  category: string;  // 资产类别，如 "A股大盘"
  region: string;    // 地区，如 "中国"
  weight: number;    // 权重，如 0.2 表示 20%
}
```

---

## 错误响应格式

所有错误响应遵循以下格式：

```json
{
  "detail": "错误描述信息"
}
```

常见 HTTP 状态码：

| 状态码 | 说明 |
|-------|------|
| 200 | 成功 |
| 201 | 创建成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |

---

## 变更日志

| 日期 | 变更 |
|-----|------|
| 2024-01 | 初始版本 |
