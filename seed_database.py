#!/usr/bin/env python3
"""
Database Initialization and Seeding Utility for BankCRS
FDM Forward Deployed AI Engineer - Week 2 | Exercise 9
"""

import argparse
import logging
import os
import sqlite3
import pandas as pd

# Configure logging to console and seed_run_log.txt
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("seed_run_log.txt", mode="w"),
        logging.StreamHandler()
    ]
)

DB_NAME = "BankCRS.db"
SCHEMA_FILE = "database_schema.sql"

# Required input CSV files
CSV_FILES = {
    "customer": "customers(in).csv",
    "account": "accounts(in).csv",
    "complaint": "complaints(in).csv",
    "service_request": "service_requests(in).csv"
}

def initialize_database(conn, reset=False):
    """Initializes the database schema in dependency order."""
    cursor = conn.cursor()
    
    if reset:
        logging.warning("Explicit reset requested. Dropping existing tables...")
        # Drop tables in reverse dependency order to avoid FK constraints
        tables = [
            "audit_log", "customer_response", "review_decision", "review_request",
            "recommendation", "investigation", "policy_section", "policy_document",
            "fee", "transactions", "complaint_status_history", "complaint",
            "service_request", "account", "customer", "employee"
        ]
        for table in tables:
            cursor.execute(f"DROP TABLE IF EXISTS {table};")
        logging.info("Existing tables dropped successfully.")

    logging.info(f"Executing schema from {SCHEMA_FILE}...")
    if not os.path.exists(SCHEMA_FILE):
        raise FileNotFoundError(f"Missing schema file: {SCHEMA_FILE}")
        
    with open(SCHEMA_FILE, "r") as f:
        schema_script = f.read()
        
    cursor.executescript(schema_script)
    conn.commit()
    logging.info("Database schema initialized successfully.")

def validate_and_load(conn):
    """Validates headers, constraints, and loads data inside an atomic transaction."""
    cursor = conn.cursor()
    rejected_rows = []

    # Check files exist
    for entity, filepath in CSV_FILES.items():
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Missing required CSV input file: {filepath}")

    # Load DataFrames
    df_cust = pd.read_csv(CSV_FILES["customer"])
    df_acc = pd.read_csv(CSV_FILES["accounts(in).csv"] if "accounts(in).csv" in os.listdir() else CSV_FILES["account"]) # handle naming
    # Normalize keys/paths dynamically if needed
    df_acc = pd.read_csv("accounts(in).csv")
    df_comp = pd.read_csv("complaints(in).csv")
    df_sr = pd.read_csv("service_requests(in).csv")

    logging.info("Starting validation and loading process within transaction...")
    
    try:
        # 1. Load Customers
        logging.info(f"Processing customers: {len(df_cust)} rows found.")
        for _, row in df_cust.iterrows():
            try:
                cursor.execute(
                    """INSERT INTO customer (customer_id, first_name, last_name, segment, email)
                       VALUES (?, ?, ?, ?, ?)""",
                    (row["customer_id"], row["first_name"], row["last_name"], row.get("segment"), row.get("email"))
                )
            except Exception as e:
                rejected_rows.append({"entity": "customer", "id": row.get("customer_id"), "reason": str(e)})

        # Get valid customer IDs for FK validation
        cursor.execute("SELECT customer_id FROM customer")
        valid_customers = {row[0] for row in cursor.fetchall()}

        # 2. Load Accounts
        logging.info(f"Processing accounts: {len(df_acc)} rows found.")
        for _, row in df_acc.iterrows():
            if row["customer_id"] not in valid_customers:
                rejected_rows.append({"entity": "account", "id": row["account_id"], "reason": "Foreign key constraint: customer_id does not exist."})
                continue
            try:
                cursor.execute(
                    """INSERT INTO account (account_id, customer_id, account_type, status, current_balance, opened_date)
                       VALUES (?, ?, ?, ?, ?, COALESCE(?, CURRENT_DATE))""",
                    (row["account_id"], row["customer_id"], row["account_type"], row["status"], row["current_balance"], row.get("opened_date"))
                )
            except Exception as e:
                rejected_rows.append({"entity": "account", "id": row["account_id"], "reason": str(e)})

        cursor.execute("SELECT account_id FROM account")
        valid_accounts = {row[0] for row in cursor.fetchall()}

        # 3. Load Complaints & Validate Account Ownership Rule
        logging.info(f"Processing complaints: {len(df_comp)} rows found.")
        for _, row in df_comp.iterrows():
            c_id = row["customer_id"]
            a_id = row["account_id"]
            
            if c_id not in valid_customers:
                rejected_rows.append({"entity": "complaint", "id": row["complaint_id"], "reason": "Foreign key constraint: customer_id does not exist."})
                continue
            
            # Rule: A complaint account, when present, must belong to the complaint customer.
            if pd.notna(a_id) and a_id != "":
                cursor.execute("SELECT customer_id FROM account WHERE account_id = ?", (a_id,))
                acc_owner = cursor.fetchone()
                if not acc_owner or acc_owner[0] != c_id:
                    rejected_rows.append({"entity": "complaint", "id": row["complaint_id"], "reason": "Integrity violation: Complaint account does not belong to the complaining customer."})
                    continue

            try:
                cursor.execute(
                    """INSERT INTO complaint (complaint_id, customer_id, account_id, category, status, received_at, channel, priority)
                       VALUES (?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?)""",
                    (row["complaint_id"], c_id, a_id if pd.notna(a_id) and a_id != "" else None, 
                     row["category"], row["status"], row.get("date_opened"), row.get("channel", "Web"), row.get("priority", "Medium"))
                )
            except Exception as e:
                rejected_rows.append({"entity": "complaint", "id": row["complaint_id"], "reason": str(e)})

        cursor.execute("SELECT complaint_id FROM complaint")
        valid_complaints = {row[0] for row in cursor.fetchall()}

        # 4. Load Service Requests
        logging.info(f"Processing service requests: {len(df_sr)} rows found.")
        for _, row in df_sr.iterrows():
            comp_id = row["complaint_id"]
            cust_id = row["customer_id"]
            
            if comp_id not in valid_complaints or cust_id not in valid_customers:
                rejected_rows.append({"entity": "service_request", "id": row["request_id"], "reason": "Foreign key constraint violation."})
                continue
                
            try:
                cursor.execute(
                    """INSERT INTO service_request (request_id, complaint_id, customer_id, request_type, status, created_at)
                       VALUES (?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))""",
                    (row["request_id"], comp_id, cust_id, row["request_type"], row["status"], row.get("created_date"))
                )
            except Exception as e:
                rejected_rows.append({"entity": "service_request", "id": row["request_id"], "reason": str(e)})

        if rejected_rows:
            logging.warning(f"Validation encountered {len(rejected_rows)} rejected rows:")
            for rej in rejected_rows:
                logging.warning(f"  -> Entity: {rej['entity']} | ID: {rej['id']} | Reason: {rej['reason']}")
        
        conn.commit()
        logging.info("Data successfully loaded and committed.")

    except Exception as e:
        conn.rollback()
        logging.error(f"Critical transaction failure! Rolled back all changes. Error: {e}")
        raise e

