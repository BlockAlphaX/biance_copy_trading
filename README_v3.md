# Binance Futures Copy Trading System v3.0

<div align="center">

![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**专业级币安合约跟单交易系统 - 带 Web 管理界面**

[English](README.md) | [中文文档](README_v3.md)

</div>

---

## ⚠️ 风险警告

**合约交易具有极高风险，可能导致全部本金损失。请务必：**
- ✅ 在测试网充分测试后再使用实盘
- ✅ 从低杠杆和小资金开始
- ✅ 设置合理的风险控制参数
- ✅ 不要投入超过您承受能力的资金

**作者不对使用本软件造成的任何损失负责。**

---

## ✨ 核心特性

### 🎯 v3.0 新功能

#### 🌐 Web 管理界面
- **现代化 Dashboard** - React + TypeScript + Ant Design
- **实时监控** - WebSocket 实时推送交易和系统状态
- **可视化图表** - ECharts 数据可视化
- **完整管理** - 账户、交易、风险、日志全方位管理

#### 🔧 RESTful API
- **FastAPI 后端** - 高性能异步 API
- **完整文档** - Swagger/OpenAPI 自动文档
- **JWT 认证** - 安全的 API 访问控制
- **WebSocket 支持** - 实时数据推送

#### 📊 功能模块
- **总览页面** - 实时统计、图表、交易流
- **交易监控** - 历史查询、筛选、导出
- **账户管理** - 余额、持仓、杠杆设置
- **性能监控** - CPU、内存、API 使用率
- **风险管理** - 告警、紧急停止
- **日志查看** - 系统、交易、错误日志
- **系统设置** - 完整配置管理

### 🚀 核心交易功能

#### 实时跟单
- ✅ WebSocket 实时监控主账户交易
- ✅ 多账户并发跟单
- ✅ 灵活的跟单比例配置
- ✅ 智能订单去重

#### 风险控制
- ✅ 余额检查和并发安全
- ✅ MIN_NOTIONAL 验证
- ✅ 最小/最大订单限制
- ✅ 交易对白名单/黑名单
- ✅ 熔断器保护
- ✅ Rate Limit 管理

#### 高级功能
- ✅ 精确的价格和数量精度处理
- ✅ 自动杠杆和保证金配置
- ✅ 单向/双向持仓模式
- ✅ 全仓/逐仓保证金模式
- ✅ 部分成交处理
- ✅ 时间同步和重试机制

---

## 📋 系统要求

### 运行环境
- **Python**: 3.11+
- **Node.js**: 18+ (仅开发前端时需要)
- **操作系统**: Linux / macOS / Windows

### 币安账户
- 币安合约账户（主账户 + 跟随账户）
- API Key 和 Secret（需要合约交易权限）
- **不要授予提现权限！**

---

## 🚀 快速开始

### 方式一：使用 Make（推荐）

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/binance_copy_trading.git
cd binance_copy_trading

# 2. 初始化设置
make setup

# 3. 创建配置文件
make create-config

# 4. 编辑配置文件
vim config.futures.yaml

# 5. 启动 Web 服务器
make run

# 访问 http://localhost:8000
```

### 方式二：手动安装

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt
pip install -r requirements-web.txt

# 3. 运行数据库迁移
alembic upgrade head

# 4. 配置
cp config.futures.example.yaml config.futures.yaml
# 编辑 config.futures.yaml

# 5. 启动服务
python web_server.py
```

### 方式三：Docker 部署

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

---

## 📖 配置说明

### 基础配置 (config.futures.yaml)

```yaml
# API 端点
base_url: "https://fapi.binance.com"  # 实盘
# base_url: "https://testnet.binancefuture.com"  # 测试网

# 主账户配置
master:
  api_key: "your_master_api_key"
  api_secret: "your_master_secret"

# 跟随账户配置
followers:
  - name: "follower1"
    api_key: "follower1_api_key"
    api_secret: "follower1_secret"
    copy_ratio: 1.0  # 跟单比例
    enabled: true

# 交易配置
trading:
  leverage: 10  # 杠杆倍数
  margin_type: "CROSSED"  # CROSSED 或 ISOLATED
  position_mode: "one_way"  # one_way 或 hedge
  min_order_amount: 10  # 最小订单金额 (USDT)
  max_order_amount: 10000  # 最大订单金额 (USDT)

# 风险管理
risk_management:
  enabled: true
  max_position_ratio: 0.8  # 最大持仓比例
  stop_loss_ratio: 0.1  # 止损比例
  
# 过滤器
filters:
  symbols_whitelist: []  # 交易对白名单（空=全部）
  symbols_blacklist: []  # 交易对黑名单

# Rate Limit
rate_limit:
  max_weight_per_minute: 1200
  buffer_ratio: 0.8

# 熔断器
circuit_breaker:
  failure_threshold: 5
  timeout_seconds: 60
```

---

## 💻 使用指南

### Web 界面操作

#### 1. 访问 Dashboard
打开浏览器访问 `http://localhost:8000`

#### 2. 系统控制
- **启动/停止** - 点击右上角按钮控制系统
- **重启** - 重启跟单引擎

#### 3. 监控交易
- **实时交易流** - 总览页面查看最新交易
- **历史查询** - 交易页面筛选和导出
- **统计分析** - 查看成功率、盈亏等指标

#### 4. 账户管理
- **查看余额** - 实时账户余额
- **设置杠杆** - 调整账户杠杆
- **启用/禁用** - 控制账户跟单状态

#### 5. 风险管理
- **查看告警** - 实时风险告警
- **紧急停止** - 一键停止所有交易

### API 使用

#### 获取系统状态
```bash
curl http://localhost:8000/api/status
```

#### 启动系统
```bash
curl -X POST http://localhost:8000/api/start
```

#### 获取交易历史
```bash
curl http://localhost:8000/api/trades/history?page=1&size=20
```

完整 API 文档：`http://localhost:8000/docs`

### 命令行管理

```bash
# 使用 Make 命令
make start      # 启动应用
make stop       # 停止应用
make restart    # 重启应用
make status     # 查看状态
make logs       # 查看日志
make follow     # 实时查看日志

# 或使用管理脚本
./scripts/manage.sh start
./scripts/manage.sh status
./scripts/manage.sh logs 100
```

---

## 🏗️ 项目结构

```
binance_copy_trading/
├── src/                          # 核心交易逻辑
│   ├── binance_futures_client.py # 币安合约客户端
│   ├── config_loader.py          # 配置加载
│   ├── trade_logger.py           # 交易日志
│   └── ...
├── web/                          # Web 应用
│   ├── api/                      # FastAPI 后端
│   │   ├── main.py              # API 入口
│   │   ├── routes/              # API 路由
│   │   ├── services/            # 业务逻辑
│   │   └── websocket.py         # WebSocket
│   ├── db/                       # 数据库
│   │   ├── models.py            # 数据模型
│   │   └── session.py           # 数据库会话
│   └── frontend/                 # React 前端
│       ├── src/
│       │   ├── pages/           # 页面组件
│       │   ├── components/      # 通用组件
│       │   ├── services/        # API 服务
│       │   └── stores/          # 状态管理
│       └── package.json
├── migrations/                   # 数据库迁移
├── tests/                        # 测试
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   └── e2e/                     # 端到端测试
├── scripts/                      # 管理脚本
│   └── manage.sh                # 应用管理
├── logs/                         # 日志文件
├── config.futures.yaml           # 配置文件
├── docker-compose.yml            # Docker 配置
├── Dockerfile                    # Docker 镜像
├── Makefile                      # Make 命令
└── README.md                     # 文档
```

---

## 🧪 测试

### 运行所有测试
```bash
make test
```

### 运行特定测试
```bash
make test-unit          # 单元测试
make test-integration   # 集成测试
make test-e2e          # 端到端测试
```

### 代码质量
```bash
make lint    # 代码检查
make format  # 代码格式化
```

---

## 🚀 部署

### 生产环境部署

#### 使用部署脚本
```bash
./deploy.sh user@your-server.com /opt/binance-trading
```

#### 使用 Docker
```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f app

# 4. 停止服务
docker-compose down
```

#### 使用 Systemd
```bash
# 1. 创建服务文件
sudo vim /etc/systemd/system/binance-trading.service

# 2. 添加配置
[Unit]
Description=Binance Copy Trading
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/binance_copy_trading
ExecStart=/path/to/venv/bin/python web_server.py
Restart=always

[Install]
WantedBy=multi-user.target

# 3. 启动服务
sudo systemctl daemon-reload
sudo systemctl enable binance-trading
sudo systemctl start binance-trading
```

---

## 📊 监控和维护

### 日志管理
```bash
# 查看应用日志
make logs

# 实时跟踪日志
make follow

# 查看 Docker 日志
docker-compose logs -f
```

### 数据库管理
```bash
# 创建迁移
make db-migrate msg="your migration message"

# 升级数据库
make db-upgrade

# 查看迁移历史
make db-history
```

### 备份
```bash
# 备份数据和配置
make backup
```

---

## 🔧 开发

### 前端开发
```bash
# 安装依赖
make frontend-install

# 开发模式
make frontend-dev

# 构建生产版本
make frontend-build
```

### 后端开发
```bash
# 开发模式（自动重载）
make run-dev

# 运行测试
make test

# 代码检查
make lint
```

---

## 📚 API 文档

访问 `http://localhost:8000/docs` 查看完整的 Swagger API 文档。

### 主要端点

#### 系统管理
- `GET /api/status` - 系统状态
- `POST /api/start` - 启动系统
- `POST /api/stop` - 停止系统
- `POST /api/restart` - 重启系统

#### 账户管理
- `GET /api/accounts` - 获取所有账户
- `GET /api/accounts/{name}/balance` - 账户余额
- `GET /api/accounts/{name}/positions` - 持仓信息

#### 交易监控
- `GET /api/trades/recent` - 最近交易
- `GET /api/trades/history` - 历史交易
- `GET /api/trades/stats` - 交易统计

#### WebSocket
- `WS /ws/trades` - 实时交易推送
- `WS /ws/metrics` - 实时指标推送

---

## ❓ 常见问题

### 1. 如何在测试网测试？
修改 `config.futures.yaml` 中的 `base_url` 为测试网地址，并使用测试网 API Key。

### 2. 如何设置杠杆？
在配置文件中设置 `trading.leverage`，或在 Web 界面的账户管理页面设置。

### 3. 如何添加多个跟随账户？
在 `config.futures.yaml` 的 `followers` 数组中添加多个账户配置。

### 4. 遇到 Rate Limit 错误怎么办？
系统会自动管理 Rate Limit。如果频繁触发，可以降低 `rate_limit.max_weight_per_minute`。

### 5. 如何备份数据？
运行 `make backup` 会自动备份数据库、日志和配置文件。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

---

## 🙏 致谢

- [Binance API](https://binance-docs.github.io/apidocs/futures/cn/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Ant Design](https://ant.design/)

---

## 📞 联系方式

- **Issues**: [GitHub Issues](https://github.com/yourusername/binance_copy_trading/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/binance_copy_trading/discussions)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个 Star！**

Made with ❤️ by [Your Name]

</div>
