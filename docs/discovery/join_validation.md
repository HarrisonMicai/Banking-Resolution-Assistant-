- **Before JOINS**

Use COUNT(\*) and COUNT(DISTINCT complaint_id).

- **SELECT** **COUNT**(\*) **AS** _total_complaints_,
- **COUNT**(**DISTINCT** complaint_id) **AS** distinct_complaints
- **FROM** complaint;
  - - This counts the total number of rows in the complaint table.
      - Total_complaints = 10
      - Distinct_complaints = 10
- **After JOINS**
  - **SELECT** **COUNT**(\*) **AS** _total_joined_rows_,
  - **COUNT**(**DISTINCT** complaint_id) **AS** distinct_joined_complaints
  - **FROM** complaint **AS** _c_
  - **INNER** **JOIN** customer **AS** _cu_
  - **ON** _c_.customer_id = _cu_.customer_id
  - **LEFT** **JOIN** account **AS** _a_ **ON** _c_.account_id = _a_.account_id;
    - **This counts the total number of rows after joining complaints and customers and accounts.**
    - **Distinct__joined_complaints = 10_**
    - **_Total_joined_rows = 10_**
- **One-to-Many Duplication**
  - **A single record in one table, such as a customer, is associated with multiple complaints, so when doing a join with these tables, each complaint that is joined with the customer table will have its corresponding customer associated.**
  - **There will be multiple rows for customers with multiple complaints, which create duplication in the result set of counting rows because the same customer information will appear multiple times for its complaints.**
  - **With 3 complaints for a customer it will result in 3 rows for the same customer, with different details for complaints but the same customer. This is the reason why the count of the totals rows after joining may exceed the count of distinct complaints in the complaint table.**
  - **Because the counts are equal for both we can assume that there are unique customers for each complaint, meaning that there are no multiple complaints for the same complaint_id.**