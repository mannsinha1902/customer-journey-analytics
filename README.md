# Customer Journey Analytics & Churn Prediction

An end-to-end **portfolio demonstration** using synthetic e-commerce transactions to explore customer behavior, monthly retention, RFM segmentation, and churn prediction. Inspired by prior customer analytics project work; **no employer or customer data is included**.

## Business questions
- Which customer groups drive revenue and repeat purchasing?
- How does retention vary by acquisition cohort?
- Which previously active customers are unlikely to purchase in the next 90 days?

## Stack
Python, pandas, NumPy, scikit-learn, Matplotlib, PostgreSQL SQL, Power BI (dashboard guide), pytest, GitHub Actions.

## Quick start
Requires Python 3.10+; run commands from repository root.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
python -m src.generate_data
python -m src.pipeline
python -m pytest -q
```

The synthetic CSV is already included, so data generation is optional. Pipeline outputs go to `outputs/` (ignored by Git): `customer_segments.csv`, `cohort_retention.csv`, `model_dataset.csv`, `metrics.json`, `churn_model.joblib`, and `segments.png`.

## Analytical methodology
- **Revenue:** quantity × unit price; one transaction ID represents one order.
- **RFM:** features computed using transactions strictly before **2025-07-01**. Recency = days since last purchase, frequency = distinct orders, monetary = cumulative revenue. Quantile ranks form customer segments.
- **Cohorts:** first purchase month defines acquisition cohort; retention is the fraction of cohort customers purchasing in each subsequent calendar month. Recent cohort months have incomplete observation windows.
- **Churn label:** for customers with history before **2025-07-01**, `churned=1` means **no purchase in the following 90 days**. This is an operational proxy for inactivity, not a confirmed account cancellation. Features never use future purchases.
- **Model:** stratified 75/25 random train/test split, standardized RFM features, class-weighted logistic regression; report ROC AUC, average precision, confusion matrix, and classification metrics. Synthetic data results do not establish real-world performance.

### Important limitations
The dataset is simulated, not representative of a real retailer. The random split can be optimistic for forecasting future periods. A production evaluation should use multiple historical cutoffs, temporal validation, realistic cohort maturity, calibration, drift monitoring, and business-specific intervention costs. This demo uses one cutoff and does not claim production readiness.

## Repository structure
```
data/                 synthetic sample transactions
src/                  generation, validation, RFM, cohorts, churn model
sql/                  PostgreSQL DDL and analytical queries
tests/                automated unit/integration checks
docs/                 Power BI guide and GitHub publishing guide
.github/workflows/    CI tests
```

## Power BI
Follow [`docs/powerbi_guide.md`](docs/powerbi_guide.md). No `.pbix` is bundled; the guide describes how to build the dashboard from exported CSVs.

## Publish
See [`docs/publish_to_github.md`](docs/publish_to_github.md).

## Privacy and attribution
All transaction records are fictional and generated with a fixed random seed. Do not upload employer code, client data, secrets, or proprietary dashboards.

## License
MIT — see `LICENSE`.
