
import pytest

from app.rag.ingestion_service import IngestionService


def test_load_valid_manifest(tmp_path):
    manifest = tmp_path / "manifest.csv"

    manifest.write_text(
        "source_id,title,document_type,version,"
        "effective_date,access_label,status,relative_path\n"
        "KB-001,Account Policy,Policy,1.0,"
        "2026-01-01,Internal,Approved,policy.docx\n",
        encoding="utf-8"
    )

    service = IngestionService(manifest_path=manifest)

    records = service._load_manifest()

    assert len(records) == 1
    assert records[0]["source_id"] == "KB-001"


def test_missing_manifest_rejected(tmp_path):
    service = IngestionService(
        manifest_path=tmp_path / "missing.csv"
    )

    with pytest.raises(FileNotFoundError):
        service._load_manifest()


def test_missing_manifest_headers_rejected(tmp_path):
    manifest = tmp_path / "manifest.csv"

    manifest.write_text(
        "source_id,title\nKB-001,Account Policy\n",
        encoding="utf-8"
    )

    service = IngestionService(manifest_path=manifest)

    with pytest.raises(ValueError, match="missing headers"):
        service._load_manifest()


def test_duplicate_source_id_rejected(tmp_path):
    """All records with duplicate source IDs should be rejected."""

    service = IngestionService()

    records = [
        {
            "source_id": "KB-001",
            "relative_path": "policy1.docx"
        },
        {
            "source_id": "KB-001",
            "relative_path": "policy2.docx"
        },
        {
            "source_id": "KB-002",
            "relative_path": "policy3.docx"
        }
    ]

    duplicate_ids = service._find_duplicate_source_ids(records)

    assert "KB-001" in duplicate_ids
    assert "KB-002" not in duplicate_ids

    assert len(service.rejected_records) == 2


def test_missing_effective_date_rejected():
    """A missing effective date should be identified."""

    service = IngestionService()

    record = {
        "source_id": "KB-001",
        "title": "Account Policy",
        "document_type": "Policy",
        "version": "1.0",
        "effective_date": "",
        "access_label": "Internal",
        "status": "Approved",
        "relative_path": "policy.docx"
    }

    missing_fields = service._missing_required_fields(record)

    assert "effective_date" in missing_fields


def test_all_required_fields_present():
    """A complete record should have no missing fields."""

    service = IngestionService()

    record = {
        "source_id": "KB-001",
        "title": "Account Policy",
        "document_type": "Policy",
        "version": "1.0",
        "effective_date": "2026-01-01",
        "access_label": "Internal",
        "status": "Approved",
        "relative_path": "policy.docx"
    }

    assert service._missing_required_fields(record) == []


def test_valid_docx_file(tmp_path):
    knowledge_base = tmp_path / "knowledge_base"
    knowledge_base.mkdir()

    document = knowledge_base / "policy.docx"
    document.write_bytes(b"test document")

    service = IngestionService(
        knowledge_base_dir=knowledge_base
    )

    record = {"relative_path": "policy.docx"}

    path, error = service._validate_document_file(record)

    assert path == document.resolve()
    assert error is None


def test_missing_docx_file(tmp_path):
    knowledge_base = tmp_path / "knowledge_base"
    knowledge_base.mkdir()

    service = IngestionService(
        knowledge_base_dir=knowledge_base
    )

    record = {"relative_path": "missing.docx"}

    path, error = service._validate_document_file(record)

    assert path is None
    assert "File does not exist" in error


def test_path_outside_knowledge_base_is_rejected(tmp_path):
    knowledge_base = tmp_path / "knowledge_base"
    knowledge_base.mkdir()
    outside_file = tmp_path / "outside.docx"
    outside_file.write_bytes(b"not part of the knowledge base")

    service = IngestionService(knowledge_base_dir=knowledge_base)
    path, error = service._validate_document_file({
        "relative_path": "..\\outside.docx"
    })

    assert path is None
    assert error == "File path is outside the knowledge base directory"


