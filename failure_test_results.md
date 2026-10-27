# Failure Test Results

## Test Case 1: Missing File Handling
* **Scenario:** Attempting to execute `complaint_analysis.py` when `complaints.csv` is absent from the directory path.
* **Observed Behavior:** The script successfully intercepted the `FileNotFoundError` check, printed a controlled error message to `stderr`, and exited gracefully with exit code `1`.
* **Evidence:** `Error: Required file 'complaints.csv' not found.`

## Test Case 2: Incomplete Rows / Missing Columns
* **Scenario:** Running the validation script on a CSV missing mandatory schema columns (e.g., missing `resolved_date`).
* **Observed Behavior:** The validation function identified the schema mismatch against the required columns contract and terminated execution safely with a descriptive error notification.
* **Evidence:** `Error: Missing required columns: ['resolved_date']`