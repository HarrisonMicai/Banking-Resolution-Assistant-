class CustomerRepository:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_by_id(self, customer_id: str):
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            # Parameterized query
            cursor.execute(
                "SELECT * FROM customer WHERE customer_id = ?", 
                (customer_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None