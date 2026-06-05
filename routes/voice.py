# routes/voice.py

from fastapi import APIRouter, HTTPException, Request, Query
from fastapi.responses import Response

from services.twilio_service import (
    generate_voice_token,
    build_outgoing_call_twiml,
    build_current_forwarding_twiml,
)

from services.call_service import (
    create_call_log,
    update_call_log_status,
    get_call_log_by_sid,
    create_call_event,
    get_call_by_id,
    MISSED_STATUSES,
)

from services.patient_service import find_patient_by_phone
from services.websocket_manager import websocket_manager
from services.notification_service import (
    send_gchat_missed_call_alert,
    log_notification_result,
)

from utils.phone import normalize_phone


router = APIRouter(prefix="/voice", tags=["Voice"])


@router.get("/token")
def get_voice_token(identity: str = Query("scanx_web_dialer")):
    """
    Frontend calls this to get Twilio Voice SDK token.
    """

    try:
        token = generate_voice_token(identity)

        return {
            "identity": identity,
            "token": token,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/outgoing")
async def outgoing_call(request: Request):
    """
    Twilio calls this when browser Twilio Voice SDK starts an outgoing call.

    Expected params from frontend SDK:
    - to
    - staff_phone optional
    - appointment_id optional
    """

    form = await request.form()

    to_number = form.get("to")
    staff_phone = form.get("staff_phone")
    appointment_id = form.get("appointment_id")
    call_sid = form.get("CallSid")

    if not to_number:
        response = Response(
            content="<Response><Say>Destination number is missing.</Say><Hangup/></Response>",
            media_type="application/xml",
        )
        return response

    normalized_to = normalize_phone(to_number)

    # Create call log for outgoing call
    call_log_id = create_call_log(
        patient_number=normalized_to,
        direction="outbound",
        call_sid=call_sid,
        status="initiated",
        appointment_id=appointment_id,
        staff_phone=staff_phone,
    )

    create_call_event(
        call_log_id=call_log_id,
        twilio_call_sid=call_sid,
        event_type="outgoing_initiated",
        event_payload=dict(form),
    )

    await websocket_manager.broadcast_call_event(
        "outgoing_call_started",
        {
            "call_log_id": call_log_id,
            "phone": normalized_to,
            "status": "initiated",
        },
    )

    twiml = build_outgoing_call_twiml(normalized_to)

    return Response(content=twiml, media_type="application/xml")


@router.post("/incoming")
async def incoming_call(request: Request):
    """
    Twilio incoming call webhook.

    For Phase 1:
    - Do NOT ring tablets.
    - Do NOT activate IVR.
    - Preserve current forwarding to CLIENT_FORWARD_NUMBER.
    - Log inbound call for visibility.
    """

    form = await request.form()

    from_number = form.get("From")
    call_sid = form.get("CallSid")

    normalized_from = normalize_phone(from_number)

    matched_patient = find_patient_by_phone(normalized_from) if normalized_from else None

    appointment_id = matched_patient.get("appointment_id") if matched_patient else None

    call_log_id = create_call_log(
        patient_number=normalized_from,
        direction="inbound",
        call_sid=call_sid,
        status="initiated",
        appointment_id=appointment_id,
        staff_phone=None,
    )

    create_call_event(
        call_log_id=call_log_id,
        twilio_call_sid=call_sid,
        event_type="incoming_initiated",
        event_payload=dict(form),
    )

    await websocket_manager.broadcast_call_event(
        "incoming_call_started",
        {
            "call_log_id": call_log_id,
            "phone": normalized_from,
            "display_name": matched_patient.get("full_name") if matched_patient else "Unknown Caller",
            "is_known_patient": bool(matched_patient),
            "status": "initiated",
        },
    )

    twiml = build_current_forwarding_twiml()

    return Response(content=twiml, media_type="application/xml")


@router.post("/status")
async def voice_status(request: Request):
    """
    Twilio status callback endpoint.

    Handles both outgoing and incoming call status updates.
    """

    form = await request.form()

    call_sid = form.get("CallSid")
    call_status = form.get("CallStatus") or form.get("DialCallStatus") or "unknown"
    duration_raw = form.get("CallDuration") or form.get("DialCallDuration") or 0

    try:
        duration = int(duration_raw)
    except Exception:
        duration = 0

    if not call_sid:
        return {"ok": False, "reason": "Missing CallSid"}

    existing_call = get_call_log_by_sid(call_sid)

    updated_call = update_call_log_status(
        call_sid=call_sid,
        status=call_status,
        duration=duration,
    )

    call_log_id = None

    if updated_call:
        call_log_id = updated_call.get("id")
    elif existing_call:
        call_log_id = existing_call.get("id")

    create_call_event(
        call_log_id=call_log_id,
        twilio_call_sid=call_sid,
        event_type=call_status,
        event_payload=dict(form),
    )

    call_data = get_call_by_id(call_log_id) if call_log_id else None

    await websocket_manager.broadcast_call_event(
        "call_status_changed",
        {
            "call_log_id": call_log_id,
            "call_sid": call_sid,
            "status": call_status,
            "duration": duration,
            "call": call_data,
        },
    )

    # Missed call logic
    if call_status.lower() in MISSED_STATUSES and call_data:
        await websocket_manager.broadcast_call_event(
            "missed_call",
            {
                "call_log_id": call_log_id,
                "phone": call_data.get("patient_number"),
                "display_name": call_data.get("display_name", "Unknown Caller"),
                "status": call_status,
                "call": call_data,
            },
        )

        notification_result = await send_gchat_missed_call_alert(call_data)

        log_notification_result(
            call_log_id=call_log_id,
            notification_type="missed_call_gchat",
            destination="google_chat",
            status="sent" if notification_result.get("sent") else "failed",
            payload=notification_result.get("payload") or notification_result,
            error_message=notification_result.get("error") or notification_result.get("reason"),
        )

        await websocket_manager.broadcast_call_event(
            "missed_call_notification_sent",
            {
                "call_log_id": call_log_id,
                "destination": "google_chat",
                "status": "sent" if notification_result.get("sent") else "failed",
                "result": notification_result,
            },
        )

    return {
        "ok": True,
        "call_sid": call_sid,
        "status": call_status,
        "duration": duration,
    }