# routes/patients.py

from fastapi import APIRouter, Query
from services.patient_service import (
    search_patients,
    find_patient_by_phone,
    get_patient_call_history_by_phone,
)

router = APIRouter(prefix="/patients", tags=["Patients"])


@router.get("/search")
def search_patients_api(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100),
):
    results = search_patients(q, limit)

    return {
        "query": q,
        "count": len(results),
        "results": results,
    }


@router.get("/lookup-by-phone")
def lookup_patient_by_phone(phone: str):
    patient = find_patient_by_phone(phone)

    if not patient:
        return {
            "found": False,
            "display_name": "Unknown Caller",
            "phone": phone,
            "patient": None,
        }

    return {
        "found": True,
        "display_name": patient.get("full_name") or "Unknown Caller",
        "phone": phone,
        "patient": patient,
    }


@router.get("/call-history")
def patient_call_history(phone: str, limit: int = Query(50, ge=1, le=200)):
    return {
        "phone": phone,
        "history": get_patient_call_history_by_phone(phone, limit),
    }