# Week 3 Review Reflection

Follow-up: Authentication has since been temporarily disabled for local
development; customer, account, and complaint routes are currently
unauthenticated.

## What changed

Following the blocking review findings, customer/account/complaint APIs now
require configured OIDC RS256 bearer tokens and enforce the agreed role
matrix. Complaint deletion is supervisor-only and preserves the complaint and
status history while retaining the deleting subject and timestamp. The
history endpoint now uses its event response schema and returns a not-found
error for unknown or soft-deleted complaint IDs.

## What went well

- The API fails closed when authentication configuration is absent; no
  hard-coded development token was introduced.
- Tests use an overridden identity dependency for ordinary application
  scenarios and separately verify JWT signature/claims and denied roles.
- Soft deletion preserves the history rows and records who performed the
  deletion.
- Full suite passes: 45 passed.

## What remains

- Configure the actual issuer, audience, JWKS endpoint, and roles claim before
  deployment.
- Audit event production for retrieved documents, recommendations, analyst
  overrides, and approval decisions must be implemented alongside those
  future API features.
- No remote PR/review/approval was created; changes remain local on
  `Sprint-2` per user direction.
