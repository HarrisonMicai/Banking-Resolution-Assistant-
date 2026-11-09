# Tasks: Policy RAG Behavior

**Governed by:** [spec.md](./spec.md) | **Plan:** [plan.md](./plan.md) | **Clarifications:** [clarification-log.md](./clarification-log.md) | **Training sources:** [KB-GUIDE](./KB-GUIDE.md), [BUL-2026-01](./BUL-2026-01.md), [BUL-2026-02](./BUL-2026-02.md)

The tasks are behavior-level because this spec pack contains no RAG
architecture or code-location design. Resolve the decision tasks before
production implementation. Do not invent source modules or technology choices
to satisfy this task list.

## Phase 1 — Close specification prerequisites

- [ ] T001 [P] [Plan:1.1] Record the KB-GUIDE source map and both synthetic bulletins separately from named production repositories/systems, owners, and production approval process in `specs/policy-rag/clarification-log.md` [Spec: REQ-001, REQ-011, REQ-012, REQ-013; KB-GUIDE §§1–2; BUL-2026-01; BUL-2026-02]
- [ ] T002 [P] [Plan:1.1] Approve the employee role-to-evidence/action matrix, including access-label permissions, in `specs/policy-rag/clarification-log.md` [Spec: REQ-008; Preconditions; NFR Security/Privacy; KB-GUIDE §3]
- [ ] T003 [P] [Plan:1.2] Approve supported and unsupported complaint-question examples and scenario-specific required information in `specs/policy-rag/clarification-log.md` [Spec: REQ-005, REQ-007; NG-5]
- [ ] T004 [P] [Plan:1.2] Approve labeled retrieval benchmark queries, applicable-source/section labels, expected results for all ten KB-GUIDE scenarios and five BUL-2026-01 threshold cases, and denominator for the 90% target in `specs/policy-rag/clarification-log.md` [Spec: REQ-003, REQ-011, REQ-013; KB-GUIDE §4; BUL-2026-01]
- [ ] T005 [P] [Plan:1.3] Approve citation presentation and a human-verifiable locator for operational facts; retain the KB-GUIDE policy metadata in `specs/policy-rag/clarification-log.md` [Spec: REQ-004; KB-GUIDE §3]

## Phase 2 — Implement approved retrieval and provenance

- [ ] T006 [Plan:2.1] Restrict retrieval to manifest-listed, approved, applicable, authorized sources using status, effective date, and access label; apply KB-GUIDE authority rules and verify superseded/historical sources are not treated as current authority [Spec: REQ-001, REQ-008, REQ-011, REQ-012; FR-3; BR-1; KB-GUIDE §§1–3; BUL-2026-02]
- [ ] T007 [Plan:2.1] Measure applicable-policy retrieval on the approved labeled benchmark, including natural-language and overlapping-topic cases, and meet the 90% acceptance target [Spec: REQ-003; KB-GUIDE §§1, 4]
- [ ] T008 [Plan:2.2] Preserve the distinction among verified facts, policy evidence, system analysis, and human decisions throughout retrieval and presentation [Spec: REQ-002; FR-2; IE-2]
- [ ] T009 [Plan:2.2] Attach resolvable source attribution to every recommendation, including policy `source_id`, `title`, `version`, `effective_date`, `section_title`, `chunk_id`, and approved operational-fact locator; validate each citation against retrieved metadata and its supporting passage [Spec: REQ-004, REQ-012; BR-3; KB-GUIDE §3; BUL-2026-02]

## Phase 3 — Implement safe answer and human-review behavior

