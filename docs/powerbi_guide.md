# Power BI dashboard build guide

Run `python -m src.pipeline` first. In Power BI Desktop, use **Get data > Text/CSV** to import:
- `data/sample_transactions.csv` for transactions
- `outputs/customer_segments.csv` for segment-level insights
- `outputs/cohort_retention.csv` for the cohort retention matrix (unpivot month-index columns in Power Query)
- `outputs/model_dataset.csv` for observed churn labels (demonstration only)

Create the calculated column `Revenue = sample_transactions[quantity] * sample_transactions[unit_price]` and measures:
```dax
Total Revenue = SUM(sample_transactions[Revenue])
Customers = DISTINCTCOUNT(sample_transactions[customer_id])
Orders = DISTINCTCOUNT(sample_transactions[transaction_id])
Average Order Value = DIVIDE([Total Revenue], [Orders])
```

Suggested pages:
1. **Executive overview**: KPI cards, monthly revenue line chart, revenue by customer.
2. **Customer segmentation**: segment count bar chart, monetary value by segment.
3. **Retention**: cohort-month rows, cohort-index columns, retention percentage conditional-format heatmap.
4. **Churn**: class balance and recency/frequency distributions split by observed churn.

Note: `model_dataset.csv` includes ground-truth churn labels, not out-of-sample predictions. Model evaluation is in `outputs/metrics.json`. This project does not include a `.pbix` file; create and save the report locally and commit screenshots or a sanitized PBIX if desired.
