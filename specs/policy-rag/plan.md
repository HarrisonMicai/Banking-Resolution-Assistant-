# Implementation Plan: Policy RAG Behavior

**Spec:** [spec.md](./spec.md) | **Clarifications:** [clarification-log.md](./clarification-log.md)
**Status:** Behavior-level plan; technical design and code locations are
intentionally deferred.
**Knowledge base guide:** [KB-GUIDE v1.0](./KB-GUIDE.md), approved synthetic
training content only. **Operational bulletins:** [BUL-2026-01 v1.0](./BUL-2026-01.md)
(Internal) and [BUL-2026-02 v1.0](./BUL-2026-02.md) (Restricted), both approved
synthetic training content.

## Summary

Implement and validate the behavior in the source-of-truth RAG contract:
retrieve only approved evidence, keep verified facts distinct from policy
evidence and generated analysis, cite evidence with traceable provenance,
abstain safely when evidence is missing or unsupported, and preserve human
review and audit boundaries.

This plan does not choose an AI model, search/indexing approach, storage
technology, API contract, or source-code structure. Those choices require
architecture and source-governance inputs that are not present in this spec
pack.

## Constraints and prerequisites

- `spec.md` is the behavior contract; implementation and QA must not redefine
  its acceptance criteria.
- Use only approved policy sources and approved operational systems.
- For the training corpus, follow the KB-GUIDE source map and authority rules:
  current approved policy/playbooks govern within scope; bulletins clarify
  unless explicit replacement is stated; FAQs summarize; KB-010 is not
  precedent; KB-001-OLD is superseded.
- Apply BUL-2026-02's source-manifest verification, retrieved-content trust
  boundary, citation validation, superseded-source filtering, abstention, and
  release tests.
- Apply BUL-2026-01's KB-002 threshold clarification only to proposed
  compensation amounts; keep disputed transaction amount distinct and retain
  the bulletin's exact CAD boundary outcomes.
- Honor BUL-2026-02's Restricted classification; training approval does not
  resolve the role-to-access-label matrix.
- Do not treat KB-GUIDE's synthetic approval as approval for production
  systems, repositories, or data.
- Development and test data must be synthetic or approved training data.
- Resolve the open source inventory, authorization matrix, evaluation corpus,
  scenario requirements, and citation presentation in
  [clarification-log.md](./clarification-log.md) before production access or
  final sign-off.
- The current repository does not include a RAG architecture/design artifact.
  Exact implementation files, interfaces, and test infrastructure must be
  selected in a separate architecture step, not guessed here.
- The current API documentation says authentication is disabled. REQ-008 is a
  target security requirement, not a claim about current runtime behavior;
  do not expose customer or policy data until the required access controls are
  in place.

## Implementation steps

### Phase 1 — Close source and access decisions

#### Plan 1.1 — Approve source inventory and access boundary

- **Requirements:** REQ-001, REQ-008, REQ-012
- **Spec references:** Source and access boundaries; Preconditions; FR-3; NFR
  Security and Privacy
- **Work:** Record named approved policy repositories and operational systems,
  their approval owner, and role-based read/action permissions. Preserve the
  stated constraint that source categories alone do not authorize a source.
  Record the KB-GUIDE synthetic source map separately from any production
  source inventory.
- **Exit evidence:** Source allowlist and role matrix are approved and
  traceable to the open questions in CL-RAG-006 and CL-RAG-007.

#### Plan 1.2 — Finalize scenario and evaluation definitions

- **Requirements:** REQ-003, REQ-005, REQ-007, REQ-013
- **Spec references:** REQ-003, REQ-005, REQ-007; CL-RAG-009 through CL-RAG-011
- **Work:** Approve representative labeled test cases, supported/unsupported
  question examples, and scenario-specific required information/evidence.
  Include each of the ten retrieval scenarios in the source-of-truth spec.
  Retain the carried-forward 90% retrieval target unless the product owner
  changes it through a spec update.
- **Exit evidence:** QA can identify the retrieval denominator, applicable
  policies, missing-information cases, and unsupported cases without
  interpretation.

#### Plan 1.3 — Finalize citation presentation

- **Requirements:** REQ-004
- **Spec references:** Citation and metadata contract; CL-RAG-001 and
  CL-RAG-008
