# Complaint creation transaction

## Transaction boundary

Creating a complaint and its initial `SUBMITTED` status event is one database
transaction. The complaint is flushed first to obtain its generated ID, then
the status event is inserted. The transaction commits only after both writes
succeed. Any write failure rolls the session back.

## Failure-injection evidence

`app/tests/test_transactions.py::test_status_event_insert_failure_rolls_back_complaint`
injects a database error during the status-event insert, after the complaint
insert has been flushed. It verifies the API returns 500 and that inspection
of the database finds zero complaint rows and zero status-event rows.

`app/tests/test_transactions.py::test_complaint_and_initial_status_event_commit_together`
verifies that the success path persists both rows and links the initial event
to the created complaint.

`app/tests/test_transactions.py::test_repeated_create_request_creates_separate_complaints`
demonstrates the current retry behavior: sending the same request twice creates
two complaints and two initial events.

## Idempotency consideration

Complaint creation currently has no idempotency key. Retrying a successful
`POST /complaints` request creates another complaint (and its initial event);
the operation is not idempotent. For retry-safe clients, a future change can
accept an `Idempotency-Key`, persist it with a unique constraint, and replay
the original response for repeated keys. Until then, clients should not
automatically retry an ambiguous create request without first checking whether
the complaint was created.
