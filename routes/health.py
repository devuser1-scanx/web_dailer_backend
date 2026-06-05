from fastapi import APIRouter
from database import test_db_connection

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check():
    return {
        "status": "ok",
        "service": "ScanX Web Dialer Backend",
    }


@router.get("/db")
def database_health_check():
    try:
        is_connected = test_db_connection()

        return {
            "status": "ok" if is_connected else "error",
            "database": "connected" if is_connected else "not_connected",
        }

    except Exception as e:
        return {
            "status": "error",
            "database": "not_connected",
            "error": str(e),
        }