- **Work:** Confirm user-facing citation presentation and operational-fact
  locator. Retain the KB-GUIDE policy metadata: `source_id`, `title`,
  `version`, `effective_date`, `status`, `access_label`, `section_title`, and
  `chunk_id`; expose the citation fields and use status/access labels for
  authority and access filtering.
- **Exit evidence:** Reviewers can verify each cited policy passage and
  operational fact against its approved source.

### Phase 2 — Implement grounded retrieval and evidence provenance

#### Plan 2.1 — Enforce approved retrieval scope

- **Requirements:** REQ-001, REQ-003, REQ-011, REQ-012
- **Spec references:** FR-3; BR-1; Source and access boundaries
- **Work:** Restrict evidence retrieval to the approved source inventory and
  filter by approved status, effective applicability, and requester access
  label; evaluate natural-language and overlapping-topic queries against the
  approved labeled cases. Retrieval design should account for metadata and
  query meaning and evaluate reranking as recommended by KB-GUIDE; the exact
  retrieval/reranking implementation remains an architecture decision.
- **Exit evidence:** No unapproved source appears in returned evidence and the
  retrieval benchmark meets the 90% target.

#### Plan 2.2 — Preserve evidence categories and traceability

- **Requirements:** REQ-002, REQ-004
- **Spec references:** FR-2; BR-2/3; IE-2; Citation and metadata contract
- **Work:** Keep verified operational facts, policy evidence, system analysis,
  and human decisions distinguishable. Attach source metadata and locators to
  evidence used by recommendations.
- **Exit evidence:** 100% of generated recommendations have verifiable
  supporting fact and policy references; evidence categories are correct in
  the labeled test set.

### Phase 3 — Implement safe answer and review behavior

#### Plan 3.1 — Abstain for missing, conflicting, or unsupported evidence

- **Requirements:** REQ-005, REQ-006, REQ-007, REQ-010, REQ-011
- **Spec references:** Safe behavior for unsupported requests; EC-3/4/5;
  NFR Reliability; related clarification CL-RAG-002
- **Work:** Withhold unsupported conclusions, identify the reason, flag
  conflicts, route current-authority conflicts to the policy owner, and
  preserve manual investigation when a dependency is unavailable. Apply the
  KB-GUIDE precedence rules for bulletins, FAQs, historical cases, and
  superseded sources.
- **Exit evidence:** No recommendation is produced for the contract's
  insufficient-evidence, conflict, unsupported-question, or dependency-failure
  cases.

#### Plan 3.2 — Preserve human decision and audit boundaries

- **Requirements:** REQ-008, REQ-009, REQ-010, REQ-013
- **Spec references:** Preconditions; NG-1; BR-4/5; NFR Security, Privacy,
  Auditability; IE-5/6
- **Work:** Apply the approved authorization matrix, keep recommendations as
  drafts, require human approval for gated actions, and retain audit evidence
  required by the contract.
- **Exit evidence:** Unauthorized access is denied; no final decision or
  gated action occurs without recorded human approval; retrieved sources and
  recommendations are auditable.

#### Plan 3.3 — Enforce retrieved-content integrity and trust boundary

- **Requirements:** REQ-004, REQ-009, REQ-012
- **Spec references:** Retrieved-content trust boundary and release controls;
  BUL-2026-02 Required Controls
- **Work:** Treat retrieved content as evidence only, ignore embedded
  instructions that attempt to change authorization, reveal secrets, or bypass
  approvals, validate source identities against the manifest, and validate
  each citation against retrieved metadata and its supporting passage.
- **Exit evidence:** All six BUL-2026-02 release tests pass; no unlisted source
  or unsupported citation is accepted, and retrieved text cannot bypass access
  or approval rules.

#### Plan 3.4 — Apply compensation thresholds without amount confusion

- **Requirements:** REQ-013
- **Spec references:** Compensation threshold evaluation scenarios;
  BUL-2026-01 Clarifications and Evaluation note; KB-GUIDE KB-002
- **Work:** Apply the stated boundary outcomes only to proposed compensation,
  preserve CAD currency and cent precision, and do not substitute a disputed
  transaction amount for a compensation proposal.
- **Exit evidence:** All four threshold amounts and the disputed-amount
  distinction produce exactly the outcomes specified in `spec.md`; required
  supervisor approval and senior escalation gates remain intact.

### Phase 4 — Acceptance verification

