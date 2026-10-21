- QUERIE
  - **SELECT** \*
  - **FROM** complaint
  - **WHERE** account_id **IS** **NULL**;
- RESULT
  - Because all the complaints have an account__id the result is rows that are empty for the complaints. This verifies that all the complaints have an account_id associated with them. to verify this i made this query to subtract the complaints and accounts to determine how many complaints are not associated with an account_id;_

| **SELECT**                                                              |
| ----------------------------------------------------------------------- |
| **COUNT**(\*) **AS** total_complaints,                                  |
| **COUNT**(account_id) **AS** complaints_with_account,                   |
| **COUNT**(\*) - **COUNT**(account_id) **AS** complaints_without_account |
| **FROM**                                                                |
| complaint;                                                              |