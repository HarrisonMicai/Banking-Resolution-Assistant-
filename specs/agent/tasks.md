# Execution Tasks — Exercise 5.1.1

## Phase 1: Requirement Review & Design Artifacts (Steps 1–2)
- [ ] **T-1:** Review Week 1 Policy RAG Behavior Spec (`FR-1`–`FR-6`, `BR-1`–`BR-6`, `EC-1`–`EC-6`, `IE-1`–`IE-7`), Week 4 `RetrievalService` API Contract, and Sprint 3 rubric; record resolved ambiguities in `plan.md`.
- [ ] **T-2:** Author `spec/agent/spec.md` defining SQL, RAG, Case-Management, and Artifact lookup contracts, workflow states, abstention rules (`BR-7`), and error handling (`EC-1`–`EC-6`).
- [ ] **T-3:** Finalize `plan.md` and `tasks.md` for feature branch review and handover to Exercise 5.1.2 (Tool Catalogue).

## Phase 2: FastMCP Lookup & RAG Wrapper Tools (Step 3a)
- [ ] **T-4:** Implement `app/mcp/server.py` using FastMCP with `readOnlyHint=True` annotations (`NG-1`, `NG-3`).
- [ ] **T-5:** Implement `search_approved_policies` wrapping `RetrievalService.retrieve()` from `app/rag/retrieval_service.py` (default `rerank=True`), mapping `[]` -> `EC-3` and `RuntimeError`/`ValueError` -> `EC-5`.
- [ ] **T-6:** Enforce `user_role` authorization in `search_approved_policies` before allowing `access_label="Restricted"` (`BR-9`, `NFR Security`).
- [ ] **T-7:** Implement read-only artifact lookup tools (`get_spec`, `get_plan`, `list_tasks`) in `app/mcp/server.py` with section-level filtering on `spec/agent/spec.md`.
- [ ] **T-8:** Define/stub read-only `get_complaint_case` and `get_customer_account_facts` MCP tool interfaces returning structured `EC-1`, `EC-2`, and `EC-4` payloads.

## Phase 3: LangChain Agent Controller & Guardrails (Step 3b)
- [ ] **T-9:** Create `app/agent/schemas.py` defining Pydantic `SystemAnalysisOutput`, `Citation`, and `WorkflowStage` (`IE-2`, `IE-3`).
- [ ] **T-10:** Implement `app/agent/controller.py` connecting LangChain to `app/mcp/server.py` via `langchain-mcp-adapters` with `with_structured_output(SystemAnalysisOutput)` and a 5-step tool-call cap.
- [ ] **T-11:** Implement deterministic abstention (`BR-7`) when `EC-1`, `EC-2`, `EC-3`, or `EC-4` is triggered, and graceful degradation (`EC-5`) on service failure.
- [ ] **T-12:** Implement post-generation citation check (`BR-3`, `BR-8`) and state transition lock blocking automated `Approval` or `Closure` (`BR-4`, `BR-5`, `EC-6`).

## Phase 4: Verification & Handover to 5.1.2 (Steps 4–5)
- [ ] **T-13:** Write unit and failure-injection tests in `app/tests/test_mcp_lookup.py` and `app/tests/test_investigation_agent.py` covering normal grounded drafts, `Restricted` role checks, `EC-1`–`EC-6` error paths, and blocked case closure.
- [ ] **T-14:** Run `python -m pytest` across `test_retrieval.py` and new Sprint 3 tests; capture test evidence.
- [ ] **T-15:** Update `README.md` with setup, FastMCP + LangChain architecture notes, limitations, and handover readiness for Exercise 5.1.2.
- [ ] **T-16:** Commit all artifacts to the assigned feature branch, open PR linking `spec/agent/spec.md`, and request coach review before merging.