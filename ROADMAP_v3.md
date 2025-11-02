# Binance Copy Trading v3.0 开发计划

## 🎯 目标：Web 管理界面 + 实时监控 + 策略回测

---

## 📋 Phase 1: 后端 API 服务 (FastAPI)

### 1.1 基础架构
- [ ] 创建 FastAPI 应用 (`web/api/main.py`)
- [ ] 实现 CORS 中间件
- [ ] 添加认证中间件（JWT Token）
- [ ] 实现 WebSocket 支持（实时数据推送）
- [ ] 配置日志和错误处理

### 1.2 核心 API 端点

#### 系统管理
- [ ] `GET /api/status` - 获取系统状态
- [ ] `POST /api/start` - 启动跟单引擎
- [ ] `POST /api/stop` - 停止跟单引擎
- [ ] `POST /api/restart` - 重启跟单引擎
- [ ] `GET /api/config` - 获取当前配置
- [ ] `PUT /api/config` - 更新配置

#### 账户管理
- [ ] `GET /api/accounts` - 获取所有账户信息
- [ ] `GET /api/accounts/{name}/balance` - 获取账户余额
- [ ] `GET /api/accounts/{name}/positions` - 获取持仓信息
- [ ] `POST /api/accounts/{name}/leverage` - 设置杠杆

#### 交易监控
- [ ] `GET /api/trades/recent` - 获取最近交易
- [ ] `GET /api/trades/history` - 获取历史交易（分页）
- [ ] `GET /api/trades/stats` - 获取交易统计
- [ ] `WS /ws/trades` - 实时交易推送

#### 性能监控
- [ ] `GET /api/metrics/rate-limit` - Rate limit 统计
- [ ] `GET /api/metrics/circuit-breaker` - 熔断器状态
- [ ] `GET /api/metrics/performance` - 性能指标
- [ ] `WS /ws/metrics` - 实时指标推送

#### 风险管理
- [ ] `GET /api/risk/summary` - 风险摘要
- [ ] `POST /api/risk/emergency-stop` - 紧急停止
- [ ] `GET /api/risk/alerts` - 告警列表

---

## 📋 Phase 2: 前端 Dashboard (React + TypeScript)

### 2.1 技术栈
- **框架**: React 18 + TypeScript
- **UI 库**: Ant Design / Material-UI
- **图表**: ECharts / Recharts
- **状态管理**: Zustand / Redux Toolkit
- **路由**: React Router v6
- **HTTP 客户端**: Axios
- **WebSocket**: Socket.io-client
- **构建工具**: Vite

### 2.2 页面结构

#### 2.2.1 总览页面 (`/dashboard`)
**组件**:
- 系统状态卡片（运行状态、运行时长、版本）
- 实时交易流（最近 10 笔交易）
- 关键指标卡片（成功率、总交易量、今日盈亏）
- 账户余额概览（饼图）
- 交易量趋势图（折线图，24小时）

#### 2.2.2 交易监控页面 (`/trades`)
**组件**:
- 交易列表（表格，支持筛选和排序）
  - 时间、交易对、方向、数量、价格、状态
  - 主账户/跟随账户标识
- 交易详情抽屉
- 实时交易流（WebSocket）
- 交易统计卡片
- 导出功能（CSV/Excel）

#### 2.2.3 账户管理页面 (`/accounts`)
**组件**:
- 主账户信息卡片
  - 余额、持仓、杠杆设置
- 跟随账户列表
  - 每个账户的卡片视图
  - 余额、持仓、跟单比例
  - 启用/禁用开关
  - 熔断器状态指示器
- 账户性能对比图表
- 杠杆和保证金类型设置

#### 2.2.4 性能监控页面 (`/metrics`)
**组件**:
- Rate Limit 仪表盘
  - 当前使用率（仪表盘图）
  - 历史趋势（折线图）
  - 等待次数统计
- 熔断器状态面板
  - 每个账户的熔断器状态
  - 状态转换历史
- 系统性能指标
  - CPU、内存使用率
  - WebSocket 连接状态
  - API 响应时间

#### 2.2.5 风险管理页面 (`/risk`)
**组件**:
- 风险摘要仪表盘
  - 总持仓风险
  - 单账户风险
  - 日内亏损统计
- 告警列表
  - 余额不足告警
  - 熔断器触发告警
  - Rate limit 告警
- 紧急停止按钮
- 风险规则配置

#### 2.2.6 策略回测页面 (`/backtest`)
**组件**:
- 回测参数配置表单
  - 时间范围选择
  - 交易对选择
  - 跟单比例设置
  - 风险参数设置
- 回测结果展示
  - 收益曲线图
  - 回撤曲线图
  - 交易明细表
  - 性能指标（夏普比率、最大回撤等）
- 对比分析（多个策略对比）

#### 2.2.7 设置页面 (`/settings`)
**组件**:
- 基础配置
  - API 地址、环境切换
