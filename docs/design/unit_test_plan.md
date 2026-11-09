# Unit Test Plan (Step 1)

## Scope
Validate business rules, domain transitions, repository validation boundaries, and escalation criteria for the Banking Complaint Resolution Assistant service layer.

## Test Cases
1. **Happy Paths:**
   - Successful complaint creation with valid customer and account foreign key existence.
   - Valid status transitions (SUBMITTED -> UNDER_REVIEW -> RESOLVED -> CLOSED) accompanied by status history logging.
2. **Boundary & Validation Cases:**
   - Invalid status progressions throwing a `ValueError` (e.g., SUBMITTED -> CLOSED).
   - Missing customer check triggering a `404`/`ValueError` exception.
3. **Escalation Indicator Cases:**
   - High priority or urgent severity triggering mandatory supervisor/immediate escalation per the escalation matrix.
   - Fraud category or security trigger words (unauthorized, threats of harm) correctly flagging immediate escalation review requirements.