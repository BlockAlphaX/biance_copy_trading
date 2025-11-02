#!/bin/bash

# Binance Copy Trading v3.0 自动化安装脚本
# 用途：一键创建 Web 管理界面 + 实时监控 + 策略回测

set -e  # 遇到错误立即退出

echo "=========================================="
echo "  Binance Copy Trading v3.0 Setup"
echo "  Web Dashboard + Monitoring + Backtest"
echo "=========================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo -e "${YELLOW}[1/10] 检查 Python 版本...${NC}"
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python 版本: $python_version"

# 检查 Node.js 版本
echo -e "${YELLOW}[2/10] 检查 Node.js 版本...${NC}"
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo "Node.js 版本: $node_version"
else
    echo -e "${RED}错误: 未安装 Node.js${NC}"
    echo "请访问 https://nodejs.org/ 安装 Node.js"
    exit 1
fi

# 创建目录结构
echo -e "${YELLOW}[3/10] 创建项目目录结构...${NC}"
mkdir -p web/api/routes
mkdir -p web/api/models
mkdir -p web/frontend/src/{components,hooks,services,store,utils}
mkdir -p web/frontend/src/components/{Dashboard,Trades,Accounts,Metrics,Risk,Backtest,Settings}
mkdir -p web/frontend/public
mkdir -p backtest
mkdir -p monitoring
mkdir -p tests/{unit,integration,e2e}
mkdir -p logs

echo -e "${GREEN}✓ 目录结构创建完成${NC}"

# 安装后端依赖
echo -e "${YELLOW}[4/10] 安装后端依赖...${NC}"
cat > requirements-web.txt << 'EOF'
# Web 服务依赖
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

# 其他
pydantic==2.5.0
pydantic-settings==2.1.0
EOF

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
  "type": "module",
  "scripts": {
    "dev": "vite",
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
    "ahooks": "^3.7.8"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
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
})
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

  frontend:
    image: node:18-alpine
    working_dir: /app
    volumes:
      - ./web/frontend:/app
    ports:
      - "5173:5173"
    command: npm run dev
    depends_on:
      - backend
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - backend
      - frontend
    restart: unless-stopped
EOF

echo -e "${GREEN}✓ Docker 配置创建完成${NC}"

# 创建 .gitignore
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
EOF

echo -e "${GREEN}✓ .gitignore 更新完成${NC}"

# 创建启动脚本
echo -e "${YELLOW}[9/10] 创建启动脚本...${NC}"

cat > start_dev.sh << 'EOF'
#!/bin/bash

echo "启动 Binance Copy Trading v3.0 开发环境..."

# 启动后端
echo "启动后端服务..."
python web_server.py &
BACKEND_PID=$!

# 等待后端启动
sleep 3

# 启动前端
echo "启动前端服务..."
cd web/frontend
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "  开发环境已启动"
echo "=========================================="
echo "后端 API: http://localhost:8000"
echo "API 文档: http://localhost:8000/docs"
echo "前端界面: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "=========================================="

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT
wait
EOF

chmod +x start_dev.sh

cat > start_prod.sh << 'EOF'
#!/bin/bash

echo "启动 Binance Copy Trading v3.0 生产环境..."
docker-compose up -d

echo ""
echo "=========================================="
echo "  生产环境已启动"
echo "=========================================="
echo "访问地址: http://localhost"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
echo "=========================================="
EOF

chmod +x start_prod.sh

echo -e "${GREEN}✓ 启动脚本创建完成${NC}"

# 创建 README
echo -e "${YELLOW}[10/10] 创建快速开始文档...${NC}"

cat > QUICKSTART_v3.md << 'EOF'
# Binance Copy Trading v3.0 快速开始

## 🚀 开发环境

### 前置要求
- Python 3.9+
- Node.js 18+
- npm 或 yarn

### 启动步骤

1. **安装依赖**（已完成）
   ```bash
   pip install -r requirements.txt -r requirements-web.txt
   cd web/frontend && npm install
   ```

2. **配置**
   ```bash
   cp config.example.yaml config.yaml
   # 编辑 config.yaml，填入 API 密钥
   ```

3. **启动开发服务器**
   ```bash
   ./start_dev.sh
   ```

4. **访问**
   - 前端: http://localhost:5173
   - API 文档: http://localhost:8000/docs
   - WebSocket: ws://localhost:8000/ws

## 🐳 生产环境（Docker）

### 启动

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

### 访问
- Dashboard: http://localhost

## 📊 功能说明

### 1. 总览页面
- 系统状态监控
- 实时交易流
- 关键指标展示

### 2. 交易监控
- 历史交易查询
- 实时交易推送
- 交易详情查看

### 3. 账户管理
- 主账户信息
- 跟随账户管理
- 杠杆和保证金设置

### 4. 性能监控
- Rate Limit 使用率
- 熔断器状态
- 系统性能指标

### 5. 风险管理
- 风险摘要
- 告警列表
- 紧急停止

### 6. 策略回测
- 历史数据回测
- 性能分析
- 策略优化

## 🔧 开发指南

### 后端开发

```bash
# 启动后端（热重载）
uvicorn web.api.main:app --reload --port 8000
```

### 前端开发

```bash
cd web/frontend
npm run dev
```

### 添加新的 API 端点

1. 在 `web/api/routes/` 创建路由文件
2. 在 `web/api/main.py` 注册路由
3. 更新 API 文档

### 添加新的前端页面

1. 在 `web/frontend/src/components/` 创建组件
2. 在 `web/frontend/src/App.tsx` 添加路由
3. 在侧边栏菜单添加入口

## 📝 API 文档

访问 http://localhost:8000/docs 查看完整的 API 文档（Swagger UI）

## 🐛 故障排查

### 后端无法启动
- 检查端口 8000 是否被占用
- 检查 Python 依赖是否完整安装
- 查看日志: `logs/api.log`

### 前端无法访问
- 检查 Node.js 版本
- 重新安装依赖: `npm install`
- 检查代理配置: `vite.config.ts`

### WebSocket 连接失败
- 检查后端是否正常运行
- 检查防火墙设置
- 查看浏览器控制台错误

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
echo "1. 配置 API 密钥"
echo "   cp config.example.yaml config.yaml"
echo "   # 编辑 config.yaml"
echo ""
echo "2. 启动开发环境"
echo "   ./start_dev.sh"
echo ""
echo "3. 访问 Dashboard"
echo "   http://localhost:5173"
echo ""
echo "4. 查看 API 文档"
echo "   http://localhost:8000/docs"
echo ""
echo "📖 详细文档："
echo "   - ROADMAP_v3.md - 完整开发计划"
echo "   - QUICKSTART_v3.md - 快速开始指南"
echo ""
echo "=========================================="
