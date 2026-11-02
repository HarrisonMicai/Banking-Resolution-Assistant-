from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from app.core.dependencies.dependencies import check_database_health

router = APIRouter(prefix="/health", tags=["Health Checks"])


@router.get("/live", status_code=status.HTTP_200_OK)
def liveness_check():
    return {"status": "alive"}


@router.get("/ready", status_code=status.HTTP_200_OK)
def readiness_check():
    if not check_database_health():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "database": "disconnected"},
        )
    return {"status": "ready", "database": "connected"}