- 交易配置
  - 杠杆、保证金类型、持仓模式
  - 交易对白名单/黑名单
- 风险管理配置
  - 最大持仓、日内亏损限制
- 通知配置
  - Telegram、Email 设置
- 高级配置
  - Rate limit、熔断器参数

---

## 📋 Phase 3: 策略回测引擎

### 3.1 数据层
- [ ] 创建回测数据模型 (`src/backtest/models.py`)
- [ ] 实现历史数据加载器
  - 从交易日志加载
  - 从币安 API 获取历史数据
- [ ] 数据预处理和清洗

### 3.2 回测引擎
- [ ] 创建回测引擎核心 (`src/backtest/engine.py`)
  - 事件驱动架构
  - 时间序列回放
  - 订单模拟执行
- [ ] 实现滑点和手续费模拟
- [ ] 实现持仓管理
- [ ] 实现资金管理

### 3.3 性能分析
- [ ] 创建性能分析器 (`src/backtest/analyzer.py`)
  - 收益率计算
  - 最大回撤计算
  - 夏普比率、索提诺比率
  - 胜率、盈亏比
  - 交易频率分析
- [ ] 生成回测报告

### 3.4 策略优化
- [ ] 参数优化器（网格搜索）
- [ ] 蒙特卡洛模拟
- [ ] 敏感性分析

---

## 📋 Phase 4: 实时监控系统

### 4.1 数据采集
- [ ] 创建指标采集器 (`src/monitoring/collector.py`)
  - 系统指标（CPU、内存、磁盘）
  - 应用指标（交易数、成功率）
  - API 指标（响应时间、错误率）
- [ ] 实现时序数据存储（SQLite/InfluxDB）

### 4.2 实时推送
- [ ] WebSocket 服务器实现
- [ ] 实时数据流处理
- [ ] 数据聚合和降采样

### 4.3 告警系统
- [ ] 告警规则引擎
- [ ] 告警通知（Telegram、Email、Webhook）
- [ ] 告警历史记录

---

## 📋 Phase 5: 部署和运维

### 5.1 容器化
- [ ] 创建 Dockerfile
- [ ] 创建 docker-compose.yml
- [ ] 配置环境变量

### 5.2 部署脚本
- [ ] 一键部署脚本
- [ ] 自动更新脚本
- [ ] 备份和恢复脚本

### 5.3 文档
- [ ] API 文档（Swagger/OpenAPI）
- [ ] 用户手册
- [ ] 部署指南
- [ ] 故障排查指南

---

## 📁 项目结构（v3.0）

```
binance_copy_trading/
├── main.py                                 # 主程序入口
├── web_server.py                           # Web 服务器入口 (NEW)
├── config.example.yaml
├── requirements.txt
├── requirements-web.txt                    # Web 依赖 (NEW)
├── Dockerfile                              # Docker 配置 (NEW)
├── docker-compose.yml                      # Docker Compose (NEW)
├── README.md
├── CHANGELOG.md
├── ROADMAP_v3.md                           # 本文件 (NEW)
│
├── src/                                    # 核心交易引擎
│   ├── binance_futures_client.py
│   ├── futures_copy_trade_engine.py
│   ├── rate_limiter.py
│   ├── circuit_breaker.py
│   ├── trade_logger.py
│   ├── config_loader.py
│   └── logger.py
│
├── web/                                    # Web 服务 (NEW)
│   ├── api/                                # FastAPI 后端
│   │   ├── main.py                         # FastAPI 应用
│   │   ├── auth.py                         # 认证中间件
│   │   ├── websocket.py                    # WebSocket 处理
│   │   ├── routes/                         # API 路由
│   │   │   ├── system.py                   # 系统管理
│   │   │   ├── accounts.py                 # 账户管理
│   │   │   ├── trades.py                   # 交易监控
│   │   │   ├── metrics.py                  # 性能监控
│   │   │   ├── risk.py                     # 风险管理
│   │   │   └── backtest.py                 # 回测接口
│   │   └── models/                         # 数据模型
│   │       ├── request.py
│   │       └── response.py
│   │
│   └── frontend/                           # React 前端
│       ├── public/
│       ├── src/
│       │   ├── components/                 # 组件
│       │   │   ├── Dashboard/
│       │   │   ├── Trades/
│       │   │   ├── Accounts/
│       │   │   ├── Metrics/
│       │   │   ├── Risk/
│       │   │   ├── Backtest/
│       │   │   └── Settings/
│       │   ├── hooks/                      # 自定义 Hooks
│       │   ├── services/                   # API 服务
│       │   ├── store/                      # 状态管理
│       │   ├── utils/                      # 工具函数
│       │   ├── App.tsx
│       │   └── main.tsx
│       ├── package.json
│       ├── tsconfig.json
│       └── vite.config.ts
│
├── backtest/                               # 回测引擎 (NEW)
│   ├── engine.py                           # 回测引擎核心
│   ├── data_loader.py                      # 数据加载器
│   ├── analyzer.py                         # 性能分析器
│   ├── optimizer.py                        # 参数优化器
│   └── models.py                           # 数据模型
│
├── monitoring/                             # 监控系统 (NEW)
│   ├── collector.py                        # 指标采集器
│   ├── storage.py                          # 时序数据存储
│   ├── alerting.py                         # 告警系统
│   └── notifier.py                         # 通知服务
│
├── tests/                                  # 测试 (NEW)
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
└── logs/                                   # 日志目录
    ├── futures_trades.jsonl
    ├── api.log
    └── metrics.db
```

