"""交易监控 API"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

from ..services import trade_service

router = APIRouter()
logger = logging.getLogger(__name__)


class Trade(BaseModel):
    """交易记录"""
    id: str
    timestamp: str
    account: str  # master or follower name
    symbol: str
    side: str
    quantity: float
    price: float
    status: str
    order_type: str
    position_side: str


class TradeStats(BaseModel):
    """交易统计"""
    total_trades: int
    successful_trades: int
    failed_trades: int
    success_rate: float
    total_volume: float


@router.get("/trades/recent", response_model=List[Trade])
async def get_recent_trades(
    limit: int = Query(default=50, le=200),
    account: Optional[str] = None
):
    """
    获取最近交易
    
    返回最近的交易记录，支持按账户筛选
    """
    try:
        trades = trade_service.list_recent_trades(limit=limit, account=account)
        return [Trade(**trade) for trade in trades]
    except Exception as exc:
        logger.error("Failed to load recent trades", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/trades/history", response_model=List[Trade])
async def get_trade_history(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    symbol: Optional[str] = None,
    account: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, le=200)
):
    """
    获取历史交易
    
    支持时间范围、交易对、账户筛选和分页
    """
    try:
        trades = trade_service.query_trade_history(
            start_time=start_time,
            end_time=end_time,
            symbol=symbol,
            account=account,
            page=page,
            page_size=page_size
        )
        return [Trade(**trade) for trade in trades]
    except Exception as exc:
        logger.error("Failed to query trade history", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/trades/stats", response_model=TradeStats)
async def get_trade_stats():
    """
    获取交易统计
    
    返回交易统计信息
    """
    try:
        stats = trade_service.get_trade_statistics()
        return TradeStats(**stats)
    except Exception as exc:
        logger.error("Failed to build trade stats", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/trades/{trade_id}")
async def get_trade_detail(trade_id: str):
    """
    获取交易详情
    
    返回指定交易的详细信息
    """
    try:
        trade = trade_service.get_trade_detail(trade_id)
    except Exception as exc:
        logger.error("Failed to get trade detail", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
    
    if not trade:
        raise HTTPException(status_code=404, detail="Trade not found")
    
    return trade
