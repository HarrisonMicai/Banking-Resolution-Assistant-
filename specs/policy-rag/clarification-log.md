# Policy RAG Clarification Log

**Status:** Working contract; open decisions below must be resolved before
production source access or final authorization testing.

## Resolved or carried-forward decisions

| ID | Question | Decision used in `spec.md` | Evidence / provenance | Status |
|---|---|---|---|---|
| CL-RAG-001 | What metadata must identify retrieved policy evidence? | Display source ID, title, version, date, and section with each cited policy source. | [Related clarification log](../complaint-resolution/clarification-log.md), CL-004 | Carried forward |
| CL-RAG-002 | What happens when evidence is insufficient or unavailable? | Abstain from an unsupported answer; clearly identify the unverified state and alert the operator when a dependency fails. Keep manual investigation available. | [Related clarification log](../complaint-resolution/clarification-log.md), CL-005; current spec NFR Reliability | Carried forward |
| CL-RAG-003 | What measurable retrieval and citation targets already exist? | At least 90% of investigations with applicable policy evidence retrieve applicable evidence; 100% of generated recommendations contain source attribution. | [Related clarification log](../complaint-resolution/clarification-log.md), “Measurable Success Criteria” | Carried forward |
| CL-RAG-004 | How should evidence be distinguished? | Keep customer assertions, verified operational facts, policy evidence, system-generated analysis, and human decisions distinguishable. | [Related clarification log](../complaint-resolution/clarification-log.md), CL-002; current spec IE-2 | Resolved |
| CL-RAG-005 | Can the assistant make or execute the final complaint decision? | No. Recommendations are drafts and actions needing approval remain gated by a human reviewer. | [Related clarification log](../complaint-resolution/clarification-log.md), CL-001; current spec NG-1 and BR-4/5 | Resolved |
| CL-RAG-012 | What is the approved source inventory for synthetic retrieval training? | Use the source map in [KB-GUIDE v1.0](./KB-GUIDE.md): KB-001–KB-009 are current-topic sources; KB-010 is historical and non-authoritative; KB-001-OLD is superseded and historical only. | User-provided KB-GUIDE, §§1–2; status Approved synthetic training document | Resolved for synthetic training |
| CL-RAG-013 | How should source authority be resolved in the training corpus? | Current approved policy/playbooks govern within scope; bulletins clarify unless explicit replacement is stated; FAQs summarize; historical cases are not precedent; superseded sources are not current authority; current-authority conflicts abstain and route to the policy owner. | User-provided KB-GUIDE, §2 | Resolved for synthetic training |
| CL-RAG-014 | What metadata supports filtering and deterministic citations? | Use `source_id`, `title`, `version`, `effective_date`, `status`, `access_label`, `section_title`, and `chunk_id`; expose the citation fields and enforce status/access filtering as specified in `spec.md`. | User-provided KB-GUIDE, §3 | Resolved for synthetic training |
| CL-RAG-015 | Which retrieval evaluation scenarios are required? | Include all ten suggested scenarios from KB-GUIDE §4 with expected pass conditions in `spec.md`. The guide does not provide the concrete labeled query corpus or samples. | User-provided KB-GUIDE, §4 | Scenario types resolved; test cases open |
| CL-RAG-016 | What source-integrity and retrieved-instruction controls are required? | Validate retrieved source identity against the approved manifest; treat retrieved text as evidence, not control instructions; validate citations against retrieved metadata and passage; exclude superseded sources from current answers; abstain for no evidence or conflicting current evidence. Run all six release tests in `spec.md`. | User-provided [BUL-2026-02](./BUL-2026-02.md), Required Controls and Release Test Requirements | Resolved for synthetic training |
| CL-RAG-017 | How should KB-002 compensation thresholds handle boundary amounts? | Apply BUL-2026-01's exact outcomes at CAD 1,000.00, CAD 1,000.01, CAD 10,000.00, and CAD 10,000.01; keep the disputed transaction amount distinct from proposed compensation; preserve currency and cent precision. The bulletin clarifies but does not replace KB-002. | User-provided [BUL-2026-01](./BUL-2026-01.md), Clarifications and Evaluation note | Resolved for synthetic training |

## Open questions

| ID | Question to resolve | Why it matters | Owner / evidence needed | Status |
|---|---|---|---|---|
| CL-RAG-006 | Which named production policy repositories and operational systems are approved, and who approves changes to that list? | The synthetic training corpus is approved by KB-GUIDE; its approval does not authorize real sources or production data access. | Product/data owner to provide the production source inventory, owners, and approval process. | Open |
| CL-RAG-007 | Which roles may read each evidence category/access label, and which actions are restricted to reviewers/supervisors? | KB-GUIDE defines `Internal` and `Restricted` labels but does not map users/roles to either label or actions. | Security/product owner to provide the role, access-label, and action matrix. | Open |
| CL-RAG-008 | What citation presentation and locator are required for an operational fact? | The existing metadata decision specifies policy metadata, but not how a fact is located within an operational system. | Product/data owner to approve a human-verifiable fact locator and presentation. | Open |
| CL-RAG-009 | What concrete corpus, query examples, and sampling rules define the 90% retrieval measure and ten scenario tests? | KB-GUIDE lists the ten test types but does not include specific queries, answer keys, labels, or a denominator. | QA/product owner to approve representative labeled cases, expected relevant sources/sections, and denominator. | Open |
| CL-RAG-010 | Which complaint fields are critical for each supported scenario, and what evidence is sufficient to recommend? | The system must identify missing information and abstain, but required fields vary by scenario and are not listed in this RAG spec. | Complaint operations owner to provide scenario-specific required information and evidence rules. | Open |
| CL-RAG-011 | Which question categories are supported within fee-review and service-related complaints? | The initial product scope excludes full product-line coverage; the supported question boundary needs examples for QA. | Product owner to approve supported and unsupported question examples. | Open |

## Authoring review record

- The acceptance criteria are mapped to requirements in [spec.md](./spec.md),
  and plan/task traceability is recorded in [plan.md](./plan.md) and
  [tasks.md](./tasks.md).
- The review checked the requested FDM concerns: user-visible behavior,
  measurable acceptance, explicit source/access boundaries, safe unsupported
  behavior, traceability, and removal of implementation choices from the spec.
- [KB-GUIDE v1.0](./KB-GUIDE.md) is recorded as approved synthetic training
  content only; it is not real bank policy or production-source authorization.
- [BUL-2026-02 v1.0](./BUL-2026-02.md) is recorded as approved synthetic,
  Restricted training content; its access label must be honored and its
  controls do not authorize any production source or data.
- [BUL-2026-01 v1.0](./BUL-2026-01.md) is recorded as approved synthetic,
  Internal training content that clarifies KB-002 threshold boundaries without
  replacing the standard.
- No separate FDM checklist document was present in the policy-RAG artifact
  directory; the review used the checklist concerns stated in the request and
  the spec-quality criteria.
- Open decisions are called out rather than filled with guessed source names,
  roles, schemas, retrieval algorithms, or code locations.