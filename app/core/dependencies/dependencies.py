from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import connection


def check_database_health() -> bool:
    """Check that the API's configured SQLAlchemy database is reachable."""
    try:
        with connection.engine.connect() as db_connection:
            db_connection.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError:
        return False
