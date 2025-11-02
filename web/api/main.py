"""
Binance Copy Trading v3.0 - FastAPI Backend
Web 管理界面和实时监控 API 服务
"""

from fastapi import Depends, FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import json
import logging
from typing import Dict, Any

from .routes import system, accounts, trades, metrics, risk, logs
from .state import ws_manager
from .auth import get_current_subject, verify_token
from .services import trade_service, metrics_service
from web.db.session import init_database

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("🚀 Starting Binance Copy Trading v3.0 API Server...")
    try:
        init_database()
    except Exception:  # pragma: no cover - initialization should not fail during normal operation
        logger.exception("Failed to initialize database schema")
        raise
    yield
    logger.info("🛑 Shutting down API Server...")


# 创建 FastAPI 应用
app = FastAPI(
    title="Binance Copy Trading API",
    description="Web 管理界面和实时监控 API",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
auth_dependency = Depends(get_current_subject)

app.include_router(system.router, prefix="/api", tags=["系统管理"], dependencies=[auth_dependency])
app.include_router(accounts.router, prefix="/api", tags=["账户管理"], dependencies=[auth_dependency])
app.include_router(trades.router, prefix="/api", tags=["交易监控"], dependencies=[auth_dependency])
app.include_router(metrics.router, prefix="/api", tags=["性能监控"], dependencies=[auth_dependency])
app.include_router(risk.router, prefix="/api", tags=["风险管理"], dependencies=[auth_dependency])
app.include_router(logs.router, prefix="/api", tags=["日志管理"], dependencies=[auth_dependency])


@app.get("/")
async def root():
    """根路径"""
    return {
        "name": "Binance Copy Trading API",
        "version": "3.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


async def _authenticate_websocket(websocket: WebSocket) -> bool:
    """Validate websocket authentication via token query or header."""
    token = websocket.query_params.get("token")
    if not token:
        auth_header = websocket.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ", 1)[1].strip()
    if not token:
        await websocket.close(code=1008, reason="Missing authentication token")
        return False
    try:
        verify_token(token)
    except HTTPException as exc:
        logger.warning("WebSocket authentication failed: %s", exc.detail)
        await websocket.close(code=1008, reason=exc.detail)
        return False
    return True


async def _send_trade_snapshot(websocket: WebSocket, *, limit: int = 50) -> None:
    """Send recent trades snapshot to websocket client."""
    bounded_limit = max(1, min(int(limit), 200))
    trades = trade_service.list_recent_trades(limit=bounded_limit)
    await websocket.send_json({
        "type": "trade_snapshot",
        "limit": bounded_limit,
        "data": trades,
    })


async def _send_metrics_snapshot(websocket: WebSocket) -> None:
    """Send metrics snapshot to websocket client."""
    payload: Dict[str, Any] = {
        "type": "metrics_snapshot",
        "rate_limit": metrics_service.get_rate_limit_metrics(),
        "circuit_breakers": metrics_service.get_circuit_breaker_status(),
        "websocket_connections": ws_manager.get_connection_count(),
    }
    try:
        payload["system_performance"] = metrics_service.get_system_performance()
    except RuntimeError:
        payload["system_performance"] = None
    await websocket.send_json(payload)


@app.websocket("/ws/trades")
async def websocket_trades(websocket: WebSocket):
    """WebSocket endpoint streaming trade updates."""
    if not await _authenticate_websocket(websocket):
        return

    await ws_manager.connect(websocket)
    ws_manager.subscribe(websocket, "trades")

    try:
        await _send_trade_snapshot(websocket)

        while True:
            message = await websocket.receive_text()
            if not message:
                continue

            if message.strip().lower() == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                logger.debug("Ignoring non-JSON websocket message: %s", message)
                continue

            action = str(payload.get("action", "")).lower()
            if action == "refresh":
                await _send_trade_snapshot(websocket, limit=payload.get("limit", 50))
            elif action in {"unsubscribe", "close"}:
                await websocket.close(code=1000)
                break
    except WebSocketDisconnect:
        logger.info("Trade websocket client disconnected")
    except Exception:
        logger.exception("Trade websocket error")
    finally:
        ws_manager.unsubscribe(websocket, "trades")
        ws_manager.disconnect(websocket)


@app.websocket("/ws/metrics")
async def websocket_metrics(websocket: WebSocket):
    """WebSocket endpoint streaming metrics snapshots."""
    if not await _authenticate_websocket(websocket):
        return

    await ws_manager.connect(websocket)
    ws_manager.subscribe(websocket, "metrics")

    try:
        await _send_metrics_snapshot(websocket)

        while True:
            message = await websocket.receive_text()
            if not message:
                continue

            if message.strip().lower() == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            try:
                payload = json.loads(message)
            except json.JSONDecodeError:
                logger.debug("Ignoring non-JSON websocket message: %s", message)
                continue

            action = str(payload.get("action", "")).lower()
            if action == "refresh":
                await _send_metrics_snapshot(websocket)
            elif action in {"unsubscribe", "close"}:
                await websocket.close(code=1000)
                break
    except WebSocketDisconnect:
        logger.info("Metrics websocket client disconnected")
    except Exception:
        logger.exception("Metrics websocket error")
    finally:
        ws_manager.unsubscribe(websocket, "metrics")
        ws_manager.disconnect(websocket)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接端点"""
    if not await _authenticate_websocket(websocket):
        return
    await ws_manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            logger.debug(f"Received: {data}")
            
            # 这里可以处理客户端发来的订阅请求等
            # 例如：{"action": "subscribe", "channel": "trades"}
            
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info("Client disconnected")


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
