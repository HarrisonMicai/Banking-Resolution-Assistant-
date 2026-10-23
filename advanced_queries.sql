--age bucket analysis
-- number of days it takes to solve complaint
-- find the age of every complaint

SELECT 
(JULIANDAY('now') - JULIANDAY("received_at")) /30 
FROM complaint;

--Use CASE for unresolved age buckets 0-7, 8-30 and 31+ days.
SELECT 
    age_bucket,
    COUNT(*) AS complaint_count
FROM (
    SELECT 
        CASE 
            WHEN (julianday('now') - julianday(received_at)) <= 7 THEN '0-7 days'
            WHEN (julianday('now') - julianday(received_at)) <= 30 THEN '8-30 days'
            ELSE '31+ days'
        END AS age_bucket
    FROM complaint
    WHERE status != 'RESOLVED'
) grouped_complaints
GROUP BY age_bucket
ORDER BY 
    CASE age_bucket
        WHEN '0-7 days' THEN 1
        WHEN '8-30 days' THEN 2
        ELSE 3
    END;

--Use a CTE to identify repeat complainants.
WITH complaint_counts AS (
    SELECT 
        "customer_id", 
        COUNT("complaint_id") AS complaint_count
    FROM 
        complaint
    GROUP BY 
        "customer_id"
)
SELECT 
    "customer_id", 
    "complaint_count"
FROM 
    complaint_counts
WHERE 
    "complaint_count" > 1;
