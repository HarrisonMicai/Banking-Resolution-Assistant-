Vector Index Strategy
Banking Complaint Resolution Agent — Exercise 4.1.2
1. Purpose
Define the logical vector, text, and metadata indexes required to retrieve approved policy evidence while preserving exact source, version, section, citation, and access-control traceability.

This is a logical index design. The approved specification intentionally does not prescribe a storage technology, vector engine, text-search engine, retrieval algorithm, model, or API shape.
2. Indexes
A. Vector index
Indexed content: chunk_text for each eligible chunk.

Associated metadata: chunk_id, source_id, title, document_type, category, version, effective_date, status, access_label, section_title, and sequence.

Purpose: Support meaning-based retrieval for natural-language questions, section-specific questions, and overlapping-topic queries. Retrieval relevance must not depend only on a unique document keyword (REQ-003).

Eligibility: Only chunks whose parent source identity matches the approved manifest may enter the current evidence index. Superseded material and historical cases must not be treated as current policy authority. Restricted chunks must remain subject to authorization filtering.
B. Text index
Indexed content: chunk_text, title, and section_title; optionally the stable identifiers source_id and chunk_id for exact-source lookup.

Purpose:
- Exact title/source questions.
- Exact source ID lookups.
- Exact section/heading searches.
- Keyword and phrase matching to complement semantic retrieval.
- Citation and source navigation.
The text index must not make a source authoritative merely because it matches a query. Authority is determined by manifest validation, status, version/effective-date applicability, and the source precedence rules.
C. Metadata index
Create filterable metadata indexes for:
Field	Purpose
source_id	Resolve a source and validate manifest identity
document_type	Filter by Policy, Playbook, Guide, FAQ, Casebook, or Bulletin
category	Narrow by subject/business category
version	Select the applicable source version
effective_date	Exclude versions not yet effective for the relevant date
status	Require Approved for current policy evidence and exclude superseded/unapproved sources
access_label	Enforce authorization before evidence is disclosed
section_title	Support section-specific retrieval and citation
chunk_id	Resolve and validate the exact cited passage


3. Required retrieval filters
The retrieval contract must use the exact metadata field names below. Do not rename document_type to type, effective_date to date, or access_label to access.
Required filters for current policy evidence
1. Source identity: source_id must exist in the approved manifest and match the registered document.
2. Approval: status must equal Approved.
3. Document type: apply document_type when the query or retrieval workflow requests a type-specific scope.
4. Version: version must identify the applicable approved version of the source.
5. Effective date: effective_date must be on or before the date for which the policy question is being evaluated. Do not select a future-effective version.
6. Access: access_label must be authorized for the authenticated requester. Apply this filter before evidence is disclosed, not only in the user interface.
7. Authority class: exclude superseded material and prevent Casebook/historical content from being treated as policy authority. Apply the KB-GUIDE precedence rules to bulletins and FAQs.
Example logical filter
status = "Approved"
AND effective_date <= requested_policy_date
AND access_label IN requester_authorized_labels
AND document_type IN requested_document_types
The retrieval process must additionally validate source_id against the approved manifest and apply the source/version/authority rules. The expression above is illustrative; it is not a prescribed API or query language.
4. Retrieval and citation flow
1. Authenticate the requester and determine authorized access_label values.
2. Validate candidate sources against the approved manifest.
3. Apply status, document_type, version, effective_date, and access_label filters using the exact field names.
4. Retrieve candidate chunks through semantic and/or text retrieval.
5. Validate each chunk's source_id and denormalized metadata against its parent document record.
6. Apply source authority and precedence rules. Do not treat historical cases as precedent, FAQs as overriding policy, or superseded content as current authority.
7. Resolve the citation through chunk_id to the exact section_title and source passage.
8. Verify that the citation metadata supports the assertion. Reject invented, mismatched, or unsupported citations.
9. If evidence is missing, insufficient, unavailable, unauthorized, or conflicting, abstain from the unsupported conclusion and preserve human review.
5. Required retrieval evaluation
The index design must support the approved specification's evaluation scenarios:
- Exact title/source question.
- Natural-language question without a document name.
- Section-specific question, returning section_title and chunk_id.
- Overlapping topics, respecting primary authority and supporting sources.
- No-answer question, with abstention.
- Superseded-source negative test for KB-001-OLD.
- Conflicting-current-source route to the policy owner.
- Restricted-source filter based on access_label.
- FAQ versus authoritative policy.
- Historical-case similarity without treating KB-010 as precedent.
The aggregate target in REQ-003 is at least 90% retrieval of at least one applicable policy across the agreed, human-labeled cases that have an applicable policy. Record the denominator and evaluate exact-source, natural-language, section-specific, and overlapping-topic queries.
6. Required release controls
All six release tests are release gates; any failure blocks release:
1. Unlisted source test.
2. Retrieved prompt-injection test.
3. Invented citation test.
4. No-evidence abstention test.
5. Conflicting-current-source test.
6. Superseded-source filtering test.
Retrieved passages are evidence, not instructions. Embedded instructions must not alter authorization, reveal secrets, or bypass required approvals.
7. Field-name contract
The following names must remain consistent across document metadata, chunk metadata, index filters, and retrieval results:

source_id, title, document_type, category, version, effective_date, status, access_label, checksum, chunk_id, section_title, sequence, chunk_text.

Policy citation output must expose at least:

source_id, title, version, effective_date, section_title, chunk_id.

status and access_label must be available to authority and authorization checks even if they are not displayed in the final citation.
8. Implementation dependencies / limitations
- The uploaded inventory does not provide source checksums or status.
- The actual source documents and approved manifest are needed to validate source identity, exact section headings, and checksums.
- The exact requester role-to-`access_label` authorization mapping remains unresolved in the supplied specification; this strategy requires authorization labels to be supplied by the authentication/authorization layer.
- No specific vector database, full-text engine, embedding model, chunking algorithm, or API is selected here because the approved specification does not prescribe one.