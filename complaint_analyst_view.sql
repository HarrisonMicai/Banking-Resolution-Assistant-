CREATE VIEW complaint_anaylst_view AS 
SELECT
	complaint_id,
	customer_id,
	account_id,
	channel,
	category,
	complaint_text,
	priority,
	status,
	received_at,
	assigned_analyst_id
	FROM complaint;

 