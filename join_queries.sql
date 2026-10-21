SELECT 
    c.complaint_id,
    c.customer_id,
    c.account_id,
    c.channel,
    c.category,
    c.complaint_text,
    c.priority,
    c.status,
    c.received_at,
    c.assigned_analyst_id, 
    cu.first_name,
    cu.last_name,
    cu.email,
    cu.phone_number,
    cu.segment,
    cu.date_created,
    a.account_number,
    a.account_type,
    a.current_balance,
    a.opened_date
FROM 
    complaint AS c
INNER JOIN 
    customer AS cu ON c.customer_id = cu.customer_id
LEFT JOIN 
    account AS a ON c.account_id = a.account_id;