"""WebSocket 管理器"""

import json
import logging
from typing import List, Dict, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketManager:
    """WebSocket 连接管理器"""
    
    def __init__(self):
        # 活跃的 WebSocket 连接
        self.active_connections: List[WebSocket] = []
        # 订阅管理：{channel: [websocket1, websocket2, ...]}
        self.subscriptions: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket):
        """接受新的 WebSocket 连接"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection. Total: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """断开 WebSocket 连接"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        # 从所有订阅中移除
        for channel in self.subscriptions:
            if websocket in self.subscriptions[channel]:
                self.subscriptions[channel].remove(websocket)
        
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")
    
    def subscribe(self, websocket: WebSocket, channel: str):
        """订阅频道"""
        if channel not in self.subscriptions:
            self.subscriptions[channel] = []
        
        if websocket not in self.subscriptions[channel]:
            self.subscriptions[channel].append(websocket)
            logger.info(f"WebSocket subscribed to channel: {channel}")
    
    def unsubscribe(self, websocket: WebSocket, channel: str):
        """取消订阅频道"""
        if channel in self.subscriptions and websocket in self.subscriptions[channel]:
            self.subscriptions[channel].remove(websocket)
            logger.info(f"WebSocket unsubscribed from channel: {channel}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """发送个人消息"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Error sending personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """广播消息给所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_to_channel(self, channel: str, message: Dict[str, Any]):
        """广播消息给特定频道的订阅者"""
        if channel not in self.subscriptions:
            return
        
        disconnected = []
        for connection in self.subscriptions[channel]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to channel {channel}: {e}")
                disconnected.append(connection)
        
        # 清理断开的连接
        for connection in disconnected:
            self.disconnect(connection)
    
    def get_connection_count(self) -> int:
        """获取活跃连接数"""
        return len(self.active_connections)
    
    def get_channel_subscribers(self, channel: str) -> int:
        """获取频道订阅者数量"""
        return len(self.subscriptions.get(channel, []))
