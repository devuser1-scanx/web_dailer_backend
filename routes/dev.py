# routes/dev.py

from fastapi import APIRouter
from services.websocket_manager import websocket_manager

router = APIRouter(prefix="/dev", tags=["Development"])


@router.post("/broadcast-test")
async def broadcast_test():
    await websocket_manager.broadcast_call_event(
        "test_event",
        {
            "message": "Hello from backend",
            "status": "ok",
        },
    )

    return {
        "status": "broadcasted",
    }