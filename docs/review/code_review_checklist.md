# Week 3 Code Review Checklist

Review scope: Week 3 API implementation and the requested fixes on local
`Sprint-2`, against `specs/complaint-resolution/Banking Spec 1.3.1.md`.

Follow-up: Authentication has since been temporarily disabled. Customer,
account, and complaint routes are unauthenticated; run locally only.

| Review area | Result | Evidence / comment | Blocking |
|---|---|---|---|
| Spec alignment | PARTIAL | Complaint routes now require OIDC/JWT identity and roles, and complaint deletion retains the record/history with actor/timestamp. Document retrieval, recommendation, analyst override, and approval audit events remain unimplemented because those features/endpoints are not present. | YES before complete spec sign-off |
| Correctness | PASS | Status-history returns its event response schema; history lookup first verifies the complaint is active; soft delete hides the complaint but retains complaint/event rows and records the deleting subject/time. | NO |
| Layer boundaries | PASS | Routes delegate to services/repositories. Authentication and role checks are reusable FastAPI dependencies. | NO |
| Parameterized SQL | PASS | Reviewed persistence uses SQLAlchemy ORM filters and model operations; no interpolated SQL was found. | NO |
| Secrets / data protection | PASS WITH DEPLOYMENT GATE | All customer/account/complaint routes enforce configured RS256 JWT verification and role policies. Issuer/audience/JWKS settings are not yet known and must be configured before valid access is possible. No static-token bypass exists. | YES until configured |
| Tests | PASS | Full suite: 45 passed, 16 warnings. Added JWT claim/signature, missing-auth, role-denial, history-contract, unknown-history, and soft-delete-retention coverage. | NO |
| Errors / logging | PASS WITH FOLLOW-UP | Auth failures map to structured 401/403/503 errors, preserving the bearer challenge header. Existing error-code mapping still partly depends on human-readable detail strings. | NO |
| Documentation | PASS WITH LIMITATION | `READ_ME_API.md` documents auth configuration/roles, history and soft-delete behavior. Full audit event types for documents/recommendations/overrides/approvals await those features. | NO |
| PR scope / review process | OPEN | Per user direction, changes remain on `Sprint-2`. No remote PR exists; no GitHub PR creation/review-comment capability is available in this session. No approval or merge occurred. | YES for formal remote review |

## Review findings and disposition

### Resolved in the local implementation

1. **Authentication/authorization:** Customer, account, and complaint routes
   now validate RS256 bearer JWTs using configured issuer, audience, and JWKS
   URL. Reads allow `analyst`, `supervisor`, and `specialist`; create/update
   allow `analyst`; delete allows `supervisor`. Missing configuration fails
   closed. Provider settings must be supplied before deployment.
2. **Complaint deletion/history retention:** Complaint deletion is now a
   supervisor-only soft delete. `ComplaintSoftDeletion` records actor subject
   and timestamp while retaining the complaint and its status events; normal
   complaint reads/history return not found after deletion.
3. **Status-history contract:** `GET /complaints/{id}/status-history` returns
   `ComplaintStatusEventRead`, including previous/new status, timestamp,
   event ID, and notes.
4. **Unknown complaint history:** The service verifies the complaint exists
   and is not soft-deleted before returning history; missing records produce
   the standard 404.

### Still open

1. **Full audit coverage:** Current complaint status events and soft-delete
   metadata are retained. The API has no document retrieval, recommendation,
   analyst override, or approval endpoints, so those event types cannot yet be
   emitted. They remain required before full spec sign-off.
2. **Remote PR gate:** No remote PR or reviewer/coach approval is recorded.
   The changes are local and uncommitted on `Sprint-2`; no remote PR creation
   capability was available.
3. **Identity provider config:** Issuer, audience, and JWKS URL remain unset.
   The API correctly rejects missing credentials and fails closed if a token
   is presented while settings are incomplete.

## Verification

- `.\.venv\Scripts\python.exe -m pytest app\tests -q`: **45 passed**, exit
  code 0; **16 warnings**.
- `git diff --check`: **PASS**.
- No remote review comments, approval, or merge were made.

**Recommendation: do not expose externally until OIDC settings are configured.
Formal merge approval remains outstanding.**
