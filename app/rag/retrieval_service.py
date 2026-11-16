
import os
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env", override=True)

CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
COLLECTION_NAME = "banking_complaints"

EMBEDDING_MODEL = "gemini-embedding-001"
EMBEDDING_DIMENSIONS = 768


class RetrievalService:
    """Semantic retrieval service for banking policy evidence."""

    def __init__(self, collection=None, embedding_client=None):
        self.embedding_client = embedding_client or genai.Client(
            api_key=os.getenv("GOOGLE_API_KEY")
        )

        if collection is not None:
            self.collection = collection
        else:
            self.chroma_client = chromadb.PersistentClient(
                path=str(CHROMA_DIR)
            )
            self.collection = self.chroma_client.get_collection(
                name=COLLECTION_NAME
            )

    def _embed_query(self, query: str) -> list[float]:
        """Convert a user query into a Gemini query embedding."""

        response = self.embedding_client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=query,
            config=types.EmbedContentConfig(
                task_type="RETRIEVAL_QUERY",
                output_dimensionality=EMBEDDING_DIMENSIONS
            )
        )

        return response.embeddings[0].values
    
    def _build_metadata_filter(
        self,
        document_type=None,
        version=None,
        access_label=None
    ):
        """Build ChromaDB metadata filters."""

        conditions = [
            {"status": {"$eq": "Approved"}}
        ]

        if document_type:
            conditions.append({
                "document_type": {"$eq": document_type}
            })

        if version:
            conditions.append({
                "version": {"$eq": str(version)}
            })

        if access_label:
            conditions.append({
                "access_label": {"$eq": access_label}
            })

        if len(conditions) == 1:
            return conditions[0]

        return {"$and": conditions}


    
    def _tokenize(self, text: str) -> set[str]:
        """Convert text into normalized searchable terms."""

        import re

        stop_words = {
            "the", "a", "an", "is", "are", "was", "were",
            "what", "when", "where", "how", "why", "who",
            "to", "of", "in", "on", "for", "and", "or",
            "does", "do", "can", "must", "should"
        }

        words = set(re.findall(r"\b[a-z0-9]+\b", text.lower()))

        return words - stop_words

    def _rerank(self, query: str, results: list[dict]) -> list[dict]:
        """Rerank retrieved chunks using deterministic keyword overlap."""

        query_words = self._tokenize(query)

        for result in results:
            document_words = self._tokenize(result["text"])

            overlap = query_words.intersection(document_words)
            union = query_words.union(document_words)

            # Jaccard similarity: overlap divided by total unique terms.
            rerank_score = (
                len(overlap) / len(union) if union else 0.0
            )

            result["rerank_score"] = rerank_score
            result["keyword_overlap"] = len(overlap)

        # Higher keyword overlap first; original similarity breaks ties.
        results.sort(
            key=lambda item: (
                item["rerank_score"],
                item["original_score"]
            ),
            reverse=True
        )

        for rank, result in enumerate(results, start=1):
            result["rerank_rank"] = rank

        return results




    
    def retrieve(
        self,
        query,
        top_k=5,
        document_type=None,
        version=None,
        access_label=None,
        rerank=False
    ):
        # 1. Validate input
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query cannot be empty.")

        if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k <= 0:
            raise ValueError("top_k must be a positive integer.")

        # 2. Generate embedding and search ChromaDB
        try:
            query_embedding = self._embed_query(query.strip())

            metadata_filter = self._build_metadata_filter(
                document_type=document_type,
                version=version,
                access_label=access_label
            )

            response = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=metadata_filter,
                include=["documents", "metadatas", "distances"]
            )

        except Exception as exc:
            raise RuntimeError("Retrieval service unavailable") from exc

        # 3. Convert ChromaDB results into structured results
        results = []

        documents = response["documents"][0]
        metadatas = response["metadatas"][0]
        distances = response["distances"][0]

        for document, metadata, distance in zip(
            documents, metadatas, distances
        ):
            similarity = 1.0 - distance

            results.append({
                "text": document,
                "score": similarity,
                "original_score": similarity,
                "distance": distance,
                "rerank_score": None,
                "rerank_rank": None,
                "keyword_overlap": None,
                "metadata": metadata
            })

        # 4. Apply optional reranking
        if rerank and results:
            results = self._rerank(query, results)

        # 5. Return results
        return results

    