def test_run_marks_ingestion_failed_when_a_document_is_rejected(tmp_path):
    knowledge_base = tmp_path / "knowledge_base"
    knowledge_base.mkdir()
    manifest = tmp_path / "manifest.csv"
    manifest.write_text(
        "source_id,title,document_type,version,"
        "effective_date,access_label,status,relative_path\n"
        "KB-001,Account Policy,Policy,1.0,"
        "2026-01-01,Internal,Approved,missing.docx\n",
        encoding="utf-8",
    )
    service = IngestionService(
        manifest_path=manifest,
        knowledge_base_dir=knowledge_base,
        output_path=tmp_path / "documents.jsonl",
        run_log_path=tmp_path / "ingestion_run_log.json",
    )

    summary = service.run()

    assert summary["rejected_records"] == 1
    assert summary["status"] == "failed"


def test_unsupported_file_extension(tmp_path):
    knowledge_base = tmp_path / "knowledge_base"
    knowledge_base.mkdir()

    document = knowledge_base / "policy.pdf"
    document.write_bytes(b"test document")

    service = IngestionService(
        knowledge_base_dir=knowledge_base
    )

    record = {"relative_path": "policy.pdf"}

    path, error = service._validate_document_file(record)

    assert path is None
    assert "Unsupported file extension" in error


def test_unlisted_file_is_rejected(tmp_path):
    knowledge_base = tmp_path / "knowledge_base"
    knowledge_base.mkdir()

    listed_file = knowledge_base / "policy.docx"
    listed_file.write_bytes(b"listed")

    unlisted_file = knowledge_base / "extra_policy.docx"
    unlisted_file.write_bytes(b"unlisted")

    service = IngestionService(
        knowledge_base_dir=knowledge_base
    )

    manifest_records = [
        {"source_id": "KB-001", "relative_path": "policy.docx"}
    ]

    service._find_unlisted_files(manifest_records)

    assert len(service.rejected_records) == 1
    assert service.rejected_records[0]["relative_path"] == "extra_policy.docx"

def test_extract_docx_text(tmp_path):
    from docx import Document

    document_path = tmp_path / "sample.docx"

    document = Document()
    document.add_heading("Purpose", level=1)
    document.add_paragraph(
        "This policy explains complaint management."
    )
    document.save(document_path)

    service = IngestionService()

    paragraphs = service._extract_docx_text(document_path)

    assert len(paragraphs) == 2
    assert paragraphs[0]["text"] == "Purpose"
    assert paragraphs[0]["style"] == "Heading 1"
    assert "complaint management" in paragraphs[1]["text"]


def test_extract_sections(tmp_path):
    service = IngestionService()

    paragraphs = [
        {"text": "Purpose", "style": "Heading 1"},
        {"text": "This policy explains complaints.", "style": "Normal"},
        {"text": "Scope", "style": "Heading 1"},
        {"text": "This applies to all customers.", "style": "Normal"}
    ]

    sections = service._extract_sections(
        paragraphs,
        "KB-001"
    )

    assert len(sections) == 2
    assert sections[0]["section_title"] == "Purpose"
    assert sections[0]["sequence"] == 1
    assert sections[0]["chunk_id"] == "KB-001#purpose#0001"
    assert sections[1]["section_title"] == "Scope"


def test_run_and_write_outputs(tmp_path):
    from docx import Document
    import json

    knowledge_base = tmp_path / "knowledge_base"
    knowledge_base.mkdir()

    document_path = knowledge_base / "policy.docx"

    document = Document()
    document.add_heading("Purpose", level=1)
    document.add_paragraph(
        "This policy explains complaint management."
    )
    document.save(document_path)

    manifest_path = tmp_path / "manifest.csv"

    manifest_path.write_text(
        "source_id,title,document_type,version,"
        "effective_date,access_label,status,relative_path\n"
        "KB-001,Complaint Policy,Policy,1.0,"
        "2026-01-01,Internal,Approved,policy.docx\n",
        encoding="utf-8"
    )

    output_path = tmp_path / "processed" / "documents.jsonl"
    run_log_path = tmp_path / "processed" / "ingestion_run_log.json"

    service = IngestionService(
        manifest_path=manifest_path,
        knowledge_base_dir=knowledge_base,
        output_path=output_path,
        run_log_path=run_log_path
    )

    summary = service.run()
    service.write_outputs(summary)

    assert summary["accepted_records"] == 1
    assert summary["rejected_records"] == 0
    assert output_path.exists()
    assert run_log_path.exists()

    with output_path.open(encoding="utf-8") as file:
        records = [json.loads(line) for line in file]

    assert records[0]["source_id"] == "KB-001"
    assert records[0]["section_title"] == "Purpose"
    assert records[0]["chunk_id"] == "KB-001#purpose#0001"
