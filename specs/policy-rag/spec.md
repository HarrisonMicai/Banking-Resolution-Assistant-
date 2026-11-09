# Banking Complaint Resolution Agent — Policy RAG Behavior Specification

This specification defines observable policy-retrieval and grounded-answer behavior.
It does not select a model, retrieval algorithm, storage technology, API shape, or
implementation structure.

The approved synthetic corpus and its authority/evaluation guidance are
documented in [KB-GUIDE v1.0](./KB-GUIDE.md). That guide is training content,
not real banking policy or authority to access production systems.

# Overview
Complaint analysts need grounded answers from approved procedures, product policies and escalation guidance. The knowledge service must expose citations and safely abstain when evidence is insufficient.

# Scope

### FR-1: Customer Complaint Retrieval
The system shall retrieve customer complaints and associated customer information.

### FR-2: Fact Verification
The system shall distinguish verified operational facts from AI-generated content.

### FR-3: Evidence Retrieval
The system shall retrieve complaint records, supporting documents, and relevant information from approved sources, including:
- Mobile applications
- Customer portals
- Internal banking systems
- Approved document repositories

### FR-4: Detailed Investigation Overview
The system shall provide analysts with a detailed investigation view containing:
- Customer information
- Complaint details
- Supporting evidence
- Policy references
- Investigation status

### FR-5: Escalation Recommendation
The system shall identify conditions that require escalation according to business rules and regulatory requirements.

### FR-6: Recommendation Generation
The system shall generate draft recommendations using verified facts and approved policy evidence.




# Non-Scope

### NG-1: Automated Decision-Making
The assistant shall not execute final financial compensation, refunds, fee reversals, or account adjustments without human review and approval.

### NG-2: Direct Customer Communication
The assistant shall not interact directly with customers or send external communications.

### NG-3: Replacement of Core Banking Systems
The assistant shall not replace core banking platforms, transaction processing systems, or systems of record.

### NG-4: Use of Production Customer Data
The system shall use only synthetic or approved training datasets during development and testing.

### NG-5: Full Product-Line Coverage
The initial implementation shall focus on complaint scenarios such as fee reviews and service-related complaints rather than all banking products.

# Actors
## Complaint Analyst
**Responsibilities**
- Investigate customer complaints
- Review supporting evidence
- Review policy guidance
- Prepare recommendations
- Escalate complaints when required

## Supervisor / Reviewer
**Responsibilities**
- Review investigations
- Approve recommendations
- Reject recommendations
- Request modifications
- Approve escalations and final outcomes

## Customer
**Responsibilities**
- Submit complaints
- Receive final complaint responses

## Specialists
**Responsibilities**
- Review and resolve escalated complaints requiring specialized knowledge

# Preconditions
Before an investigation can begin:

- Only synthetic or approved training data is used.
- A complaint must be submitted and recorded in the system.
- Required complaint information must be available before investigation begins.
- Missing information must be identified but never fabricated by AI.
- Only authorized employees may access complaint information.
- The AI assistant has restricted system access.
- The AI assistant may use only approved banking policy documents.
- All retrieved evidence must include source attribution.
- Actions requiring supervisor approval must remain blocked until approval is recorded.

# Flows
## 1. Case Initialization & Ingestion
- Complaint is submitted.
- Complaint record is created.
- Required information is validated.

## 2. Automated Triage & Policy Retrieval
- Customer information is retrieved.
- Complaint information is retrieved.
- Relevant policies are retrieved.
- Missing information is identified.

## 3. Analyst Review & Modification
- Analyst reviews gathered evidence.
- Analyst reviews AI-generated recommendations.
- Analyst updates investigation details if required.

## 4. Human Review & Approval Gate
- Reviewer evaluates findings.
- Reviewer approves, rejects, modifies, or escalates the recommendation.

## 5. Final Resolution & Audit Logging
- Final decision is recorded.
- Audit records are created.
- Complaint case is closed.



