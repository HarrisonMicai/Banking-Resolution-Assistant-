### 2. `plan.md`

```markdown
# Implementation Plan — Exercise 5.1.1: Controlled Investigation Agent

## 1. Architectural Strategy
To evolve the Banking Complaint Resolution Assistant in Sprint 3 without duplicating Week 4 components or weakening governance, we implement a **read-only FastMCP tool layer** (`app/mcp/server.py`) paired with a **bounded LangChain agent controller** (`app/agent/`).

### Key Design Choices
1. **Strict Reuse of Week 4 `RetrievalService`:** `search_approved_policies` in `app/mcp/server.py` wraps `RetrievalService.retrieve()` from `app/rag/retrieval_service.py`. Existing ChromaDB indexing, `gemini-embedding-001` embeddings, `status = Approved` filtering, and lexical Jaccard reranking remain untouched.
2. **Domain-Separated MCP Tools (Sprint 3 Alignment):** Expose clear, least-privilege (`readOnlyHint=True`) tools across **SQL** (`get_customer_account_facts`), **RAG** (`search_approved_policies`), **Case-Management** (`get_complaint_case`), and **Governance** (`get_spec`, `get_plan`, `list_tasks`).
3. **LangChain + MCP Adapter Integration:** Connect LangChain to FastMCP via `langchain-mcp-adapters` (`MultiServerMCPClient`), using `with_structured_output(SystemAnalysisOutput)` to enforce separation between **Verified Facts** and **System Analysis** (`IE-2`).
4. **Deterministic Python Guardrails Around the LLM:**
   - Pre-LLM and post-LLM checks enforce **Safe Abstention (`BR-7`)** whenever `EC-1`–`EC-4` occur.
   - Programmatic citation verification checks every `source_id` in `SystemAnalysisOutput` against the actual `search_approved_policies` tool trace (`BR-3`, `BR-8`).
   - State transition locks prevent any automated move to `Approval` or `Closure` (`BR-4`, `BR-5`, `EC-6`).

## 2. Step 1 Requirement Notes & Resolved Ambiguities
- **Week 1 Abstention vs. Week 4 Empty Results:** Week 1 requires safe abstention on insufficient evidence (`EC-3`), while Week 4 `RetrievalService.retrieve()` returns `[]` on zero matches and raises `RuntimeError` on service failure. *Resolution:* Map `[]` to `EC-3` (`ABSTAINED`) and `RuntimeError`/`ValueError` to `EC-5` (`DEGRADED`) in the MCP layer so manual investigation remains available (`NFR Reliability`).
- **Access Control Propagation (`BR-9`):** Week 4 Section 4 notes that `access_label` metadata filtering is not an authorization check. *Resolution:* `search_approved_policies` requires `user_role` and blocks `access_label="Restricted"` unless the role is authorized.
- **Sprint 3 Phased Delivery:** Exercise 5.1.1 establishes `spec/agent/spec.md`, `plan.md`, `tasks.md`, and core lookup tools on Day 1, feeding directly into **5.1.2 (Tool Catalogue)**, **Day 2 (LangChain Investigation Agent)**, **Day 3 (Mock SQL/Case Backends & FastMCP)**, **Day 4 (Approval & Denied Paths)**, and **Week 6 (LangGraph Multi-Agent Workflow)**.

## 3. Repository File Structure
- `spec/agent/spec.md` — Controlled Investigation Agent specification (Exercise 5.1.1 deliverable).
- `plan.md` — Implementation strategy and requirement notes (Exercise 5.1.1 deliverable).
- `tasks.md` — Execution checklist (Exercise 5.1.1 deliverable).
- `app/mcp/server.py` — FastMCP server exposing read-only lookup and RAG tools.
- `app/agent/schemas.py` — Pydantic contracts (`SystemAnalysisOutput`, `Citation`, `WorkflowStage`).
- `app/agent/controller.py` — LangChain + MCP orchestration, abstention guards, citation verification, and state locks.
- `app/tests/test_mcp_lookup.py` & `app/tests/test_investigation_agent.py` — Automated tests for normal, boundary, and `EC-1`–`EC-6` failure paths.

## 4. Dependencies & Limitations
- **Dependencies:** Tagged Week 4 release (`app/rag/retrieval_service.py`), ChromaDB synthetic corpus (`KB-GUIDE v1.0`), `mcp` (FastMCP), `langchain`, `langchain-mcp-adapters`, and Gemini API credentials via `.env` (no committed secrets).
- **Limitations:** Restricted to synthetic datasets (`NG-4`) and fee/service complaint scenarios (`NG-5`); human supervisor approval remains mandatory for final decisions (`BR-4`).