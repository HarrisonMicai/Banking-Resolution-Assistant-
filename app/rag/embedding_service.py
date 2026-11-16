import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# --------------------------------------------------
# PATHS AND CONFIGURATION
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data" / "processed"

CHUNKS_FILE = DATA_DIR / "chunks_selected.jsonl"
CONFIG_FILE = DATA_DIR / "embedding_config.json"
CACHE_FILE = DATA_DIR / "embedding_cache.jsonl"
SUMMARY_FILE = DATA_DIR / "embedding_run_summary.json"

load_dotenv(BASE_DIR / ".env", override=True)


def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))
    return records


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2)


def load_cache(chunks, model, dimensions):
    cached = {}
    expected_chunks = {chunk["chunk_id"]: chunk for chunk in chunks}

    if not CACHE_FILE.exists():
        return cached

    with open(CACHE_FILE, "r", encoding="utf-8") as file:
        for line in file:
            try:
                record = json.loads(line)
                if not isinstance(record, dict):
                    continue

                chunk_id = record["chunk_id"]
                chunk = expected_chunks.get(chunk_id)
                embedding = record.get("embedding", [])
                cached_chunk = record.get("chunk")

                if (
                    chunk is None
                    or not isinstance(cached_chunk, dict)
                    or record.get("model") != model
                    or record.get("dimensions") != dimensions
                    or not isinstance(embedding, list)
                    or len(embedding) != dimensions
                    or cached_chunk.get("text") != chunk.get("text")
                ):
                    continue

                cached[chunk_id] = {
                    **record,
                    "source_id": chunk["source_id"],
                    "chunk": chunk,
                }
            except (json.JSONDecodeError, KeyError):
                continue

    return cached


def write_cache(cached, chunks):
    """Replace the cache with records matching the current selected chunks."""

    temporary_file = CACHE_FILE.with_suffix(".jsonl.tmp")
    with open(temporary_file, "w", encoding="utf-8") as file:
        for chunk in chunks:
            record = cached.get(chunk["chunk_id"])
            if record is not None:
                file.write(json.dumps(record) + "\n")
        file.flush()
        os.fsync(file.fileno())

    temporary_file.replace(CACHE_FILE)


def save_batch(records, cached):
    # Persist successful batches so interrupted runs can resume.
    with open(CACHE_FILE, "a", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record) + "\n")

        file.flush()
        os.fsync(file.fileno())

    for record in records:
        cached[record["chunk_id"]] = record


def main():
    started = time.time()

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))

    model = config.get("model", "gemini-embedding-001")
    dimensions = config.get("dimensions", 768)

    # Small batches and deliberate pauses protect the free-tier quota.
    batch_size = 16
    pause_after = 80
    pause_seconds = 65

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY was not loaded from app/rag/.env")

    client = genai.Client(api_key=api_key)

    chunks = load_jsonl(CHUNKS_FILE)
    cached = load_cache(chunks, model, dimensions)

    # Reject malformed or duplicate input chunk IDs.
    seen = set()
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        if not chunk_id or not chunk.get("source_id") or not chunk.get("text"):
            raise ValueError(f"Invalid chunk record: {chunk_id}")

        if chunk_id in seen:
            raise ValueError(f"Duplicate input chunk_id: {chunk_id}")

        seen.add(chunk_id)

    pending = [
        chunk for chunk in chunks
        if chunk["chunk_id"] not in cached
    ]

    print(f"Selected chunks: {len(chunks)}")
    print(f"Already cached: {len(chunks) - len(pending)}")
    print(f"Remaining: {len(pending)}")

    processed_this_run = 0
    successful_batches = 0
    failed_batches = []

    for start in range(0, len(pending), batch_size):
        if processed_this_run >= pause_after:
            print(f"\nPausing {pause_seconds} seconds for Gemini quota...")
            time.sleep(pause_seconds)
            processed_this_run = 0

        batch = pending[start:start + batch_size]
        texts = [chunk["text"] for chunk in batch]

        print(f"\nEmbedding batch: {len(batch)} chunks")

        response = None

        for attempt in range(1, 6):
            try:
                response = client.models.embed_content(
                    model=model,
                    contents=texts,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=dimensions,
                    ),
                )
                break

            except Exception as error:
                message = str(error).lower()

                if attempt == 5:
                    print(f"Batch failed after 5 attempts: {error}")
                    failed_batches.append({
                        "chunk_ids": [c["chunk_id"] for c in batch],
                        "error": str(error),
                    })
                    break

                if "429" in message or "quota" in message or "resource_exhausted" in message:
                    wait_seconds = 65
                else:
                    wait_seconds = min(5 * attempt, 20)

                print(f"Attempt {attempt} failed. Waiting {wait_seconds}s.")
                time.sleep(wait_seconds)

        if response is None:
            continue

        if len(response.embeddings) != len(batch):
            raise RuntimeError("Gemini returned an unexpected number of embeddings.")

        records = []

        for chunk, result in zip(batch, response.embeddings):
            vector = [float(value) for value in result.values]

            if len(vector) != dimensions:
                raise ValueError(
                    f"{chunk['chunk_id']}: expected {dimensions} dimensions, "
                    f"received {len(vector)}"
                )

            records.append({
                "chunk_id": chunk["chunk_id"],
                "source_id": chunk["source_id"],
                "model": model,
                "dimensions": dimensions,
                "chunk": chunk,
                "embedding": vector,
            })

        save_batch(records, cached)

        successful_batches += 1
        processed_this_run += len(batch)

        print(f"Saved {len(records)} embeddings. Total cached: {len(cached)}")

    duration = round(time.time() - started, 2)

    write_cache(cached, chunks)

    summary = {
        "provider": "google",
        "model": model,
        "dimensions": dimensions,
        "input_chunks": len(chunks),
        "cached_embeddings": len(cached),
        "successful_batches": successful_batches,
        "failed_batches": failed_batches,
        "duration_seconds": duration,
        "completed": (
            len(cached) == len(chunks)
            and all(chunk["chunk_id"] in cached for chunk in chunks)
        ),
        "cache_file": str(CACHE_FILE),
    }

    save_json(SUMMARY_FILE, summary)

    print("\nEMBEDDING SUMMARY")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()