# Structured errors and request logging

The API error catalog and logging requirements supplied for Week 3 were not
present as separate files in the repository; this implementation follows the
catalog and required/forbidden logging fields provided with the exercise.

## Error contract

Every handled error returns the same JSON shape:

```json
{
  "code": "VALIDATION_ERROR",
  "message": "Request validation failed",
  "correlation_id": "11111111-1111-4111-8111-111111111111"
}
```

`app/error_handlers.py` maps customer and complaint not-found errors,
invalid-status transitions, validation failures, database failures, and
unexpected exceptions to stable codes and HTTP statuses. Account-not-found,
generic resource-not-found, request conflict, and bad-request codes extend the
provided catalog for existing API operations. Route handlers raise FastAPI
`HTTPException` consistently; the central handler maps each exception's
status and detail to this structured response contract.

| Code | HTTP status | Safe message |
|---|---:|---|
| `CUSTOMER_NOT_FOUND` | 404 | Customer not found |
| `COMPLAINT_NOT_FOUND` | 404 | Complaint not found |
| `INVALID_STATUS_TRANSITION` | 409 | Invalid complaint status transition |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `DEPENDENCY_UNAVAILABLE` | 503 | A required service is unavailable |
| `INTERNAL_ERROR` | 500 | An unexpected error occurred |
| `ACCOUNT_NOT_FOUND` | 404 | Account not found for this customer |
| `RESOURCE_NOT_FOUND` | 404 | Requested resource was not found |
| `CONFLICT` | 409 | The request conflicts with the current resource state |
| `BAD_REQUEST` | 400 | The request could not be completed |

Validation messages are generic; raw submitted values and validation internals
are not returned. Unexpected errors return only the catalog's safe 500 message.

## Correlation and structured logs

`app/middleware.py` accepts a caller correlation ID only when it has a UUID
shape; otherwise it creates a UUID. The ID is returned in the
`X-Correlation-ID` header and error payload. `app/core/logging_config.py`
emits one JSON record per request with `timestamp`, `level`,
`correlation_id`, `operation`, `outcome`, and `duration_ms` (plus `status_code`).
Operation names use the HTTP method and route template; request bodies,
complaint descriptions, customer records, credentials, and exception text are
not logged. Unexpected exceptions are converted at the middleware boundary to
a safe response, preventing exception details from being emitted in a server
traceback during ordinary request handling.

## Failure evidence

`failure_matrix.csv` and `sample_logs.jsonl` record sanitized examples for
missing/invalid requests, unavailable database, and unexpected errors.
`app/tests/test_error_handling.py` exercises these cases and checks the
response/log correlation IDs and sensitive-data exclusions. The transaction
tests continue to verify atomic complaint plus initial status-event creation.
