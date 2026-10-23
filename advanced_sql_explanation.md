# **Query Documentation: Repeat Complainants with Escalated Complaints**

## **Purpose**

Identify customers who have submitted multiple complaints and highlight any complaints that have been escalated. This helps analysts prioritize high-risk or repeat complainants and identify customers requiring additional investigation or intervention.

# **Boundaries**

### **Data Scope**

The query operates on the complaint table.

Fields used:

- complaint_id
- customer_id
- status

The query analyzes complaint activity at the customer level and identifies escalated complaints.

### **Time Scope**

No time restriction is applied.

All complaint records in the database are included regardless of:

- Submission date
- Resolution date
- Status change date

If business requirements require a specific analysis period, a filter can be added:

WHERE received_at >= '2026-01-01'

### **Business Rules**

- A repeat complainant is a customer with more than one complaint.
- An escalated complaint is a complaint with:

status = 'ESCALATED'

# **Partitions**

### **Customer Partition**

Data is grouped by:

customer_id

This partition enables calculation of:

- Complaint counts per customer
- Repeat complainants

### **Status Partition**

Complaint status is used to isolate escalated complaints:

status = 'ESCALATED'

This partition identifies customers whose complaints require higher-level review.

# **Expected Grain**

### **Source Grain**

The source table (complaint) is stored at:

One row per complaint.

### **Output Grain**

The output is stored at:

One row per customer.

Each row represents a unique customer and summarizes complaint activity.

# **Output Structure**

| **Column**             | **Description**                              |
| ---------------------- | -------------------------------------------- |
| customer_id            | Unique customer identifier                   |
| complaint_count        | Total complaints submitted by customer       |
| escalated_complaint_id | Complaint ID of escalated complaint (if any) |

### **Example Output**

| **customer_id** | **complaint_count** | **escalated_complaint_id** |
| --------------- | ------------------- | -------------------------- |
| CUST001         | 3                   | COMP002                    |
| CUST002         | 2                   | COMP005                    |
| CUST003         | 5                   | NULL                       |
| CUST004         | 4                   | COMP007                    |

# **Representative SQL**

WITH ComplaintCounts AS (

SELECT

customer_id,

COUNT(_) AS complaint_count_

_FROM complaint_

_GROUP BY customer_id_

_HAVING COUNT(_) > 1

)

SELECT

cc.customer_id,

cc.complaint_count,

c.complaint_id AS escalated_complaint_id

FROM ComplaintCounts cc

LEFT JOIN complaint c

ON cc.customer_id = c.customer_id

AND c.status = 'ESCALATED'

ORDER BY cc.complaint_count DESC;

\`

# **Validation**

## **Data Integrity Validation**

Verify that all complaints reference valid customers:

SELECT \*

FROM complaint c

LEFT JOIN customer cu

ON c.customer_id = cu.customer_id

WHERE cu.customer_id IS NULL;

Expected result:

0 rows

## **Complaint Count Validation**

Validate counts manually for sample customers:

SELECT

customer_id,

COUNT(\*)

FROM complaint

GROUP BY customer_id;

Compare totals against the query output.

## **Escalation Validation**

Verify escalated complaints:

SELECT

complaint_id,

customer_id,

status

FROM complaint

WHERE status = 'ESCALATED';

Confirm these complaint IDs appear in the result set.

## **Duplicate Check**

Ensure customers appear only once in the summary output:

SELECT

customer_id,

COUNT(_)_

_FROM (_

_&lt;query&gt;_

_)_

_GROUP BY customer_id_

_HAVING COUNT(_) > 1;

Expected result:

0 rows

## **Performance Considerations**

Recommended indexes:

CREATE INDEX idx_complaint_customer

ON complaint(customer_id);

CREATE INDEX idx_complaint_status

ON complaint(status);

CREATE INDEX idx_complaint_customer_status

ON complaint(customer_id, status);

Benefits:

- Faster aggregation by customer
- Faster escalation filtering
- Improved performance as complaint volume grows

# **Success Criteria**

The query is considered successful when:

- Only customers with more than one complaint are returned.
- Complaint counts match source data.
- Escalated complaints are correctly identified.
- No orphaned customer references exist.
- Query executes within acceptable performance thresholds.

This documentation provides the **boundaries, partitions, grain, representative results, and validation evidence** expected in an advanced SQL solution design document.