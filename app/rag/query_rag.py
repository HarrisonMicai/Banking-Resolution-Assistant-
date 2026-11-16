
import os
from datetime import date
from pathlib import Path

import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types

from app.rag.retrieval_policy import (
    build_policy_filter,
    get_permitted_labels,
)


# ============================================================
# 1. CONFIGURATION
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
CHROMA_DIR = BASE_DIR / "data" / "chroma_db"

load_dotenv(BASE_DIR / ".env", override=True)

EMBEDDING_MODEL = "gemini-embedding-001"
GENERATION_MODEL = "gemini-3.8-flash"

DIMENSIONS = 768
TOP_K = 5

# Initial threshold for cosine distance.
# Lower distances indicate more similar results.
MAX_DISTANCE = 0.65

# Demo user role.
# Internal users can access approved Public and Internal documents.
USER_ACCESS = "Internal"


# ============================================================
# 2. INITIALIZE CLIENTS
# ============================================================

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise RuntimeError(
        "GOOGLE_API_KEY is missing from app/rag/.env"
    )

client = genai.Client(api_key=api_key)

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

collection = chroma_client.get_collection(
    name="banking_complaints"
)


# ============================================================
# 4. QUESTION EMBEDDING
# ============================================================

def embed_question(question):
    """Convert a user question into a Gemini query embedding."""

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=DIMENSIONS,
        ),
    )

    return response.embeddings[0].values


# ============================================================
# 5. DOCUMENT RETRIEVAL AND FILTERING
# ============================================================

def retrieve_context(question, user_access=USER_ACCESS, as_of_date=None):
    """
    Retrieve relevant documents using ChromaDB.

    Filters:
    - Only Approved documents.
    - Only documents permitted by user access level.
    - Exclude Casebook sources and sources effective after the policy date.
    - Only results below the configured distance threshold.
    """

    query_vector = embed_question(question)

    permitted_labels = get_permitted_labels(user_access)
    policy_date = as_of_date or date.today()

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=TOP_K,
        where=build_policy_filter(permitted_labels, policy_date),
        include=[
            "documents",
            "metadatas",
            "distances",
        ],
    )

    retrieved = []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for index, document in enumerate(documents):

        metadata = metadatas[index] or {}
        distance = distances[index]

        # Similarity threshold.
        if distance > MAX_DISTANCE:
            continue

        retrieved.append({
            "text": document,
            "source_id": metadata.get("source_id", "Unknown"),
            "title": metadata.get("title", "Untitled"),
            "section": metadata.get(
                "section_title",
                "Unknown"
            ),
            "access_label": metadata.get(
                "access_label",
                "Unknown"
            ),
            "status": metadata.get(
                "status",
                "Unknown"
            ),
            "distance": distance,
        })

    return retrieved


# ============================================================
# 6. QUESTION CLASSIFICATION
# ============================================================

def classify_question(question):
    """
    Basic keyword-based restricted-request guardrail.

    Actual document authorization is enforced separately
    through ChromaDB metadata filters.
    """

    restricted_terms = [
        "customer password",
        "social security number",
        "private account information",
        "confidential customer account",
        "internal credentials",
    ]

    normalized = question.lower()

    if any(term in normalized for term in restricted_terms):
        return "FILTERED"

    return "PENDING"


# ============================================================
# 7. ANSWER GENERATION
# ============================================================

def generate_answer(question, retrieved):
    """Generate an answer grounded in retrieved documents."""

    context = "\n\n".join(
        f"""
Source ID: {item['source_id']}
Document: {item['title']}
Section: {item['section']}
Access Label: {item['access_label']}
Content:
{item['text']}
"""
        for item in retrieved
    )

    prompt = f"""
You are a Banking Complaint Resolution Assistant.

Answer the user's question using ONLY the approved
knowledge-base context provided below.

REQUIREMENTS:

1. Do not invent banking policies, procedures, or thresholds.
2. Do not use outside knowledge to fill missing information.
3. Explain the answer clearly and professionally.
4. Cite the source IDs supporting your answer.
5. If the context does not adequately answer the question,
   state that there is insufficient information.
6. Do not reveal information beyond the retrieved context.

KNOWLEDGE BASE CONTEXT:

{context}

USER QUESTION:

{question}

Provide your answer:
"""

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=prompt,
    )

    return response.text or (
        "I could not generate a response from the available context."
    )


# ============================================================
# 8. COMPLETE RAG QUESTION WORKFLOW
# ============================================================

def ask_question(question):

    print("\n" + "=" * 65)
    print("BANKING COMPLAINT RESOLUTION ASSISTANT")
    print("=" * 65)

    # Step 1: Basic restricted-request guardrail.
    classification = classify_question(question)

    if classification == "FILTERED":

        print("\nCLASSIFICATION: FILTERED")
        print("Reason: The request involves restricted information.")
        print("Response: I cannot provide that information.")

        return

    # Step 2: Retrieve approved and authorized context.
    print("\nStep 1: Embedding user question...")
    print("Step 2: Searching ChromaDB...")

    retrieved = retrieve_context(
        question,
        user_access=USER_ACCESS,
    )

    # Step 3: Determine whether sufficient context was retrieved.
    if not retrieved:

        print("\nCLASSIFICATION: UNSUPPORTED")
        print("No sufficiently relevant approved documents found.")
        print(
            "Response: I don't have sufficient information "
            "in the knowledge base to answer that question."
        )

        return

    print("\nCLASSIFICATION: SUPPORTED")

    # Step 4: Display retrieval results.
    print("\n" + "-" * 65)
    print("RETRIEVED KNOWLEDGE BASE SOURCES")
    print("-" * 65)

    for index, item in enumerate(retrieved, start=1):

        print(f"\nSource {index}")
        print(f"Source ID: {item['source_id']}")
        print(f"Title: {item['title']}")
        print(f"Section: {item['section']}")
        print(f"Access: {item['access_label']}")
        print(f"Status: {item['status']}")
        print(f"Cosine Distance: {item['distance']:.4f}")

        print("\nRetrieved Content:")
        print(item["text"][:400])

    # Step 5: Generate answer.
    print("\n" + "-" * 65)
    print("GENERATING GROUNDED RESPONSE...")
    print("-" * 65)

    answer = generate_answer(question, retrieved)

    print("\nASSISTANT RESPONSE")
    print("-" * 65)
    print(answer)

    print("\n" + "=" * 65)


# ============================================================
# 9. INTERACTIVE TERMINAL DEMO
# ============================================================

def main():

    print("\n" + "=" * 65)
    print("BANKING COMPLAINT RESOLUTION ASSISTANT")
    print("=" * 65)

    print(f"Vector Collection: {collection.name}")
    print(f"Indexed Chunks: {collection.count()}")
    print(f"Embedding Model: {EMBEDDING_MODEL}")
    print(f"Generation Model: {GENERATION_MODEL}")
    print(f"User Access Level: {USER_ACCESS}")

    print("\nAvailable commands:")
    print("  Type a question to query the knowledge base.")
    print("  Type 'exit' to quit.")

    while True:

        question = input("\nYour question: ").strip()

        if question.lower() in ["exit", "quit"]:
            print("\nClosing Banking Assistant.")
            break

        if not question:
            continue

        try:
            ask_question(question)

        except Exception as error:
            print(f"\nError processing question: {error}")


if __name__ == "__main__":
    main()
