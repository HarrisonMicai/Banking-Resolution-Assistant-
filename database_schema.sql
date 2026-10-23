use BankCRS
-- ==========================================
-- EMPLOYEE
-- ==========================================
CREATE TABLE employee (
    employee_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    role TEXT NOT NULL
);
-- ==========================================
-- CUSTOMER
-- ==========================================
CREATE TABLE customer (
    customer_id TEXT PRIMARY KEY,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    email TEXT UNIQUE,
    phone_number TEXT,
    segment TEXT,
    date_created DATETIME DEFAULT CURRENT_TIMESTAMP
);
-- ==========================================
-- ACCOUNT
-- ==========================================
CREATE TABLE account (
    account_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    account_number TEXT UNIQUE NOT NULL,
    account_type TEXT NOT NULL,
    status TEXT NOT NULL,
    current_balance DECIMAL(15,2) DEFAULT 0,
    opened_date DATE NOT NULL,
    FOREIGN KEY (customer_id)
        REFERENCES customer(customer_id)
);
-- ==========================================
-- COMPLAINT
-- ==========================================
CREATE TABLE complaint (
    complaint_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    account_id TEXT,
    channel TEXT NOT NULL,
    category TEXT NOT NULL,
    complaint_text TEXT NOT NULL,
    priority TEXT,
    status TEXT NOT NULL,
    received_at DATETIME NOT NULL,
    assigned_analyst_id TEXT,
    FOREIGN KEY (customer_id)
        REFERENCES customer(customer_id),
    FOREIGN KEY (account_id)
        REFERENCES account(account_id),
    FOREIGN KEY (assigned_analyst_id)
        REFERENCES employee(employee_id)
);
-- ==========================================
-- COMPLAINT STATUS HISTORY
-- ==========================================
CREATE TABLE complaint_status_history (
    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
    complaint_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    changed_by TEXT,
    changed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    comments TEXT,
    FOREIGN KEY (complaint_id)
        REFERENCES complaint(complaint_id),
    FOREIGN KEY (changed_by)
        REFERENCES employee(employee_id)
);
-- ==========================================
-- TRANSACTIONS
-- ==========================================
CREATE TABLE transactions (
    transaction_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    amount DECIMAL(15,2) NOT NULL,
    processed_at DATETIME NOT NULL,
    balance_before DECIMAL(15,2),
    balance_after DECIMAL(15,2),
    description TEXT,
    FOREIGN KEY (account_id)
        REFERENCES account(account_id)
);
-- ==========================================
-- FEE
-- ==========================================
CREATE TABLE fee (
    fee_id TEXT PRIMARY KEY,
    account_id TEXT NOT NULL,
    transaction_id TEXT,
    fee_type TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    charged_at DATETIME NOT NULL,
    reversed_flag INTEGER DEFAULT 0,
    FOREIGN KEY (account_id)
        REFERENCES account(account_id),
    FOREIGN KEY (transaction_id)
        REFERENCES transactions(transaction_id)
);
-- ==========================================
-- SERVICE REQUEST
-- ==========================================
CREATE TABLE service_request (
    request_id TEXT PRIMARY KEY,
    customer_id TEXT,
    account_id TEXT,
    request_type TEXT,
    status TEXT,
    created_at DATETIME,
    closed_at DATETIME,
    FOREIGN KEY (customer_id)
        REFERENCES customer(customer_id),
    FOREIGN KEY (account_id)
        REFERENCES account(account_id)
);
-- ==========================================
-- POLICY DOCUMENT
-- ==========================================
CREATE TABLE policy_document (
    policy_id TEXT PRIMARY KEY,
    policy_name TEXT NOT NULL,
    version_number TEXT,
    effective_date DATE,
    status TEXT
);
-- ==========================================
-- POLICY SECTION
-- ==========================================
CREATE TABLE policy_section (
    section_id TEXT PRIMARY KEY,
    policy_id TEXT NOT NULL,
    section_title TEXT,
    section_text TEXT,
    FOREIGN KEY (policy_id)
        REFERENCES policy_document(policy_id)
);
-- ==========================================
-- INVESTIGATION
-- ==========================================
CREATE TABLE investigation (
    investigation_id TEXT PRIMARY KEY,
    complaint_id TEXT NOT NULL,
    analyst_id TEXT NOT NULL,
    started_at DATETIME,
    completed_at DATETIME,
    investigation_summary TEXT,
    FOREIGN KEY (complaint_id)
        REFERENCES complaint(complaint_id),
    FOREIGN KEY (analyst_id)
        REFERENCES employee(employee_id)
);
-- ==========================================
-- RECOMMENDATION
-- ==========================================
CREATE TABLE recommendation (
    recommendation_id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL,
    recommendation_text TEXT,
    confidence_score DECIMAL(5,2),
    generated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (investigation_id)
        REFERENCES investigation(investigation_id)
);
-- ==========================================
-- REVIEW REQUEST
-- ==========================================
CREATE TABLE review_request (
    review_request_id TEXT PRIMARY KEY,
    complaint_id TEXT NOT NULL,
    recommendation_id TEXT NOT NULL,
    reviewer_id TEXT NOT NULL,
    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT,
    FOREIGN KEY (complaint_id)
        REFERENCES complaint(complaint_id),
    FOREIGN KEY (recommendation_id)
        REFERENCES recommendation(recommendation_id),
    FOREIGN KEY (reviewer_id)
        REFERENCES employee(employee_id)
);
-- ==========================================
-- REVIEW DECISION
-- ==========================================
CREATE TABLE review_decision (
    decision_id TEXT PRIMARY KEY,
    review_request_id TEXT NOT NULL,
    decision TEXT CHECK (
        decision IN (
            'APPROVED',
            'REJECTED',
            'REQUEST_CHANGES',
            'ESCALATED'
        )
    ),
    decision_reason TEXT,
    decision_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (review_request_id)
        REFERENCES review_request(review_request_id)
);
-- ==========================================
-- CUSTOMER RESPONSE
-- ==========================================
CREATE TABLE customer_response (
    response_id TEXT PRIMARY KEY,
    complaint_id TEXT NOT NULL,
    response_text TEXT NOT NULL,
    approved_by TEXT,
    sent_date DATETIME,
    FOREIGN KEY (complaint_id)
        REFERENCES complaint(complaint_id),
    FOREIGN KEY (approved_by)
        REFERENCES employee(employee_id)
);
-- ==========================================
-- AUDIT LOG
-- ==========================================
CREATE TABLE audit_log (
    audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_name TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    performed_by TEXT,
    event_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    details TEXT,
    FOREIGN KEY (performed_by)
        REFERENCES employee(employee_id)
);