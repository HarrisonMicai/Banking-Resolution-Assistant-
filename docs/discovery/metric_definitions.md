### **Numerator**

The **numerator** represents the number of records that meet the metric criteria.

For the closed-case duration metric:

- **Closed Cases Count** = Number of complaints that reached a status of **'CLOSED'** or **'RESOLVED'**.
- When calculating average resolution time, the numerator is the **total resolution days** across all closed complaints.

Example:

Complaint A = 5 days

Complaint B = 8 days

Complaint C = 7 days

Numerator = 5 + 8 + 7 = 20 resolution days

### **Denominator**

The **denominator** is the total number of records included in the calculation.

For average resolution time:

Average Resolution Days =

Total Resolution Days ÷ Number of Closed Cases

Using the example above:

Average Resolution Days =

20 ÷ 3 = 6.67 days

- Denominator = Count of complaints with a status of **'CLOSED'** or **'RESOLVED'**
- Cases that remain open or unresolved are not included in the denominator.

### **Filters**

The metric applies the following filters:

#### **1\. Status Filter**

Only complaints with a final status of:

'CLOSED'

'RESOLVED'

are included.

WHERE h.new_status IN ('CLOSED', 'RESOLVED')

Purpose:

- Excludes active complaints.
- Ensures resolution time is calculated only for completed cases.

#### **2\. Category Filter**

Results are grouped by complaint category:

GROUP BY c.category

Examples:

- Billing
- Service Quality
- Fraud
- Account Access

Purpose:

- Allows comparison of resolution performance across categories.

#### **3\. Date Calculation Filter**

Resolution duration is calculated using:

julianday(resolved_at) - julianday(received_at)

Where:

- received_at = complaint submission date
- resolved_at = first date the complaint reached CLOSED or RESOLVED

Purpose:

- Measures elapsed time from complaint receipt to resolution.

### **Limitations**

#### **1\. Data Quality**

Metrics depend entirely on accurate data.

Potential issues:

- Missing complaint records
- Missing status history records
- Incorrect timestamps
- Duplicate status updates

Any of these can distort resolution calculations.

#### **2\. Resolution Status Assumptions**

The calculation assumes:

CLOSED

RESOLVED

represent completed cases.

If the organization also uses statuses such as:

COMPLETED

FINALIZED

SETTLED

those complaints would be excluded unless added to the query.

#### **3\. Timestamp Accuracy**

Resolution duration depends on:

- received_at
- changed_at

If timestamps are inconsistent or recorded in different time zones, resolution times may be inaccurate.

#### **4\. Multiple Resolution Events**

A complaint could move through statuses such as:

OPEN

IN_PROGRESS

RESOLVED

REOPENED

RESOLVED

The query uses:

MIN(h.changed_at)

which returns the first resolution date.

This may understate the true time required if cases are reopened.

#### **5\. No Date Range Restriction**

The query includes all available historical data.

Without additional filters such as:

WHERE received_at >= '2025-01-01'

results may not reflect recent operational performance.

### **Unresolved Cases**

**Unresolved cases** are complaints that have not reached a status of:

CLOSED

RESOLVED

Examples:

OPEN

NEW

PENDING

IN_PROGRESS

ESCALATED

These complaints are excluded because:

- No resolution date exists.
- Resolution duration cannot be calculated.

Including unresolved cases would produce inaccurate averages because the end date is unknown.

### **Distinct Counts**

A **distinct count** measures unique values rather than total records.

Example:

| **Customer** | **Complaints** |
| ------------ | -------------- |
| C001         | 3              |
| C002         | 2              |
| C003         | 1              |

Total complaints:

6

Distinct customers:

COUNT(DISTINCT customer_id)

Result:

3

### **Considerations for Distinct Counts**

#### **Multiple Complaints by One Customer**

If a customer submits several complaints:

Customer C001:

\- Complaint 1

\- Complaint 2

\- Complaint 3

The customer is counted only once in a distinct customer count.

This means:

- Complaint volume may be high.
- Distinct customer count may remain low.

#### **Customers Across Multiple Categories**

Example:

Customer C001:

\- Billing Complaint

\- Fraud Complaint

When grouped by category:

| **Category** | **Distinct Customers** |
| ------------ | ---------------------- |
| Billing      | 1                      |
| Fraud        | 1                      |

The same customer appears in multiple categories, so category totals should not be summed to estimate the overall number of unique customers.

### **Summary**

- **Numerator:** Total closed complaints or total resolution days.
- **Denominator:** Number of complaints closed/resolved.
- **Filters:** Status (CLOSED, RESOLVED), category grouping, and resolution-date calculation.
- **Limitations:** Data quality, status definitions, timestamp accuracy, reopened complaints, and lack of date filtering.
- **Unresolved Cases:** Excluded because no resolution date exists.
- **Distinct Counts:** Count unique customers rather than total complaints and may differ significantly from complaint volume.