"""日志管理 API"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import logging

from ..services import log_service

router = APIRouter()
logger = logging.getLogger(__name__)


class LogEntry(BaseModel):
    """日志条目"""
    timestamp: str
    level: str
    type: str  # system, trade, error
    message: str
    details: Optional[dict] = None


@router.get("/logs/system", response_model=List[LogEntry])
async def get_system_logs(
    limit: int = Query(default=100, le=1000),
    level: Optional[str] = None
):
    """
    获取系统日志
    
    返回系统运行日志
    """
    try:
        entries = log_service.get_system_logs(limit=limit, level=level)
        return [LogEntry(**entry) for entry in entries]
    except Exception as exc:
        logger.error("Failed to fetch system logs", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/logs/trades", response_model=List[LogEntry])
async def get_trade_logs(
    limit: int = Query(default=100, le=1000),
    account: Optional[str] = None
):
    """
    获取交易日志
    
    返回交易相关日志
    """
    try:
        entries = log_service.get_trade_logs(limit=limit, account=account)
        return [LogEntry(**entry) for entry in entries]
    except Exception as exc:
        logger.error("Failed to fetch trade logs", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/logs/errors", response_model=List[LogEntry])
async def get_error_logs(
    limit: int = Query(default=100, le=1000)
):
    """
    获取错误日志
    
    返回错误和异常日志
    """
    try:
        entries = log_service.get_error_logs(limit=limit)
        return [LogEntry(**entry) for entry in entries]
    except Exception as exc:
        logger.error("Failed to fetch error logs", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.delete("/logs/clear")
async def clear_logs(log_type: str = Query(..., regex="^(system|trade|error|all)$")):
    """
    清理日志
    
    清理指定类型的日志文件
    """
    try:
        result = log_service.clear_logs(log_type)
        logger.info("Cleared %s logs", log_type)
        return {
            "message": f"{log_type} logs cleared successfully",
            "timestamp": datetime.now().isoformat(),
            "details": result
        }
    
    except Exception as e:
        logger.error(f"Failed to clear logs: {e}")
        raise HTTPException(status_code=500, detail=str(e))