---

## 🔧 技术栈总结

### 后端
- **核心引擎**: Python 3.9+
- **Web 框架**: FastAPI 0.104+
- **WebSocket**: FastAPI WebSocket + Socket.io
- **数据库**: SQLite (开发) / PostgreSQL (生产)
- **时序数据**: InfluxDB (可选)
- **认证**: JWT Token
- **API 文档**: Swagger/OpenAPI

### 前端
- **框架**: React 18 + TypeScript 5
- **构建工具**: Vite 5
- **UI 库**: Ant Design 5 / Material-UI
- **图表**: ECharts 5 / Recharts
- **状态管理**: Zustand / Redux Toolkit
- **HTTP**: Axios
- **WebSocket**: Socket.io-client
- **样式**: TailwindCSS / Styled-components

### 部署
- **容器**: Docker + Docker Compose
- **反向代理**: Nginx
- **进程管理**: Supervisor / PM2
- **监控**: Prometheus + Grafana (可选)

---

## 📅 开发时间估算

| Phase | 任务 | 预计时间 |
|-------|------|----------|
| Phase 1 | 后端 API 服务 | 2-3 天 |
| Phase 2 | 前端 Dashboard | 3-4 天 |
| Phase 3 | 策略回测引擎 | 2-3 天 |
| Phase 4 | 实时监控系统 | 1-2 天 |
| Phase 5 | 部署和运维 | 1 天 |
| **总计** | | **9-13 天** |

---

## 🎯 里程碑

### v3.0-alpha (基础版)
- ✅ 后端 API 基础框架
- ✅ 前端基础页面（总览、交易监控）
- ✅ WebSocket 实时推送
- ✅ 基础认证

### v3.0-beta (完整版)
- ✅ 所有 API 端点
- ✅ 所有前端页面
- ✅ 策略回测功能
- ✅ 实时监控系统
- ✅ 告警通知

### v3.0-stable (生产版)
- ✅ 性能优化
- ✅ 安全加固
- ✅ 完整测试
- ✅ 文档完善
- ✅ Docker 部署

---

## 🚀 快速开始（v3.0）

### 开发环境

```bash
# 1. 安装后端依赖
pip install -r requirements.txt
pip install -r requirements-web.txt

# 2. 安装前端依赖
cd web/frontend
npm install

# 3. 启动后端服务
python web_server.py

# 4. 启动前端开发服务器
cd web/frontend
npm run dev

# 5. 访问
# 前端: http://localhost:5173
# API 文档: http://localhost:8000/docs
```

### 生产部署

```bash
# 使用 Docker Compose
docker-compose up -d

# 访问
# Dashboard: http://localhost:3000
# API: http://localhost:8000
```

---

## 📊 预期效果

### 功能对比

| 功能 | v2.1 | v3.0 |
|------|------|------|
| 命令行界面 | ✅ | ✅ |
| Web 界面 | ❌ | ✅ |
| 实时监控 | ⚠️ (日志) | ✅ (Dashboard) |
| 历史查询 | ⚠️ (文件) | ✅ (数据库) |
| 策略回测 | ❌ | ✅ |
| 告警通知 | ❌ | ✅ |
| 远程管理 | ❌ | ✅ |
| 多用户支持 | ❌ | ✅ |

### 用户体验提升

- 📱 **可视化**: 从命令行到图形界面
- 🔍 **可观测性**: 实时监控所有指标
- 📊 **数据分析**: 历史数据查询和分析
- 🎯 **策略优化**: 回测验证策略效果
- 🚨 **主动告警**: 异常情况及时通知
- 🌐 **远程管理**: 随时随地管理系统

---

## ⚠️ 注意事项

1. **安全性**
   - 使用 HTTPS（生产环境）
   - 实现强密码策略
   - 限制 API 访问频率
   - 定期更新依赖

2. **性能**
   - 前端使用虚拟滚动（大数据列表）
   - 后端使用缓存（Redis）
   - 数据库索引优化
   - WebSocket 连接池管理

3. **可靠性**
   - 实现健康检查
   - 自动重启机制
   - 数据备份策略
   - 灾难恢复计划

---

## 📞 开发支持

如有问题或建议，请提交 Issue 或 Pull Request。

**让我们一起打造最强大的币安合约跟单系统！** 🚀
