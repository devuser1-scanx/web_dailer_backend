# services/call_service.py

from sqlalchemy import text
from database import SessionLocal
from services.patient_service import find_patient_by_phone
from utils.phone import normalize_phone, phone_search_pattern


MISSED_STATUSES = {"no-answer", "busy", "failed", "canceled", "cancelled"}


def create_companion_tables_if_not_exists():
    """
    Creates only new dialer-specific companion tables.
    Does NOT modify existing clinics, patients, call_logs, or appointment tables.
    """

    sql = text("""
        CREATE TABLE IF NOT EXISTS dialer_call_events (
            id SERIAL PRIMARY KEY,
            call_log_id INTEGER REFERENCES call_logs(id),
            twilio_call_sid VARCHAR(100),
            event_type VARCHAR(50),
            event_payload JSONB,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS dialer_call_notifications (
            id SERIAL PRIMARY KEY,
            call_log_id INTEGER REFERENCES call_logs(id),
            notification_type VARCHAR(50),
            destination VARCHAR(255),
            status VARCHAR(50),
            payload JSONB,
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS dialer_call_notes (
            id SERIAL PRIMARY KEY,
            call_log_id INTEGER REFERENCES call_logs(id),
            note TEXT,
            created_by VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS dialer_call_dispositions (
            id SERIAL PRIMARY KEY,
            call_log_id INTEGER REFERENCES call_logs(id),
            disposition VARCHAR(100),
            created_by VARCHAR(100),
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS dialer_ivr_config (
            id SERIAL PRIMARY KEY,
            config_key VARCHAR(100) UNIQUE NOT NULL,
            config_value JSONB,
            active BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
    """)

    with SessionLocal() as db:
        db.execute(sql)
        db.commit()


def create_call_log(
    patient_number: str,
    direction: str,
    call_sid: str | None = None,
    status: str = "initiated",
    appointment_id: str | None = None,
    staff_phone: str | None = None,
) -> int:
    """
    Inserts into existing call_logs table.
    """

    normalized_number = normalize_phone(patient_number)

    sql = text("""
        INSERT INTO call_logs (
            appointment_id,
            staff_phone,
            patient_number,
            direction,
            call_sid,
            status,
            duration,
            created_at,
            updated_at
        )
        VALUES (
            :appointment_id,
            :staff_phone,
            :patient_number,
            :direction,
            :call_sid,
            :status,
            0,
            NOW(),
            NOW()
        )
        RETURNING id
    """)

    with SessionLocal() as db:
        call_log_id = db.execute(
            sql,
            {
                "appointment_id": appointment_id,
                "staff_phone": staff_phone,
                "patient_number": normalized_number,
                "direction": direction,
                "call_sid": call_sid,
                "status": status,
            },
        ).scalar()
        db.commit()

    return call_log_id


def update_call_log_status(
    call_sid: str,
    status: str,
    duration: int = 0,
) -> dict | None:
    """
    Updates existing call_logs status using Twilio call_sid.
    """

    sql = text("""
        UPDATE call_logs
        SET
            status = :status,
            duration = COALESCE(:duration, duration),
            updated_at = NOW()
        WHERE call_sid = :call_sid
        RETURNING *
    """)

    with SessionLocal() as db:
        row = db.execute(
            sql,
            {
                "call_sid": call_sid,
                "status": status,
                "duration": duration,
            },
        ).mappings().first()
        db.commit()

    return dict(row) if row else None


def get_call_log_by_sid(call_sid: str) -> dict | None:
    sql = text("""
        SELECT *
        FROM call_logs
        WHERE call_sid = :call_sid
        LIMIT 1
    """)

    with SessionLocal() as db:
        row = db.execute(sql, {"call_sid": call_sid}).mappings().first()

    return dict(row) if row else None


def create_call_event(
    call_log_id: int | None,
    twilio_call_sid: str | None,
    event_type: str,
    event_payload: dict,
):
    sql = text("""
        INSERT INTO dialer_call_events (
            call_log_id,
            twilio_call_sid,
            event_type,
            event_payload,
            created_at
        )
        VALUES (
            :call_log_id,
            :twilio_call_sid,
            :event_type,
            CAST(:event_payload AS JSONB),
            NOW()
        )
    """)

    import json

    with SessionLocal() as db:
        db.execute(
            sql,
            {
                "call_log_id": call_log_id,
                "twilio_call_sid": twilio_call_sid,
                "event_type": event_type,
                "event_payload": json.dumps(event_payload),
            },
        )
        db.commit()