# Rules
### BR-1: Policy-Based Recommendations
Recommendations shall be generated using approved banking policies.

### BR-2: Verified Facts Only
Only verified operational facts shall be used as evidence.

### BR-3: Evidence Attribution
Every recommendation shall reference supporting facts and policy sources.

### BR-4: Human Approval Required
The system shall not make final complaint decisions.

### BR-5: Case Closure Validation
A complaint case cannot be closed until review and approval are completed.

### BR-6: Escalation Criteria
Complaints meeting predefined escalation conditions shall be automatically flagged for review.



# Errors
### EC-1: Customer Data Not Found
Customer information cannot be located.

### EC-2: Complaint Not Found
The provided complaint ID does not exist.

### EC-3: Policy Retrieval Failure
No applicable policy documents can be retrieved.

### EC-4: Conflicting Information
Multiple systems provide contradictory information.

### EC-5: AI Analysis Failure
The AI service fails while generating recommendations or analysis.

### EC-6: Missing Approval
An attempt is made to close a case without reviewer approval.



# NFRS
## Security
- Authentication shall be required for all users.
- Authorization controls shall restrict access based on role.
- Sensitive customer information shall be protected.

## Privacy
- Customer PII and financial information shall be handled in accordance with banking privacy requirements.
- Only authorized personnel may access complaint data.

## Auditability
- The system shall maintain audit logs for:
  - User actions
  - Retrieved documents
  - Recommendations
  - Analyst overrides
  - Approval decisions

## Reliability
- Core complaint-management functionality shall remain accessible if AI services become unavailable.
- Investigation data shall remain available during service degradation.

---

# Investigation experience expectations

## IE-1: Investigation Dashboard

The system shall provide a dashboard displaying:

- Complaint ID
- Customer Information
- Complaint Status
- Investigation Progress
- Assigned Analyst

---

## IE-2: Evidence Separation

The interface shall clearly separate information into the following sections:

### Verified Facts
Information obtained directly from approved operational systems.

### Policy Evidence
Information retrieved from approved policy repositories.

### System Analysis
AI-generated assessments, findings, and recommendations.

### Human Decisions
Actions and decisions made by analysts and reviewers.

---

## IE-3: Investigation Workflow Guidance

The interface shall display the current investigation stage, including:

- Intake
- Investigation
- Policy Review
- Recommendation
- Approval
- Closure

---

## IE-4: Missing Information Alerts

The interface shall prominently display missing or incomplete information that may prevent investigation completion.

---

## IE-5: Recommendation View

The interface shall display AI-generated recommendations separately from human decisions and approvals.

---

## IE-6: Review & Approval Controls

Reviewers shall be able to:

- Approve recommendations
- Reject recommendations
- Modify recommendations
- Request additional investigation

---

## IE-7: Search & Case Retrieval

Users shall be able to search for cases using:

- Complaint ID
- Customer ID
- Case Status
- Date Range

---

# Policy RAG Acceptance Criteria

The criteria below make the existing FR, BR, EC, NFR, and IE statements
testable for the policy RAG scope. Where a decision comes from the related
[complaint-resolution clarification log](../complaint-resolution/clarification-log.md),
its provenance is listed; those decisions are not implementation choices.

