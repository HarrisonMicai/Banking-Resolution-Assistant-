
from typing import Literal
import traceback

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.rag.answer_service import GroundedAnswerService


router = APIRouter(prefix="/answers", tags=["Grounded Answers"])


# --------------------------------------------------
# REQUEST MODEL
# --------------------------------------------------

class GroundedAnswerRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    user_access: Literal["Public", "Internal", "Restricted"] = "Internal"
    top_k: int = Field(default=5, ge=1, le=20)


# --------------------------------------------------
# RESPONSE MODELS
# --------------------------------------------------

class CitationResponse(BaseModel):
    source_id: str
    title: str
    section: str
    version: str


class GroundedAnswerResponse(BaseModel):
    answer: str
    supported: bool
    confidence: Literal["high", "medium", "low"]
    citations: list[CitationResponse]
    limitations: list[str]


# --------------------------------------------------
# SERVICE
# --------------------------------------------------

_service = None


def get_answer_service():
    global _service

    if _service is None:
        _service = GroundedAnswerService()

    return _service


# --------------------------------------------------
# ENDPOINT
# --------------------------------------------------

@router.post(
    "/grounded",
    response_model=GroundedAnswerResponse
)
def generate_grounded_answer(
    payload: GroundedAnswerRequest,
    request: Request
):
    try:
        print("\n========== GROUNDED ANSWER REQUEST ==========", flush=True)

        service = get_answer_service()

        print("Answer service initialized.", flush=True)
        print("Calling service.answer()...", flush=True)

        result = service.answer(
            question=payload.question,
            user_access=payload.user_access,
            top_k=payload.top_k
        )

        print("Service returned successfully.", flush=True)
        print("============================================\n", flush=True)

        return result

    except Exception as exc:
        print("\n========== GROUNDED ANSWER FAILURE ==========", flush=True)
        traceback.print_exc()
        print(f"Exception type: {type(exc).__name__}", flush=True)
        print(f"Exception message: {exc}", flush=True)
        print("=============================================\n", flush=True)

        raise