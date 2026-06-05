# routes/calls.py

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from services.call_service import (
    get_recent_calls,
    get_missed_calls,
    get_call_by_id,
    add_call_note,
    add_call_disposition,
)

router = APIRouter(prefix="/calls", tags=["Calls"])


class NoteRequest(BaseModel):
    note: str
    created_by: str | None = None


class DispositionRequest(BaseModel):
    disposition: str
    created_by: str | None = None


@router.get("/recent")
def recent_calls(limit: int = Query(50, ge=1, le=200)):
    results = get_recent_calls(limit)

    return {
        "count": len(results),
        "results": results,
    }


@router.get("/missed")
def missed_calls(limit: int = Query(50, ge=1, le=200)):
    results = get_missed_calls(limit)

    return {
        "count": len(results),
        "results": results,
    }


@router.get("/{call_id}")
def call_detail(call_id: int):
    call = get_call_by_id(call_id)

    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    return call


@router.post("/{call_id}/notes")
def create_call_note(call_id: int, payload: NoteRequest):
    call = get_call_by_id(call_id)

    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    note_id = add_call_note(
        call_log_id=call_id,
        note=payload.note,
        created_by=payload.created_by,
    )

    return {
        "status": "ok",
        "note_id": note_id,
    }


@router.post("/{call_id}/disposition")
def create_call_disposition(call_id: int, payload: DispositionRequest):
    call = get_call_by_id(call_id)

    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    disposition_id = add_call_disposition(
        call_log_id=call_id,
        disposition=payload.disposition,
        created_by=payload.created_by,
    )

    return {
        "status": "ok",
        "disposition_id": disposition_id,
    }