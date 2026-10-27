# Database Integrity Report
Generated: 2026-10-27 19:16:00

## 1. Source vs. Inserted Record Counts
| Entity | Source Count | Inserted Count | Status |
| :--- | :--- | :--- | :--- |
| Customer | 100 | 100 | MATCH |
| Account | 250 | 250 | MATCH |
| Complaint | 150 | 150 | MATCH |
| Service Request | 80 | 80 | MATCH |

## 2. Integrity and Relationship Checks
* **Orphan Accounts (Accounts without valid Customer):** 0 (Expected: 0)
* **Complaint/Account Ownership Mismatches:** 0 (Expected: 0)

## Conclusion
Database integrity verification completed successfully. All constraints and ownership validations passed.