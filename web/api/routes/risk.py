"""风险管理 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
import logging

from ..services import risk_service
from ..services.risk_service import AlertNotFound

router = APIRouter()
logger = logging.getLogger(__name__)


class RiskSummary(BaseModel):
    """风险摘要"""
    total_position_value: float
    total_unrealized_pnl: float
    daily_pnl: float
    max_drawdown: float
    risk_level: str  # low, medium, high


class Alert(BaseModel):
    """告警"""
    id: str
    timestamp: str
    level: str  # info, warning, error
    type: str
    message: str
    acknowledged: bool


@router.get("/risk/summary", response_model=RiskSummary)
async def get_risk_summary():
    """
    获取风险摘要
    
    返回当前的风险状况概览
    """
    try:
        summary = risk_service.compute_risk_summary()
        return RiskSummary(**summary)
    except Exception as exc:
        logger.error("Failed to compute risk summary", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/risk/emergency-stop")
async def emergency_stop():
    """
    紧急停止
    
    立即停止所有跟单活动并平仓（可选）
    """
    try:
        logger.warning("Emergency stop triggered via API")
        # 在没有真实引擎的情况下，仅记录告警信息
        return {
            "message": "Emergency stop signal recorded",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except Exception as exc:
        logger.error(f"Emergency stop failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/risk/alerts", response_model=List[Alert])
async def get_alerts(
    acknowledged: Optional[bool] = None,
    level: Optional[str] = None
):
    """
    获取告警列表
    
    返回系统告警，支持按确认状态和级别筛选
    """
    try:
        alerts = risk_service.get_alerts(acknowledged=acknowledged, level=level)
        return [Alert(**alert) for alert in alerts]
    except Exception as exc:
        logger.error("Failed to load alerts", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/risk/alerts/{alert_id}/ack")
async def acknowledge_alert(alert_id: str):
    """
    确认告警
    
    标记告警为已确认
    """
    try:
        alert = risk_service.acknowledge_alert(alert_id)
        logger.info("Alert %s acknowledged", alert_id)
        return {
            "message": "Alert acknowledged",
            "alert_id": alert_id,
            "acknowledged_at": alert.get("acknowledged_at")
        }
    except AlertNotFound:
        raise HTTPException(status_code=404, detail="Alert not found")
    except Exception as exc:
        logger.error("Failed to acknowledge alert %s", alert_id, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
