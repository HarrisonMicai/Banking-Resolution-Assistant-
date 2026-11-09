# FDM Forward Deployed AI Engineer

## Knowledge Base Content Map and Retrieval Guide

**Document ID:** KB-GUIDE | **Version:** 1.0 | **Effective date:** 2026-06-20
**Status:** Approved synthetic training document | **Owner:** Knowledge Management | **Classification:** Internal
**Purpose:** RAG ingestion, retrieval, citation, evaluation, and agent-workflow
training

> **Training notice:** This is synthetic operational content designed to
> resemble a detailed internal-bank knowledge base. It is not a real bank
> policy, legal advice, regulatory interpretation, or customer instruction.
> When evidence is missing, conflicting, or outside scope, the system must
> abstain and route to an authorized human reviewer.

## 1. Corpus design

The corpus intentionally contains overlapping terminology across complaints,
approvals, fees, digital access, service standards, mortgage servicing,
analyst workflow, governance, FAQs, historical cases, and bulletins. Retrieval
should use metadata and query meaning, with reranking, rather than relying on
one unique keyword per document.

| Source | Primary authority | Important overlap | Typical evaluation |
|---|---|---|---|
| KB-001 | End-to-end complaint lifecycle and closure | KB-005 communication; KB-007 analyst workflow | Intake, investigation, closure, final ownership |
| KB-002 | Escalation and approval authority | KB-003/006 redress; bulletins | Threshold boundaries, specialist routes, stale approval |
| KB-003 | Fees/charges investigation | KB-002 approval; KB-001 lifecycle | Fee evidence and refund-promise limits |
| KB-004 | Digital/access operations and security indicators | KB-002 fraud route; KB-008 data safety | MFA, account takeover, safe diagnostics |
| KB-005 | Communication, service-level, and accessibility | KB-001 ownership; KB-008 UI safety | Overdue updates, accessible service |
| KB-006 | Mortgage-servicing investigation | KB-002 redress/legal route | Payment allocation and hardship boundaries |
| KB-007 | Analyst workflow and failure recovery | All operational sources | Evidence structure and recovery |
| KB-008 | AI governance/security/audit | Bulletin 2026-02 | RAG/tool controls and release blocking |
| KB-009 | Short FAQ answers with references | All current policies | FAQ retrieval and citation validation |
| KB-010 | Historical case examples, not authority | All policies | Similarity retrieval and precedent warning |
| KB-001-OLD | Historical superseded policy | KB-001 current | Version-filtering negative test |

The approved synthetic bulletins referenced above are
[BUL-2026-01](./BUL-2026-01.md) and [BUL-2026-02](./BUL-2026-02.md).
BUL-2026-01 is Internal and clarifies KB-002 compensation-threshold boundaries
without replacing the standard. BUL-2026-02 is Restricted and clarifies RAG
source/citation controls; it does not authorize changes to system controls.
When testing KB-002 threshold behavior, keep the disputed transaction amount
distinct from a proposed compensation amount.

## 2. Authority rules

- Current approved policy/playbook is authoritative within its stated scope.
- Bulletins clarify but do not replace their referenced policy unless
  explicitly stated.
- FAQ summarizes and points to authority; it does not override policy.
- Historical casebook is illustrative and not precedent.
- Superseded sources are historical only.
- When current authoritative sources conflict, abstain and route to the policy
  owner.

## 3. Required metadata

| Field | Example | Use |
|---|---|---|
| `source_id` | KB-002 | Citation and filtering |
| `title` | Escalation, Approval and Decision Authority Standard | Human-readable citation |
| `version` | 2.1 | Current-version logic |
| `effective_date` | 2026-02-15 | Applicability |
| `status` | Approved / Superseded | Authority filtering |
| `access_label` | Internal / Restricted | Authorization |
| `section_title` | 3. Financial Redress Thresholds | Passage-level citation |
| `chunk_id` | KB-002#s3#0002 | Deterministic trace |

## 4. Suggested retrieval tests

1. Exact title/source question.
2. Natural-language question without document name.
3. Question requiring a section-specific answer.
4. Question where two documents overlap.
5. No-answer question requiring abstention.
6. Superseded-source negative test.
7. Conflicting-source route.
8. Restricted-source filter.
9. FAQ versus authoritative-policy preference.
10. Historical-case similarity without outcome copying.
