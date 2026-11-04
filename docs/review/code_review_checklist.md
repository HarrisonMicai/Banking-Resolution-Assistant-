# Week 3 Code Review Checklist

Checklist derived from the exercise requirements supplied in the task. The
separate `code_review_checklist.md` resource was not present in the repository.

| Review area | Result | Evidence / comment | Blocking |
|---|---|---|---|
| Spec alignment | PARTIAL | Complaint/customer retrieval and intake align with FR-1, FR-3, Core Flow 1, EC-1, and EC-2. Authentication/authorization required by Security preconditions is absent; auditability and human approval requirements are not implemented in this scope. | YES before external use |
| Correctness | PASS | Complaint creation and its initial status event are committed atomically. Repository failures roll back and re-raise. Full suite passes. | NO |
| Layer boundaries | REVIEW | HTTP errors are raised with FastAPI `HTTPException` and formatted centrally. The current complaint/customer routes also access SQLAlchemy sessions directly rather than delegating persistence through the repository/service layers. | NO |
| Parameterized SQL | PASS WITH SCOPE NOTE | API persistence uses SQLAlchemy query/model operations; customer repository uses a bound `?` parameter. No string-built SQL was identified in the reviewed route path. | NO |
| Secrets / data protection | PARTIAL | Structured logging uses an allow-list and excludes request bodies and exception text; error bodies use safe messages. Authentication/access control is absent. Sonar security hotspot results remain unavailable until Connected Mode is configured. | YES before external use |
| Tests | PASS | Full suite: 30 passed, 10 warnings. Integration suite: 6 passed in standard order twice and reverse order once. | NO |
| Errors / logging | PASS WITH FOLLOW-UP | Standardized error body, correlation header, and request log are exercised. `HTTP_ERROR_CODES` depends on exact detail strings, which is brittle. | NO |
| Documentation | PARTIAL | Integration setup and results are documented. Review-specific source templates were absent; local PR evidence and this checklist were created from the requirements supplied in the prompt. | NO |
| SonarQube | USER-REPORTED FIXES; SECURITY REVIEW PENDING | User reports using the built-in VS Code SonarQube extension, fixing asynchronous-code findings and duplication findings. The exact rules/findings and post-fix scan are not recorded here. Security hotspot retrieval still reports that the workspace is not bound to a remote SonarQube project. | Security review evidence pending |
| PR scope / base | FAIL | `Sprint-2` is 14 commits ahead of `origin/main`; its current committed tree includes 5,835 files under `app/venv/`. Those generated files are staged for removal from the branch tree, but the cleanup is not committed. The remote has no `develop` branch and no matching open PR was found. | YES |

## Local review findings

### BLOCKING

1. **PR hygiene:** the branch comparison contains 5,835 vendored virtual
   environment files. Narrow the branch/PR to intended source, tests, and
   evidence before review; generated environments must not be submitted.
2. **Security/spec:** the approved specification requires authentication and
   role-based access, but no such protection is present on the API routes.
   Do not expose these endpoints externally until the requirement is met or
   the scope is formally approved.
3. **Review process:** no PR exists for `Sprint-2`, and `origin` has no
   `develop` branch. Confirm the target branch and create the scoped feature
   PR before requesting coach/reviewer approval.
4. **Sonar evidence:** user reports fixing asynchronous-code and duplication
   findings reported by the VS Code SonarQube extension. Record the finding
   details and rerun result in the PR evidence. Security hotspot retrieval
   remains unavailable until Connected Mode is configured and the hotspots
   are reviewed.

### NON-BLOCKING

1. **Error-code mapping maintainability:** route detail strings are used as
   lookup keys for error codes. A future wording change can silently fall back
   to a generic code; a typed error code or status-to-code mapping would be
   less fragile.
2. **Layering:** routes make direct database calls. This works for the current
   API but couples the HTTP layer to SQLAlchemy and duplicates persistence
   orchestration.
3. **Deprecation cleanup:** SQLAlchemy warns about `declarative_base()` and
   `datetime.utcnow()`; these warnings did not fail tests.
4. **Local schema edit:** `app/schemas/complaint_schema.py` has an uncommitted
   change removing `Field` descriptions and adding trailing whitespace. It is
   not part of this review scope and should remain excluded unless
   intentionally requested.

## Review comments / resolution trail

- Local findings above are review comments prepared for the PR.
- No remote comments were posted because no PR exists.
- Domain/repository test failures were fixed; the complete suite now passes.
- Generated virtual-environment files are staged for removal from the branch
  tree, and ignore rules were added. Commit the cleanup before creating a PR.
- Authentication/authorization, SonarQube security hotspot review, and PR
  target confirmation remain unresolved. User-reported Sonar async and
  duplication fixes need their result captured in the PR evidence.
- Current merge recommendation: **DO NOT MERGE**.