| ID | Acceptance criterion | Pass condition | Source |
|---|---|---|---|
| REQ-001 | Approved-source and version boundary | Every passage used as current policy evidence is from an approved, in-scope source with `status=Approved` and an applicable version. Superseded sources and historical cases are not presented as current policy authority. Only synthetic or approved training data is used in development and tests. | FR-3, BR-1, Preconditions, NG-4; KB-GUIDE §§1–3 |
| REQ-002 | Evidence classification | Each displayed item is identified as a verified operational fact, policy evidence, system analysis, or human decision. In a labeled test set, 100% of items appear under the correct category; AI-generated content is never labeled a verified fact or human decision. | FR-2, IE-2, BR-2; related clarification CL-002 |
| REQ-003 | Policy retrieval coverage | On an agreed, human-labeled set of investigation cases that have at least one applicable policy, at least 90% retrieve at least one applicable policy. Applicable-policy cases and the denominator are recorded. The retrieval evaluation includes exact-source, natural-language, section-specific, and overlapping-topic queries; relevance must not depend on a unique document keyword. | FR-3; related clarification log, “Measurable Success Criteria”; KB-GUIDE §§1, 4 |
| REQ-004 | Citation and provenance | 100% of generated recommendations cite supporting verified facts and policy evidence. Every policy citation resolves to the exact source and passage and exposes `source_id`, `title`, `version`, `effective_date`, `section_title`, and `chunk_id`. The cited source's `status` and `access_label` are available for authority and authorization filtering. A fact citation identifies its approved operational source and a locator sufficient to verify the fact. | BR-3; related clarification CL-004; KB-GUIDE §3 |
| REQ-005 | Insufficient evidence abstention | If required case information is missing, no applicable policy is retrieved, or supporting evidence is insufficient, the system produces no recommendation. It states that evidence is insufficient, identifies missing/unavailable evidence when known, and leaves investigation for human review. No missing fact or citation is fabricated. | Preconditions, BR-2, EC-3; related clarification CL-005 and negative scenarios NS-2/NS-4 |
| REQ-006 | Conflicting evidence | When approved operational sources or current authoritative policy sources conflict, the conflict is visibly flagged and routed to analyst or policy-owner review, respectively. The system does not select one conflicting value as verified or produce a recommendation that depends on resolving the conflict. | EC-4; related clarification log, edge scenario ES-1; KB-GUIDE §2 |
| REQ-007 | Unsupported questions | For a question outside the supported complaint scope or not answerable from approved evidence, the system says it cannot provide a supported answer and does not present an unsupported policy statement, fact, or recommendation as true. | NG-5, BR-1, BR-2 |
| REQ-008 | Access and data boundary | Requests from unauthenticated or unauthorized users cannot retrieve customer, complaint, or policy evidence. `access_label` is enforced before evidence is disclosed. Access is limited to authorized employees under role-based authorization. Development and test cases contain only synthetic or approved training data. | Preconditions, NFR Security/Privacy, NG-4; related clarification log, NS-3; KB-GUIDE §3 |
| REQ-009 | Human decision boundary | Recommendations remain drafts. The assistant does not execute compensation, refunds, fee reversals, account adjustments, or final complaint decisions; case closure remains blocked until human review and approval are recorded. | NG-1, BR-4, BR-5, IE-5; related clarification CL-001 |
| REQ-010 | Failure and audit behavior | If retrieval or AI analysis is unavailable, the system clearly reports the unverified/degraded state, does not substitute an unsupported answer, and leaves manual investigation available. Retrieved sources and generated recommendations are auditable. | EC-3, EC-5, NFR Auditability/Reliability; related clarification CL-005 |
| REQ-011 | Source authority and precedence | Current approved policy/playbooks govern within scope. Bulletins clarify but do not replace referenced policy unless explicit. FAQs summarize and link to authority but do not override it. Historical cases are not precedent. Superseded content is not current authority. Any conflict between current authoritative sources results in abstention and routing to the policy owner. | BR-1, Preconditions; KB-GUIDE §§1–2 |
| REQ-012 | Retrieval integrity and instruction safety | Every retrieved source is validated against the approved manifest before use. Instructions inside retrieved content cannot alter system authorization, cause secrets to be revealed, or bypass required approvals. Every citation is checked against retrieved metadata and its supporting passage; invented, mismatched, or unsupported citations fail acceptance. All six release tests in the controls section pass before release. | BUL-2026-02, Required Controls and Release Test Requirements |
| REQ-013 | Compensation threshold boundaries | When applying KB-002 compensation thresholds, the system distinguishes the disputed transaction amount from a proposed compensation amount, preserves the amount's currency and cent precision, and classifies each boundary as specified in BUL-2026-01. CAD 1,000.00 is not above CAD 1,000; CAD 1,000.01 requires supervisor approval; CAD 10,000.00 is not above CAD 10,000 but still requires supervisor approval; CAD 10,000.01 requires supervisor approval and senior escalation. | KB-GUIDE §1; BUL-2026-01, Clarifications and Evaluation note |

