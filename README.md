# Banking Resolution Assistant

## Application structure

Application code lives in the `app/` Python package:

```text
app/
├── api/           # HTTP routes and API wiring
├── core/          # Shared configuration and infrastructure
├── models/        # Domain models
├── repositories/  # Database access
├── schemas/       # API request and response schemas
└── services/      # Business logic and complaint analysis
```

The `api/` and `schemas/` packages are ready for future API code.

## Complaint analysis

Run the existing command from the repository root with
`python complaint_analysis.py`. Its implementation is in
`app/services/complaint_analysis.py`. It reads `complaints.csv` and writes
`complaint_analysis_output.csv` in the current working directory.

## Data access

`app/core/database_manager.py` manages SQLite connections and transactions.
Repositories in `app/repositories/` own database queries and use parameterized
SQL. Set `DB_NAME` in the environment to select a database file; the default is
`BankCRS.db`.

```python
from app.core.database_manager import DatabaseManager
from app.repositories.customer_repository import CustomerRepository

db_manager = DatabaseManager()
customer_repo = CustomerRepository(db_manager)

customer = customer_repo.get_by_id("CUST-12345")
print(customer)
```