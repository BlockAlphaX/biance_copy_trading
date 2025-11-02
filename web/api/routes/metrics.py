"""性能监控 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import logging

from ..services import metrics_service
from ..state import ws_manager

router = APIRouter()
logger = logging.getLogger(__name__)


class RateLimitMetrics(BaseModel):
    """Rate Limit 指标"""
    total_requests: int
    current_weight: int
    weight_limit: int
    utilization: float
    wait_count: int
    total_wait_time: float


class CircuitBreakerStatus(BaseModel):
    """熔断器状态"""
    name: str
    state: str  # CLOSED, OPEN, HALF_OPEN
    success_rate: float
    failure_count: int
    total_calls: int


class SystemMetrics(BaseModel):
    """系统指标"""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    websocket_connections: int


@router.get("/metrics/rate-limit", response_model=RateLimitMetrics)
async def get_rate_limit_metrics():
    """
    获取 Rate Limit 统计
    
    返回 API 限流使用情况
    """
    try:
        metrics = metrics_service.get_rate_limit_metrics()
        return RateLimitMetrics(**metrics)
    except Exception as exc:
        logger.error("Failed to gather rate limit metrics", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/metrics/circuit-breaker", response_model=List[CircuitBreakerStatus])
async def get_circuit_breaker_status():
    """
    获取熔断器状态
    
    返回所有跟随账户的熔断器状态
    """
    try:
        statuses = metrics_service.get_circuit_breaker_status()
        return [CircuitBreakerStatus(**status) for status in statuses]
    except Exception as exc:
        logger.error("Failed to gather circuit breaker status", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/metrics/performance", response_model=SystemMetrics)
async def get_performance_metrics():
    """
    获取系统性能指标
    
    返回 CPU、内存、磁盘使用率等
    """
    try:
        metrics = metrics_service.get_system_performance()
    except RuntimeError as exc:
        logger.error("psutil module is required for system metrics", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return SystemMetrics(
        cpu_percent=metrics["cpu_percent"],
        memory_percent=metrics["memory_percent"],
        disk_percent=metrics["disk_percent"],
        websocket_connections=ws_manager.get_connection_count()
    )


@router.get("/metrics/system")
async def get_system_info():
    """
    获取系统信息
    
    返回系统详细信息
    """
    try:
        import psutil
        import platform
    except ImportError as exc:
        raise HTTPException(status_code=500, detail="psutil module not available") from exc
    
    return {
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": platform.python_version(),
        "cpu_count": psutil.cpu_count(),
        "total_memory": psutil.virtual_memory().total,
        "available_memory": psutil.virtual_memory().available
    }
