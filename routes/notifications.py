# routes/notifications.py

from fastapi import APIRouter
from services.notification_service import send_gchat_missed_call_alert

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.post("/test-gchat")
async def test_gchat_notification():
    test_call = {
        "display_name": "Test Patient",
        "patient_number": "+15551234567",
        "status": "no-answer",
        "created_at": "Test Time",
    }

    result = await send_gchat_missed_call_alert(test_call)

    return result