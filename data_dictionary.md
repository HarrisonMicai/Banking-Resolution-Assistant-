# **EMPLOYEE**

### **Purpose**

Stores bank employees involved in complaint handling, reviews, approvals, and investigations.

| **Column**  | **Type** | **Nullable** | **Key/Constraint** | **Source** | **Example**                                             |
| ----------- | -------- | ------------ | ------------------ | ---------- | ------------------------------------------------------- |
| employee_id | TEXT     | No           | Primary Key        | HR System  | EMP001                                                  |
| first_name  | TEXT     | No           | None               | HR System  | Sarah                                                   |
| last_name   | TEXT     | No           | None               | HR System  | Johnson                                                 |
| email       | TEXT     | Yes          | Unique             | HR System  | [sarah.johnson@bank.com](mailto:sarah.johnson@bank.com) |
| role        | TEXT     | No           | None               | HR System  | Analyst                                                 |

# **CUSTOMER**

### **Purpose**

Stores customer demographic and contact information.

| **Column**   | **Type** | **Nullable** | **Key/Constraint**        | **Source**       | **Example**                                               |
| ------------ | -------- | ------------ | ------------------------- | ---------------- | --------------------------------------------------------- |
| customer_id  | TEXT     | No           | Primary Key               | CRM              | CUST1001                                                  |
| first_name   | TEXT     | No           | None                      | CRM              | Michael                                                   |
| last_name    | TEXT     | No           | None                      | CRM              | Brown                                                     |
| email        | TEXT     | Yes          | Unique                    | CRM              | [michael.brown@email.com](mailto:michael.brown@email.com) |
| phone_number | TEXT     | Yes          | None                      | CRM              | 555-123-4567                                              |
| segment      | TEXT     | Yes          | None                      | CRM              | Premium                                                   |
| date_created | DATETIME | Yes          | Default CURRENT_TIMESTAMP | System Generated | 2026-10-20 09:15:00                                       |

# **ACCOUNT**

### **Purpose**

Stores customer banking account information.

| **Column**      | **Type**      | **Nullable** | **Key/Constraint**                 | **Source**   | **Example** |
| --------------- | ------------- | ------------ | ---------------------------------- | ------------ | ----------- |
| account_id      | TEXT          | No           | Primary Key                        | Core Banking | ACC1001     |
| customer_id     | TEXT          | No           | Foreign Key → customer.customer_id | Customer     | CUST1001    |
| account_number  | TEXT          | No           | Unique                             | Core Banking | 987654321   |
| account_type    | TEXT          | No           | None                               | Core Banking | Checking    |
| status          | TEXT          | No           | None                               | Core Banking | Active      |
| current_balance | DECIMAL(15,2) | Yes          | Default 0                          | Core Banking | 2540.75     |
| opened_date     | DATE          | No           | None                               | Core Banking | 2024-05-10  |

# **COMPLAINT**

### **Purpose**

Captures customer complaints submitted through any channel.

| **Column**          | **Type** | **Nullable** | **Key/Constraint**        | **Source**               | **Example**                |
| ------------------- | -------- | ------------ | ------------------------- | ------------------------ | -------------------------- |
| complaint_id        | TEXT     | No           | Primary Key               | Complaint Intake System  | CMP1001                    |
| customer_id         | TEXT     | No           | FK → customer.customer_id | Customer                 | CUST1001                   |
| account_id          | TEXT     | Yes          | FK → account.account_id   | Account                  | ACC1001                    |
| channel             | TEXT     | No           | None                      | Customer Submission      | Email                      |
| category            | TEXT     | No           | None                      | Complaint Classification | Fee Dispute                |
| complaint_text      | TEXT     | No           | None                      | Customer Submission      | Charged an unexpected fee. |
| priority            | TEXT     | Yes          | None                      | Complaint Engine         | High                       |
| status              | TEXT     | No           | None                      | Workflow System          | Open                       |
| received_at         | DATETIME | No           | None                      | Intake System            | 2026-10-20 10:00:00        |
| assigned_analyst_id | TEXT     | Yes          | FK → employee.employee_id | Complaint Assignment     | EMP001                     |

# **COMPLAINT_STATUS_HISTORY**

### **Purpose**

Tracks status changes throughout the complaint lifecycle.

| **Column**   | **Type** | **Nullable** | **Key/Constraint**          | **Source**         | **Example**              |
| ------------ | -------- | ------------ | --------------------------- | ------------------ | ------------------------ |
| history_id   | INTEGER  | No           | PK, Auto Increment          | System Generated   | 1                        |
| complaint_id | TEXT     | No           | FK → complaint.complaint_id | Complaint Workflow | CMP1001                  |
| old_status   | TEXT     | Yes          | None                        | Complaint Workflow | Open                     |
| new_status   | TEXT     | No           | None                        | Complaint Workflow | Under Review             |
| changed_by   | TEXT     | Yes          | FK → employee.employee_id   | Employee Action    | EMP001                   |
| changed_at   | DATETIME | Yes          | Default CURRENT_TIMESTAMP   | System Generated   | 2026-10-20 11:00:00      |
| comments     | TEXT     | Yes          | None                        | Employee Notes     | Initial review completed |

# **TRANSACTIONS**

### **Purpose**

Stores account transactions that may be related to complaints.

| **Column**       | **Type**      | **Nullable** | **Key/Constraint**      | **Source**   | **Example**         |
| ---------------- | ------------- | ------------ | ----------------------- | ------------ | ------------------- |
| transaction_id   | TEXT          | No           | Primary Key             | Core Banking | TXN50001            |
| account_id       | TEXT          | No           | FK → account.account_id | Account      | ACC1001             |
| transaction_type | TEXT          | No           | None                    | Core Banking | Withdrawal          |
| amount           | DECIMAL(15,2) | No           | None                    | Core Banking | 35.00               |
| processed_at     | DATETIME      | No           | None                    | Core Banking | 2026-10-18 12:35:00 |
| balance_before   | DECIMAL(15,2) | Yes          | None                    | Core Banking | 3000.00             |
| balance_after    | DECIMAL(15,2) | Yes          | None                    | Core Banking | 2965.00             |
| description      | TEXT          | Yes          | None                    | Core Banking | ATM Withdrawal Fee  |

# **FEE**

### **Purpose**

Records fees assessed against customer accounts.

| **Column**     | **Type**      | **Nullable** | **Key/Constraint**               | **Source**     | **Example**         |
| -------------- | ------------- | ------------ | -------------------------------- | -------------- | ------------------- |
| fee_id         | TEXT          | No           | Primary Key                      | Billing System | FEE10001            |
| account_id     | TEXT          | No           | FK → account.account_id          | Account        | ACC1001             |
| transaction_id | TEXT          | Yes          | FK → transactions.transaction_id | Transaction    | TXN50001            |
| fee_type       | TEXT          | No           | None                             | Billing System | Overdraft Fee       |
| amount         | DECIMAL(10,2) | No           | None                             | Billing System | 35.00               |
| charged_at     | DATETIME      | No           | None                             | Billing System | 2026-10-18 12:35:00 |
| reversed_flag  | INTEGER       | Yes          | Default 0                        | Billing System | 0                   |

# **SERVICE_REQUEST**

### **Purpose**

Tracks non-complaint customer service activities.

| **Column**   | **Type** | **Nullable** | **Key/Constraint**        | **Source**                | **Example**         |
| ------------ | -------- | ------------ | ------------------------- | ------------------------- | ------------------- |
| request_id   | TEXT     | No           | Primary Key               | Customer Service Platform | SR1001              |
| customer_id  | TEXT     | Yes          | FK → customer.customer_id | Customer                  | CUST1001            |
| account_id   | TEXT     | Yes          | FK → account.account_id   | Account                   | ACC1001             |
| request_type | TEXT     | Yes          | None                      | Customer Service          | Address Change      |
| status       | TEXT     | Yes          | None                      | Workflow                  | Closed              |
| created_at   | DATETIME | Yes          | None                      | Service Platform          | 2026-10-10 08:00:00 |
| closed_at    | DATETIME | Yes          | None                      | Service Platform          | 2026-10-10 09:00:00 |

# **POLICY_DOCUMENT**

### **Purpose**

Stores complaint-resolution and compliance policies.

| **Column**     | **Type** | **Nullable** | **Key/Constraint** | **Source**        | **Example**         |
| -------------- | -------- | ------------ | ------------------ | ----------------- | ------------------- |
| policy_id      | TEXT     | No           | Primary Key        | Governance System | POL001              |
| policy_name    | TEXT     | No           | None               | Compliance Team   | Fee Reversal Policy |
| version_number | TEXT     | Yes          | None               | Compliance Team   | v2.1                |
| effective_date | DATE     | Yes          | None               | Compliance Team   | 2026-01-01          |
| status         | TEXT     | Yes          | None               | Compliance Team   | Active              |

# **POLICY_SECTION**

### **Purpose**

Stores sections belonging to a policy document.

| **Column**    | **Type** | **Nullable** | **Key/Constraint**             | **Source**        | **Example**                              |
| ------------- | -------- | ------------ | ------------------------------ | ----------------- | ---------------------------------------- |
| section_id    | TEXT     | No           | Primary Key                    | Governance System | SEC001                                   |
| policy_id     | TEXT     | No           | FK → policy_document.policy_id | Policy Document   | POL001                                   |
| section_title | TEXT     | Yes          | None                           | Policy Author     | Fee Eligibility                          |
| section_text  | TEXT     | Yes          | None                           | Policy Author     | Customers may receive a fee refund if... |

# **INVESTIGATION**

### **Purpose**

Stores analyst investigations for complaints.

| **Column**            | **Type** | **Nullable** | **Key/Constraint**          | **Source**             | **Example**            |
| --------------------- | -------- | ------------ | --------------------------- | ---------------------- | ---------------------- |
| investigation_id      | TEXT     | No           | Primary Key                 | Investigation Workflow | INV1001                |
| complaint_id          | TEXT     | No           | FK → complaint.complaint_id | Complaint              | CMP1001                |
| analyst_id            | TEXT     | No           | FK → employee.employee_id   | Employee               | EMP001                 |
| started_at            | DATETIME | Yes          | None                        | Investigation Workflow | 2026-10-20 11:00:00    |
| completed_at          | DATETIME | Yes          | None                        | Investigation Workflow | 2026-10-21 14:00:00    |
| investigation_summary | TEXT     | Yes          | None                        | Analyst                | Fee assessed in error. |

