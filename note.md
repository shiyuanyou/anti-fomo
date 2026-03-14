# anti-fomo 项目进展总结

**更新时间：2026-03-13**

---

## 当前版本状态

### V2 开发完成 ✅
- 完成前后端重构
- 后端：Python FastAPI
- 前端：Vue 3 + Vite + TypeScript
- 支持 Nginx 挂载部署

### V3 进行中 🚧
- 真实历史指标数据层
- 通过 akshare 获取代理指数历史行情
- 本地数据缓存

### V3.5 开发中 🚧
- 前端工程化重构完成
- 双模式运行架构（本地模式/云端模式）
- 配置分享功能开发中

---

## 项目架构

```
anti-fomo/
├── run.py              # CLI 入口（v1 监控）
├── serve.py            # Web 服务入口（v2）
├── api/                # FastAPI 后端
│   ├── main.py         # 应用入口
│   ├── routers/        # 路由处理
│   ├── models/         # SQLAlchemy 模型
│   ├── schemas/        # Pydantic schemas
│   ├── crud/           # 数据库操作
│   └── services/       # 业务逻辑
├── web/                # Vue 3 前端
├── scripts/            # 数据处理脚本
├── src/                # 核心引擎（v1）
└── docs/               # 开发文档
```

---

## 产品线规划

| 版本 | 目标 | 状态 |
|------|------|------|
| V1 | 官网简洁版（免登录） | 待开发 |
| V2 | 本地开源增强版 | ✅ 完成 |
| V3 | 真实历史数据层 | 🚧 进行中 |
| V3.5 | 配置分享功能 | 🚧 开发中 |
| V4 | 桌面增强版 | 规划中 |

---

## 本周工作

1. 完成 todo list 整理
2. 创建 MVP 到产品级路线文档
3. 文档重新整理

---

## 待办事项（优先级）

### P0 - 数据底座
- 指数基础信息入库（名称、代码、类型、区域、风格）
- 指数聚合数据（周度、月度、年度 OHLC）
- 核心指标计算

### P1 - 云版主线
- Home Page
- 指数展示页
- 模板对比优化
- 社区最佳组合展示

### P2 - 本地增强
- 高级指数统计
- 购物车与组合能力
- AI 分析入口

---

## 技术栈

- **后端**：Python 3.8+ / FastAPI / SQLAlchemy / SQLite
- **前端**：Vue 3 / Vite / TypeScript / Pinia / Chart.js
- **数据**：akshare / pandas / numpy
- **部署**：Nginx
