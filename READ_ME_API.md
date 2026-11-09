# FastAPI Application - Banking Complaint Resolution Assistant

This project implements a production-aware Python API backend for the Banking Complaint Resolution Assistant, adhering to a clean, layered architecture (`app/`).

## Prerequisites
- **Python 3.10+**
- Install dependencies from the repository root:
  ```powershell
  .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  ```
- The current API is configured to use SQLite (`customer.db`); PostgreSQL is
  not required by the current application configuration.

Authentication is currently disabled. Run this API only in a trusted local
development environment; do not expose it to untrusted networks or use it with
real customer data.

## Project Directory Structure
```text
app/
 ├ main.py
 ├ core/
 │   ├ config.py
 │   └ dependencies/
 │       └ dependencies.py
 ├ api/
 │   └ routers/
 │       ├ health.py
 │       ├ customers.py
 │       └ complaints.py
 ├ schemas/
 ├ services/
 ├ repositories/
 ├ models/
 └ tests/


 # Activate Virtual Environment:

# Windows (PowerShell):

Bash
.venv\Scripts\activate


# macOS / Linux:

Bash
source .venv/bin/activate

# Install Dependencies:

Bash
pip install fastapi uvicorn pydantic-settings psycopg2-binary python-dotenv


# Run FASTAPI in env:

uvicorn app.main:app --reload

## Create an account before submitting a complaint

In Swagger (`/docs`), create a customer with `POST /customers`, then use its
returned `customer_id` with `POST /accounts`. The account response contains the
`account_id` required by `POST /complaints`.

Example request for `POST /accounts`:

```json
{
  "customer_id": 1,
  "account_type": "CHECKING",
  "balance": 0
}
```

`balance` is optional and defaults to `0`. Use the returned account ID and the
same customer ID when creating the complaint.

Complaint history is available through
`GET /complaints/{complaint_id}/status-history`. Complaint deletion is a
supervisor-only soft delete: normal complaint reads return not found, while
the complaint record, status history, and deletion actor/timestamp are retained
in the database. No retention/purge job is configured.