- [ ] T010 [Plan:3.1] Withhold recommendations and explain the evidence gap for missing required information or when no applicable policy is retrieved [Spec: REQ-005; Preconditions; EC-3]
- [ ] T011 [Plan:3.1] Flag contradictory operational evidence for analyst review and current authoritative-policy conflicts for policy-owner review; abstain from recommendations dependent on unresolved conflicts [Spec: REQ-006, REQ-011; EC-4; KB-GUIDE §2]
- [ ] T012 [Plan:3.1] Abstain from unsupported or out-of-scope questions without inventing facts, policy statements, or citations [Spec: REQ-007; NG-5; BR-2]
- [ ] T013 [Plan:3.1] On retrieval or AI failure, report the unverified state, avoid unsupported fallback answers, and preserve manual investigation [Spec: REQ-010; EC-5; NFR Reliability]
- [ ] T014 [Plan:3.2] Enforce the approved role/access-label matrix and verify that unauthorized users cannot retrieve customer, complaint, or restricted policy evidence [Spec: REQ-008; NFR Security/Privacy; KB-GUIDE §3]
- [ ] T015 [Plan:3.2] Keep recommendations non-final and block gated actions and case closure until human approval is recorded [Spec: REQ-009; NG-1; BR-4/5]
- [ ] T016 [Plan:3.2] Record audit evidence for user actions, retrieved documents, recommendations, overrides, and approval decisions [Spec: REQ-010; NFR Auditability]
- [ ] T017 [Plan:3.3] Treat retrieved passages as untrusted evidence: ignore embedded instructions to change authorization, reveal secrets, or bypass approvals, and preserve the applicable access and human-approval boundaries [Spec: REQ-009, REQ-012; BUL-2026-02 Required Controls]
- [ ] T018 [Plan:3.4] Verify the five BUL-2026-01 cases: proposed compensation at CAD 1,000.00, CAD 1,000.01, CAD 10,000.00, and CAD 10,000.01, plus a disputed transaction amount distinct from proposed compensation; confirm the stated approval/escalation outcomes and preserve currency/cent precision [Spec: Compensation threshold evaluation scenarios; REQ-013]

## Phase 4 — Verify acceptance

- [ ] T019 [Plan:4.1] Execute the approved benchmark and all ten KB-GUIDE retrieval scenarios for REQ-001 through REQ-013 using only synthetic or approved training data [Spec: Required retrieval evaluation scenarios]
- [ ] T020 [Plan:4.1] Record pass/fail evidence for retrieval coverage, authority precedence, citation metadata, abstention, source boundaries, access control, human approval, failure handling, auditability, retrieved-content integrity, and compensation threshold outcomes; route any behavior change through a spec update [Spec: Authoring review record; REQ-001 through REQ-013]
- [ ] T021 [Plan:4.1] Run all six BUL-2026-02 release tests: unlisted source, retrieved prompt injection, invented citation, no-evidence abstention, conflicting current source, and superseded-source filtering; block release if any fails [Spec: Retrieved-content trust boundary and release controls; REQ-012]

## Dependency and implementation-path notes

- T001–T005 can proceed independently with the responsible owners.
- T006–T016 require the relevant Phase 1 decisions. Concrete code-file paths
  and test locations are intentionally deferred until an architecture/design
  artifact identifies them; this task list does not guess those locations.
- T017 requires the source manifest and approved role/access/approval rules.
- T018–T021 require the implementation and approved test corpus.

## Plan-to-task traceability

| Plan item | Tasks |
|---|---|
| 1.1 | T001, T002 |
| 1.2 | T003, T004 |
| 1.3 | T005 |
| 2.1 | T006, T007 |
| 2.2 | T008, T009 |
| 3.1 | T010, T011, T012, T013 |
| 3.2 | T014, T015, T016 |
| 3.3 | T017 |
| 3.4 | T018 |
| 4.1 | T019, T020, T021 |

REQ-011 authority and precedence behavior is implemented under Plan 2.1 and
3.1 (T006, T011) and verified under Plan 4.1 (T018–T019). REQ-012 source
integrity and instruction-safety behavior is implemented under Plans 1.1, 2.1,
2.2, and 3.3 (T001, T006, T009, T017) and verified by T018–T020.
REQ-013 threshold behavior is clarified under Plan 1.2 (T004), preserved under
Plans 3.2 and 3.4, and tested by T018–T020.

## Task quality review

- Every task references a plan item and specification requirement/section.
- Decision-dependent work is preceded by explicit owner-confirmation tasks.
- No task selects an unapproved technology, source repository, or code path.
