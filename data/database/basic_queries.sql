-- =========================================================================
-- FDM FORWARD DEPLOYED AI ENGINEER - EXERCISE 2.1.2: BASIC QUERIES
-- =========================================================================

-- Q1: List all open complaints with high or critical priority
SELECT 
    complaint_id,
    customer_id,
    category,
    priority,
    status,
    received_at
FROM complaint
WHERE status = 'OPEN' 
  AND priority IN ('High', 'Critical')
ORDER BY received_at ASC;

-- Q2: Retrieve customer details for a specific segment (Parameterized)
-- Parameter: :customer_segment (e.g., 'Premier', 'Retail', 'Business')
SELECT 
    customer_id,
    first_name || ' ' || last_name AS full_name,
    email,
    phone_number,
    date_created
FROM customer
WHERE segment = :customer_segment
ORDER BY date_created DESC;

-- Q3: Count the number of complaints handled by each analyst
SELECT 
    e.employee_id,
    e.first_name || ' ' || e.last_name AS analyst_name,
    COUNT(c.complaint_id) AS total_complaints_handled
FROM employee e
LEFT JOIN complaint c ON e.employee_id = c.assigned_analyst_id
WHERE e.role = 'Analyst'
GROUP BY e.employee_id, analyst_name
ORDER BY total_complaints_handled DESC;

-- Q4: Find accounts with an active balance exceeding a threshold (Parameterized)
-- Parameter: :balance_threshold (e.g., 10000.00)
SELECT 
    account_id,
    customer_id,
    account_number,
    account_type,
    current_balance,
    opened_date
FROM account
WHERE status = 'ACTIVE' 
  AND current_balance > :balance_threshold
ORDER BY current_balance DESC;

-- Q5: Identify pending review requests awaiting evaluation
SELECT 
    rr.review_request_id,
    rr.complaint_id,
    rr.recommendation_id,
    e.first_name || ' ' || e.last_name AS reviewer_name,
    rr.requested_at,
    rr.status
FROM review_request rr
JOIN employee e ON rr.reviewer_id = e.employee_id
WHERE rr.status IN ('PENDING', 'UNDER_REVIEW')
ORDER BY rr.requested_at ASC;