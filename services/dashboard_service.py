# services/dashboard_service.py

from sqlalchemy import text
from database import SessionLocal


MISSED_STATUSES = ("no-answer", "busy", "failed", "canceled", "cancelled")


def get_dashboard_summary(
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict:
    """
    Returns business-friendly dashboard summary.

    If no date range is provided, it uses today's date.
    If start_date and end_date are provided, it filters between both dates.
    """

    date_filter_sql = """
        DATE(cl.created_at) BETWEEN
        COALESCE(CAST(:start_date AS DATE), CURRENT_DATE)
        AND
        COALESCE(CAST(:end_date AS DATE), COALESCE(CAST(:start_date AS DATE), CURRENT_DATE))
    """

    summary_sql = text(f"""
        SELECT
            COUNT(*) AS total_calls,

            COUNT(*) FILTER (
                WHERE LOWER(COALESCE(cl.direction, '')) = 'outbound'
            ) AS outgoing_calls,

            COUNT(*) FILTER (
                WHERE LOWER(COALESCE(cl.direction, '')) = 'inbound'
            ) AS incoming_calls,

            COUNT(*) FILTER (
                WHERE LOWER(COALESCE(cl.status, '')) IN ('no-answer', 'busy', 'failed', 'canceled', 'cancelled')
            ) AS missed_calls,

            COUNT(*) FILTER (
                WHERE LOWER(COALESCE(cl.status, '')) = 'completed'
            ) AS completed_calls,

            COUNT(*) FILTER (
                WHERE LOWER(COALESCE(cl.status, '')) IN ('failed', 'busy')
            ) AS failed_or_busy_calls,

            COUNT(*) FILTER (
                WHERE LOWER(COALESCE(cl.status, '')) = 'no-answer'
            ) AS no_answer_calls,

            COALESCE(ROUND(AVG(NULLIF(cl.duration, 0))), 0) AS average_duration_seconds

        FROM call_logs cl
        WHERE {date_filter_sql}
    """)

    recent_calls_sql = text(f"""
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
        WHERE {date_filter_sql}
        ORDER BY cl.created_at DESC
        LIMIT 10
    """)

    missed_calls_sql = text(f"""
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
        WHERE {date_filter_sql}
          AND LOWER(COALESCE(cl.status, '')) IN ('no-answer', 'busy', 'failed', 'canceled', 'cancelled')
        ORDER BY cl.created_at DESC
        LIMIT 10
    """)

    params = {
        "start_date": start_date,
        "end_date": end_date,
    }

    with SessionLocal() as db:
        summary = db.execute(summary_sql, params).mappings().first()
        recent_calls = db.execute(recent_calls_sql, params).mappings().all()
        missed_calls = db.execute(missed_calls_sql, params).mappings().all()

    summary_dict = dict(summary or {})

    return {
        "start_date": start_date or "today",
        "end_date": end_date or start_date or "today",
        "total_calls": int(summary_dict.get("total_calls") or 0),
        "outgoing_calls": int(summary_dict.get("outgoing_calls") or 0),
        "incoming_calls": int(summary_dict.get("incoming_calls") or 0),
        "missed_calls": int(summary_dict.get("missed_calls") or 0),
        "completed_calls": int(summary_dict.get("completed_calls") or 0),
        "failed_or_busy_calls": int(summary_dict.get("failed_or_busy_calls") or 0),
        "no_answer_calls": int(summary_dict.get("no_answer_calls") or 0),
        "average_duration_seconds": int(summary_dict.get("average_duration_seconds") or 0),
        "recent_calls": [_format_call_row(dict(row)) for row in recent_calls],
        "missed_calls_list": [_format_call_row(dict(row)) for row in missed_calls],
    }


def _format_call_row(row: dict) -> dict:
    patient_name = row.get("patient_name")

    if patient_name:
        patient_name = patient_name.strip()

    row["display_name"] = patient_name if patient_name else "Unknown Caller"
    row["is_known_patient"] = bool(patient_name)
    row["is_missed"] = (row.get("status") or "").lower() in MISSED_STATUSES

    return row