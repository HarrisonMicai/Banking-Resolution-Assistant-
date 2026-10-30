class ComplaintRepository:
    def __init__(self, db_manager):
        self.db_manager = db_manager

    def get_by_id(self, complaint_id: str):
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM complaint WHERE complaint_id = ?", 
                (complaint_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None

    def get_for_customer(self, customer_id: str):
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM complaint WHERE customer_id = ?", 
                (customer_id,)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def create(self, complaint_data: dict):
        with self.db_manager.transaction() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO complaint (
                    complaint_id, customer_id, account_id, channel, 
                    category, complaint_text, priority, status, received_at, assigned_analyst_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    complaint_data.get("complaint_id"),
                    complaint_data.get("customer_id"),
                    complaint_data.get("account_id"),
                    complaint_data.get("channel"),
                    complaint_data.get("category"),
                    complaint_data.get("complaint_text"),
                    complaint_data.get("priority"),
                    complaint_data.get("status"),
                    complaint_data.get("received_at"),
                    complaint_data.get("assigned_analyst_id")
                )
            )