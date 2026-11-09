# Unit & Integration test setup

## Requirements

- Python version supported by the project
- Project dependencies installed in `.venv`
- `pytest` available in that environment

No external database is needed. The integration fixture creates an independent
in-memory SQLite database for each test, creates the application tables, and
seeds one customer and one account. The API's `get_db` dependency is overridden
to use that database; test sessions inspect the persisted state. The override
is restored and the database engine disposed after each test.

## Run the suite

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m pytest app\tests\unit -q
.\.venv\Scripts\python.exe -m pytest app\tests\integration -q
```

Run the same command a second time to check repeatability. Each test receives a
fresh database, so results do not depend on test order or data left by an
earlier run.

## Coverage

`app/tests/integration/test_api_integration.py` exercises customer lookup
(200/404), complaint creation (201/422), valid and invalid status transitions,
complaint/event rollback when the initial event insert fails, and a simulated
unavailable database. Tests assert response contracts, correlation IDs, and
database state after both successful and failed operations.
