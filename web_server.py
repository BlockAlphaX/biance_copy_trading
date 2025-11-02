#!/usr/bin/env python3
"""
Binance Copy Trading v3.0 - Web Server
启动 FastAPI Web 服务器
"""

import uvicorn
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# 确保日志目录存在
Path('logs').mkdir(exist_ok=True)


if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("  Binance Copy Trading v3.0 - Web Server")
    logger.info("=" * 60)
    logger.info("")
    logger.info("🚀 Starting API server...")
    logger.info("📚 API Documentation: http://localhost:8000/docs")
    logger.info("🔌 WebSocket: ws://localhost:8000/ws")
    logger.info("")
    
    uvicorn.run(
        "web.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )
