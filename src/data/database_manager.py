# src/data/database_manager.py
import os
import sqlite3
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment configuration
load_dotenv()

DB_NAME = os.getenv("DB_NAME", "BankCRS.db")

class DatabaseManager:
    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path

    def get_connection(self):
        """Creates and returns a new database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enables column access by name
        return conn

    @contextmanager
    def transaction(self):
        """Context manager to safely commit or rollback transactions."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()