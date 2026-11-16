
import json
import re
from pathlib import Path


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

INPUT_FILE = PROCESSED_DIR / "documents.jsonl"
BASELINE_FILE = PROCESSED_DIR / "chunks_baseline.jsonl"
SELECTED_FILE = PROCESSED_DIR / "chunks_selected.jsonl"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50


# --------------------------------------------------
# LOAD NORMALIZED DOCUMENTS
# --------------------------------------------------

def load_documents():
    documents = []

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                documents.append(json.loads(line))

    return documents


# --------------------------------------------------
# CREATE CHUNK RECORD
# --------------------------------------------------

def create_chunk(document, text, chunk_number, strategy):
    chunk = document.copy()

    original_id = document.get("chunk_id", document.get("source_id"))

    chunk["parent_chunk_id"] = original_id
    chunk["chunk_id"] = (
        f"{document['source_id']}"
        f"#section-{document.get('sequence', 0):04d}"
        f"#chunk-{chunk_number:04d}"
    )

    chunk["text"] = text
    chunk["chunk_index"] = chunk_number
    chunk["chunking_strategy"] = strategy

    return chunk


# --------------------------------------------------
# STRATEGY 1: FIXED-SIZE CHUNKING
# --------------------------------------------------

def fixed_chunking(documents):
    chunks = []

    for document in documents:
        text = document.get("text", "").strip()

        if not text:
            continue

        start = 0
        chunk_number = 1

        while start < len(text):
            end = start + CHUNK_SIZE
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    create_chunk(
                        document,
                        chunk_text,
                        chunk_number,
                        "fixed"
                    )
                )

            chunk_number += 1

            if end >= len(text):
                break

            start = end - CHUNK_OVERLAP

    return chunks


# --------------------------------------------------
# STRATEGY 2: STRUCTURE-AWARE CHUNKING
# --------------------------------------------------

def structure_aware_chunking(documents):
    chunks = []

    for document in documents:
        text = document.get("text", "").strip()

        if not text:
            continue

        # Split on paragraph boundaries.
        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(r"\n\s*\n", text)
            if paragraph.strip()
        ]

        # If ingestion flattened the paragraphs,
        # treat the entire section as one paragraph.
        current_text = ""
        chunk_number = 1

        for paragraph in paragraphs:
            candidate = (
                f"{current_text}\n\n{paragraph}"
                if current_text else paragraph
            )

            if len(candidate) <= CHUNK_SIZE:
                current_text = candidate
            else:
                if current_text:
                    chunks.append(
                        create_chunk(
                            document,
                            current_text,
                            chunk_number,
                            "structure_aware"
                        )
                    )
                    chunk_number += 1

                # Split oversized paragraphs safely.
                if len(paragraph) > CHUNK_SIZE:
                    for start in range(0, len(paragraph), CHUNK_SIZE):
                        piece = paragraph[start:start + CHUNK_SIZE].strip()

                        if piece:
                            chunks.append(
                                create_chunk(
                                    document,
                                    piece,
                                    chunk_number,
                                    "structure_aware"
                                )
                            )
                            chunk_number += 1

                    current_text = ""
                else:
                    current_text = paragraph

        if current_text:
            chunks.append(
                create_chunk(
                    document,
                    current_text,
                    chunk_number,
                    "structure_aware"
                )
            )

    return chunks


# --------------------------------------------------
# VALIDATE CHUNKS
# --------------------------------------------------

def validate_chunks(chunks):
    ids = [chunk["chunk_id"] for chunk in chunks]

    duplicate_ids = len(ids) - len(set(ids))
    empty_chunks = sum(
        1 for chunk in chunks
        if not chunk.get("text", "").strip()
    )
    missing_sources = sum(
        1 for chunk in chunks
        if not chunk.get("source_id")
    )
    oversized_chunks = sum(
        1 for chunk in chunks
        if len(chunk.get("text", "")) > CHUNK_SIZE
    )

    results = {
        "total_chunks": len(chunks),
        "duplicate_ids": duplicate_ids,
        "empty_chunks": empty_chunks,
        "missing_sources": missing_sources,
        "oversized_chunks": oversized_chunks,
        "passed": (
            duplicate_ids == 0
            and empty_chunks == 0
            and missing_sources == 0
        )
    }

    return results


# --------------------------------------------------
# SAVE JSONL
# --------------------------------------------------

def save_chunks(chunks, output_file):
    with output_file.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk, ensure_ascii=False) + "\n")


# --------------------------------------------------
# MAIN PIPELINE
# --------------------------------------------------

def main():
    documents = load_documents()

    baseline_chunks = fixed_chunking(documents)
    selected_chunks = structure_aware_chunking(documents)

    baseline_validation = validate_chunks(baseline_chunks)
    selected_validation = validate_chunks(selected_chunks)

    save_chunks(baseline_chunks, BASELINE_FILE)
    save_chunks(selected_chunks, SELECTED_FILE)

    print("\nCHUNKING COMPLETE")
    print("------------------------------")

    print("Input documents:", len(documents))

    print("\nBaseline:")
    print(json.dumps(baseline_validation, indent=4))

    print("\nStructure-aware:")
    print(json.dumps(selected_validation, indent=4))

    print("\nGenerated files:")
    print(BASELINE_FILE)
    print(SELECTED_FILE)


if __name__ == "__main__":
    main()
