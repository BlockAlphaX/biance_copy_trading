#!/bin/bash

# Binance Copy Trading v3.0 自动化安装脚本
# 用途：一键创建 Web 管理界面 + 实时监控（不含策略回测）

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  Binance Copy Trading v3.0 Setup"
echo "  Web Dashboard + Real-time Monitoring"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo -e "${YELLOW}[1/10] 检查 Python 版本...${NC}"
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version 2>&1 | awk '{print $2}')
    echo "Python 版本: $python_version"
else
    echo -e "${RED}错误: 未安装 Python3${NC}"
    exit 1
fi

# 检查 Node.js 版本
echo -e "${YELLOW}[2/10] 检查 Node.js 版本...${NC}"
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo "Node.js 版本: $node_version"
else
    echo -e "${RED}错误: 未安装 Node.js${NC}"
    echo "请访问 https://nodejs.org/ 安装 Node.js 18+"
    exit 1
fi

# 创建目录结构
echo -e "${YELLOW}[3/10] 创建项目目录结构...${NC}"
mkdir -p web/api/routes
mkdir -p web/api/models
mkdir -p web/frontend/src/{components,hooks,services,store,utils}
mkdir -p web/frontend/src/components/{Dashboard,Trades,Accounts,Metrics,Risk,Logs,Settings}
mkdir -p web/frontend/public
mkdir -p monitoring
mkdir -p tests/{unit,integration,e2e}
mkdir -p logs

echo -e "${GREEN}✓ 目录结构创建完成${NC}"

# 安装后端依赖
echo -e "${YELLOW}[4/10] 创建后端依赖文件...${NC}"
cat > requirements-web.txt << 'EOF'
# Web 服务依赖 (v3.0)
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-socketio==5.10.0
aiofiles==23.2.1

# 数据库
sqlalchemy==2.0.23
alembic==1.12.1
aiosqlite==0.19.0

# 数据处理
pandas==2.1.3
numpy==1.26.2

# 监控和指标
psutil==5.9.6

# 其他
pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0
EOF

echo -e "${BLUE}安装后端依赖（这可能需要几分钟）...${NC}"
pip install -r requirements-web.txt
echo -e "${GREEN}✓ 后端依赖安装完成${NC}"

# 创建前端项目
echo -e "${YELLOW}[5/10] 初始化前端项目...${NC}"
cd web/frontend

# 创建 package.json
cat > package.json << 'EOF'
{
  "name": "binance-copy-trading-dashboard",
  "version": "3.0.0",
  "description": "Binance Futures Copy Trading Web Dashboard",
  "type": "module",
  "scripts": {
    "dev": "vite --host",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "antd": "^5.11.5",
    "@ant-design/icons": "^5.2.6",
    "echarts": "^5.4.3",
    "echarts-for-react": "^3.0.2",
    "axios": "^1.6.2",
    "socket.io-client": "^4.5.4",
    "zustand": "^4.4.7",
    "dayjs": "^1.11.10",
    "ahooks": "^3.7.8",
    "lodash-es": "^4.17.21"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@types/lodash-es": "^4.17.12",
    "@typescript-eslint/eslint-plugin": "^6.10.0",
    "@typescript-eslint/parser": "^6.10.0",
    "@vitejs/plugin-react": "^4.2.0",
    "eslint": "^8.53.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.4",
    "typescript": "^5.2.2",
    "vite": "^5.0.0"
  }
}
EOF

# 创建 tsconfig.json
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
EOF

# 创建 tsconfig.node.json
cat > tsconfig.node.json << 'EOF'
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
EOF

# 创建 vite.config.ts
cat > vite.config.ts << 'EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'antd-vendor': ['antd', '@ant-design/icons'],
          'chart-vendor': ['echarts', 'echarts-for-react'],
        },
      },
    },
  },
})
EOF

# 创建 .eslintrc.cjs
cat > .eslintrc.cjs << 'EOF'
module.exports = {
  root: true,
  env: { browser: true, es2020: true },
  extends: [
    'eslint:recommended',
    'plugin:@typescript-eslint/recommended',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.cjs'],
  parser: '@typescript-eslint/parser',
  plugins: ['react-refresh'],
  rules: {
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    '@typescript-eslint/no-explicit-any': 'warn',
  },
}
EOF

echo -e "${GREEN}✓ 前端项目配置完成${NC}"

# 安装前端依赖
echo -e "${YELLOW}[6/10] 安装前端依赖（这可能需要几分钟）...${NC}"
npm install
echo -e "${GREEN}✓ 前端依赖安装完成${NC}"

cd ../..

# 创建 Docker 配置
echo -e "${YELLOW}[7/10] 创建 Docker 配置...${NC}"

cat > Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt requirements-web.txt ./

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt -r requirements-web.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p logs

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "web_server.py"]
EOF

cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./config.yaml:/app/config.yaml
    environment:
      - PYTHONUNBUFFERED=1
    restart: unless-stopped
    networks:
      - app-network

  frontend:
    image: node:18-alpine
    working_dir: /app
    volumes:
      - ./web/frontend:/app
      - /app/node_modules
    ports:
      - "5173:5173"
    command: npm run dev
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - app-network

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./web/frontend/dist:/usr/share/nginx/html:ro
    depends_on:
      - backend
    restart: unless-stopped
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
EOF

# 创建 nginx.conf
cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream backend {
        server backend:8000;
    }

    server {
        listen 80;
        server_name localhost;

        # 前端静态文件
        location / {
            root /usr/share/nginx/html;
            try_files $uri $uri/ /index.html;
        }

        # API 代理
        location /api {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_cache_bypass $http_upgrade;
        }

        # WebSocket 代理
        location /ws {
            proxy_pass http://backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "Upgrade";
            proxy_set_header Host $host;
        }
    }
}
EOF

echo -e "${GREEN}✓ Docker 配置创建完成${NC}"

# 更新 .gitignore
echo -e "${YELLOW}[8/10] 更新 .gitignore...${NC}"
cat >> .gitignore << 'EOF'

# v3.0 新增
web/frontend/node_modules/
web/frontend/dist/
web/frontend/.vite/
logs/*.db
*.pyc
__pycache__/
.env
.venv/
venv/
*.log
.DS_Store
EOF

echo -e "${GREEN}✓ .gitignore 更新完成${NC}"

# 创建启动脚本
echo -e "${YELLOW}[9/10] 创建启动脚本...${NC}"

cat > start_dev.sh << 'EOF'
#!/bin/bash

echo "=========================================="
echo "  启动 Binance Copy Trading v3.0"
echo "  开发环境"
echo "=========================================="
echo ""

# 检查配置文件
if [ ! -f "config.yaml" ]; then
    echo "⚠️  警告: config.yaml 不存在"
    echo "请先复制并配置："
    echo "  cp config.example.yaml config.yaml"
    echo "  # 编辑 config.yaml 填入 API 密钥"
    exit 1
fi

# 启动后端
echo "🚀 启动后端服务..."
python web_server.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "🚀 启动前端服务..."
cd web/frontend
npm run dev &
FRONTEND_PID=$!

cd ../..

echo ""
echo "=========================================="
echo "  ✓ 开发环境已启动"
echo "=========================================="
echo ""
echo "📱 前端界面: http://localhost:5173"
echo "📚 API 文档: http://localhost:8000/docs"
echo "🔌 WebSocket: ws://localhost:8000/ws"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "=========================================="

# 等待用户中断
trap "echo ''; echo '正在停止服务...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait
EOF

chmod +x start_dev.sh

cat > start_prod.sh << 'EOF'
#!/bin/bash

echo "=========================================="
echo "  启动 Binance Copy Trading v3.0"
echo "  生产环境 (Docker)"
echo "=========================================="
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: 未安装 Docker"
    echo "请访问 https://www.docker.com/ 安装 Docker"
    exit 1
fi

# 检查配置文件
if [ ! -f "config.yaml" ]; then
    echo "⚠️  警告: config.yaml 不存在"
    echo "请先复制并配置："
    echo "  cp config.example.yaml config.yaml"
    exit 1
fi

# 构建前端
echo "📦 构建前端..."
cd web/frontend
npm run build
cd ../..

# 启动 Docker
echo "🐳 启动 Docker 容器..."
docker-compose up -d

echo ""
echo "=========================================="
echo "  ✓ 生产环境已启动"
echo "=========================================="
echo ""
echo "🌐 访问地址: http://localhost"
echo ""
echo "📋 常用命令:"
echo "  查看日志: docker-compose logs -f"
echo "  停止服务: docker-compose down"
echo "  重启服务: docker-compose restart"
echo "=========================================="
EOF

chmod +x start_prod.sh

echo -e "${GREEN}✓ 启动脚本创建完成${NC}"

# 创建快速开始文档
echo -e "${YELLOW}[10/10] 创建快速开始文档...${NC}"

cat > QUICKSTART_v3.md << 'EOF'
# Binance Copy Trading v3.0 快速开始

## 🎯 系统功能

- ✅ Web 管理界面
- ✅ 实时监控 Dashboard
- ✅ 账户管理
- ✅ 交易监控
- ✅ 性能指标
- ✅ 风险管理
- ✅ 日志查看
- ✅ 告警通知

## 🚀 开发环境

### 前置要求
- Python 3.9+
- Node.js 18+
- npm 或 yarn

### 启动步骤

1. **配置 API 密钥**
   ```bash
   cp config.example.yaml config.yaml
   # 编辑 config.yaml，填入你的 API 密钥
   ```

2. **启动开发服务器**
   ```bash
   ./start_dev.sh
   ```

3. **访问**
   - 前端: http://localhost:5173
   - API 文档: http://localhost:8000/docs
   - WebSocket: ws://localhost:8000/ws

## 🐳 生产环境（Docker）

### 启动

```bash
# 一键启动
./start_prod.sh

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 访问
- Dashboard: http://localhost

## 📊 页面说明

### 1. 总览页面 (`/`)
- 系统运行状态
- 实时交易流
- 关键指标卡片
- 账户余额概览
- 交易量趋势图

### 2. 交易监控 (`/trades`)
- 交易历史列表
- 实时交易推送
- 交易详情查看
- 数据导出功能

### 3. 账户管理 (`/accounts`)
- 主账户信息
- 跟随账户列表
- 余额和持仓
- 杠杆设置
- 熔断器状态

### 4. 性能监控 (`/metrics`)
- Rate Limit 使用率
- 熔断器状态面板
- 系统性能指标
- API 响应时间

### 5. 风险管理 (`/risk`)
- 风险摘要
- 告警列表
- 紧急停止
- 风险规则配置

### 6. 日志查看 (`/logs`)
- 系统日志
- 交易日志
- 错误日志
- 日志搜索和筛选

### 7. 系统设置 (`/settings`)
- 基础配置
- 交易配置
- 风险管理配置
- 通知配置

## 🔧 开发指南

### 后端开发

```bash
# 启动后端（热重载）
cd /path/to/project
uvicorn web.api.main:app --reload --port 8000
```

### 前端开发

```bash
cd web/frontend
npm run dev
```

### 添加新的 API 端点

1. 在 `web/api/routes/` 创建或编辑路由文件
2. 在 `web/api/main.py` 注册路由
3. 访问 http://localhost:8000/docs 查看 API 文档

### 添加新的前端页面

1. 在 `web/frontend/src/components/` 创建组件
2. 在 `web/frontend/src/App.tsx` 添加路由
3. 在侧边栏菜单添加入口

## 📝 API 文档

访问 http://localhost:8000/docs 查看完整的 Swagger API 文档

## 🐛 故障排查

### 后端无法启动
- 检查端口 8000 是否被占用: `lsof -i :8000`
- 检查 Python 依赖: `pip list | grep fastapi`
- 查看日志: `tail -f logs/api.log`

### 前端无法访问
- 检查 Node.js 版本: `node --version`
- 重新安装依赖: `cd web/frontend && npm install`
- 检查端口 5173: `lsof -i :5173`

### WebSocket 连接失败
- 检查后端是否正常运行
- 检查浏览器控制台错误
- 确认代理配置正确

### Docker 启动失败
- 检查 Docker 是否运行: `docker ps`
- 查看容器日志: `docker-compose logs`
- 重新构建: `docker-compose build --no-cache`

## 📞 获取帮助

- 查看 ROADMAP_v3.md 了解完整计划
- 提交 Issue 报告问题
- 查看 CHANGELOG.md 了解更新历史

---

**祝您使用愉快！** 🎉
EOF

echo -e "${GREEN}✓ 文档创建完成${NC}"

echo ""
echo "=========================================="
echo -e "${GREEN}  ✓ v3.0 安装完成！${NC}"
echo "=========================================="
echo ""
echo "📚 下一步："
echo ""
echo "1️⃣  配置 API 密钥"
echo "   ${BLUE}cp config.example.yaml config.yaml${NC}"
echo "   ${BLUE}# 编辑 config.yaml 填入你的 API 密钥${NC}"
echo ""
echo "2️⃣  启动开发环境"
echo "   ${BLUE}./start_dev.sh${NC}"
echo ""
echo "3️⃣  访问 Dashboard"
echo "   ${GREEN}http://localhost:5173${NC}"
echo ""
echo "4️⃣  查看 API 文档"
echo "   ${GREEN}http://localhost:8000/docs${NC}"
echo ""
echo "📖 详细文档："
echo "   - ${BLUE}ROADMAP_v3.md${NC} - 完整开发计划"
echo "   - ${BLUE}QUICKSTART_v3.md${NC} - 快速开始指南"
echo ""
echo "=========================================="
echo ""
echo "💡 提示: 使用 ${YELLOW}./start_prod.sh${NC} 启动生产环境（Docker）"
echo ""
