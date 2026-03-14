# 开发事故报告

本文档记录开发过程中遇到的坑和事故，供 AI Agent 参考以避免重复犯错。

---

## 2026-03-14: crypto.randomUUID 浏览器兼容性问题

### 问题描述

**现象**: 用户在生产环境点击"+添加资产"按钮时，控制台报错:
```
TypeError: crypto.randomUUID is not a function
```

**影响范围**: 
- 添加新资产功能完全不可用
- 复制模板功能不可用
- 首页无法显示可视化组合

### 根本原因

`crypto.randomUUID()` 是较新的浏览器 API，需要在安全上下文（HTTPS 或 localhost）中运行，且 Safari 和部分旧浏览器不支持。

### 修复方案

添加特性检测和回退处理：
```typescript
function generateId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  // 回退到简单的 UUID v4 实现
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}
```

### 改进措施

1. **前端开发规范**
   - 禁止直接使用需要安全上下文的 API（crypto.subtle, getUserMedia 等）
   - 使用 polyfill 或特性检测
   - 优先使用成熟稳定的库（如 uuid）

2. **测试策略**
   - 添加 Playwright/Cypress E2E 测试覆盖核心用户流程
   - 在 CI 中使用多个浏览器进行测试
   - 生产环境部署后自动触发冒烟测试

3. **监控告警**
   - 前端接入 Sentry 或类似错误监控
   - 捕获运行时 JavaScript 错误并上报

---

## 2024-01: v3.5 开发 - assets.py 数据访问错误

### 问题描述

前端发送的数据结构是 `{"portfolio": {"total_amount": 100000, "holdings": [...]}}`，后端接收到 `config.portfolio` 已经是 `{"total_amount": 100000, "holdings": [...]}`，但代码写的是 `config.portfolio["portfolio"]`，导致永远访问不到数据。

### 错误代码

```python
# 错误
if "portfolio" in config.portfolio and "holdings" in config.portfolio["portfolio"]:
    for holding in config.portfolio["portfolio"]["holdings"]:
```

### 修复后

```python
# 正确
if "holdings" in config.portfolio:
    for holding in config.portfolio["holdings"]:
```

---

## 2024-01: Docker 部署问题

### Bug: requirements.txt 拼写错误

**文件:** `requirements.txt:12`
依赖包名拼写错误，`lembi` 应为 `alembic`（数据库迁移工具）。

### Bug: Dockerfile.api 缺少 config.asset.yaml 处理

直接 COPY 不存在的 config.asset.yaml 文件导致 Docker 构建失败。

**修复:**
```dockerfile
RUN if [ ! -f config.asset.yaml ]; then echo "portfolio: {}" > config.asset.yaml; fi
```

### Bug: docker-compose volume 挂载不存在的文件

挂载不存在的 config.asset.yaml 文件导致容器启动失败。

**修复:**
移除该 volume 挂载，改为在 Dockerfile 中创建默认文件。

---

## 前端开发安全规范

1. **禁止直接使用需要安全上下文的浏览器 API**
   - `crypto.subtle`, `crypto.getRandomValues` 需要 HTTPS
   - `getUserMedia`, `geolocation` 需要用户授权
   - 优先使用成熟稳定的库（如 uuid）

2. **浏览器兼容性检查**
   - 使用 caniuse.com 或 MDN 确认 API 兼容性
   - 考虑 Safari 和旧浏览器用户
   - 添加 polyfill 或特性检测

3. **运行时错误监控**
   - 前端接入 Sentry 或类似错误监控
   - 捕获并上报 JavaScript 运行时错误
