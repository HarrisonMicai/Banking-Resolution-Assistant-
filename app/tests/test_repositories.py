# tests/test_repositories.py
import pytest
import sqlite3
from app.core.database_manager import DatabaseManager
from app.repositories.customer_repository import CustomerRepository
from app.repositories.complaint_repository import ComplaintRepository

@pytest.fixture
def db_manager(tmp_path):
    # Setup an isolated test database
    db_file = tmp_path / "test_bank.db"
    manager = DatabaseManager(db_path=str(db_file))
    
    # Initialize basic schema for testing
    with manager.get_connection() as conn:
        conn.execute("""
        CREATE TABLE customer (
            customer_id TEXT PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            email TEXT UNIQUE,
            phone_number TEXT,
            segment TEXT,
            date_created DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.execute("""
        CREATE TABLE complaint (
            complaint_id TEXT PRIMARY KEY,
            customer_id TEXT NOT NULL,
            account_id TEXT,
            channel TEXT NOT NULL,
            category TEXT NOT NULL,
            complaint_text TEXT NOT NULL,
            priority TEXT,
            status TEXT NOT NULL,
            received_at DATETIME NOT NULL,
            assigned_analyst_id TEXT
        );
        """)
        conn.commit()
    return manager

def test_customer_get_by_id_valid(db_manager):
    with db_manager.get_connection() as conn:
        conn.execute(
            "INSERT INTO customer (customer_id, first_name, last_name, email) VALUES (?, ?, ?, ?)",
            ("CUST-001", "Jane", "Doe", "jane.doe@example.com")
        )
        conn.commit()

    repo = CustomerRepository(db_manager)
    customer = repo.get_by_id("CUST-001")
    
    assert customer is not None
    assert customer["first_name"] == "Jane"

def test_customer_get_by_id_missing(db_manager):
    repo = CustomerRepository(db_manager)
    customer = repo.get_by_id("NON-EXISTENT")
    assert customer is None

def test_complaint_creation_failure_rollback(db_manager):
    repo = ComplaintRepository(db_manager)
    bad_data = {
        "complaint_id": "COMP-001",
        # Missing required 'customer_id' to intentionally trigger constraint/failure
    }
    
    with pytest.raises(Exception):
        repo.create(bad_data)

    # Verify nothing was committed to the database due to rollback
    assert repo.get_by_id("COMP-001") is None