def get_recent_calls(limit: int = 50) -> list[dict]:
    """
    Recent calls with patient name if matched.
    """

    sql = text("""
        SELECT
            cl.id,
            cl.appointment_id,
            cl.staff_phone,
            cl.patient_number,
            cl.direction,
            cl.call_sid,
            cl.status,
            cl.duration,
            cl.created_at,
            cl.updated_at,
            a.first_name,
            a.last_name,
            CONCAT_WS(' ', a.first_name, a.last_name) AS patient_name,
            a.email,
            a.appointment_type,
            a.clinic_id,
            a.location,
            a.calendar,
            c.name AS clinic_name
        FROM call_logs cl
        LEFT JOIN appointment a
            ON a.appointment_id = cl.appointment_id
            OR REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(a.phone, ''), '+', ''), '-', ''), ' ', ''), '(', '')
               ILIKE CONCAT('%', REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(cl.patient_number, ''), '+', ''), '-', ''), ' ', ''), '(', ''), '%')
        LEFT JOIN clinics c ON c.id = a.clinic_id
        ORDER BY cl.created_at DESC
        LIMIT :limit
    """)

    with SessionLocal() as db:
        rows = db.execute(sql, {"limit": limit}).mappings().all()

    return [_format_call_row(dict(row)) for row in rows]


def get_missed_calls(limit: int = 50) -> list[dict]:
    """
    Missed calls with patient name if known, otherwise Unknown Caller.
    """

    sql = text("""
        SELECT
            cl.id,
            cl.appointment_id,
            cl.staff_phone,
            cl.patient_number,
            cl.direction,
            cl.call_sid,
            cl.status,
            cl.duration,
            cl.created_at,
            cl.updated_at,
            a.first_name,
            a.last_name,
            CONCAT_WS(' ', a.first_name, a.last_name) AS patient_name,
            a.email,
            a.appointment_type,
            a.clinic_id,
            a.location,
            a.calendar,
            c.name AS clinic_name
        FROM call_logs cl
        LEFT JOIN appointment a
            ON a.appointment_id = cl.appointment_id
            OR REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(a.phone, ''), '+', ''), '-', ''), ' ', ''), '(', '')
               ILIKE CONCAT('%', REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(cl.patient_number, ''), '+', ''), '-', ''), ' ', ''), '(', ''), '%')
        LEFT JOIN clinics c ON c.id = a.clinic_id
        WHERE LOWER(COALESCE(cl.status, '')) IN ('no-answer', 'busy', 'failed', 'canceled', 'cancelled')
        ORDER BY cl.created_at DESC
        LIMIT :limit
    """)

    with SessionLocal() as db:
        rows = db.execute(sql, {"limit": limit}).mappings().all()

    return [_format_call_row(dict(row)) for row in rows]


def get_call_by_id(call_id: int) -> dict | None:
    sql = text("""
        SELECT
            cl.id,
            cl.appointment_id,
            cl.staff_phone,
            cl.patient_number,
            cl.direction,
            cl.call_sid,
            cl.status,
            cl.duration,
            cl.created_at,
            cl.updated_at,
            a.first_name,
            a.last_name,
            CONCAT_WS(' ', a.first_name, a.last_name) AS patient_name,
            a.email,
            a.appointment_type,
            a.clinic_id,
            a.location,
            a.calendar,
            c.name AS clinic_name
        FROM call_logs cl
        LEFT JOIN appointment a
            ON a.appointment_id = cl.appointment_id
            OR REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(a.phone, ''), '+', ''), '-', ''), ' ', ''), '(', '')
               ILIKE CONCAT('%', REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(cl.patient_number, ''), '+', ''), '-', ''), ' ', ''), '(', ''), '%')
        LEFT JOIN clinics c ON c.id = a.clinic_id
        WHERE cl.id = :call_id
        LIMIT 1
    """)

    with SessionLocal() as db:
        row = db.execute(sql, {"call_id": call_id}).mappings().first()

    return _format_call_row(dict(row)) if row else None


def add_call_note(call_log_id: int, note: str, created_by: str | None = None):
    sql = text("""
        INSERT INTO dialer_call_notes (
            call_log_id,
            note,
            created_by,
            created_at
        )
        VALUES (
            :call_log_id,
            :note,
            :created_by,
            NOW()
        )
        RETURNING id
    """)

    with SessionLocal() as db:
        note_id = db.execute(
            sql,
            {
                "call_log_id": call_log_id,
                "note": note,
                "created_by": created_by,
            },
        ).scalar()
        db.commit()

    return note_id


def add_call_disposition(
    call_log_id: int,
    disposition: str,
    created_by: str | None = None,
):
    sql = text("""
        INSERT INTO dialer_call_dispositions (
            call_log_id,
            disposition,
            created_by,
            created_at
        )
        VALUES (
            :call_log_id,
            :disposition,
            :created_by,
            NOW()
        )
        RETURNING id
    """)

    with SessionLocal() as db:
        disposition_id = db.execute(
            sql,
            {
                "call_log_id": call_log_id,
                "disposition": disposition,
                "created_by": created_by,
            },
        ).scalar()
        db.commit()

    return disposition_id


def _format_call_row(row: dict) -> dict:
    patient_name = row.get("patient_name")

    if patient_name:
        patient_name = patient_name.strip()

    row["display_name"] = patient_name if patient_name else "Unknown Caller"
    row["is_known_patient"] = bool(patient_name)
    row["is_missed"] = (row.get("status") or "").lower() in MISSED_STATUSES

    return row