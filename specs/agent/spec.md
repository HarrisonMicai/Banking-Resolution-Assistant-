# Controlled Investigation Agent Specification (`spec/agent/spec.md`)

**Traceability & Baselines:**
- **Week 1 Foundation:** *Banking Complaint Resolution Agent — Policy RAG Behavior Specification* (`FR-1`–`FR-6`, `NG-1`–`NG-5`, `BR-1`–`BR-6`, `EC-1`–`EC-6`, `IE-1`–`IE-7`)
- **Week 4 Contract:** *Retrieval Service API Contract* (`app/rag/retrieval_service.py` -> `RetrievalService.retrieve()`)
- **Sprint 3 Alignment:** Controlled Complaint Investigation Workflow (SQL, RAG, and Case-Management tool domains; least-privilege MCP boundaries; LangGraph readiness)
- **Corpus Authority:** `KB-GUIDE v1.0` (Synthetic training corpus only)

---

## 1. Purpose & Scope
This specification defines the **Controlled Investigation Agent** for Exercise 5.1.1. The agent orchestrates complaint triage, structured/policy evidence gathering, and grounded recommendation drafting via **LangChain** and **FastMCP**—reusing Week 4 services without duplicating retrieval logic or bypassing human approval gates.

### In Scope (Mapped to Week 1 `FR-*`)
- **Customer & Operational Data Lookup (`FR-1`, `FR-2`):** Retrieve customer profiles, account facts, and transaction/fee logs via read-only SQL tools.
- **Approved Policy Retrieval (`FR-3`):** Search approved banking policies (`status = Approved`) via a read-only MCP tool wrapping `RetrievalService.retrieve()`.
- **Case & Evidence Separation (`FR-2`, `FR-4`, `IE-2`):** Read complaint details and write draft findings strictly into **System Analysis**, keeping **Verified Facts**, **Policy Evidence**, and **Human Decisions** isolated.
- **Escalation & Draft Recommendations (`FR-5`, `FR-6`):** Flag regulatory/business escalation conditions (`BR-6`) and generate citation-backed draft recommendations (`BR-1`, `BR-3`), or safely abstain (`BR-7`).

### Out of Scope / Hard Boundaries (Mapped to Week 1 `NG-*` & `BR-*`)
- **No Automated Decisions (`NG-1`, `BR-4`):** The agent shall never approve, reject, or close complaints, nor execute refunds, fee reversals, or account adjustments.
- **No Direct Customer Contact (`NG-2`):** The agent shall never send emails, SMS, or external messages to the **Customer** actor.
- **No Core Banking Mutation (`NG-3`):** All SQL, RAG, and Case tools bound to the agent are strictly read-only (`readOnlyHint: true`).
- **No Production Data (`NG-4`):** Only approved synthetic datasets (`KB-GUIDE v1.0`) may be used.
- **Product Scope (`NG-5`):** Restricted to initial scenarios (fee reviews and service-related complaints).
- **No Direct Vector DB Access:** The agent shall not query ChromaDB directly; all policy retrieval must route through the MCP `search_approved_policies` tool.

---

## 2. Interfaces (FastMCP Tools & LangChain Runtime)

All tools are exposed through `app/mcp/server.py` (**FastMCP**) with `readOnlyHint=True` and `destructiveHint=False` to enforce least privilege.

### 2.1 SQL / Structured Data Domain
#### Tool: `get_customer_account_facts`
- **Traceability:** `FR-1`, `FR-2`, `EC-1`, `EC-4`, Sprint 3 SQL User Story
- **Privilege:** `READ_ONLY`
- **Inputs:** `customer_id` (string, required), `complaint_id` (string, required)
- **Outputs:** Verified customer profile, fee history, and transaction records mapped to **Verified Facts (`IE-2`)**.
- **Error & Unavailable Paths:**
  - Missing customer record -> Returns `EC-1` (*Customer Data Not Found*).
  - Contradictory records across sources -> Returns `EC-4` (*Conflicting Information*).
  - SQL database unavailable -> Returns `EC-5` (*Service Degraded*).

### 2.2 RAG Policy Domain (Connects MCP -> Week 4 `RetrievalService`)
#### Tool: `search_approved_policies`
- **Traceability:** `FR-3`, `BR-1`, `BR-3`, `EC-3`, Week 4 `RetrievalService.retrieve()`
- **Privilege:** `READ_ONLY` (Role-checked for `access_label="Restricted"`)
- **Underlying Implementation:** Delegates directly to `app/rag/retrieval_service.py` -> `RetrievalService.retrieve()`.
- **Inputs:**
  - `query` (string, required): Search query derived from complaint category and verified facts.
  - `top_k` (integer, optional, default `5`): Maximum chunks to return.
  - `document_type` (string, optional): Filter (`"Policy"`, `"Procedure"`, `"Escalation"`).
  - `version` (string, optional): Filter by document version.
  - `access_label` (string, optional): Passed only after verifying analyst role permissions (`BR-9`).
  - `rerank` (boolean, optional, default `True`): Enables deterministic lexical Jaccard reranking.
  - `user_role` (string, required): Active caller role for authorization verification.
- **Outputs:** List of chunks with `text`, `score`, `rerank_score`, and `metadata` (`source_id`, `document_type`, `version`, `access_label`, `status="Approved"`).
- **Error & Unavailable Paths:**
  - Unauthorized `Restricted` request -> Returns `AUTH_DENIED` (`NFR Security`).
  - Empty result list `[]` -> Returns `EC-3` (*Policy Retrieval Failure* -> triggers **Safe Abstention**).
  - `ValueError` or `RuntimeError` (ChromaDB/Gemini outage) -> Returns `EC-5` (*Service Degraded*).

