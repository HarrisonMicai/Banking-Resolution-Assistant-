
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types


# ============================================================
# 1. PATHS AND CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "app" / "rag" / "data" / "processed"

CHUNKS_FILE = PROCESSED_DIR / "chunks_selected.jsonl"
CONFIG_FILE = PROCESSED_DIR / "embedding_config.json"
CHECKPOINT_FILE = PROCESSED_DIR / "embedding_cache.jsonl"
RUN_LOG_FILE = PROCESSED_DIR / "embedding_run_log.json"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
ENV_FILE = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_FILE, override=True)


# ============================================================
# 2. CONFIGURATION AND CLIENT INITIALIZATION
# ============================================================

def load_config():
    """Load and validate the embedding configuration."""

    if not CONFIG_FILE.exists():
        raise FileNotFoundError(f"Configuration not found: {CONFIG_FILE}")

    with open(CONFIG_FILE, "r", encoding="utf-8") as file:
        config = json.load(file)

    required_fields = ["provider", "model", "dimensions", "batch_size"]

    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing configuration field: {field}")

    if config["provider"].lower() != "google":
        raise ValueError("This service currently supports Google Gemini.")

    if int(config["dimensions"]) <= 0 or int(config["batch_size"]) <= 0:
        raise ValueError("Dimensions and batch size must be positive.")

    return config


def initialize_client():
    """Initialize the Gemini embedding client."""

    api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY is missing from .env.")

    return genai.Client(api_key=api_key)


# ============================================================
# 3. CHUNK LOADING AND VALIDATION
# ============================================================

