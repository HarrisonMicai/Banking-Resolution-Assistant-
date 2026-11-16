
# Retrieval Service API Contract

## 1. Purpose

The Retrieval Service provides semantic search over the approved banking complaint knowledge base.

It supports:
- Semantic retrieval using Gemini embeddings.
- Configurable top-k results.
- Metadata filtering.
- Optional deterministic lexical reranking.
- Inspectable retrieval scores and source metadata.

## 2. Implementation

**Module:** `app/rag/retrieval_service.py`

**Class:** `RetrievalService`

**Method:** `retrieve()`

## 3. Request Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| query | string | Yes | User question or search query |
| top_k | integer | No | Maximum number of results. Default: 5 |
| document_type | string | No | Filter by document type |
| version | string | No | Filter by document version |
| access_label | string | No | Filter by access classification |
| rerank | boolean | No | Enable lexical reranking. Default: false |

Example:

```python
results = service.retrieve(
    query="When is supervisor approval required?",
    top_k=5,
    document_type="Policy",
    access_label="Restricted",
    rerank=True
)
```

## 4. Metadata Filtering

All retrieval requests include the following condition:

- `status = Approved`

Optional filters:
- `document_type`
- `version`
- `access_label`

Multiple filters are combined using logical AND.

Only documents satisfying all supplied conditions are returned.

Access-label filtering is not a substitute for authorization. The calling application must enforce the requesting user's permissions.

## 5. Response Structure

The method returns a list of result dictionaries.

Each result contains:

| Field | Type | Description |
|---|---|---|
| text | string | Retrieved document chunk |
| score | float | Original semantic similarity score |
| original_score | float | Original semantic similarity score before reranking |
| distance | float | ChromaDB vector distance |
| rerank_score | float or null | Lexical Jaccard similarity when reranking is enabled |
| rerank_rank | integer or null | Position after reranking |
| keyword_overlap | integer or null | Number of overlapping query and document terms |
| metadata | object | Source and document metadata |

The semantic similarity score is calculated as:

`score = 1 - distance`

When reranking is disabled, reranking fields remain null.

When enabled, results are sorted by lexical Jaccard similarity, with original semantic similarity used as a tie-breaker.

## 6. Example Response

```json
[
  {
    "text": "Supervisor approval is required for certain complaint outcomes.",
    "score": 0.75,
    "original_score": 0.75,
    "distance": 0.25,
    "rerank_score": 0.12,
    "rerank_rank": 1,
    "keyword_overlap": 2,
    "metadata": {
      "source_id": "KB-002",
      "document_type": "Policy",
      "version": "2.1",
      "access_label": "Restricted",
      "status": "Approved"
    }
  }
]
```

*Example values are illustrative, not measured retrieval output.*

## 7. Error Handling

| Condition | Expected behavior |
|---|---|
| Empty or whitespace-only query | Raise ValueError |
| Invalid top_k | Raise ValueError |
| No matching documents | Return an empty list |
| Embedding service unavailable | Raise RuntimeError |
| Vector store unavailable | Raise RuntimeError |
| Retrieval operation fails | Raise RuntimeError |

## 8. Dependencies

- ChromaDB persistent vector store
- Gemini embedding model: `gemini-embedding-001`
- Embedding dimensionality: 768
- Approved knowledge-base documents and metadata

## 9. Downstream Integration

The retrieval service is intended to be called by a downstream answer-generation component.

The downstream component should:
1. Submit the user's question.
2. Receive the retrieved chunks and metadata.
3. Use the returned evidence to generate a grounded answer.
4. Preserve source IDs for citations and traceability.
5. Avoid generating unsupported claims when evidence is insufficient.

## 10. Testing

Automated tests are located at:

`app/tests/test_retrieval.py`

Run them from the repository root:

```powershell
python -m pytest app/tests/test_retrieval.py -v
```
