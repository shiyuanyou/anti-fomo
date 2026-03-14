# Anti-FOMO 服务重构方案

## 1. 项目背景

Anti-FOMO 是一个资产配置认知工具，帮助投资者对抗 FOMO（错失恐惧症）。当前系统采用单体架构，BFF（Backend for Frontend）和后台服务混合在一起，限制了独立部署和扩展能力。

## 2. 重构目标

- 分离 BFF 和 Backend 服务，支持独立部署
- 引入 API Gateway 统一入口，降低维护和测试成本
- 数据库拆分，实现数据隔离
- 采用 gRPC 作为服务间通讯，学习现代微服务架构

## 3. 架构设计

### 3.1 整体架构图

```
                              ┌─────────────────────┐
                              │   Traefik (Gateway) │
                              │   :80  → web        │
                              │   :8000 → bff       │
                              └──────────┬──────────┘
                                         │
              ┌──────────────────────────┼──────────────────────────┐
              │                          │                          │
              ▼                          ▼                          ▼
    ┌─────────────────┐       ┌─────────────────┐         ┌─────────────────┐
    │      Web        │       │   BFF (FastAPI)│         │  Backend (FastAPI)│
    │   Vue 3 + Vite  │       │  Port: 8001    │◄──gRPC──│   Port: 8002    │
    │   Port: 3000    │       │                 │         │                 │
    └─────────────────┘       └────────┬────────┘         └────────┬────────┘
                                      │                           │
                              ┌────────▼────────┐         ┌────────▼────────┐
                              │  SQLite-bff.db │         │ SQLite-jobs.db  │
                              │ (templates,    │         │ (jobs, reports)│
                              │  shares)        │         │                 │
                              └─────────────────┘         └────────┬────────┘
                                                                     │
                                      ┌──────────────────────────────┘
                                      ▼
                           ┌─────────────────────┐
                           │  External Services │
                           │  - akshare (数据)  │
                           │  - Tongyi (AI)    │
                           │  - 通知服务        │
                           └─────────────────────┘
```

### 3.2 服务职责

| 服务 | 职责 | 端口 | 依赖 |
|------|------|------|------|
| **Web** | Vue 3 前端 | 3000 (dev) / 80 (prod) | BFF |
| **BFF** | 为前端提供 API 聚合、用户数据管理 | 8001 | SQLite-bff.db |
| **Backend** | 定时任务、市场数据、AI 分析、报告生成 | 8002 | SQLite-jobs.db, akshare, Tongyi |
| **Traefik** | API Gateway，反向代理，服务发现 | 80 / 8000 | - |

## 4. 服务间通讯

### 4.1 为什么选择 gRPC

| 特性 | gRPC | REST API | GraphQL |
|------|------|----------|---------|
| 性能 | ★★★★★ | ★★★ | ★★★ |
| 类型安全 | ★★★★★ | ★★ | ★★★ |
| 代码生成 | ★★★★★ | ★ | ★★ |
| 学习曲线 | 中高 | 低 | 中 |
| 云原生支持 | ★★★★★ | ★★★ | ★★★ |

**选择理由**：
- Protobuf 提供强类型契约，与 Pydantic 理念一致
- gRPC 是云原生时代标准（Kubernetes-native）
- 生成代码减少手动维护工作量
- 适合学习现代微服务架构

### 4.2 gRPC 服务定义

```protobuf
// shared/proto/service.proto
syntax = "proto3";

package antifomo;

service PortfolioService {
  // 获取组合数据
  rpc GetPortfolio(GetPortfolioRequest) returns (PortfolioResponse);
  
  // 获取市场数据
  rpc GetMarketData(GetMarketDataRequest) returns (MarketDataResponse);
  
  // 触发 AI 分析
  rpc AnalyzeWithAI(AIAnalyzeRequest) returns (AIAnalyzeResponse);
  
  // 生成报告
  rpc GenerateReport(ReportRequest) returns (ReportResponse);
}

message GetPortfolioRequest {
  string user_id = 1;
}

message PortfolioResponse {
  repeated Holding holdings = 1;
  double total_value = 2;
}

message Holding {
  string symbol = 1;
  string name = 2;
  double weight = 3;
  double value = 4;
}
// ... more messages
```

### 4.3 通讯流程

```
BFF (8001)                              Backend (8002)
    │                                         │
    │  ── gRPC: GetMarketData ──▶            │
    │                                         │
    │                                    获取市场数据
    │                                    (akshare)
    │                                         │
    │  ◀── MarketDataResponse ──             │
    │                                         │
处理响应                                  返回结果
返回前端
```

## 5. 数据库拆分

### 5.1 拆分策略

```
┌─────────────────────────────────────────────────────────┐
│                     API Gateway (Traefik)               │
└──────────────────────────┬──────────────────────────────┘
                           │
           ┌───────────────┴───────────────┐
           ▼                               ▼
    ┌──────────────┐               ┌──────────────┐
    │     BFF      │               │   Backend    │
    │   (FastAPI)  │ ─── gRPC ──▶  │   (FastAPI)  │
    └──────┬───────┘               └──────┬───────┘
           │                               │
    ┌──────▼───────┐               ┌──────▼───────┐
    │ SQLite-bff   │               │ SQLite-jobs  │
    │ (anti-fomo   │               │ (anti-fomo   │
    │    -bff.db)  │               │    -jobs.db)  │
    └──────────────┘               └──────────────┘
```

