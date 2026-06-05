# services/patient_service.py

from sqlalchemy import text
from database import SessionLocal
from utils.phone import phone_search_pattern


def search_patients(query: str, limit: int = 20) -> list[dict]:
    """
    Search patients by:
    - first name
    - last name
    - full name
    - phone number
    - email

    We use appointment as the primary lookup source because it has phone, name, email,
    clinic_id, and appointment_id.
    """

    q = (query or "").strip()

    if not q:
        return []

    phone_digits = phone_search_pattern(q)

    sql = text("""
        SELECT
            a.appointment_id,
            a.first_name,
            a.last_name,
            CONCAT_WS(' ', a.first_name, a.last_name) AS full_name,
            a.phone,
            a.email,
            a.appointment_type,
            a.category,
            a.appointment_datetime,
            a.date,
            a.time,
            a.clinic_id,
            a.location,
            a.calendar,
            c.name AS clinic_name,
            c.city AS clinic_city
        FROM appointment a
        LEFT JOIN clinics c ON c.id = a.clinic_id
        WHERE
            a.first_name ILIKE :text_query
            OR a.last_name ILIKE :text_query
            OR CONCAT_WS(' ', a.first_name, a.last_name) ILIKE :text_query
            OR a.email ILIKE :text_query
            OR REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(a.phone, ''), '+', ''), '-', ''), ' ', ''), '(', '') ILIKE :phone_query
        ORDER BY
            COALESCE(a.appointment_datetime, a.date) DESC NULLS LAST,
            a.created_at DESC NULLS LAST
        LIMIT :limit
    """)

    with SessionLocal() as db:
        rows = db.execute(
            sql,
            {
                "text_query": f"%{q}%",
                "phone_query": f"%{phone_digits or q}%",
                "limit": limit,
            },
        ).mappings().all()

    return [dict(row) for row in rows]


def find_patient_by_phone(phone: str) -> dict | None:
    """
    Match caller number to the most recent/upcoming appointment.

    Used for:
    - missed call identification
    - incoming caller name display
    - patient call history mapping
    """

    phone_digits = phone_search_pattern(phone)

    if not phone_digits:
        return None

    sql = text("""
        SELECT
            a.appointment_id,
            a.first_name,
            a.last_name,
            CONCAT_WS(' ', a.first_name, a.last_name) AS full_name,
            a.phone,
            a.email,
            a.appointment_type,
            a.appointment_datetime,
            a.date,
            a.time,
            a.clinic_id,
            a.location,
            a.calendar,
            c.name AS clinic_name,
            c.city AS clinic_city
        FROM appointment a
        LEFT JOIN clinics c ON c.id = a.clinic_id
        WHERE
            REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(a.phone, ''), '+', ''), '-', ''), ' ', ''), '(', '')
            ILIKE :phone_query
        ORDER BY
            CASE
                WHEN COALESCE(a.appointment_datetime, a.date) >= NOW() THEN 0
                ELSE 1
            END,
            COALESCE(a.appointment_datetime, a.date) DESC NULLS LAST,
            a.created_at DESC NULLS LAST
        LIMIT 1
    """)

    with SessionLocal() as db:
        row = db.execute(
            sql,
            {
                "phone_query": f"%{phone_digits}%",
            },
        ).mappings().first()

    return dict(row) if row else None


def get_patient_call_history_by_phone(phone: str, limit: int = 50) -> list[dict]:
    """
    Get call history for a patient using phone number.

    Since call_logs has patient_number, this is the safest first version.
    """

    phone_digits = phone_search_pattern(phone)

    if not phone_digits:
        return []

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
               ILIKE :phone_query
        LEFT JOIN clinics c ON c.id = a.clinic_id
        WHERE
            REPLACE(REPLACE(REPLACE(REPLACE(COALESCE(cl.patient_number, ''), '+', ''), '-', ''), ' ', ''), '(', '')
            ILIKE :phone_query
        ORDER BY cl.created_at DESC
        LIMIT :limit
    """)

    with SessionLocal() as db:
        rows = db.execute(
            sql,
            {
                "phone_query": f"%{phone_digits}%",
                "limit": limit,
            },
        ).mappings().all()

    return [dict(row) for row in rows]