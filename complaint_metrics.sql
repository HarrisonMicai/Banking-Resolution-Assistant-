-- Count of complaints by category, status, and month
SELECT 
	STRFTIME('%Y-%m', "received_at") AS month,
	"category",
	"status",
	COUNT(*) AS complaint_count
	FROM complaint
	GROUP BY month, "category", "status";

-- Count of distinct customers by category, status, and month
 SELECT 
    strftime('%Y-%m', "received_at") AS month,
    "category",
    "status",
    COUNT(DISTINCT "customer_id") AS distinct_customer_count
FROM 
    complaint
GROUP BY 
    month, "category", "status";

--Calculate closed-case duration by category: Resolution Query
SELECT c."category",
AVG(JULIANDAY(sr."closed_at") - JULIANDAY(c."received_at")) AS 
average_duration_days
FROM complaint c
JOIN service_request sr ON c."complaint_id" = sr."request_id"
WHERE c."status" = 'closed'
GROUP BY c."category";

	