# **RECOMMENDATION**

### **Purpose**

Stores AI or analyst-generated recommendations resulting from investigations.

| **Column**          | **Type**     | **Nullable** | **Key/Constraint**                  | **Source**         | **Example**                |
| ------------------- | ------------ | ------------ | ----------------------------------- | ------------------ | -------------------------- |
| recommendation_id   | TEXT         | No           | Primary Key                         | Decision Engine    | REC1001                    |
| investigation_id    | TEXT         | No           | FK → investigation.investigation_id | Investigation      | INV1001                    |
| recommendation_text | TEXT         | Yes          | None                                | AI Model / Analyst | Reverse fee and apologize. |
| confidence_score    | DECIMAL(5,2) | Yes          | None                                | AI Model           | 92.50                      |
| generated_at        | DATETIME     | Yes          | Default CURRENT_TIMESTAMP           | System Generated   | 2026-10-21 14:05:00        |

# **REVIEW_REQUEST**

### **Purpose**

Routes recommendations for managerial or compliance review.

| **Column**        | **Type** | **Nullable** | **Key/Constraint**                    | **Source**         | **Example**         |
| ----------------- | -------- | ------------ | ------------------------------------- | ------------------ | ------------------- |
| review_request_id | TEXT     | No           | Primary Key                           | Review Workflow    | REV1001             |
| complaint_id      | TEXT     | No           | FK → complaint.complaint_id           | Complaint          | CMP1001             |
| recommendation_id | TEXT     | No           | FK → recommendation.recommendation_id | Recommendation     | REC1001             |
| reviewer_id       | TEXT     | No           | FK → employee.employee_id             | Assignment Process | EMP010              |
| requested_at      | DATETIME | Yes          | Default CURRENT_TIMESTAMP             | System Generated   | 2026-10-21 14:10:00 |
| status            | TEXT     | Yes          | None                                  | Review Workflow    | Pending             |

# **REVIEW_DECISION**

### **Purpose**

Captures reviewer decisions for submitted recommendations.

| **Column**        | **Type** | **Nullable** | **Key/Constraint**                                    | **Source**       | **Example**               |
| ----------------- | -------- | ------------ | ----------------------------------------------------- | ---------------- | ------------------------- |
| decision_id       | TEXT     | No           | Primary Key                                           | Review Workflow  | DEC1001                   |
| review_request_id | TEXT     | No           | FK → review_request.review_request_id                 | Review Request   | REV1001                   |
| decision          | TEXT     | Yes          | CHECK(APPROVED, REJECTED, REQUEST_CHANGES, ESCALATED) | Reviewer         | APPROVED                  |
| decision_reason   | TEXT     | Yes          | None                                                  | Reviewer         | Evidence supports refund. |
| decision_date     | DATETIME | Yes          | Default CURRENT_TIMESTAMP                             | System Generated | 2026-10-21 15:00:00       |

# **CUSTOMER_RESPONSE**

### **Purpose**

Stores approved responses sent to customers.

| **Column**    | **Type** | **Nullable** | **Key/Constraint**          | **Source**             | **Example**                        |
| ------------- | -------- | ------------ | --------------------------- | ---------------------- | ---------------------------------- |
| response_id   | TEXT     | No           | Primary Key                 | Response Management    | RESP001                            |
| complaint_id  | TEXT     | No           | FK → complaint.complaint_id | Complaint              | CMP1001                            |
| response_text | TEXT     | No           | None                        | Analyst / AI Draft     | We have reversed the disputed fee. |
| approved_by   | TEXT     | Yes          | FK → employee.employee_id   | Reviewer               | EMP010                             |
| sent_date     | DATETIME | Yes          | None                        | Communication Platform | 2026-10-21 16:00:00                |

# **AUDIT_LOG**

### **Purpose**

Provides a complete audit trail of actions performed in the system for compliance and governance.

| **Column**      | **Type** | **Nullable** | **Key/Constraint**        | **Source**       | **Example**                        |
| --------------- | -------- | ------------ | ------------------------- | ---------------- | ---------------------------------- |
| audit_id        | INTEGER  | No           | PK, Auto Increment        | System Generated | 1                                  |
| entity_name     | TEXT     | No           | None                      | Audit Service    | COMPLAINT                          |
| entity_id       | TEXT     | No           | None                      | Audit Service    | CMP1001                            |
| action_type     | TEXT     | No           | None                      | Audit Service    | UPDATE                             |
| performed_by    | TEXT     | Yes          | FK → employee.employee_id | Employee/System  | EMP001                             |
| event_timestamp | DATETIME | Yes          | Default CURRENT_TIMESTAMP | System Generated | 2026-10-21 15:30:00                |
| details         | TEXT     | Yes          | None                      | Audit Service    | Status updated from Open to Closed |