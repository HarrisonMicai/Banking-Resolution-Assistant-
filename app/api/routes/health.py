from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.dependencies.dependencies import check_database_health
from app.schemas.health_schema import LivenessResponse, ReadinessResponse

router = APIRouter(prefix="/health", tags=["Health Checks"])


@router.get("/live", response_model=LivenessResponse, status_code=status.HTTP_200_OK)
def liveness_check():
    return {"status": "alive"}


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ReadinessResponse}},
    status_code=status.HTTP_200_OK,
)
def readiness_check():
    if not check_database_health():
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "database": "disconnected"},
        )
    return {"status": "ready", "database": "connected"}