def load_chunks():
    """Load selected chunks and validate their required fields."""

    if not CHUNKS_FILE.exists():
        raise FileNotFoundError(f"Chunks file not found: {CHUNKS_FILE}")

    chunks = []

    with open(CHUNKS_FILE, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                chunk = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(
                    f"Invalid JSON on line {line_number}: {error}"
                ) from error

            validate_chunk(chunk, line_number)
            chunks.append(chunk)

    if not chunks:
        raise ValueError("No chunks were found.")

    validate_unique_chunk_ids(chunks)

    return chunks


def validate_chunk(chunk, line_number):
    """Validate the required fields of an individual chunk."""

    required_fields = ["chunk_id", "source_id", "text"]

    for field in required_fields:
        if not chunk.get(field):
            raise ValueError(
                f"Chunk on line {line_number} is missing {field}."
            )

    if not isinstance(chunk["text"], str):
        raise ValueError(f"Chunk text on line {line_number} must be a string.")


def validate_unique_chunk_ids(chunks):
    """Ensure every chunk has a unique identifier."""

    chunk_ids = [chunk["chunk_id"] for chunk in chunks]

    if len(chunk_ids) != len(set(chunk_ids)):
        raise ValueError("Duplicate chunk_id values detected.")


# ============================================================
# 4. EMBEDDING UTILITIES
# ============================================================

def normalize_vector(vector):
    """Normalize an embedding vector."""

    magnitude = sum(value * value for value in vector) ** 0.5

    if magnitude == 0:
        raise ValueError("Cannot normalize a zero-length vector.")

    return [value / magnitude for value in vector]


def validate_embedding(vector, dimensions):
    """Validate embedding dimensions and values."""

    if len(vector) != dimensions:
        raise ValueError(
            f"Expected {dimensions} dimensions, received {len(vector)}."
        )

    if not all(isinstance(value, (int, float)) for value in vector):
        raise ValueError("Embedding contains non-numeric values.")

    return True


# ============================================================
# 5. CHECKPOINT MANAGEMENT
# ============================================================

def load_checkpoint():
    """Load previously generated embeddings from JSONL."""

    cached_embeddings = {}

    if not CHECKPOINT_FILE.exists():
        return cached_embeddings

    with open(CHECKPOINT_FILE, "r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            if not line.strip():
                continue

            try:
                record = json.loads(line)
                chunk_id = record.get("chunk_id")

                if chunk_id:
                    cached_embeddings[chunk_id] = record

            except json.JSONDecodeError:
                print(f"Skipping invalid checkpoint line {line_number}.")

    return cached_embeddings


def is_valid_cached_record(record, chunk, model, dimensions):
    """Determine whether a cached embedding can be reused."""

    if record.get("model") != model:
        return False

    if record.get("dimensions") != dimensions:
        return False

    cached_chunk = record.get("chunk", {})

    if cached_chunk.get("text") != chunk.get("text"):
        return False

    embedding = record.get("embedding")

    if not isinstance(embedding, list):
        return False

    if len(embedding) != dimensions:
        return False

    return True


def create_checkpoint_record(chunk, vector, model, dimensions):
    """Create a standardized checkpoint record."""

    return {
        "chunk_id": chunk["chunk_id"],
        "source_id": chunk["source_id"],
        "model": model,
        "dimensions": dimensions,
        "chunk": chunk,
        "embedding": vector,
    }


def save_checkpoint(records):
    """Append successful embeddings to the checkpoint file."""

    with open(CHECKPOINT_FILE, "a", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record) + "\n")

        file.flush()
        os.fsync(file.fileno())


# ============================================================
# 6. GEMINI RATE-LIMIT AND RETRY HANDLING
# ============================================================

def is_rate_limit_error(error):
    """Identify Gemini rate-limit responses."""

    message = str(error).lower()

    return any(
        indicator in message
        for indicator in ["429", "resource_exhausted", "quota"]
    )


def get_retry_delay(error_message):
    """Extract the retry delay supplied by Gemini."""

    patterns = [
        r"retry in\s+(\d+(?:\.\d+)?)\s*s",
        r"retryDelay['\"]?\s*[:=]\s*['\"]?(\d+(?:\.\d+)?)s",
    ]

    for pattern in patterns:
        match = re.search(pattern, error_message, re.IGNORECASE)

        if match:
            return float(match.group(1))

    return None


def wait_before_retry(error, attempt):
    """Determine how long to wait before another API request."""

    if is_rate_limit_error(error):
        server_delay = get_retry_delay(str(error))

        return max(60, server_delay + 5 if server_delay else 60)

    return 2 ** attempt


# ============================================================
# 7. GEMINI EMBEDDING REQUEST
# ============================================================

def embed_batch(client, model, texts, dimensions):
    """Request embeddings for a batch of document text."""

    embed_config = types.EmbedContentConfig(
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=dimensions,
    )

    response = client.models.embed_content(
        model=model,
        contents=texts,
        config=embed_config,
    )

    if not response.embeddings:
        raise ValueError("Gemini returned no embeddings.")

    if len(response.embeddings) != len(texts):
        raise ValueError("Embedding count does not match batch size.")

    return response.embeddings


def embed_batch_with_retry(
    client,
    model,
    texts,
    dimensions,
    metrics,
    max_attempts=5,
):
    """Request embeddings with retry handling."""

    for attempt in range(1, max_attempts + 1):
        try:
            metrics["api_calls"] += 1

            return embed_batch(
                client,
                model,
                texts,
                dimensions,
            )

        except Exception as error:
            if attempt == max_attempts:
                raise

            wait_seconds = wait_before_retry(error, attempt)

            print(
                f"Embedding request failed: {error}\n"
                f"Retrying in {wait_seconds:.0f} seconds "
                f"(attempt {attempt + 1}/{max_attempts})..."
            )

            time.sleep(wait_seconds)


# ============================================================
# 8. BATCH PROCESSING
# ============================================================

def build_batch_records(
    batch,
    embeddings,
    model,
    dimensions,
    should_normalize,
):
    """Validate vectors and prepare checkpoint records."""

    records = []

    for chunk, embedding_result in zip(batch, embeddings):
        vector = list(embedding_result.values)

        validate_embedding(vector, dimensions)

        if should_normalize:
            vector = normalize_vector(vector)

        record = create_checkpoint_record(
            chunk,
            vector,
            model,
            dimensions,
        )

        records.append(record)

    return records


def process_batch(
    batch,
    client,
    config,
    metrics,
):
    """Generate and validate embeddings for one batch."""

    texts = [chunk["text"] for chunk in batch]

    embeddings = embed_batch_with_retry(
        client=client,
        model=config["model"],
        texts=texts,
        dimensions=config["dimensions"],
        metrics=metrics,
    )

    return build_batch_records(
        batch=batch,
        embeddings=embeddings,
        model=config["model"],
        dimensions=config["dimensions"],
        should_normalize=config.get("normalize", True),
    )


def record_failed_batch(batch, error):
    """Record the chunks affected by a failed batch."""

    return [
        {
            "chunk_id": chunk["chunk_id"],
            "source_id": chunk["source_id"],
            "error": str(error),
        }
        for chunk in batch
    ]


# ============================================================
# 9. EMBEDDING PIPELINE
# ============================================================

def generate_embeddings(chunks, config, client):
    """Generate embeddings while reusing valid checkpoints."""

    model = config["model"]
    dimensions = int(config["dimensions"])
    batch_size = int(config["batch_size"])

    cached_embeddings = load_checkpoint()

    results = []
    chunks_to_process = []

    metrics = {
        "api_calls": 0,
        "batches_attempted": 0,
    }

    # Reuse cached embeddings where possible.
    for chunk in chunks:
        record = cached_embeddings.get(chunk["chunk_id"])

        if record and is_valid_cached_record(
            record,
            chunk,
            model,
            dimensions,
        ):
            results.append({
                "chunk": chunk,
                "embedding": record["embedding"],
            })
        else:
            chunks_to_process.append(chunk)

    print(f"Cached embeddings: {len(results)}")
    print(f"Remaining chunks: {len(chunks_to_process)}")

    failed_chunks = []
    items_since_pause = 0

    # Process only chunks that do not have valid cached embeddings.
    for start in range(0, len(chunks_to_process), batch_size):
        batch = chunks_to_process[start:start + batch_size]
        batch_number = metrics["batches_attempted"] + 1

        # Pause after approximately 90 processed items.
        if items_since_pause >= 90:
            print("Rate-limit safety pause: 65 seconds.")
            time.sleep(65)
            items_since_pause = 0

        metrics["batches_attempted"] += 1

        print(
            f"\nProcessing batch {batch_number}: "
            f"{len(batch)} chunks"
        )

        try:
            records = process_batch(
                batch=batch,
                client=client,
                config=config,
                metrics=metrics,
            )

            # Persist each successful batch immediately.
            save_checkpoint(records)

            results.extend([
                {
                    "chunk": record["chunk"],
                    "embedding": record["embedding"],
                }
                for record in records
            ])

            items_since_pause += len(batch)

            print(f"Saved {len(records)} embeddings.")

        except Exception as error:
            print(f"Batch {batch_number} failed: {error}")

            failed_chunks.extend(
                record_failed_batch(batch, error)
            )

    return {
        "results": results,
        "failed_chunks": failed_chunks,
        "metrics": metrics,
    }


# ============================================================
# 10. RUN SUMMARY
# ============================================================

def save_run_summary(
    started_at,
    completed_at,
    duration_seconds,
    chunks,
    output,
    config,
):
    """Save pipeline execution statistics."""

    results = output["results"]
    failed_chunks = output["failed_chunks"]
    metrics = output["metrics"]

    all_chunks_embedded = len(results) == len(chunks)

    summary = {
        "started_at": started_at,
        "completed_at": completed_at,
        "duration_seconds": round(duration_seconds, 2),
        "provider": config["provider"],
        "model": config["model"],
        "dimensions": config["dimensions"],
        "batch_size": config["batch_size"],
        "normalize": config.get("normalize", True),
        "input_chunks": len(chunks),
        "embeddings_available": len(results),
        "failed_chunks": len(failed_chunks),
        "batches_attempted": metrics["batches_attempted"],
        "api_calls": metrics["api_calls"],
        "usage_metadata": None,
        "cost": None,
        "usage_note": (
            "Token usage and cost were not exposed by the embedding "
            "response. Consult provider usage records if cost evidence "
            "is required."
        ),
        "checkpoint_file": str(CHECKPOINT_FILE),
        "status": (
            "completed"
            if all_chunks_embedded and not failed_chunks
            else "completed_with_failures"
        ),
        "failures": failed_chunks,
    }

    with open(RUN_LOG_FILE, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    return summary


# ============================================================
# 11. MAIN EXECUTION
# ============================================================

def main():
    """Execute the complete embedding pipeline."""

    start_time = time.time()
    started_at = datetime.now(timezone.utc).isoformat()

    print("Starting embedding pipeline...\n")

    config = load_config()
    client = initialize_client()
    chunks = load_chunks()

    print(f"Loaded chunks: {len(chunks)}")
    print(f"Provider: {config['provider']}")
    print(f"Model: {config['model']}")
    print(f"Dimensions: {config['dimensions']}")
    print(f"Batch size: {config['batch_size']}")

    output = generate_embeddings(
        chunks=chunks,
        config=config,
        client=client,
    )

    duration = time.time() - start_time
    completed_at = datetime.now(timezone.utc).isoformat()

    summary = save_run_summary(
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=duration,
        chunks=chunks,
        output=output,
        config=config,
    )

    print("\n" + "=" * 50)
    print("EMBEDDING PIPELINE SUMMARY")
    print("=" * 50)

    print(f"Input chunks: {len(chunks)}")
    print(f"Embeddings available: {len(output['results'])}")
    print(f"Failed chunks: {len(output['failed_chunks'])}")
    print(f"API calls: {output['metrics']['api_calls']}")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Status: {summary['status']}")

    print(f"\nCheckpoint: {CHECKPOINT_FILE}")
    print(f"Run summary: {RUN_LOG_FILE}")

    if summary["status"] == "completed":
        print("\nAll chunks have valid embeddings.")
    else:
        print("\nSome chunks failed. Rerun to retry uncached chunks.")


if __name__ == "__main__":
    main()
