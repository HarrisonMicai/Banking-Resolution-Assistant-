# Week 3 Pull Request Evidence

## Status

**Draft only — not ready to submit or merge.** No matching open pull request
was found for `Sprint-2`. The requested base branch `develop` does not exist on
the configured `origin` remote. No PR creation capability is available in this
workspace session, so no remote PR or coach review request has been made.

The current branch is 14 commits ahead of `origin/main`. Its committed tree
includes 5,835 generated files under `app/venv/`. They are staged for removal
from the branch tree (without deleting the local environment), but the cleanup
must be committed before a feature PR is submitted.

The local uncommitted change to `app/schemas/complaint_schema.py` is not part
of this PR draft and should not be included without a separate scope decision.
It also contains trailing whitespace, so a repository-wide `git diff --check`
will report it until the owner cleans or excludes that local edit.

## Proposed title

`Micai Harrison Perform Pull Request Code Review (Week 3)`

The consultant name is inferred from existing commit authors and should be
confirmed before submission.

## Summary

- Implement complaint and customer REST API flows.
- Create complaints and initial status events atomically.
- Return structured API errors with correlation IDs.
- Emit safe structured request logs.
- Add unit and isolated integration coverage.

## Spec sections implemented

- Functional Requirements: **FR-1 Customer Complaint Retrieval** and
  **FR-3 Evidence Retrieval** (complaint/customer data retrieval and intake
  behavior only).
- Core Flows: **Case Initialization & Ingestion**.
- Error Conditions: **EC-1 Customer Data Not Found** and
  **EC-2 Complaint Not Found**.
- Non-Functional Requirements: **Security**, **Privacy**, and **Reliability**
  error/logging behaviors.

This scope does not implement all requirements in those sections. In
particular, API authentication/authorization, audit logging, policy evidence,
and human approval workflows remain outside the current implementation.

## Acceptance evidence

- Isolated integration fixture seeds a synthetic customer and account in
  in-memory SQLite.
- Integration tests exercise customer lookup, complaint create, valid and
  invalid status updates, initial status-event rollback, database dependency
  failure, response contracts, correlation IDs, and persisted database state.
- Integration suite passed twice in standard order and once in reverse order;
  see `integration_test_report.txt`.
- Structured error and logging tests cover safe responses and correlation IDs.

## Tests

- `.\.venv\Scripts\python.exe -m pytest app\tests\integration -q`:
  **6 passed**, repeated twice.
- Same six integration tests in reverse order: **6 passed**.
- Full `.\.venv\Scripts\python.exe -m pytest app\tests -q`:
  **30 passed, 10 warnings**.

## SonarQube review

SonarQube for IDE analysis was triggered for the complaint/customer/account
routes, application setup, error handlers, complaint schema, and integration
test files. The user reports that the built-in VS Code extension identified
asynchronous-code errors and duplication findings and that they fixed those
findings. The exact rule IDs/findings and a post-fix scan result were not
provided in this review record; add that evidence before reviewer sign-off.
Security hotspot retrieval remains blocked because this workspace is not
bound to a SonarQube Cloud/Server project. This is separate from the reported
local IDE findings.

## Risks and limitations

1. **BLOCKING:** the branch tree includes 5,835 virtual-environment files.
   Their removal is staged but not committed. Commit the cleanup and confirm
   the resulting PR diff contains only intentional files.
2. **BLOCKING before external use:** the approved spec requires authentication
   and role-based access, which are not implemented on these API routes.
3. **BLOCKING:** `develop` is absent from `origin`; confirm the correct base or
   have the repository owner create it.
4. **REVIEW EVIDENCE PENDING:** record the SonarQube finding details and
   post-fix scan result reported by the user. Configure Connected Mode and
   review security hotspots if the review requires server-side hotspot
   evidence.
5. **NON-BLOCKING:** SQLAlchemy emits existing deprecation warnings for
   `declarative_base()` and `datetime.utcnow()`.
6. **NON-BLOCKING:** some HTTP error codes are selected by matching detail
   strings, so changing route detail text can break the mapping.

## Review focus

- Confirm the intended Week 3 scope and accepted spec sections.
- Remove virtual-environment and generated files from the PR.
- Verify API authentication/authorization scope against the approved spec.
- Review SonarQube findings, especially security hotspots.
- Confirm reviewer approval and acceptance evidence before merge.

## Review and merge decision

- Local review evidence is recorded in `code_review_checklist.md`.
- No GitHub inline comments or PR review have been submitted because no
  matching PR exists.
- **Decision: DO NOT MERGE** until all blocking items above are resolved,
  reviewer approval is recorded, and the feature PR targets the approved base.
- Do not merge without coach approval.