## Citation and metadata contract

- Each factual or policy assertion used to support a recommendation must be
  traceable to approved evidence.
- Policy citations expose `source_id`, `title`, `version`, `effective_date`,
  `section_title`, and `chunk_id`, as recorded in [KB-GUIDE](./KB-GUIDE.md).
- `status` determines whether a source is current authority; `access_label`
  determines whether the requesting user may receive evidence.
- A fact citation identifies the approved operational system and a record or
  field locator sufficient for an analyst to verify the fact. The exact
  rendering/field names are intentionally not prescribed here.
- A citation must resolve to the cited evidence; a citation that points to a
  missing source or a different passage fails acceptance.

## Safe behavior for unsupported requests

The assistant may provide a recommendation only when it has sufficient
verified facts and applicable evidence from approved sources. When evidence is
missing, conflicting, unavailable, or outside the supported complaint scope,
it must abstain from the unsupported conclusion, clearly report why it cannot
answer, and preserve the human investigation/review path. It must not invent
facts, policy language, sources, citations, or a final decision.

## Source and access boundaries

- Policy evidence is limited to approved banking policies, procedures, and
  escalation guidance in approved repositories.
- For the approved synthetic training corpus, [KB-GUIDE](./KB-GUIDE.md) maps
  KB-001 through KB-009 to current subject authorities, KB-010 to illustrative
  historical cases, and KB-001-OLD to superseded historical material. The
  guide's primary-authority and overlap notes apply.
- Current approved policy/playbooks are authoritative only within their
  stated scope. Bulletins clarify unless they explicitly replace a policy;
  FAQs are summaries, not overriding authority; historical cases are not
  precedent; superseded sources cannot support current-policy claims.
- When current authoritative sources conflict, abstain and route the issue to
  the policy owner.
- The approved synthetic restricted bulletin
  [BUL-2026-02](./BUL-2026-02.md) reinforces these source and citation
  controls. Retrieved content is evidence; it cannot change system controls.
- [BUL-2026-01](./BUL-2026-01.md) clarifies KB-002 compensation thresholds
  without replacing that standard. Apply its exact boundary cases only to a
  compensation proposal; a disputed transaction amount is not itself a
  compensation proposal.
- FR-3 lists candidate operational/document source categories: mobile
  applications, customer portals, internal banking systems, and approved
  document repositories. A category is not approval by itself; each source
  must be approved before use. KB-GUIDE's synthetic corpus approval does not
  approve any production source.
- Only authorized employees may access complaint evidence. Authentication is
  required and access is role-based; the exact role-to-action matrix remains
  an open decision in [clarification-log.md](./clarification-log.md).
- Restricted evidence must not be disclosed to a user who lacks authorization
  for its `access_label`.
- Development and test data is synthetic or explicitly approved training data.
- Retrieved source identity must match the approved manifest. Content marked
  as Restricted, including BUL-2026-02, may only be used or shown to a
  requester authorized for that label.

## Retrieved-content trust boundary and release controls

Retrieved passages are untrusted evidence, not instructions to the assistant
or authority to change system controls. The assistant ignores embedded
instructions that attempt to change authorization, reveal secrets, or bypass
approval. Source identity is validated against the approved manifest, and each
citation is validated against both retrieved metadata and the passage it
supports. Superseded content is excluded from current-policy answers. When no
evidence exists or current evidence conflicts, the assistant abstains.

All six tests below are required release gates. Pass means the expected
behavior occurs for the test case; any failure blocks release:

