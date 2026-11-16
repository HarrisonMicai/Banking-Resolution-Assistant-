import csv
import importlib
from datetime import date
from types import SimpleNamespace

import chromadb
from docx import Document
import pytest

from app.rag import chunking, vector_store
from app.rag.ingestion_service import IngestionService


def _write_policy(path, sentence):
    document = Document()
    document.add_heading("Complaint handling", level=1)
    document.add_paragraph(sentence)
    document.save(path)


def _load_query_module(monkeypatch, collection):
    import dotenv

    monkeypatch.setenv("GOOGLE_API_KEY", "offline-test-key")
    monkeypatch.setattr(
        dotenv,
        "load_dotenv",
        lambda *args, **kwargs: False,
    )
    monkeypatch.setattr(
        chromadb,
        "PersistentClient",
        lambda **kwargs: SimpleNamespace(
            get_collection=lambda name: collection
        ),
    )
    query_rag = importlib.import_module("app.rag.query_rag")
    monkeypatch.setattr(query_rag, "collection", collection)
    return query_rag


def test_ingestion_to_query_retrieves_only_eligible_policy_evidence(
    tmp_path, monkeypatch
):
    knowledge_base = tmp_path / "knowledge_base"
    knowledge_base.mkdir()
    sources = [
        ("KB-PUBLIC", "Policy", "Approved", "Public", "2026-01-01"),
        ("KB-INTERNAL", "Policy", "Approved", "Internal", "2026-02-01"),
        ("KB-RESTRICTED", "Policy", "Approved", "Restricted", "2026-02-01"),
        ("KB-FUTURE", "Policy", "Approved", "Internal", "2026-07-01"),
        ("KB-OLD", "Policy", "Superseded", "Internal", "2025-01-01"),
        ("KB-CASE", "Casebook", "Approved", "Internal", "2024-01-01"),
    ]

    manifest_path = tmp_path / "manifest.csv"
    with manifest_path.open("w", newline="", encoding="utf-8") as manifest_file:
        writer = csv.writer(manifest_file)
        writer.writerow([
            "source_id",
            "title",
            "document_type",
            "version",
            "effective_date",
            "access_label",
            "status",
            "relative_path",
        ])
        for source_id, document_type, status, access_label, effective_date in sources:
            relative_path = f"{source_id}.docx"
            _write_policy(
                knowledge_base / relative_path,
                f"Evidence text for {source_id}.",
            )
            writer.writerow([
                source_id,
                f"{source_id} title",
                document_type,
                "1.0",
                effective_date,
                access_label,
                status,
                relative_path,
            ])

    service = IngestionService(
        manifest_path=manifest_path,
        knowledge_base_dir=knowledge_base,
        output_path=tmp_path / "processed" / "documents.jsonl",
        run_log_path=tmp_path / "processed" / "ingestion_run_log.json",
    )
    summary = service.run()
    service.write_outputs(summary)
    assert summary["status"] == "completed"
    assert summary["accepted_records"] == len(sources)

    chunks = chunking.structure_aware_chunking(service.accepted_records)
    assert chunking.validate_chunks(chunks)["passed"]

    chunks_file = tmp_path / "processed" / "chunks_selected.jsonl"
    chunking.save_chunks(chunks, chunks_file)
    embedding_records = [
        {
            "chunk_id": chunk["chunk_id"],
            "source_id": chunk["source_id"],
            "chunk": chunk,
            "embedding": [1.0, 0.0],
        }
        for chunk in chunks
    ]

    monkeypatch.setattr(vector_store, "CHROMA_DIR", tmp_path / "chroma")
    monkeypatch.setattr(vector_store, "CHUNKS_FILE", chunks_file)
    monkeypatch.setattr(
        vector_store,
        "INGESTION_LOG_FILE",
        tmp_path / "processed" / "ingestion_run_log.json",
    )
    collection = vector_store.build_index(embedding_records, dimensions=2)
    assert vector_store.validate_index(
        collection,
        embedding_records,
        dimensions=2,
    )["validation_passed"]

    query_rag = _load_query_module(monkeypatch, collection)
    monkeypatch.setattr(query_rag, "embed_question", lambda question: [1.0, 0.0])

    retrieved = query_rag.retrieve_context(
        "How should a complaint be handled?",
        user_access="Internal",
        as_of_date=date(2026, 6, 1),
    )

    assert {item["source_id"] for item in retrieved} == {
        "KB-PUBLIC",
        "KB-INTERNAL",
    }
    assert all(item["status"] == "Approved" for item in retrieved)
    assert all(item["access_label"] in {"Public", "Internal"} for item in retrieved)


def test_query_rejects_unknown_access_level(monkeypatch):
    query_rag = _load_query_module(monkeypatch, object())
    monkeypatch.setattr(query_rag, "embed_question", lambda question: [1.0, 0.0])

    with pytest.raises(ValueError, match="Invalid user access level"):
        query_rag.retrieve_context(
            "How should a complaint be handled?",
            user_access="Unknown",
        )


def test_query_discards_results_above_similarity_threshold(monkeypatch):
    class LowRelevanceCollection:
        def query(self, **kwargs):
            return {
                "documents": [["Irrelevant document"]],
                "metadatas": [[
                    {
                        "source_id": "KB-IRRELEVANT",
                        "title": "Unrelated",
                        "section_title": "Other",
                        "access_label": "Internal",
                        "status": "Approved",
                    }
                ]],
                "distances": [[0.9]],
            }

    query_rag = _load_query_module(monkeypatch, LowRelevanceCollection())
    monkeypatch.setattr(query_rag, "embed_question", lambda question: [1.0, 0.0])

    retrieved = query_rag.retrieve_context(
        "How should a complaint be handled?",
        user_access="Internal",
        as_of_date=date(2026, 6, 1),
    )

    assert retrieved == []


def test_no_retrieved_evidence_abstains_without_generation(
    monkeypatch, capsys
):
    query_rag = _load_query_module(monkeypatch, object())
    monkeypatch.setattr(query_rag, "retrieve_context", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        query_rag,
        "generate_answer",
        lambda *args, **kwargs: pytest.fail(
            "Answer generation must not run when retrieval returns no evidence"
        ),
    )

    query_rag.ask_question("What is the policy for an unsupported situation?")

    output = capsys.readouterr().out
    assert "CLASSIFICATION: UNSUPPORTED" in output
    assert "don't have sufficient information" in output