### 5.2 数据表规划

| 数据库 | 表名 | 说明 | 读写频率 |
|--------|------|------|----------|
| **anti-fomo-bff.db** | templates | 官方资产配置模板 | 读多写少 |
| | shares | 用户导出的配置分享 | 读多写少 |
| **anti-fomo-jobs.db** | jobs | 定时任务执行记录 | 写多读少 |
| | reports | 生成的报告 | 写多读少 |
| | notifications | 通知记录 | 写多读少 |

### 5.3 保留在 YAML 的数据

以下数据保留在 `config.asset.yaml`，不存入数据库：

- **portfolio**: 用户持仓配置（BFF 需要直接读写）
- **asset_allocation**: 资产配置比例
- **threshold**: 波动率阈值配置

### 5.4 数据库迁移步骤

1. **创建新数据库**
   ```bash
   # BFF 数据库
   sqlite3 data/bff/anti-fomo-bff.db
   
   # Jobs 数据库
   sqlite3 data/jobs/anti-fomo-jobs.db
   ```

2. **迁移现有数据**
   - templates, shares → anti-fomo-bff.db
   - jobs, reports → anti-fomo-jobs.db

3. **更新配置**
   ```yaml
   # bff/config.yaml
   database:
     url: sqlite:///data/bff/anti-fomo-bff.db
   
   # backend/config.yaml
   database:
     url: sqlite:///data/jobs/anti-fomo-jobs.db
   ```

## 6. 目录结构

```
anti-fomo/
├── apps/
│   ├── bff/                    # BFF 服务
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   └── main.py         # FastAPI 应用工厂
│   │   ├── routers/
│   │   │   ├── assets.py        # 资产配置 API
│   │   │   ├── templates.py    # 模板 API
│   │   │   └── shares.py       # 分享 API
│   │   ├── schemas/
│   │   │   ├── asset.py
│   │   │   ├── template.py
│   │   │   └── share.py
│   │   ├── crud/
│   │   │   ├── asset.py
│   │   │   ├── template.py
│   │   │   └── share.py
│   │   ├── models/
│   │   │   ├── database.py
│   │   │   ├── template.py
│   │   │   └── share.py
│   │   ├── requirements.txt
│   │   └── .env
│   │
│   └── backend/                # 后台服务
│       ├── app/
│       │   ├── __init__.py
│       │   └── main.py         # FastAPI 应用工厂
│       ├── services/           # gRPC 服务
│       │   └── proto/
│       │       ├── service.proto
│       │       └── service_pb2.py
│       ├── jobs/               # 定时任务
│       │   ├── daily_check.py
│       │   └── weekly_report.py
│       ├── engines/            # 业务引擎 (原 src/)
│       │   ├── portfolio_engine/
│       │   ├── market_engine/
│       │   ├── decision_engine/
│       │   ├── report_engine/
│       │   └── ai_engine/
│       ├── requirements.txt
│       └── .env
│
├── gateway/                     # API Gateway 配置
│   └── traefik.yml
│
├── shared/                      # 共享代码
│   ├── proto/                  # Protobuf 定义
│   │   ├── service.proto
│   │   └── generate.sh
│   └── constants/
│
├── configs/                     # 配置文件
│   ├── bff.yaml
│   ├── backend.yaml
│   └── config.asset.yaml
│
├── data/                       # 数据目录
│   ├── bff/
│   │   └── anti-fomo-bff.db
│   └── jobs/
│       └── anti-fomo-jobs.db
│
├── logs/
├── cache/
├── base_datas/
├── web/                        # 前端 (不变)
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
└── docker/
    ├── Dockerfile.bff
    ├── Dockerfile.backend
    ├── Dockerfile.web
    ├── docker-compose.yml
    ├── traefik.yml
    └── nginx.conf
```

## 7. API 路由设计

### 7.1 BFF 路由 (Port 8001)

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/assets | 获取资产配置 |
| POST | /api/save | 保存资产配置 |
| GET | /api/templates | 获取模板列表 |
| POST | /api/templates | 创建模板 |
| GET | /api/templates/{id} | 获取模板详情 |
| GET | /api/shares | 获取分享列表 |
| POST | /api/shares | 创建分享 |

### 7.2 Backend 路由 (Port 8002)

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/jobs/run | 触发定时任务 |
| GET | /api/jobs/status | 获取任务状态 |
| GET | /api/reports | 获取报告列表 |
| GET | /api/reports/{id} | 获取报告详情 |
| POST | /api/ai/analyze | AI 分析 |

### 7.3 gRPC 服务

| 服务 | 方法 | 说明 |
|------|------|------|
| PortfolioService | GetPortfolio | 获取组合数据 |
| | GetMarketData | 获取市场数据 |
| | AnalyzeWithAI | AI 分析 |
| JobService | RunDailyCheck | 执行日度检查 |
| | RunWeeklyReport | 生成周报 |

