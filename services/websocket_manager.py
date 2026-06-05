# services/websocket_manager.py

from fastapi import WebSocket
from typing import Dict, List
import json
import asyncio


class WebSocketManager:
    """
    Manages active WebSocket connections.

    Phase 1:
    - Stores connections in memory.
    - Good for local development and Cloud Run single-instance setup.

    Future:
    - If Cloud Run scales to multiple instances, use Redis Pub/Sub or Google Pub/Sub
      behind this manager to broadcast events across instances.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_meta: Dict[WebSocket, dict] = {}

    async def connect(self, websocket: WebSocket, meta: dict | None = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        self.connection_meta[websocket] = meta or {}

        await self.send_personal_message(
            websocket,
            {
                "type": "connection_established",
                "message": "Connected to ScanX Web Dialer live updates.",
                "meta": meta or {},
            },
        )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

        if websocket in self.connection_meta:
            del self.connection_meta[websocket]

    async def send_personal_message(self, websocket: WebSocket, message: dict):
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception:
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """
        Broadcasts message to all connected dashboard clients.
        """

        disconnected = []

        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, default=str))
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    async def broadcast_call_event(
        self,
        event_type: str,
        payload: dict,
    ):
        await self.broadcast(
            {
                "type": event_type,
                "payload": payload,
            }
        )

    def get_connection_count(self) -> int:
        return len(self.active_connections)

    def get_connections_meta(self) -> list[dict]:
        return list(self.connection_meta.values())


websocket_manager = WebSocketManager()