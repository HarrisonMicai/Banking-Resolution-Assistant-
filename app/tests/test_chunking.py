import json
from pathlib import Path

path = Path("app/rag/data/processed/chunks_selected.jsonl")

print(f"Testing chunk file: {path}")

targets = {
    "KB-002": "3. Financial Redress Thresholds",
    "KB-003": "2. Required Intake Fields",
    "KB-004": "4. Security Escalation Indicators"
}

with path.open(encoding="utf-8") as f:
    chunks = [json.loads(line) for line in f]

for source, section in targets.items():
    matches = [
        c for c in chunks
        if c.get("source_id") == source
        and c.get("section_title") == section
    ]

    print(f"\n{source} | {section}")
    print("Matching chunks:", len(matches))

    for chunk in matches:
        print("Chunk ID:", chunk["chunk_id"])
        print("Text:", chunk["text"][:350])


import json
from pathlib import Path

path = Path("app/rag/data/processed/chunks_selected.jsonl")

with path.open("r", encoding="utf-8") as file:
    chunks = [json.loads(line) for line in file]

for chunk in chunks:
    if chunk.get("source_id") == "KB-002":
        print("\nSection:", repr(chunk.get("section_title")))
        print("Chunk ID:", chunk.get("chunk_id"))
        print("Text:", chunk.get("text"))