
import json
from pathlib import Path
from collections import Counter

import chromadb

from app.rag.retrieval_policy import parse_effective_date


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

CACHE_FILE = DATA_DIR / "embedding_cache.jsonl"
CONFIG_FILE = DATA_DIR / "embedding_config.json"
VALIDATION_FILE = DATA_DIR / "vector_index_validation.json"
CHUNKS_FILE = DATA_DIR / "chunks_selected.jsonl"
INGESTION_LOG_FILE = DATA_DIR / "ingestion_run_log.json"

CHROMA_DIR = BASE_DIR / "data" / "chroma_db"
COLLECTION_NAME = "banking_complaints"


# Only approved, flat metadata fields are stored in ChromaDB.
METADATA_FIELDS = [
    "source_id",
    "title",
    "document_type",
    "version",
    "effective_date",
    "access_label",
    "status",
    "relative_path",
    "checksum",
    "section_title",
    "sequence",
    "chunk_index",
    "chunking_strategy",
    "parent_chunk_id",
]


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_embeddings():
    records = []

    with open(CACHE_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    if not records:
        raise ValueError("Embedding cache is empty.")

    return records


def load_chunks():
    chunks = []
    with open(CHUNKS_FILE, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                chunks.append(json.loads(line))
    return chunks


def prepare_metadata(chunk):
    """Convert chunk metadata into ChromaDB-compatible scalar values."""

    metadata = {}

    for field in METADATA_FIELDS:
        value = chunk.get(field)

        if value is None:
            continue

        if field == "effective_date":
            value = int(parse_effective_date(value).strftime("%Y%m%d"))

        if isinstance(value, (str, int, float, bool)):
            metadata[field] = value
        else:
            metadata[field] = str(value)

    return metadata


def validate_ingestion_gate():
    if not INGESTION_LOG_FILE.exists():
        raise FileNotFoundError(
            f"Ingestion run log not found: {INGESTION_LOG_FILE}"
        )

    run_log = load_json(INGESTION_LOG_FILE)
    summary = run_log.get("summary", {})
    rejected = run_log.get("rejected_documents", [])

    if (
        summary.get("status") != "completed"
        or summary.get("rejected_records") != 0
        or rejected
    ):
        raise RuntimeError(
            "Refusing to build the vector index: ingestion did not complete "
            "cleanly. Rerun ingestion and resolve rejected documents."
        )


def validate_input(records, expected_dimensions, expected_chunks=None):
    ids = [record["chunk_id"] for record in records]

    duplicates = [
        chunk_id
        for chunk_id, count in Counter(ids).items()
        if count > 1
    ]

    if duplicates:
        raise ValueError(f"Duplicate chunk IDs found: {duplicates[:5]}")

    if expected_chunks is not None:
        expected_by_id = {chunk["chunk_id"]: chunk for chunk in expected_chunks}
        record_by_id = {record["chunk_id"]: record for record in records}

        if set(record_by_id) != set(expected_by_id):
            raise ValueError(
                "Embedding cache IDs do not match the selected chunk IDs."
            )

        stale_chunks = [
            chunk_id
            for chunk_id, record in record_by_id.items()
            if record.get("chunk") != expected_by_id[chunk_id]
        ]
        if stale_chunks:
            raise ValueError(
                "Embedding cache contains stale chunk data: "
                f"{stale_chunks[:5]}"
            )

    for record in records:
        if not record.get("source_id"):
            raise ValueError(
                f"Missing source_id for {record.get('chunk_id')}"
            )

        vector = record.get("embedding", [])

        if len(vector) != expected_dimensions:
            raise ValueError(
                f"Invalid dimensions for {record['chunk_id']}: "
                f"{len(vector)}"
            )

        if not record.get("chunk", {}).get("text"):
            raise ValueError(
                f"Missing document text for {record['chunk_id']}"
            )

        parse_effective_date(record["chunk"].get("effective_date"))


def get_client():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)

    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def delete_existing_collection(client):
    """Delete the existing collection to support a clean rebuild."""

    existing = client.list_collections()

    names = [
        item if isinstance(item, str) else item.name
        for item in existing
    ]

    if COLLECTION_NAME in names:
        client.delete_collection(name=COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")


def build_index(records, dimensions, batch_size=100):
    validate_ingestion_gate()
    validate_input(records, dimensions, load_chunks())

    client = get_client()

    # Full rebuild: prevents duplicate records across repeated runs.
    delete_existing_collection(client)

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={
            "description": "Banking complaint knowledge base",
            "embedding_model": "gemini-embedding-001",
            "embedding_dimensions": dimensions,
            "hnsw:space": "cosine",
        },
        embedding_function=None,
    )

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]

        collection.add(
            ids=[record["chunk_id"] for record in batch],
            embeddings=[
                record["embedding"] for record in batch
            ],
            documents=[
                record["chunk"]["text"] for record in batch
            ],
            metadatas=[
                prepare_metadata(record["chunk"])
                for record in batch
            ],
        )

        print(
            f"Indexed {min(start + len(batch), len(records))}"
            f"/{len(records)} records"
        )

    return collection


