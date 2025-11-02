# Binance Copy Trading Dashboard

现代化的币安合约跟单系统 Web 管理界面。

## 技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **Ant Design** - UI 组件库
- **Vite** - 构建工具
- **Zustand** - 状态管理
- **React Router** - 路由管理
- **ECharts** - 数据可视化
- **Socket.IO** - WebSocket 实时通信
- **Axios** - HTTP 客户端

## 功能特性

### 📊 总览页面
- 实时系统状态监控
- 关键指标展示（交易量、成功率、盈亏）
- 账户余额分布图
- 交易量趋势图
- 实时交易流

### 💱 交易监控
- 交易历史查询
- 多维度筛选（时间、交易对、账户）
- 交易详情查看
- 实时交易推送
- 数据导出功能

### 👤 账户管理
- 主账户和跟随账户管理
- 账户余额和持仓查看
- 杠杆设置
- 账户启用/禁用控制

### 📈 性能监控
- API Rate Limit 监控
- 系统资源使用（CPU、内存）
- API 响应时间统计
- 熔断器状态

### ⚠️ 风险管理
- 风险等级评估
- 持仓风险展示
- 告警列表和确认
- 紧急停止功能

### 📝 日志查看
- 系统日志
- 交易日志
- 错误日志
- 日志筛选和搜索

### ⚙️ 系统设置
- 基础配置管理
- 交易参数设置
- 风险控制配置
- 通知配置

## 快速开始

### 安装依赖

```bash
npm install
```

### 配置环境变量

复制 `.env.example` 到 `.env` 并修改配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=http://localhost:8000
```

### 开发模式

```bash
npm run dev
```

访问 http://localhost:5173

### 生产构建

```bash
npm run build
```

构建产物在 `dist/` 目录。

### 预览生产构建

```bash
npm run preview
```

## 项目结构

```
src/
├── components/          # 通用组件
│   └── Layout/         # 布局组件
├── pages/              # 页面组件
│   ├── Dashboard/      # 总览页面
│   ├── Trades/         # 交易监控
│   ├── Accounts/       # 账户管理
│   ├── Metrics/        # 性能监控
│   ├── Risk/           # 风险管理
│   ├── Logs/           # 日志查看
│   └── Settings/       # 系统设置
├── services/           # API 服务
│   ├── api.ts          # REST API
│   └── websocket.ts    # WebSocket
├── stores/             # 状态管理
│   ├── useSystemStore.ts
│   ├── useTradeStore.ts
│   └── useAccountStore.ts
├── App.tsx             # 应用入口
├── main.tsx            # 主文件
└── index.css           # 全局样式
```

## API 接口

### 系统管理
- `GET /api/status` - 获取系统状态
- `POST /api/start` - 启动系统
- `POST /api/stop` - 停止系统
- `POST /api/restart` - 重启系统
- `GET /api/config` - 获取配置
- `PUT /api/config` - 更新配置

### 账户管理
- `GET /api/accounts` - 获取所有账户
- `GET /api/accounts/{name}/balance` - 获取余额
- `GET /api/accounts/{name}/positions` - 获取持仓
- `POST /api/accounts/{name}/leverage` - 设置杠杆
- `PUT /api/accounts/{name}/enable` - 启用/禁用

### 交易监控
- `GET /api/trades/recent` - 最近交易
- `GET /api/trades/history` - 历史交易
- `GET /api/trades/stats` - 交易统计
- `GET /api/trades/{id}` - 交易详情

### WebSocket 事件
- `trade` - 实时交易推送
- `metrics` - 实时指标推送
- `alert` - 告警推送

## 开发指南

### 添加新页面

1. 在 `src/pages/` 创建新页面组件
2. 在 `src/App.tsx` 添加路由
3. 在 `src/components/Layout/index.tsx` 添加菜单项

### 添加新 API

在 `src/services/api.ts` 添加新的 API 方法：

```typescript
export const newApi = {
  getData: () => apiClient.get('/api/new-endpoint'),
};
```

### 添加新状态

在 `src/stores/` 创建新的 Zustand store：

```typescript
import { create } from 'zustand';

interface NewState {
  data: any;
  setData: (data: any) => void;
}

export const useNewStore = create<NewState>((set) => ({
  data: null,
  setData: (data) => set({ data }),
}));
```

## 部署

### Docker 部署

```bash
docker build -t binance-dashboard .
docker run -p 80:80 binance-dashboard
```

### Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/dist;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## 许可证

MIT
