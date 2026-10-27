# Banking-Resolution-Assistant-

Initial project structure:

spec/ — requirements and specifications

docs/ — project documentation

data/ — datasets and data-related assets

src/ — application source code

tests/ — automated tests

Add language- and framework-specific setup as the implementation stack is chosen.

# Python
pycache/ *.py[cod] *.pyo *.pyd *.egg-info/ venv/ .venv/ env/

# Node
node_modules/ npm-debug.log* yarn-debug.log* yarn-error.log*

# Environment Variables
.env .env.local .env.*.local

# Databases
*.db *.sqlite *.sqlite3

# Logs
logs/ *.log

# IDE
.vscode/ .idea/ *.iml

# OS
.DS_Store Thumbs.db

# Build
dist/ build/ coverage/

# Testing
.pytest_cache/ .coverage

Misc
*.swp *.swo


## Data Access Layer & Repositories

### Configuration
The data layer relies on configuration variables defined via environment files (see `environment_example.txt`). Ensure your local environment maps parameters correctly:
- `DB_NAME`: Target database filename or connection target.

### Responsibilities
- **DatabaseManager (`src/data/database_manager.py`)**: Handles the database connection lifecycle and provides transactional context managers (`transaction()`) that handle automated commits and rollbacks on errors.
- **Repositories (`src/data/*_repository.py`)**: Encapsulate persistence logic, querying, and object mapping for entities like Customers, Accounts, and Complaints.

### Where SQL is Allowed and Prohibited
- **Allowed:** Exclusively inside designated repository files (`src/data/`). Repositories are the single source of truth for handling queries and raw database commands.
- **Prohibited:** Raw SQL statements are strictly prohibited inside business workflow logic, UI layers, API route handlers, or agent tool wrappers. All database interaction must flow through repository methods using **parameterized queries** to protect against SQL injection vulnerabilities.

### Example Call
```python
from src.data.database_manager import DatabaseManager
from src.data.customer_repository import CustomerRepository

db_manager = DatabaseManager()
customer_repo = CustomerRepository(db_manager)

# Fetch customer record safely
customer = customer_repo.get_by_id("CUST-12345")
print(customer)