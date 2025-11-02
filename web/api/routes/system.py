"""系统管理 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
import logging
from datetime import datetime, timezone

from ..services import system_service
from ..services.config_service import ConfigError

router = APIRouter()
logger = logging.getLogger(__name__)


class SystemStatus(BaseModel):
    """系统状态响应"""
    running: bool
    version: str
    start_time: Optional[str]
    uptime_seconds: Optional[int]


class ConfigUpdate(BaseModel):
    """配置更新请求"""
    config: Dict[str, Any]


def _calculate_uptime(start_time: Optional[str]) -> Optional[int]:
    if not start_time:
        return None
    try:
        start_str = start_time.replace("Z", "+00:00")
        started = datetime.fromisoformat(start_str)
    except ValueError:
        return None
    if started.tzinfo is None:
        started = started.replace(tzinfo=timezone.utc)
    return int((datetime.now(timezone.utc) - started).total_seconds())


@router.get("/status", response_model=SystemStatus)
async def get_status():
    """
    获取系统状态
    
    返回系统运行状态、版本信息和运行时长
    """
    try:
        state = system_service.get_engine_state()
    except Exception as exc:
        logger.error("Failed to get engine state", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
    
    uptime = _calculate_uptime(state.get("start_time"))
    return SystemStatus(
        running=state.get("running", False),
        version=state.get("version", "unknown"),
        start_time=state.get("start_time"),
        uptime_seconds=uptime
    )


@router.post("/start")
async def start_engine():
    """
    启动跟单引擎
    
    启动币安合约跟单引擎，开始监控主账户交易
    """
    try:
        system_service.start_engine()
        logger.info("Copy trading engine marked as running")
        return {"message": "Engine started successfully", "status": "running"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to start engine", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/stop")
async def stop_engine():
    """
    停止跟单引擎
    
    停止币安合约跟单引擎，停止监控和跟单
    """
    try:
        system_service.stop_engine()
        logger.info("Copy trading engine marked as stopped")
        return {"message": "Engine stopped successfully", "status": "stopped"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to stop engine", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/restart")
async def restart_engine():
    """
    重启跟单引擎
    
    先停止再启动跟单引擎
    """
    try:
        system_service.restart_engine()
        logger.info("Copy trading engine restart recorded")
        return {"message": "Engine restarted successfully", "status": "running"}
    except Exception as exc:
        logger.error("Failed to restart engine", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/config")
async def get_config():
    """
    获取当前配置
    
    返回系统当前的配置信息
    """
    try:
        config_data, path, is_example = system_service.get_config(redact=True)
    except Exception as exc:
        logger.error("Failed to load configuration", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
    
    response: Dict[str, Any] = dict(config_data)
    response["_source"] = str(path)
    response["_is_example"] = is_example
    return response


@router.put("/config")
async def update_config(config_update: ConfigUpdate):
    """
    更新配置
    
    更新系统配置（需要重启引擎生效）
    """
    try:
        destination = system_service.update_config(config_update.config)
        logger.info("Configuration written to %s", destination)
        return {
            "message": "Configuration updated successfully",
            "path": str(destination),
            "note": "Please restart the engine for changes to take effect"
        }
    except ConfigError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to update config", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
