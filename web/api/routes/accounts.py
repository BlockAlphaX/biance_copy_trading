"""账户管理 API"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List
import logging

from ..services import account_service

router = APIRouter()
logger = logging.getLogger(__name__)


class AccountInfo(BaseModel):
    """账户信息"""
    name: str
    type: str  # master or follower
    balance: float
    available_balance: float
    leverage: int
    margin_type: str
    position_mode: str
    enabled: bool


class Position(BaseModel):
    """持仓信息"""
    symbol: str
    side: str
    size: float
    entry_price: float
    mark_price: float
    unrealized_pnl: float
    leverage: int


class LeverageUpdate(BaseModel):
    """杠杆更新请求"""
    leverage: int


@router.get("/accounts", response_model=List[AccountInfo])
async def get_accounts():
    """
    获取所有账户信息
    
    返回主账户和所有跟随账户的信息
    """
    try:
        accounts = account_service.list_accounts()
        return [AccountInfo(**account) for account in accounts]
    except Exception as exc:
        logger.error("Failed to load account list", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/accounts/{name}/balance")
async def get_account_balance(name: str):
    """
    获取账户余额
    
    返回指定账户的余额信息
    """
    try:
        return account_service.get_account_balance(name)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Account '{name}' not found")
    except Exception as exc:
        logger.error("Failed to fetch balance for %s", name, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/accounts/{name}/positions", response_model=List[Position])
async def get_account_positions(name: str):
    """
    获取账户持仓
    
    返回指定账户的所有持仓信息
    """
    try:
        positions = account_service.list_positions(name)
        return [Position(**position) for position in positions]
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Account '{name}' not found")
    except Exception as exc:
        logger.error("Failed to fetch positions for %s", name, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/accounts/{name}/leverage")
async def set_account_leverage(name: str, leverage_update: LeverageUpdate):
    """
    设置账户杠杆
    
    更新指定账户的杠杆倍数
    """
    try:
        account = account_service.update_leverage(name, leverage_update.leverage)
        logger.info("Leverage for %s set to %sx", name, leverage_update.leverage)
        return {
            "message": f"Leverage updated successfully for {name}",
            "leverage": account["leverage"]
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Account '{name}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        logger.error("Failed to set leverage for %s", name, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/accounts/{name}/enable")
async def toggle_account(name: str, enabled: bool):
    """
    启用/禁用账户
    
    启用或禁用跟随账户的跟单功能
    """
    try:
        account = account_service.set_account_enabled(name, enabled)
        logger.info("Account %s %s", name, "enabled" if enabled else "disabled")
        return {
            "message": f"Account {name} {'enabled' if enabled else 'disabled'} successfully",
            "enabled": account["enabled"]
        }
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Account '{name}' not found")
    except Exception as exc:
        logger.error("Failed to toggle account %s", name, exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))
