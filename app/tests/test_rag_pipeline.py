import json
from datetime import date

import chromadb
import pytest

from app.rag import embedding_service, vector_store
from app.rag.retrieval_policy import (
    build_policy_filter,
    get_permitted_labels,
    parse_effective_date,
)


def test_policy_filter_excludes_casebooks_and_future_sources():
    policy_filter = build_policy_filter(
        get_permitted_labels("Internal"),
        date(2026, 6, 1),
    )

    assert policy_filter == {
        "$and": [
            {"status": {"$eq": "Approved"}},
            {"access_label": {"$in": ["Public", "Internal"]}},
            {"document_type": {"$ne": "Casebook"}},
            {"effective_date": {"$lte": 20260601}},
        ]
    }


def test_chroma_filter_excludes_ineligible_sources(tmp_path):
    client = chromadb.PersistentClient(path=str(tmp_path / "chroma"))
    collection = client.create_collection(
        name="policy_filter_negative_cases",
        metadata={"hnsw:space": "cosine"},
        embedding_function=None,
    )
    sources = [
        ("public", "Policy", "Approved", "Public", 20260101),
        ("internal", "Policy", "Approved", "Internal", 20260201),
        ("restricted", "Policy", "Approved", "Restricted", 20260201),
        ("future", "Policy", "Approved", "Internal", 20260701),
        ("superseded", "Policy", "Superseded", "Internal", 20250101),
        ("casebook", "Casebook", "Approved", "Internal", 20240101),
    ]
    collection.add(
        ids=[source[0] for source in sources],
        embeddings=[[1.0, 0.0] for _ in sources],
        documents=[f"Evidence for {source[0]}" for source in sources],
        metadatas=[
            {
                "document_type": document_type,
                "status": status,
                "access_label": access_label,
                "effective_date": effective_date,
            }
            for _, document_type, status, access_label, effective_date in sources
        ],
    )

    eligible = collection.get(
        where=build_policy_filter(
            get_permitted_labels("Internal"),
            date(2026, 6, 1),
        ),
        include=["metadatas"],
    )

    assert set(eligible["ids"]) == {"public", "internal"}


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-01-02", date(2026, 1, 2)),
        ("1/2/2026", date(2026, 1, 2)),
        (date(2026, 1, 2), date(2026, 1, 2)),
        (20260102, date(2026, 1, 2)),
    ],
)
def test_parse_effective_date_supported_formats(value, expected):
    assert parse_effective_date(value) == expected


def test_parse_effective_date_rejects_invalid_values():
    with pytest.raises(ValueError, match="Invalid effective_date"):
        parse_effective_date("not-a-date")


def test_cache_reuses_vector_but_refreshes_current_chunk_metadata(
    tmp_path, monkeypatch
):
    cache_file = tmp_path / "embedding_cache.jsonl"
    monkeypatch.setattr(embedding_service, "CACHE_FILE", cache_file)

    stale_record = {
        "chunk_id": "KB-001#chunk-1",
        "source_id": "KB-001",
        "model": "gemini-embedding-001",
        "dimensions": 2,
        "chunk": {
            "chunk_id": "KB-001#chunk-1",
            "text": "Policy wording",
            "status": "Superseded",
        },
        "embedding": [0.1, 0.2],
    }
    cache_file.write_text(json.dumps(stale_record) + "\n", encoding="utf-8")
    current_chunk = {
        "chunk_id": "KB-001#chunk-1",
        "source_id": "KB-001",
        "text": "Policy wording",
        "status": "Approved",
    }

    cached = embedding_service.load_cache(
        [current_chunk],
        "gemini-embedding-001",
        2,
    )

    assert cached[current_chunk["chunk_id"]]["embedding"] == [0.1, 0.2]
    assert cached[current_chunk["chunk_id"]]["chunk"] == current_chunk


def test_cache_rejects_changed_text_or_model(tmp_path, monkeypatch):
    cache_file = tmp_path / "embedding_cache.jsonl"
    monkeypatch.setattr(embedding_service, "CACHE_FILE", cache_file)
    cache_file.write_text(
        json.dumps({
            "chunk_id": "chunk-1",
            "model": "old-model",
            "dimensions": 2,
            "chunk": {"text": "old text"},
            "embedding": [0.1, 0.2],
        }) + "\n",
        encoding="utf-8",
    )

    cached = embedding_service.load_cache(
        [{"chunk_id": "chunk-1", "source_id": "KB-001", "text": "new text"}],
        "new-model",
        2,
    )

    assert cached == {}


def test_cache_rewrite_drops_unselected_records(tmp_path, monkeypatch):
    cache_file = tmp_path / "embedding_cache.jsonl"
    monkeypatch.setattr(embedding_service, "CACHE_FILE", cache_file)
    chunk = {"chunk_id": "current"}
    records = {
        "current": {"chunk_id": "current", "embedding": [0.3]},
        "obsolete": {"chunk_id": "obsolete", "embedding": [0.4]},
    }

    embedding_service.write_cache(records, [chunk])

    written = [
        json.loads(line)
        for line in cache_file.read_text(encoding="utf-8").splitlines()
    ]
    assert [record["chunk_id"] for record in written] == ["current"]


def test_index_input_rejects_stale_cached_chunks():
    record = {
        "chunk_id": "chunk-1",
        "source_id": "KB-001",
        "embedding": [0.1, 0.2],
        "chunk": {"chunk_id": "chunk-1", "text": "old text"},
    }
    current_chunk = {"chunk_id": "chunk-1", "text": "new text"}

    with pytest.raises(ValueError, match="stale chunk data"):
        vector_store.validate_input([record], 2, [current_chunk])


def test_index_metadata_normalizes_manifest_effective_date():
    metadata = vector_store.prepare_metadata({
        "source_id": "KB-001",
        "effective_date": "1/2/2026",
    })

    assert metadata["effective_date"] == 20260102


def test_index_build_is_blocked_when_ingestion_rejected(
    tmp_path, monkeypatch
):
    log_path = tmp_path / "ingestion_run_log.json"
    log_path.write_text(
        json.dumps({
            "summary": {"status": "failed", "rejected_records": 1},
            "rejected_documents": [{"source_id": "KB-001"}],
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(vector_store, "INGESTION_LOG_FILE", log_path)

    with pytest.raises(RuntimeError, match="did not complete cleanly"):
        vector_store.validate_ingestion_gate()
