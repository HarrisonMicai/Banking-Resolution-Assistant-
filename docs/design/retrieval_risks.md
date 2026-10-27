# Retrieval Risks and Controls (`retrieval_risks.md`)

## 1. Risk Comparison Across Retrieval & Automation Methods

| Retrieval / Automation Method | Primary Risk Description | Potential Impact |
| :--- | :--- | :--- |
| **Text-to-SQL** | Injection attacks, semantic misinterpretation of schema, unauthorized table access, or incorrect aggregate calculations. | Data corruption, exposure of PII, or erroneous financial summaries. |
| **Vector Retrieval (RAG)** | Retrieval of outdated policy versions, hallucinated context matching, or semantic drift returning irrelevant clauses. | Misapplication of bank policy, incorrect customer guidance, or regulatory non-compliance. |
| **Tool / API Execution** | Unintended execution of mutating operations, parameter tampering, or unauthorized system calls. | Unintended fee reversals, unauthorized account modifications, or state corruption. |
| **Automation / Agentic Workflows** | Unsupervised multi-step execution leading to autonomous decision-making without human checkpoints (violating NG-1 & BR-4). | Unauthorized financial payouts, breach of audit protocols, and legal exposure. |

---

## 2. Mandatory Controls & Mitigations

### Validation
* **Schema Validation:** Enforce strict parameter type checking and parameterized queries for all generated SQL statements to prevent malformed or malicious execution.
* **Fact Verification (FR-2):** Ensure operational facts retrieved from structured databases are distinctly separated from AI-generated synthesis in the user interface (IE-2).

### Filtering
* **Namespace & Tenant Filtering:** Restrict vector search queries exclusively to approved active policy documents (`policy_document.status = 'ACTIVE'`), filtering out draft or deprecated guidelines.
* **PII Redaction:** Filter sensitive customer financial identifiers and credentials before passing context to LLM synthesis layers.

### Allowlists
* **SQL Read-Only Enforcement:** Restrict AI-generated queries to pre-approved views (e.g., `complaint_analyst_view`) or read-only operational tables, completely blocking `DROP`, `UPDATE`, or `DELETE` statements.
* **Tool Allolist:** Restrict agentic tool invocation to an explicit allowlist of read and investigation functions.

### Approval Controls
* **Human-in-the-Loop Gates (BR-4 / NG-1):** Hard-block final financial compensation, fee reversals, and account adjustments until an authorized `Supervisor / Reviewer` records an explicit `APPROVED` decision in the `review_decision` table.
* **Audit Logging:** Maintain immutable records in `audit_log` capturing every user action, retrieved document, recommendation override, and approval decision to ensure end-to-end traceability.