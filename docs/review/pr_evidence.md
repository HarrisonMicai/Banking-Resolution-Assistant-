# Week 3 Pull Request Evidence

## Status

Per user direction, the fixes are being made on local `Sprint-2`; no separate
feature branch or PR was requested. No remote PR exists, and no PR creation or
review-comment capability is available in this session. No remote approval,
coach review, or merge was performed.

The local worktree contains prior uncommitted Week 3 implementation changes as
well as these fixes. They have not been committed or pushed.

Follow-up: Authentication has since been temporarily disabled for local
development. The API is currently unauthenticated and must not be exposed.

## Proposed title

`Micai Harrison Perform Pull Request Code Review (Week 3)`

## Fixes and spec traceability

- API auth and role restrictions implement the Security NFR for current
  customer/account/complaint endpoints.
- Complaint soft deletion retains status history and records deletion actor
  and timestamp, supporting the Auditability NFR.
- Status history now returns the stored event fields and returns 404 for
  unknown or soft-deleted complaints.

Audit records for retrieved documents, recommendations, analyst overrides,
and approval decisions remain unimplemented because those features do not yet
exist in this API.

## Test evidence

- Command: `.\.venv\Scripts\python.exe -m pytest app\tests -q`
- Result: **45 passed**, **16 warnings**, exit code **0**.
- Coverage includes JWT validation and role restrictions, complete history
  serialization, missing complaint history, and retained soft-deleted data.

## Deployment configuration

The identity provider settings are not yet known. Before valid API access,
configure `AUTH_ISSUER`, `AUTH_AUDIENCE`, `AUTH_JWKS_URL`, and
`AUTH_ROLES_CLAIM`. The API fails closed; no static/development token bypass
is present.

## Review decision

- Local checklist updated in [`code_review_checklist.md`](./code_review_checklist.md).
- No remote PR review trail exists.
- **Do not expose externally until identity-provider settings are configured.
  Formal remote reviewer/coach approval remains outstanding.**
