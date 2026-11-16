
import json

import pytest

from app.rag.answer_service import GroundedAnswerService


# --------------------------------------------------
# MOCK RETRIEVED EVIDENCE
# --------------------------------------------------

KB_002_EVIDENCE = {
    "text": (
        "Proposed compensation exceeding the applicable "
        "analyst authority threshold requires supervisor approval."
    ),
    "score": 0.82,
    "rerank_score": 0.75,
    "metadata": {
        "source_id": "KB-002",
        "title": "Escalation, Approval and Decision Authority Standard",
        "section_title": "3. Financial Redress Thresholds",
        "version": "2.1",
        "access_label": "Internal"
    }
}


IRRELEVANT_EVIDENCE = {
    "text": "This document describes general complaint handling procedures.",
    "score": 0.78,
    "rerank_score": 0.70,
    "metadata": {
        "source_id": "KB-001",
        "title": "Enterprise Complaint Management Policy",
        "section_title": "1. Purpose",
        "version": "3",
        "access_label": "Internal"
    }
}


# --------------------------------------------------
# MOCK RETRIEVAL SERVICE
# --------------------------------------------------

class FakeRetrievalService:
    def __init__(self, evidence):
        self.evidence = evidence

    def retrieve(
        self,
        query,
        top_k=5,
        document_type=None,
        version=None,
        access_label=None,
        rerank=False
    ):
        return [
            item for item in self.evidence
            if item["metadata"]["access_label"] == access_label
        ][:top_k]


# --------------------------------------------------
# MOCK GEMINI CLIENT
# --------------------------------------------------

class FakeResponse:
    def __init__(self, payload):
        self.text = json.dumps(payload)


class FakeModels:
    def __init__(self, payload):
        self.payload = payload

    def generate_content(self, model, contents):
        return FakeResponse(self.payload)


class FakeGeminiClient:
    def __init__(self, payload):
        self.models = FakeModels(payload)


# --------------------------------------------------
# TEST GA-001: SUPPORTED QUESTION
# --------------------------------------------------

def test_supported_question_returns_verified_citation():
    generated_answer = {
        "answer": (
            "Proposed compensation exceeding the applicable "
            "analyst authority threshold requires supervisor approval."
        ),
        "supported": True,
        "confidence": "high",
        "citations": [
            {
                "source_id": "KB-002",
                "section": "3. Financial Redress Thresholds"
            }
        ],
        "limitations": []
    }

    service = GroundedAnswerService(
        retrieval_service=FakeRetrievalService([KB_002_EVIDENCE]),
        client=FakeGeminiClient(generated_answer)
    )

    result = service.answer(
        "When does proposed compensation require supervisor approval?"
    )

    assert result["supported"] is True
    assert result["confidence"] == "high"
    assert len(result["citations"]) == 1
    assert result["citations"][0]["source_id"] == "KB-002"
    assert result["citations"][0]["title"] == (
        "Escalation, Approval and Decision Authority Standard"
    )


# --------------------------------------------------
# TEST GA-002: UNSUPPORTED QUESTION
# --------------------------------------------------

def test_unsupported_question_abstains():
    generated_answer = {
        "answer": (
            "I cannot provide a reliable answer based on the "
            "available approved evidence."
        ),
        "supported": False,
        "confidence": "low",
        "citations": [],
        "limitations": [
            "The supplied knowledge base does not provide current weather information."
        ]
    }

    service = GroundedAnswerService(
        retrieval_service=FakeRetrievalService([IRRELEVANT_EVIDENCE]),
        client=FakeGeminiClient(generated_answer)
    )

    result = service.answer(
        "What is the current weather in Reykjavik?"
    )

    assert result["supported"] is False
    assert result["confidence"] == "low"
    assert result["citations"] == []
    assert len(result["limitations"]) > 0


# --------------------------------------------------
# TEST GA-003: PARTIALLY SUPPORTED QUESTION
# --------------------------------------------------

def test_partially_supported_question_returns_limitation():
    generated_answer = {
        "answer": (
            "Proposed compensation exceeding the applicable "
            "analyst authority threshold requires supervisor approval."
        ),
        "supported": True,
        "confidence": "medium",
        "citations": [
            {
                "source_id": "KB-002",
                "section": "3. Financial Redress Thresholds"
            }
        ],
        "limitations": [
            "The supplied knowledge base does not provide current weather information."
        ]
    }

    service = GroundedAnswerService(
        retrieval_service=FakeRetrievalService([KB_002_EVIDENCE]),
        client=FakeGeminiClient(generated_answer)
    )

    result = service.answer(
        "When does proposed compensation require supervisor approval, "
        "and what is the current weather in Reykjavik?"
    )

    assert result["supported"] is True
    assert len(result["citations"]) == 1
    assert len(result["limitations"]) == 1
    assert "weather" in result["limitations"][0].lower()


# --------------------------------------------------
# ADDITIONAL TEST: REJECT UNVERIFIED CITATION
# --------------------------------------------------

def test_unverified_citation_causes_safe_abstention():
    generated_answer = {
        "answer": "The policy requires supervisor approval.",
        "supported": True,
        "confidence": "high",
        "citations": [
            {
                "source_id": "KB-999",
                "section": "Invented Section"
            }
        ],
        "limitations": []
    }

    service = GroundedAnswerService(
        retrieval_service=FakeRetrievalService([KB_002_EVIDENCE]),
        client=FakeGeminiClient(generated_answer)
    )

    result = service.answer(
        "When does proposed compensation require supervisor approval?"
    )

    assert result["supported"] is False
    assert result["citations"] == []
    assert "citation" in result["limitations"][0].lower()


# --------------------------------------------------
# ADDITIONAL TEST: EMPTY QUESTION
# --------------------------------------------------

def test_empty_question_raises_value_error():
    service = GroundedAnswerService(
        retrieval_service=FakeRetrievalService([]),
        client=FakeGeminiClient({})
    )

    with pytest.raises(ValueError):
        service.answer("")
