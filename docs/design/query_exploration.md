# Database Exploration Observations: Complaint Management System

## 1. Table Summary & Record Counts
An inspection of the database reveals 14 interconnected tables governing employees, customers, accounts, complaints, and policies:
- **employee**: 10 records
- **customer**: 10 records
- **account**: 10 records
- **complaint**: 10 records
- **complaint_status_history**: 10 records
- **transactions**: 10 records
- **fee**: 10 records
- **service_request**: 10 records
- **policy_document**: 10 records
- **policy_section**: 10 records
- **investigation**: 10 records
- **recommendation**: 10 records
- **review_request**: 10 records
- **review_decision**: 10 records
- **customer_response**: 10 records
- **audit_log**: 10 records

## 2. Data Types & Integrity Patterns
- **Primary & Foreign Keys**: Standardized across all tables using text-based identifiers (e.g., `CUS001`, `ACC001`, `CMP001`) with explicit relational integrity via `FOREIGN KEY` constraints.
- **Timestamps**: Most operational log tables utilize `DATETIME` format (e.g., `2025-01-01 09:00:00`), while structural tables like `account` and `policy_document` rely on `DATE`.
- **Financial Fields**: Balances, amounts, and fees are typed as `DECIMAL(15,2)` or `DECIMAL(10,2)` to prevent floating-point rounding errors.

## 3. Unexpected Data & Null Patterns
- **Nullable Foreign Keys in Complaints**: The `complaint` table allows `account_id` to be null conceptually, though all 10 sample records currently link to an active account.
- **Unassigned/Pending Investigations**: In the `investigation` table, records like `INV002`, `INV003`, etc., have `NULL` values for `completed_at`, indicating active or open workflows where closure dates are pending.
- **Fee Reversals**: The `fee` table uses an integer flag (`reversed_flag BOOLEAN DEFAULT 0`), initialized to `FALSE` (0) across all initial records.