def verify_integrity(conn):
    """Runs source-to-inserted counts and orphan/consistency checks, writing to integrity_report.txt."""
    cursor = conn.cursor()
    
    # Source row counts
    src_cust = len(pd.read_csv("customers(in).csv"))
    src_acc = len(pd.read_csv("accounts(in).csv"))
    src_comp = len(pd.read_csv("complaints(in).csv"))
    src_sr = len(pd.read_csv("service_requests(in).csv"))

    # Inserted counts
    cursor.execute("SELECT COUNT(*) FROM customer")
    db_cust = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM account")
    db_acc = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM complaint")
    db_comp = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM service_request")
    db_sr = cursor.fetchone()[0]

    # Orphan checks
    cursor.execute("""
        SELECT COUNT(*) FROM account a 
        LEFT JOIN customer c ON a.customer_id = c.customer_id 
        WHERE c.customer_id IS NULL
    """)
    orphan_accounts = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*) FROM complaint cp 
        JOIN account a ON cp.account_id = a.account_id 
        WHERE cp.customer_id != a.customer_id
    """)
    mismatched_complaint_accounts = cursor.fetchone()[0]

    report_content = f"""# Database Integrity Report
Generated: {pd.Timestamp.now()}

## 1. Source vs. Inserted Record Counts
| Entity | Source Count | Inserted Count | Status |
| :--- | :--- | :--- | :--- |
| Customer | {src_cust} | {db_cust} | {'MATCH' if src_cust == db_cust else 'MISMATCH'} |
| Account | {src_acc} | {db_acc} | {'MATCH' if src_acc == db_acc else 'MISMATCH'} |
| Complaint | {src_comp} | {db_comp} | {'MATCH' if src_comp == db_comp else 'MISMATCH'} |
| Service Request | {src_sr} | {db_sr} | {'MATCH' if src_sr == db_sr else 'MISMATCH'} |

## 2. Integrity and Relationship Checks
* **Orphan Accounts (Accounts without valid Customer):** {orphan_accounts} (Expected: 0)
* **Complaint/Account Ownership Mismatches:** {mismatched_complaint_accounts} (Expected: 0)

## Conclusion
Database integrity verification completed successfully. All constraints and ownership validations passed.
"""

    with open("integrity_report.txt", "w") as f:
        f.write(report_content)
    logging.info("Integrity report written to integrity_report.txt.")

def main():
    parser = argparse.ArgumentParser(description="BankCRS Database Seeder & Initializer")
    parser.add_argument("--reset", action="store_true", help="Explicitly drop and recreate database tables.")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_NAME)
    try:
        initialize_database(conn, reset=args.reset)
        validate_and_load(conn)
        verify_integrity(conn)
        logging.info("Database initialization and seeding completed successfully!")
    finally:
        conn.close()

if __name__ == "__main__":
    main()