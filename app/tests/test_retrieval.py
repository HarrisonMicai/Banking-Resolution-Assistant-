
import pytest

from app.rag.retrieval_service import RetrievalService


class FakeCollection:
    def __init__(self, should_fail=False, empty=False):
        self.should_fail = should_fail
        self.empty = empty
        self.last_query = None

    def query(self, **kwargs):
        self.last_query = kwargs

        if self.should_fail:
            raise Exception("Vector store unavailable")

        if self.empty:
            return {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }

        return {
            "documents": [["Supervisor approval is required for certain complaints."]],
            "metadatas": [[{
                "source_id": "KB-002",
                "document_type": "Policy",
                "version": "2.1",
                "access_label": "Restricted",
                "status": "Approved"
            }]],
            "distances": [[0.25]]
        }


class RetrievalServiceStub(RetrievalService):
    def _embed_query(self, query):
        return [0.1, 0.2, 0.3]


def create_service(collection):
    return RetrievalServiceStub(
        collection=collection,
        embedding_client=object()
    )


def test_empty_query_raises_value_error():
    service = create_service(FakeCollection())

    with pytest.raises(ValueError):
        service.retrieve(" ")


def test_no_matches_returns_empty_list():
    service = create_service(FakeCollection(empty=True))

    results = service.retrieve("Unrelated question")

    assert results == []


def test_vector_store_failure_raises_runtime_error():
    service = create_service(FakeCollection(should_fail=True))

    with pytest.raises(RuntimeError, match="Retrieval service unavailable"):
        service.retrieve("What requires escalation?")


def test_retrieval_returns_expected_metadata_and_score():
    service = create_service(FakeCollection())

    results = service.retrieve("What requires escalation?")

    assert len(results) == 1
    assert results[0]["metadata"]["source_id"] == "KB-002"
    assert results[0]["score"] == pytest.approx(0.75)
    assert results[0]["original_score"] == pytest.approx(0.75)


def test_metadata_filters_are_applied():
    collection = FakeCollection()
    service = create_service(collection)

    service.retrieve(
        "What requires escalation?",
        document_type="Policy",
        version="2.1",
        access_label="Restricted"
    )

    applied_filter = collection.last_query["where"]

    assert applied_filter["$and"] == [
        {"status": {"$eq": "Approved"}},
        {"document_type": {"$eq": "Policy"}},
        {"version": {"$eq": "2.1"}},
        {"access_label": {"$eq": "Restricted"}}
    ]


def test_reranking_preserves_original_score():
    service = create_service(FakeCollection())

    results = service.retrieve(
        "What requires escalation?",
        rerank=True
    )

    assert len(results) == 1
    assert results[0]["original_score"] == pytest.approx(0.75)
    assert results[0]["rerank_score"] is not None
    assert results[0]["rerank_rank"] == 1
