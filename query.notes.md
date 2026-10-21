# Query Notes & Technical Choices

## 1. Filter Choice (Q1 & Q4)
- **Choice**: In Query 1, status filtering is combined with an inclusion list using `IN ('High', 'Critical')` for priority handling. In Query 4, `status = 'ACTIVE'` filters out closed or dormant accounts before applying the numerical threshold (`current_balance > :balance_threshold`).
- **Rationale**: Explicitly filtering states at the row level reduces dataset size early in execution, ensuring downstream sorting and aggregations operate only on relevant operational data.

## 2. Date Condition Choice (Q1)
- **Choice**: Timestamps are compared using standard ISO-8601 string literals (`'2025-01-01 09:00:00'`) and sorted via `ORDER BY received_at ASC`.
- **Rationale**: SQLite and most modern SQL engines store standard text datetimes in a format that sorts chronologically correct out-of-the-box, ensuring strict SLA FIFO (First-In, First-Out) review prioritization for customer support teams.

## 3. Null-Handling Choice (Q3)
- **Choice**: A `LEFT JOIN` was chosen between `employee` and `complaint` alongside a count aggregation (`COUNT(c.complaint_id)`). 
- **Rationale**: An `INNER JOIN` would inadvertently omit analysts who have zero complaints assigned. Using a `LEFT JOIN` ensures that all active analysts appear in the operational workload report, registering a count of `0` rather than disappearing from audit records.

## 4. Dialect-Specific Syntax Notes
- **String Concatenation**: Utilizes SQLite string concatenation operator (`||`) to combine `first_name` and `last_name` into a single `full_name` column (e.g., `e.first_name || ' ' || e.last_name`).
- **Parameters**: Named placeholders (`:customer_segment`, `:balance_threshold`) are designated to align with safe parameterized execution guidelines, preventing SQL injection vulnerabilities when integrated into future Python/API pipelines.