def validate_index(collection, records, dimensions):
    """Validate count, dimensions, metadata, and uniqueness."""

    stored = collection.get(
        include=["embeddings", "metadatas", "documents"]
    )

    stored_ids = stored["ids"]
    stored_embeddings = stored["embeddings"]
    stored_metadata = stored["metadatas"]
    stored_documents = stored["documents"]

    expected_ids = {record["chunk_id"] for record in records}
    actual_ids = set(stored_ids)

    duplicate_ids = [
        chunk_id
        for chunk_id, count in Counter(stored_ids).items()
        if count > 1
    ]

    missing_source_ids = [
        stored_ids[index]
        for index, metadata in enumerate(stored_metadata)
        if not metadata or not metadata.get("source_id")
    ]

    invalid_dimensions = [
        stored_ids[index]
        for index, vector in enumerate(stored_embeddings)
        if len(vector) != dimensions
    ]

    missing_documents = [
        stored_ids[index]
        for index, document in enumerate(stored_documents)
        if not document
    ]

    result = {
        "collection_name": COLLECTION_NAME,
        "embedding_model": "gemini-embedding-001",
        "expected_dimensions": dimensions,
        "expected_count": len(records),
        "actual_count": collection.count(),
        "missing_ids": sorted(expected_ids - actual_ids),
        "unexpected_ids": sorted(actual_ids - expected_ids),
        "duplicate_ids": duplicate_ids,
        "missing_source_ids": missing_source_ids,
        "invalid_dimensions": invalid_dimensions,
        "missing_documents": missing_documents,
        "metadata_records_checked": len(stored_metadata),
        "validation_passed": (
            len(records) == collection.count()
            and expected_ids == actual_ids
            and not duplicate_ids
            and not missing_source_ids
            and not invalid_dimensions
            and not missing_documents
        ),
    }

    return result


def main():
    config = load_json(CONFIG_FILE)
    dimensions = config.get("dimensions", 768)

    validate_ingestion_gate()
    records = load_embeddings()
    chunks = load_chunks()

    print(f"Loaded {len(records)} embedding records.")

    validate_input(records, dimensions, chunks)

    collection = build_index(
        records=records,
        dimensions=dimensions,
    )

    validation = validate_index(
        collection=collection,
        records=records,
        dimensions=dimensions,
    )

    with open(VALIDATION_FILE, "w", encoding="utf-8") as file:
        json.dump(validation, file, indent=2)

    print("\nVECTOR INDEX VALIDATION")
    print(json.dumps(validation, indent=2))

    if not validation["validation_passed"]:
        raise RuntimeError("Vector index validation failed.")

    print("\nSUCCESS: ChromaDB index built and validated.")


if __name__ == "__main__":
    main()
