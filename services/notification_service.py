# services/notification_service.py

from sqlalchemy import text
from database import SessionLocal
from config import (
    ENABLE_GCHAT_MISSED_CALL_ALERTS,
    GCHAT_MISSED_CALL_WEBHOOK_URL,
)
import httpx
import json


def build_missed_call_message(call_data: dict) -> dict:
    """
    Builds Google Chat message payload for missed call alerts.
    """

    display_name = call_data.get("display_name") or "Unknown Caller"
    phone = call_data.get("patient_number") or call_data.get("phone") or "N/A"
    status = call_data.get("status") or "missed"
    created_at = call_data.get("created_at") or "N/A"

    text = (
        "📞 *Missed Call Alert*\n\n"
        f"*Caller:* {display_name}\n"
        f"*Phone:* {phone}\n"
        f"*Status:* {status}\n"
        f"*Time:* {created_at}\n\n"
        "Please review and call back if needed."
    )

    return {
        "text": text
    }


async def send_gchat_missed_call_alert(call_data: dict) -> dict:
    """
    Sends missed call alert to Google Chat webhook if configured.
    """

    if not ENABLE_GCHAT_MISSED_CALL_ALERTS:
        return {
            "sent": False,
            "reason": "Google Chat missed call alerts disabled",
        }

    if not GCHAT_MISSED_CALL_WEBHOOK_URL:
        return {
            "sent": False,
            "reason": "GCHAT_MISSED_CALL_WEBHOOK_URL not configured",
        }

    payload = build_missed_call_message(call_data)

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                GCHAT_MISSED_CALL_WEBHOOK_URL,
                json=payload,
            )

        return {
            "sent": response.status_code >= 200 and response.status_code < 300,
            "status_code": response.status_code,
            "response_text": response.text,
            "payload": payload,
        }

    except Exception as e:
        return {
            "sent": False,
            "error": str(e),
            "payload": payload,
        }


def log_notification_result(
    call_log_id: int | None,
    notification_type: str,
    destination: str,
    status: str,
    payload: dict | None = None,
    error_message: str | None = None,
):
    """
    Saves notification send attempt into dialer_call_notifications.
    """

    sql = text("""
        INSERT INTO dialer_call_notifications (
            call_log_id,
            notification_type,
            destination,
            status,
            payload,
            error_message,
            sent_at,
            created_at
        )
        VALUES (
            :call_log_id,
            :notification_type,
            :destination,
            :status,
            CAST(:payload AS JSONB),
            :error_message,
            CASE WHEN :status = 'sent' THEN NOW() ELSE NULL END,
            NOW()
        )
    """)

    with SessionLocal() as db:
        db.execute(
            sql,
            {
                "call_log_id": call_log_id,
                "notification_type": notification_type,
                "destination": destination,
                "status": status,
                "payload": json.dumps(payload or {}),
                "error_message": error_message,
            },
        )
        db.commit()