# ============================================================
# RETRIEVAL EVIDENCE EXPORT
# ============================================================

import json
from datetime import datetime, timezone


def export_retrieval_samples():
    output_path = (
        Path(__file__).resolve().parent
        / "data"
        / "processed"
        / "retrieval_sample_results.json"
    )

    service = RetrievalService()

    test_cases = [
        {
            "case_id": "RET-001",
            "query": "What cases need immediate escalation?",
            "filters": {"access_label": "Restricted"},
            "expected_source_ids": ["KB-002"]
        },
        {
            "case_id": "RET-002",
            "query": "How should a disputed fee be investigated?",
            "filters": {},
            "expected_source_ids": ["KB-003"]
        }
    ]

    evidence = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "service": "RetrievalService",
        "embedding_model": EMBEDDING_MODEL,
        "embedding_dimensions": EMBEDDING_DIMENSIONS,
        "results": []
    }

    for case in test_cases:
        results = service.retrieve(
            query=case["query"],
            top_k=5,
            rerank=True,
            **case["filters"]
        )

        actual_sources = [
            result["metadata"].get("source_id")
            for result in results
        ]

        evidence["results"].append({
            "case_id": case["case_id"],
            "query": case["query"],
            "filters": case["filters"],
            "expected_source_ids": case["expected_source_ids"],
            "retrieved_source_ids": actual_sources,
            "expected_source_found": any(
                source in actual_sources
                for source in case["expected_source_ids"]
            ),
            "result_count": len(results),
            "retrieved_results": results
        })

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        json.dump(evidence, file, indent=4, ensure_ascii=False)

    print(f"Retrieval evidence saved to: {output_path}")


if __name__ == "__main__":
    export_retrieval_samples()




if __name__ == "__main__":
    service = RetrievalService()

    question = "What cases need immediate escalation?"

    print("\nBASELINE RETRIEVAL")
    print("=" * 60)

    baseline = service.retrieve(
        query=question,
        top_k=5
    )

    for rank, result in enumerate(baseline, start=1):
        print(
            f"{rank}. {result['metadata'].get('source_id')} "
            f"| Original score: {result['original_score']:.4f}"
        )

    print("\nRERANKED RETRIEVAL")
    print("=" * 60)

    reranked = service.retrieve(
        query=question,
        top_k=5,
        rerank=True
    )

    for result in reranked:
        print(
            f"Rank {result['rerank_rank']} "
            f"| {result['metadata'].get('source_id')} "
            f"| Original: {result['original_score']:.4f} "
            f"| Rerank: {result['rerank_score']:.4f} "
            f"| Overlap: {result['keyword_overlap']}"
        )

    test_cases = [
        {
            "name": "Baseline",
            "filters": {}
        },
        {
            "name": "Policy documents only",
            "filters": {
                "document_type": "Policy"
            }
        },
        {
            "name": "Version 3 only",
            "filters": {
                "version": "3"
            }
        },
        {
            "name": "Restricted documents only",
            "filters": {
                "access_label": "Restricted"
            }
        }
    ]

    for test in test_cases:
        print("\n" + "=" * 60)
        print(test["name"])
        print("=" * 60)

        results = service.retrieve(
            query=question,
            top_k=5,
            **test["filters"]
        )

        for result in results:
            metadata = result["metadata"]

            print(
                metadata.get("source_id"),
                "|",
                metadata.get("document_type"),
                "|",
                metadata.get("version"),
                "|",
                metadata.get("access_label"),
                "| Score:",
                round(result["score"], 4)
            )
