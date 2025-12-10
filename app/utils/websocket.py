"""
WebSocket support for real-time updates.

Provides WebSocket endpoints for streaming price updates
and alert notifications.
"""

from fastapi import WebSocket, WebSocketDisconnect
from typing import Dict, Set
import json
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates.

    Handles client connections, disconnections, and message broadcasting.
    """

    def __init__(self):
        """Initialize connection manager."""
        # Active connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}

        # Stock subscriptions: stock_id -> set of user_ids
        self.stock_subscriptions: Dict[str, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Accept and register a new WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()

        self.active_connections[user_id].add(websocket)

        logger.info(f"WebSocket connected: user {user_id}")

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """
        Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection
            user_id: User ID
        """
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

        logger.info(f"WebSocket disconnected: user {user_id}")

    async def send_personal_message(self, message: dict, user_id: str) -> None:
        """
        Send message to a specific user's connections.

        Args:
            message: Message dict to send
            user_id: User ID
        """
        if user_id in self.active_connections:
            disconnected = set()

            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")
                    disconnected.add(connection)

            # Clean up disconnected connections
            for connection in disconnected:
                self.disconnect(connection, user_id)

    async def broadcast_to_stock_subscribers(
        self,
        message: dict,
        stock_id: str
    ) -> None:
        """
        Broadcast message to all users subscribed to a stock.

        Args:
            message: Message dict to send
            stock_id: Stock ID
        """
        if stock_id in self.stock_subscriptions:
            for user_id in self.stock_subscriptions[stock_id]:
                await self.send_personal_message(message, user_id)

    def subscribe_to_stock(self, user_id: str, stock_id: str) -> None:
        """
        Subscribe user to stock updates.

        Args:
            user_id: User ID
            stock_id: Stock ID
        """
        if stock_id not in self.stock_subscriptions:
            self.stock_subscriptions[stock_id] = set()

        self.stock_subscriptions[stock_id].add(user_id)

        logger.info(f"User {user_id} subscribed to stock {stock_id}")

    def unsubscribe_from_stock(self, user_id: str, stock_id: str) -> None:
        """
        Unsubscribe user from stock updates.

        Args:
            user_id: User ID
            stock_id: Stock ID
        """
        if stock_id in self.stock_subscriptions:
            self.stock_subscriptions[stock_id].discard(user_id)

            if not self.stock_subscriptions[stock_id]:
                del self.stock_subscriptions[stock_id]

        logger.info(f"User {user_id} unsubscribed from stock {stock_id}")


# Global connection manager instance
manager = ConnectionManager()
