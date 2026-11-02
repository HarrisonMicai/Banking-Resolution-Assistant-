from contextlib import contextmanager
import psycopg2
from app.core.config import settings


@contextmanager
def get_db_connection():
    """Context manager to safely connect to the PostgreSQL database."""
    conn = psycopg2.connect(
        host=settings.db_host,
        port=settings.db_port,
        dbname=settings.db_name,
        user=settings.db_user,
        password=settings.db_password,
    )
    try:
        yield conn
    finally:
        conn.close()


def check_database_health() -> bool:
    """Verifies if the database is reachable and responsive."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
        return True
    except Exception:
        return False