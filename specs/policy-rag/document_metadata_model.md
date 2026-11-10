# Metadata Model

## Document fields

Each document must have metadata identifying its source, classification, version, approval status, and access restrictions.

| Field | Data Type | Required | Description |
|---|---|---|---|
| `source_id` | String | Yes | Stable, unique identifier for the source document. Must match the approved manifest. |
| `title` | String | Yes | Official title of the source document. |
| `document_type` | String | Yes | Document classification used by retrieval filtering. |
| `category` | String | Yes | Subject or business category, distinct from document type. |
| `version` | String | Yes | Version of the source document. |
| `effective_date` | Date | Yes | Date the document version becomes applicable. |
| `status` | String | Yes | Approval/lifecycle status of the document. |
| `access_label` | String | Yes | Access-control classification used by retrieval filtering. |
| `checksum` | String | Yes | SHA-256 hash used to verify document integrity. |

## Chunk fields

Each document is divided into smaller chunks for retrieval. Every chunk must retain a reference to its original document and section.

| Field | Data Type | Required | Description |
|---|---|---|---|
| `chunk_id` | String | Yes | Unique identifier for each chunk. |
| `source_id` | String | Yes | References the original document's source ID. |
| `section_title` | String | Yes | Exact heading or section from which the chunk originated. |
| `sequence` | Integer | Yes | Position of the chunk within its section. |
| `access_label` | String | Yes | Inherits the access label from the parent document. |
| `version` | String | Yes | Version of the parent document. |
| `effective_date` | Date | Yes | Effective date inherited from the parent document. |
| `status` | String | Yes | Approval status inherited from the parent document. |
| `chunk_text` | String | Yes | Actual text content stored in the chunk. |

## Validation rules

- `source_id` must be unique and match an entry in the approved knowledge-base manifest.
- `title`, `document_type`, `category`, `version`, `effective_date`, `status`, `access_label`, and `checksum` must be populated.
- `document_type` must match an approved document classification.
- `version` must match the version recorded in the approved manifest.
- `effective_date` must use the YYYY-MM-DD date format.
- `status` must equal `Approved` before a document can be used as current policy evidence.
- `access_label` must match the approved manifest.
- `checksum` must contain a valid SHA-256 hash.
- Every `chunk_id` must be unique.
- Every chunk must reference an existing `source_id`.
- `section_title` must identify the actual source section.
- `sequence` must be a positive integer.
- Chunk metadata must match the parent document's version, effective date, status, and access label.
- Superseded documents must not be used as current policy authority.

## Access filtering

The retrieval process must support the following metadata filters:

- `document_type`: Filters documents by classification.
- `version`: Identifies the applicable approved document version.
- `effective_date`: Ensures the document is effective for the requested policy date.
- `status`: Ensures only approved sources are used as current policy evidence.
- `access_label`: Restricts evidence to users authorized to access its classification.

Access filtering must occur before evidence is disclosed to the requester.

The retrieval contract must use the exact same metadata field names.

## Citation mapping

Every retrieved chunk must be traceable to its original document and section.

Policy citations must expose:

- `source_id`
- `title`
- `version`
- `effective_date`
- `section_title`
- `chunk_id`

The source's `status` and `access_label` must also be available for authority and authorization validation.

Citation resolution must follow this relationship:

`chunk_id` → `source_id` → document metadata → approved source document.

A citation must resolve to the exact source and passage used to support the generated recommendation. Missing, mismatched, or unsupported citations must be rejected.