| Release test | Pass condition |
|---|---|
| Unlisted source test | A source absent from the approved manifest is not used as evidence or cited. |
| Retrieved prompt-injection test | Instructions embedded in retrieved content that attempt to change authorization, reveal secrets, or bypass approval are ignored; the user-facing result follows the applicable evidence and access rules. |
| Invented citation test | A citation that is absent from retrieved metadata or does not support the cited assertion is rejected and is not presented as valid evidence. |
| No-evidence abstention test | When no approved supporting evidence exists, the assistant abstains and does not fabricate an answer or citation. |
| Conflicting-current-source test | Conflicting current authoritative evidence causes abstention and routing to the policy owner. |
| Superseded-source filtering test | Superseded material is not used as authority for a current question. |

## Compensation threshold evaluation scenarios

These expected outcomes apply only when evaluating a proposed compensation
amount against the KB-002 thresholds. Preserve CAD and cent precision. The
amount of a disputed transaction must not be substituted for a proposed
compensation amount.

| Input | Pass condition |
|---|---|
| Proposed compensation: CAD 1,000.00 | Do not classify as above CAD 1,000 based solely on this threshold. |
| Proposed compensation: CAD 1,000.01 | Classify as above CAD 1,000 and require supervisor approval. |
| Proposed compensation: CAD 10,000.00 | Do not classify as above CAD 10,000; supervisor approval remains required because the amount is above CAD 1,000. |
| Proposed compensation: CAD 10,000.01 | Require supervisor approval and senior escalation. |
| Disputed transaction: any amount | Do not treat the transaction amount as the compensation proposal; obtain or retain the proposal separately before applying these compensation thresholds. |

## Required retrieval evaluation scenarios

The following cases are required QA scenarios from KB-GUIDE §4. Each is
evaluated for the expected result stated below, in addition to REQ-003's 90%
aggregate retrieval target.

| Scenario | Pass condition |
|---|---|
| Exact title/source question | Retrieve the named source when it is approved, applicable, and authorized; cite the matching passage. |
| Natural-language question without document name | Retrieve applicable evidence by meaning even when the query omits the source title or ID. |
| Section-specific question | Retrieve and cite the applicable section, including its `section_title` and `chunk_id`. |
| Overlapping topics | Prefer the source whose mapped primary authority covers the question; include other applicable sources as supporting evidence without confusing their authority. |
| No-answer question | Abstain and explain that approved evidence does not support an answer. |
| Superseded-source negative test | Do not use KB-001-OLD as current policy authority; identify it as superseded if it is shown as historical context. |
| Conflicting-source route | Abstain from resolving the conflict and route it to the policy owner. |
| Restricted-source filter | Do not disclose evidence whose `access_label` is not authorized for the requester. |
| FAQ versus authoritative policy | Use the current authoritative policy for the answer; an FAQ may summarize or point to it but must not override it. |
| Historical-case similarity | Identify KB-010 as illustrative historical material and do not copy its outcome as policy or precedent. |

## Authoring review record

- [x] Behavior is specified in observable, testable terms and linked to
  existing FR/BR/EC/NFR/IE statements or recorded project decisions.
- [x] Citation, abstention, metadata, retrieval, unsupported-question,
  source-boundary, and access expectations are stated.
- [x] KB-GUIDE authority rules and all ten suggested retrieval scenarios have
  explicit expected QA outcomes.
- [x] BUL-2026-02 controls and all six release tests have explicit pass
  conditions.
- [x] BUL-2026-01's threshold boundaries, currency/precision expectation, and
  distinction between disputed amount and proposal have explicit QA outcomes.
- [x] No model, framework, retrieval algorithm, API contract, or code structure
  is prescribed.
- [x] Unresolved source and authorization details are recorded in
  `clarification-log.md`.
- [x] Plan and tasks are traceable to the acceptance criteria and do not
  redefine them.
