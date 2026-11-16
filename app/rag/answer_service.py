
"""
Grounded answer service.

Retrieves approved evidence, generates an answer using that evidence only,
and validates every citation against the retrieved chunks.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai

from app.rag.citation import format_citations
from app.rag.retrieval_policy import get_permitted_labels
from app.rag.retrieval_service import RetrievalService


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GENERATION_MODEL = os.getenv(
    "GEMINI_GENERATION_MODEL",
    "gemini-3.8-flash"
)

MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.35"))


class GroundedAnswerService:
    def __init__(
        self,
        retrieval_service=None,
        client=None,
        model=GENERATION_MODEL,
        min_similarity=MIN_SIMILARITY
    ):
        self.retrieval_service = (
            retrieval_service or RetrievalService()
        )
        self.client = client or genai.Client()
        self.model = model
        self.min_similarity = min_similarity

    def _retrieve_evidence(self, question, user_access, top_k):
        """
        Retrieve only access labels permitted for the user's access level.

        RetrievalService currently accepts one exact access_label at a time,
        so retrieve each permitted label and combine the results.
        """
        permitted_labels = get_permitted_labels(user_access)

        combined_results = []
        seen_chunks = set()

        for access_label in permitted_labels:
            results = self.retrieval_service.retrieve(
                query=question,
                top_k=top_k,
                access_label=access_label,
                rerank=True
            )

            for result in results:
                metadata = result.get("metadata", {})

                chunk_key = (
                    metadata.get("source_id"),
                    metadata.get("chunk_index"),
                    result.get("text")
                )

                if chunk_key not in seen_chunks:
                    seen_chunks.add(chunk_key)
                    combined_results.append(result)

        combined_results.sort(
            key=lambda item: item.get(
                "rerank_score",
                item.get("score", 0)
            ),
            reverse=True
        )

        return combined_results[:top_k]

    def _build_prompt(self, question, evidence):
        evidence_payload = []

        for index, item in enumerate(evidence, start=1):
            metadata = item.get("metadata", {})

            evidence_payload.append({
                "evidence_id": index,
                "text": item.get("text", ""),
                "source_id": metadata.get("source_id"),
                "title": metadata.get("title"),
                "section": (
                    metadata.get("section_title")
                    or metadata.get("section")
                ),
                "version": metadata.get("version"),
                "score": item.get("score")
            })

        return f"""
You are an enterprise Banking Complaint Resolution Assistant.

Answer the user's question using ONLY the retrieved evidence below.

STRICT RULES:
1. Do not use outside knowledge or assumptions.
2. Do not invent policy requirements, thresholds, dates, or procedures.
3. Every factual policy statement must be supported by retrieved evidence.
4. Cite only source IDs and sections explicitly present in the evidence.
5. If the evidence does not support the question, abstain.
6. If only part of a multi-part question is supported, answer only that
   portion and explain the unsupported portion in limitations.
7. Keep the answer concise and professional.

Return valid JSON only. Do not use Markdown fences.

Required JSON structure:
{{
    "answer": "Your answer",
    "supported": true,
    "confidence": "high",
    "citations": [
        {{
            "source_id": "KB-002",
            "section": "Exact section title from evidence"
        }}
    ],
    "limitations": []
}}

Confidence must be "high", "medium", or "low".

For unsupported questions:
- supported must be false
- confidence must be low
- citations must be an empty array
- limitations must explain that the supplied evidence is insufficient

For partially supported questions:
- answer only the supported portion
- supported must be true if a meaningful portion is supported
- cite the supporting evidence
- explain the unsupported portion in limitations

USER QUESTION:
{question}

RETRIEVED EVIDENCE:
{json.dumps(evidence_payload, indent=2)}
"""

    @staticmethod
    def _abstain(reason):
        return {
            "answer": (
                "I cannot provide a reliable answer based on the "
                "available approved evidence."
            ),
            "supported": False,
            "confidence": "low",
            "citations": [],
            "limitations": [reason]
        }

    def answer(self, question, user_access="Internal", top_k=5):
        if not isinstance(question, str) or not question.strip():
            raise ValueError("Question must be a non-empty string.")

        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
            raise ValueError("top_k must be a positive integer.")

        evidence = self._retrieve_evidence(
            question=question.strip(),
            user_access=user_access,
            top_k=top_k
        )

        if not evidence:
            return self._abstain(
                "No approved evidence was retrieved for this question."
            )

        best_score = max(
            item.get("score", 0)
            for item in evidence
        )

        if best_score < self.min_similarity:
            return self._abstain(
                "Retrieved evidence did not meet the minimum similarity "
                "threshold."
            )

        prompt = self._build_prompt(question.strip(), evidence)

        response = self.client.models.generate_content(
            model=self.model,
            contents=prompt
        )

        try:
            result = json.loads(response.text)
        except (json.JSONDecodeError, TypeError):
            return self._abstain(
                "The answer generator did not return valid JSON."
            )

        required_fields = {
            "answer",
            "supported",
            "citations",
            "limitations"
        }

        if not isinstance(result, dict) or not required_fields.issubset(result):
            return self._abstain(
                "The generated response did not match the required structure."
            )

        if (
            not isinstance(result["answer"], str)
            or not isinstance(result["supported"], bool)
            or not isinstance(result["citations"], list)
            or not isinstance(result["limitations"], list)
        ):
            return self._abstain(
                "The generated response contained invalid field types."
            )

        if not result["supported"]:
            result["citations"] = []
            result["confidence"] = "low"
            return result

        try:
            result["citations"] = format_citations(
                result["citations"],
                evidence
            )
        except ValueError:
            return self._abstain(
                "A generated citation could not be verified against "
                "the retrieved evidence."
            )

        confidence = result.get("confidence", "medium").lower()

        if confidence not in {"high", "medium", "low"}:
            confidence = "medium"

        result["confidence"] = confidence

        return result
