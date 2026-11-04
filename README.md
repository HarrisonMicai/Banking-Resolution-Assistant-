# Banking Resolution Assistant

## API architecture

The FastAPI application lives in `app/` and follows this request path:

```text
HTTP request
  -> app/main.py (middleware and router registration)
  -> app/api/routes/ (HTTP validation and response mapping)
  -> app/services/ (use-case orchestration and transaction boundaries)
  -> app/repositories/ (SQLAlchemy reads and persistence staging)
  -> app/models/ (ORM tables, relationships, and complaint status rules)
  -> database
```

Routes use FastAPI and Pydantic for the HTTP contract. They pass the SQLAlchemy
session and validated values to a service. Services coordinate repositories,
commit or roll back use-case transactions, and report expected business errors.
Repositories perform ORM queries and stage changes in the session; they do not
commit independently. The complaint service creates the complaint and its
initial status event in one transaction.

Pydantic request and response schemas are centralized in `app/schemas/`:
customer contracts are in `customer_schema.py`, account contracts in
`account_schema.py`, complaint contracts in `complaint_schema.py`, health
responses in `health_schema.py`, and the root response in `root_schema.py`.
The shared error response is in `error_schema.py`. Route modules import these
models so FastAPI can validate requests and generate the corresponding
OpenAPI schemas.

`app/error_handlers.py` maps HTTP, validation, and database exceptions into
the standard API error shape. Middleware in `app/main.py` supplies a
correlation ID and writes a structured request log using
`app/core/logging_config.py`.

The readiness endpoint probes the same SQLAlchemy engine used by API
requests, so it reports whether the API's configured database is reachable.

## Database configuration

The API currently uses SQLAlchemy with the SQLite URL `sqlite:///customer.db`,
configured in `app/database/connection.py`. `get_db` provides and closes a
session for each request. `app/core/config.py` is retained as the central
application settings module; its settings are not currently used to construct
the API's SQLAlchemy engine.

## Tests

Run the API test suite from the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest app\tests -q
```

Integration tests override the database dependency with a fresh in-memory
SQLite database, so they do not rely on records in `customer.db`.

## Complaint analysis script

The standalone script `complaint_analysis.py` reads `complaints.csv` from the
current working directory and writes `complaint_analysis_output.csv` there.
Run it from the repository root with:

```powershell
.\.venv\Scripts\python.exe complaint_analysis.py
```
