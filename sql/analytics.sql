-- PostgreSQL schema and sample reporting queries.
-- Import data/sample_transactions.csv into transactions after creating this table.
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    transaction_date DATE NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price > 0)
);

-- Monthly revenue and unique purchasing customers.
SELECT DATE_TRUNC('month', transaction_date)::date AS month,
       COUNT(DISTINCT customer_id) AS active_customers,
       ROUND(SUM(quantity * unit_price), 2) AS revenue
FROM transactions
GROUP BY 1 ORDER BY 1;

-- Historical RFM snapshot; align cutoff with Python pipeline.
WITH history AS (
    SELECT * FROM transactions WHERE transaction_date < DATE '2025-07-01'
)
SELECT customer_id,
       DATE '2025-07-01' - MAX(transaction_date) AS recency_days,
       COUNT(DISTINCT transaction_id) AS frequency,
       ROUND(SUM(quantity * unit_price), 2) AS monetary
FROM history GROUP BY customer_id ORDER BY monetary DESC;

-- Cohort retention counts and percentage by month since acquisition.
WITH purchases AS (
    SELECT DISTINCT customer_id, DATE_TRUNC('month', transaction_date)::date AS purchase_month
    FROM transactions WHERE transaction_date < DATE '2025-07-01'
), cohorts AS (
    SELECT customer_id, MIN(purchase_month) AS cohort_month FROM purchases GROUP BY 1
), activity AS (
    SELECT c.cohort_month,
           (EXTRACT(YEAR FROM AGE(p.purchase_month, c.cohort_month)) * 12
            + EXTRACT(MONTH FROM AGE(p.purchase_month, c.cohort_month)))::int AS month_index,
           COUNT(DISTINCT p.customer_id) AS active_customers
    FROM purchases p JOIN cohorts c USING (customer_id) GROUP BY 1,2
)
SELECT cohort_month, month_index, active_customers,
       ROUND(100.0 * active_customers /
           MAX(CASE WHEN month_index = 0 THEN active_customers END)
           OVER (PARTITION BY cohort_month), 2) AS retention_pct
FROM activity ORDER BY cohort_month, month_index;