## 8. Docker 部署

### 8.1 docker-compose.yml

```yaml
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    ports:
      - "80:80"
      - "8080:8080"
    volumes:
      - ./docker/traefik.yml:/traefik.yml:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - anti-fomo-network

  bff:
    build:
      context: .
      dockerfile: docker/Dockerfile.bff
    labels:
      - "traefik.http.routers.bff.rule=PathPrefix(`/api`)"
      - "traefik.http.services.bff.loadbalancer.server.port=8001"
    environment:
      - DATABASE_URL=sqlite:///data/bff/anti-fomo-bff.db
    volumes:
      - ./configs:/app/configs:ro
      - ./data/bff:/app/data
    networks:
      - anti-fomo-network

  backend:
    build:
      context: .
      dockerfile: docker/Dockerfile.backend
    labels:
      - "traefik.http.routers.backend.rule=PathPrefix(`/internal`)"
      - "traefik.http.services.backend.loadbalancer.server.port=8002"
    environment:
      - DATABASE_URL=sqlite:///data/jobs/anti-fomo-jobs.db
    volumes:
      - ./configs:/app/configs:ro
      - ./data/jobs:/app/data
      - ./cache:/app/cache
    networks:
      - anti-fomo-network

  web:
    build:
      context: .
      dockerfile: docker/Dockerfile.web
    labels:
      - "traefik.http.routers.web.rule=PathPrefix(`/`)"
      - "traefik.http.services.web.loadbalancer.server.port=80"
    depends_on:
      - bff
    networks:
      - anti-fomo-network

networks:
  anti-fomo-network:
    driver: bridge
```

## 9. 实施计划

### 阶段一：目录结构重构 (P0)

1. 创建 `apps/bff/` 目录，移动 `api/` 内容
2. 创建 `apps/backend/` 目录，移动 `src/` 内容
3. 创建 `shared/` 目录
4. 更新 requirements.txt

### 阶段二：数据库拆分 (P0)

1. 创建 BFF 数据库 (templates, shares 表)
2. 创建 Jobs 数据库 (jobs, reports, notifications 表)
3. 更新 database.py 配置
4. 迁移现有数据

### 阶段三：API Gateway 引入 (P1)

1. 添加 Traefik 配置
2. 更新 docker-compose.yml
3. 调整端口映射

### 阶段四：gRPC 通讯 (P1)

1. 定义 Protobuf 服务
2. 生成 Python 代码
3. 实现 BFF → Backend 调用
4. 更新路由逻辑

### 阶段五：定时任务迁移 (P2)

1. 将调度逻辑移至 Backend
2. 实现 gRPC 触发接口
3. 添加任务状态查询

### 阶段六：AI 服务对接 (P2)

1. 实现 AI 分析 gRPC 服务
2. 对接 Tongyi Qianwen
3. 添加结果缓存

## 10. 环境变量

### BFF 环境变量

```bash
# .env.bff
DATABASE_URL=sqlite:///data/bff/anti-fomo-bff.db
CONFIG_PATH=/app/configs/config.asset.yaml
BACKEND_GRPC_ADDR=backend:8002
LOG_LEVEL=INFO
```

### Backend 环境变量

```bash
# .env.backend
DATABASE_URL=sqlite:///data/jobs/anti-fomo-jobs.db
CONFIG_PATH=/app/configs/config.yaml
AKSHARE_CACHE_TTL=86400
AI_API_KEY=your-api-key
LOG_LEVEL=INFO
```

## 11. 监控与日志

### 日志目录结构

```
logs/
├── bff/
│   ├── access.log
│   └── error.log
└── backend/
    ├── daily_check.log
    ├── weekly_report.log
    └── error.log
```

### 健康检查

| 服务 | 端点 | 预期响应 |
|------|------|----------|
| BFF | GET /health | {"status": "ok"} |
| Backend | GET /health | {"status": "ok"} |
| Traefik | GET /ping | 200 OK |

## 12. 附录

### A. 技术栈

- **BFF**: FastAPI + SQLAlchemy + Pydantic
- **Backend**: FastAPI + SQLAlchemy + APScheduler
- **gRPC**: protobuf3 + grpcio-tools
- **Gateway**: Traefik v2
- **Database**: SQLite (开发) / PostgreSQL (生产)
- **Frontend**: Vue 3 + Vite + TypeScript + Pinia
- **Container**: Docker + Docker Compose

### B. 迁移检查清单

- [ ] 备份现有数据库
- [ ] 备份配置文件
- [ ] 更新所有导入路径
- [ ] 更新 Docker 构建上下文
- [ ] 更新 CI/CD 流程
- [ ] 更新文档中的路径引用
- [ ] 验证所有 API 端点
- [ ] 验证定时任务执行
- [ ] 验证 gRPC 通讯

### C. 回滚方案

如果重构失败，回滚步骤：
1. 恢复原有目录结构
2. 恢复单一数据库
3. 恢复 docker-compose.yml
4. 验证服务正常运行