### 2.3 Case-Management Domain
#### Tool: `get_complaint_case`
- **Traceability:** `FR-1`, `FR-4`, `IE-1`, `IE-7`, `EC-2`
- **Privilege:** `READ_ONLY`
- **Inputs:** `complaint_id` (string, required)
- **Outputs:** Complaint metadata, category, current workflow stage (`IE-3`), assigned analyst, and existing investigation notes.
- **Error & Unavailable Paths:**
  - Unknown `complaint_id` -> Returns `EC-2` (*Complaint Not Found*).
  - Case store unavailable -> Returns `EC-5` (*Service Degraded*).

### 2.4 Governance & Artifact Lookup Domain
- **`get_spec(section: optional string)`:** Reads `spec/agent/spec.md` (full document or specific `##` section such as `Rules`, `Errors`, `State`).
- **`get_plan()`:** Reads `plan.md` for architectural boundaries and resolved requirement notes.
- **`list_tasks(status: optional string)`:** Reads `tasks.md` filtered by `'open'` or `'done'`.

### 2.5 Orchestration Runtime (LangChain + MCP Client)
- **Framework:** LangChain agent runtime connected to `app/mcp/server.py` via `langchain-mcp-adapters` (`MultiServerMCPClient`).
- **Structured Output Contract:** Uses `with_structured_output(SystemAnalysisOutput)` to enforce strict schema separation (`IE-2`, `IE-5`):
```json
{
  "complaint_id": "string",
  "status": "DRAFT_READY | ABSTAINED | ESCALATION_REQUIRED | DEGRADED",
  "verified_facts": ["string"],
  "missing_information": ["string"],
  "escalation_triggered": false,
  "escalation_reasons": ["string"],
  "draft_recommendation": "string or null",
  "citations": [
    {
      "source_id": "KB-002",
      "version": "2.1",
      "document_type": "Policy",
      "quote": "string"
    }
  ]
}
```
- **Execution Guardrails:**
  - Hard tool-call iteration cap (max 5 tool steps per run) to prevent infinite loops (`NFR Reliability`).
  - Zero write, approval, or customer-messaging tools are bound to the LangChain model (`BR-4`, `BR-5`).

---

## 3. State & Lifecycle Rules

### Workflow Stages (Derived from Week 1 `IE-3` & `# Flows`)
`Intake` -> `Investigation` -> `Policy Review` -> `Recommendation` -> `Approval` -> `Closure` (plus `Escalated` branch)

### Agent State Permissions & Locks
1. **Allowed Execution Stages:** The agent may run only when a case is in `Investigation` or `Policy Review` (Week 1 Flow Step 2).
2. **Allowed Stage Transitions:**
   - Advances stage to `Recommendation` only when `status == "DRAFT_READY"` and all citations pass verification.
   - Keeps stage in `Investigation` and emits a **Missing Information Alert (`IE-4`)** when `EC-1`, `EC-2`, `EC-3`, or `EC-4` occurs.
3. **Hard Approval & Closure Locks (`BR-4`, `BR-5`, `EC-6`):**
   - The agent is **strictly blocked** from transitioning any case to `Approval` or `Closure`.
   - Only a **Supervisor / Reviewer** using `IE-6` controls (*Approve, Reject, Modify, Request Additional Investigation*) may record a final decision and close a case. Any automated attempt to close without recorded approval raises `EC-6`.

---

## 4. Behavioral Rules & Error Matrix

### Extended Rules (Building on Week 1 `BR-1`–`BR-6`)
- **BR-7 (Safe Abstention):** When `search_approved_policies` returns `[]` (`EC-3`), customer/complaint data is missing (`EC-1`/`EC-2`), or operational facts conflict (`EC-4`), the agent **must abstain** (`draft_recommendation = null`, `status = "ABSTAINED"`) and populate `missing_information` without fabricating facts.
- **BR-8 (Traceable Citations):** Every policy assertion in `draft_recommendation` must cite a `source_id` and `version` present in the current `search_approved_policies` tool response (`BR-3`).
- **BR-9 (Role Authorization Before Restricted Access):** The MCP server must verify `user_role` before forwarding `access_label="Restricted"` to `RetrievalService.retrieve()` (`NFR Security`).
- **BR-10 (Auditability):** All MCP tool calls, arguments, retrieved `source_id`s, and generated drafts must be logged (`NFR Auditability`).

### Error Matrix (Derived from Week 1 `EC-1`–`EC-6`)

| Error Code | Trigger Condition | Controlled Agent Behavior |
| :--- | :--- | :--- |
| **`EC-1`** | `get_customer_account_facts` cannot locate customer | Halt synthesis; set `status="ABSTAINED"`; surface `IE-4` missing info alert. |
| **`EC-2`** | `get_complaint_case` receives unknown `complaint_id` | Return structured not-found error; do not create draft record. |
| **`EC-3`** | `search_approved_policies` returns `[]` | Halt synthesis; set `status="ABSTAINED"` (`BR-7`); flag for analyst review. |
| **`EC-4`** | SQL/case facts conflict across sources | Halt synthesis; set `status="ABSTAINED"`; list conflicting fields in `IE-4` alert. |
| **`EC-5`** | SQL, `RetrievalService`, or LLM raises runtime error | Set `status="DEGRADED"`; preserve manual UI/case data (`NFR Reliability`). |
| **`EC-6`** | Attempt to transition to `Closure` without approval | Block state transition; reject action (`BR-5`). |

---

