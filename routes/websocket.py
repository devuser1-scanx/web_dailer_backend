    # routes/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from services.websocket_manager import websocket_manager

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws/calls")
async def calls_websocket(
    websocket: WebSocket,
    client_id: str | None = Query(default=None),
    clinic_id: str | None = Query(default=None),
):
    """
    WebSocket endpoint for live call dashboard updates.

    Example frontend URL:
    ws://localhost:5000/ws/calls?client_id=dashboard_1&clinic_id=1
    """

    meta = {
        "client_id": client_id,
        "clinic_id": clinic_id,
    }

    await websocket_manager.connect(websocket, meta)

    try:
        while True:
            data = await websocket.receive_text()

            # Basic heartbeat support
            if data == "ping":
                await websocket_manager.send_personal_message(
                    websocket,
                    {
                        "type": "pong",
                        "message": "alive",
                    },
                )

    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)

    except Exception:
        websocket_manager.disconnect(websocket)


@router.get("/ws/status")
def websocket_status():
    """
    Simple HTTP endpoint to check active WebSocket clients.
    """

    return {
        "active_connections": websocket_manager.get_connection_count(),
        "clients": websocket_manager.get_connections_meta(),
    }