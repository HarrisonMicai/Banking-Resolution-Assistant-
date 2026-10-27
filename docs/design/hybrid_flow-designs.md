# Hybrid Flow Designs (`hybrid_flow_designs.md`)

## Case 1: Customer Fee Dispute & Policy Check
* **Step 1 (Structured Query):** Query the `complaint`, `customer`, and `fee` tables using SQL to fetch the customer profile, fee amount, transaction date, and whether the fee was already reversed (`fee.reversed_flag`).
  * *Evidence returned:* Customer account ID, fee amount ($35.00), charge timestamp, and reversal status.
* **Step 2 (Document Retrieval):** Execute vector/text retrieval on the `policy_section` table to find sections governing overdraft fee waivers and dispute timeframes.
  * *Evidence returned:* Policy text stating fees can be waived once per 12 months for standard tier customers if reported within 30 days.
* **Step 3 (Synthesis):** Combine the structured fee record with the policy threshold to generate a draft recommendation stating whether a waiver is permissible.
  * *Evidence returned:* A synthesized draft recommendation with confidence score and source citations.
* **Step 4 (Human Approval Gate):** Route the recommendation to a Supervisor/Reviewer for final review.
  * *Human Approval:* **Required** under NG-1 and BR-4 before any fee reversal or account adjustment is executed.

## Case 2: Escalated Fraud & Disputed Card Transaction
* **Step 1 (Structured Query):** Query the `transactions` and `account` tables to retrieve transaction history, processing timestamp, and current balance before/after the disputed event.
  * *Evidence returned:* Transaction ID, amount, description, and balance delta.
* **Step 2 (Document Retrieval):** Retrieve card dispute handling and fraud escalation guidelines from `policy_document`.
  * *Evidence returned:* Specific escalation criteria and mandatory verification steps for fraudulent card activity.
* **Step 3 (Synthesis):** Collate transaction anomalies against fraud policy definitions to determine if mandatory escalation criteria (BR-6) are met.
  * *Evidence returned:* Automated flag for escalation and draft incident summary.
* **Step 4 (Human Approval Gate):** Route case to Fraud Specialist/Reviewer.
  * *Human Approval:* **Required** to confirm fraud status and authorize account lockdown or provisional credit.

## Case 3: Repeat Complainant with Special Service Level Agreement (SLA)
* **Step 1 (Structured Query):** Execute a CTE query across `complaint` and `customer` to identify repeat complaint counts and customer segment tiers (`customer.segment`).
  * *Evidence returned:* Total past complaints count (e.g., 3 complaints) and premium tier status.
* **Step 2 (Document Retrieval):** Retrieve VIP handling procedures and SLA commitment policies from the policy repository.
  * *Evidence returned:* Special handling rules requiring expedited review for premium segments.
* **Step 3 (Synthesis):** Merge historical complaint frequency with VIP service guidelines to generate an adjusted priority recommendation.
  * *Evidence returned:* Recommended priority upgrade (`HIGH`) and analyst briefing notes.
* **Step 4 (Human Approval Gate):** Present to Assigned Analyst for review and workflow adjustment.
  * *Human Approval:* **Required** to validate context and assign specialized handling resources.

## Case 4: Overdrawn Account Fee Waiver Review
* **Step 1 (Structured Query):** Extract account balance history, recent deposits, and overdraft fee logs from `transactions` and `fee`.
  * *Evidence returned:* Current balance (-$12.50) and sequence of consecutive overdraft fees.
* **Step 2 (Document Retrieval):** Retrieve hardship and fee-waiver discretionary guidelines from `policy_section`.
  * *Evidence returned:* Discretionary limits for customer service reps regarding hardship waivers.
* **Step 3 (Synthesis):** Synthesize account cash-flow trends with hardship policy parameters to draft a structured adjustment proposal.
  * *Evidence returned:* Proposal for partial fee reversal with supporting financial metrics.
* **Step 4 (Human Approval Gate):** Submit to Supervisor/Reviewer.
  * *Human Approval:* **Required** under banking governance controls for fee adjustments exceeding automated thresholds.

## Case 5: Complex Regulatory Disclosure Complaint
* **Step 1 (Structured Query):** Retrieve customer complaint text, submission channel, and account opening date from `complaint` and `account`.
  * *Evidence returned:* Complaint narrative regarding missing APR disclosure and account creation timestamp.
* **Step 2 (Document Retrieval):** Perform vector retrieval across regulatory compliance and Truth-in-Lending policy documents.
  * *Evidence returned:* Exact statutory disclosure requirements and compliance mandates applicable to the account type.
* **Step 3 (Synthesis):** Cross-reference customer complaint claims with operational audit logs and regulatory text to build an investigative timeline.
  * *Evidence returned:* Verified timeline of disclosures sent versus customer claims.
* **Step 4 (Human Approval Gate):** Escalate to Legal/Compliance Specialist Reviewer.
  * *Human Approval:* **Mandatory** due to regulatory exposure and legal risk boundaries.