#### Plan 4.1 — Verify the behavior contract end-to-end

- **Requirements:** REQ-001 through REQ-013
- **Spec references:** All rows in Policy RAG Acceptance Criteria
- **Work:** Run the approved retrieval benchmark and the source, citation,
  evidence-separation, abstention, conflict, unsupported-question, access,
  human-approval, failure, and all six bulletin release scenarios.
- **Exit evidence:** Every acceptance criterion passes against the approved
  test set; deviations are resolved by updating the spec through its normal
  review rather than silently changing plan behavior.

## Testing strategy

- **Behavior under test:** Policy retrieval and grounded investigation
  recommendations, including safe abstention and human boundaries.
- **Test data:** Synthetic or approved training data only.
- **Required evidence:** Approved source inventory; labeled cases with
  applicable-policy labels; citations resolvable to source metadata; cases for
  missing information, no matching policy, conflicts, unsupported questions,
  unauthorized access, and unavailable AI/retrieval dependencies. Include
  every required scenario in `spec.md`: exact source/title, unnamed
  natural-language, section-specific, overlap, no-answer, superseded source,
  conflicting sources, restricted source, FAQ versus authority, and historical
  similarity. Also execute all six BUL-2026-02 release tests: unlisted source,
  retrieved prompt injection, invented citation, no-evidence abstention,
  conflicting current sources, and superseded-source filtering. Include all
  five BUL-2026-01 threshold cases.
- **Pass thresholds:** At least 90% applicable-policy retrieval on the agreed
  benchmark; 100% of generated recommendations contain verifiable source
  attribution; zero recommendations for the specified abstention conditions;
  zero unauthorized evidence disclosures; all six bulletin release tests pass.
  The four threshold amounts and disputed-amount distinction must also match
  BUL-2026-01 exactly.
- **Infrastructure/tools:** Not specified. Select after architecture review;
  do not infer a framework or retrieval technology from this plan.

## Project structure

Not specified. No RAG design artifact in this pack establishes code modules,
interfaces, or test directories. Set concrete file locations during
architecture/design and map them to the tasks before implementation.

## Requirement mapping

| Requirement | Summary | Plan items | Implementation evidence |
|---|---|---|---|
| REQ-001 | Approved-source boundary | 1.1, 2.1 | Approved source inventory and retrieval behavior |
| REQ-002 | Evidence classification | 2.2 | Correctly separated evidence categories |
| REQ-003 | Policy retrieval coverage | 1.2, 2.1, 4.1 | Labeled retrieval benchmark at the specified target |
| REQ-004 | Citation and provenance | 1.3, 2.2, 4.1 | Verifiable policy metadata and fact locators |
| REQ-005 | Insufficient evidence abstention | 1.2, 3.1, 4.1 | No recommendation in insufficient-evidence cases |
| REQ-006 | Conflicting evidence | 3.1, 4.1 | Visible conflict and no dependent recommendation |
| REQ-007 | Unsupported questions | 1.2, 3.1, 4.1 | Safe unsupported-question responses |
| REQ-008 | Access and data boundary | 1.1, 3.2, 4.1 | Approved role checks and safe test-data evidence |
| REQ-009 | Human decision boundary | 3.2, 4.1 | Approval-gated actions and draft recommendations |
| REQ-010 | Failure and audit behavior | 2.2, 3.1, 3.2, 4.1 | Failure-state, manual fallback, and audit evidence |
| REQ-011 | Source authority and precedence | 2.1, 3.1, 4.1 | Authority-aware retrieval, conflict abstention, and precedence evaluation |
| REQ-012 | Retrieval integrity and instruction safety | 1.1, 2.1, 3.3, 4.1 | Manifest/source validation, passage-validated citations, untrusted-content handling, release-test evidence |
| REQ-013 | Compensation threshold boundaries | 1.2, 3.2, 3.4, 4.1 | Exact CAD boundary outcomes, separate disputed/proposed amounts, approval/escalation evidence |

## Plan quality review

- Every REQ in `spec.md` maps to one or more plan items.
- Plan items restate no new behavior; they point to the source-of-truth
  acceptance criteria.
- KB-GUIDE rules are applied to the synthetic training corpus only; they do
  not silently approve production sources.
- Technology, interfaces, and file paths remain unspecified where the source
  artifacts do not decide them.