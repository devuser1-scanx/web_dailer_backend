# routes/dashboard.py

from fastapi import APIRouter, Query
from services.dashboard_service import get_dashboard_summary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary")
def dashboard_summary(
    start_date: str | None = Query(
        default=None,
        description="Optional start date in YYYY-MM-DD format.",
    ),
    end_date: str | None = Query(
        default=None,
        description="Optional end date in YYYY-MM-DD format.",
    ),
):
    return get_dashboard_summary(start_date=start_date, end_date=end_date)