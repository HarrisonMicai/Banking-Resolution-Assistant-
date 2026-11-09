from typing import Literal

from pydantic import BaseModel


class LivenessResponse(BaseModel):
    status: Literal["alive"]


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not ready"]
    database: Literal["connected", "disconnected"]
