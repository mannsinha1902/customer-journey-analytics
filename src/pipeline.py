"""Reproducible customer analytics and churn prediction demonstration."""
from pathlib import Path
import argparse
import json
import joblib
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, classification_report, confusion_matrix, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

COLUMNS = ['transaction_id', 'customer_id', 'transaction_date', 'quantity', 'unit_price']


def generate_transactions(n_customers=450, seed=42):
    """Generate fictional customer transactions with varied purchasing behavior."""
    rng = np.random.default_rng(seed)
    rows = []
    idx = 1
    origin = pd.Timestamp('2024-01-01')
    for cid in range(1, n_customers + 1):
        first_day = int(rng.integers(0, 240))
        propensity = float(rng.beta(2, 3))
        n_orders = int(1 + rng.poisson(2 + 14 * propensity))
        for _ in range(n_orders):
            day = min(729, first_day + int(rng.exponential(65 + 220 * propensity)))
            rows.append((f'T{idx:07d}', f'C{cid:05d}', origin + pd.Timedelta(days=day),
                         int(rng.integers(1, 5)), round(float(rng.lognormal(2.8, .6)), 2)))
            idx += 1
    return pd.DataFrame(rows, columns=COLUMNS).sort_values('transaction_date').reset_index(drop=True)


def validate_transactions(df):
    missing = set(COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f'Missing columns: {sorted(missing)}')
    df = df.copy()
    df['transaction_date'] = pd.to_datetime(df['transaction_date'], errors='raise')
    if df['transaction_id'].isna().any() or df['transaction_id'].duplicated().any():
        raise ValueError('Transaction IDs must be non-null and unique')
    if df['customer_id'].isna().any() or (df[['quantity', 'unit_price']].isna().any().any()):
        raise ValueError('Customer IDs, quantity and price must not be null')
    if (df['quantity'] <= 0).any() or (df['unit_price'] <= 0).any():
        raise ValueError('Quantity and unit price must be positive')
    df['revenue'] = df['quantity'] * df['unit_price']
    return df


def rfm_table(df, as_of):
    """Calculate RFM using purchases strictly before as_of."""
    history = df[df['transaction_date'] < pd.Timestamp(as_of)]
    if history.empty:
        raise ValueError('No transactions before as_of')
    rfm = history.groupby('customer_id').agg(
        last_purchase=('transaction_date', 'max'), frequency=('transaction_id', 'nunique'),
        monetary=('revenue', 'sum')).reset_index()
    rfm['recency_days'] = (pd.Timestamp(as_of) - rfm['last_purchase']).dt.days
    rfm['r_score'] = pd.qcut(rfm['recency_days'].rank(method='first'), 5, labels=[5,4,3,2,1]).astype(int)
    for col, score in [('frequency', 'f_score'), ('monetary', 'm_score')]:
        rfm[score] = pd.qcut(rfm[col].rank(method='first'), 5, labels=[1,2,3,4,5]).astype(int)
    rfm['rfm_score'] = rfm[['r_score', 'f_score', 'm_score']].sum(axis=1)
    rfm['segment'] = np.select(
        [(rfm['r_score'] >= 4) & (rfm['f_score'] >= 4),
         (rfm['r_score'] <= 2) & (rfm['f_score'] >= 3),
         rfm['rfm_score'] >= 10],
        ['Champions', 'At Risk', 'Loyal / Potential'], default='Needs Attention')
    return rfm


def cohort_retention(df):
    """Return month-indexed retention percentages for acquisition cohorts."""
    t = df[['customer_id', 'transaction_date']].copy()
    t['month'] = t['transaction_date'].dt.to_period('M')
    t['cohort'] = t.groupby('customer_id')['month'].transform('min')
    t['cohort_index'] = (t['month'].dt.year - t['cohort'].dt.year) * 12 + (t['month'].dt.month - t['cohort'].dt.month)
    counts = t.groupby(['cohort', 'cohort_index'])['customer_id'].nunique().unstack()
    retention = counts.div(counts[0], axis=0).mul(100)
    retention.index = retention.index.astype(str)
    return retention.round(2)


def make_churn_dataset(df, cutoff, horizon_days=90):
    """Define churn as zero purchases in (cutoff, cutoff + horizon_days].

    All features are calculated strictly before cutoff to prevent label leakage.
    """
    cutoff = pd.Timestamp(cutoff)
    end = cutoff + pd.Timedelta(days=horizon_days)
    if df['transaction_date'].max() < end:
        raise ValueError('Data must cover the entire future label window')
    features = rfm_table(df, cutoff)
    future = set(df.loc[(df['transaction_date'] >= cutoff) & (df['transaction_date'] < end), 'customer_id'])
    features['churned'] = (~features['customer_id'].isin(future)).astype(int)
    return features


def train_churn_model(dataset, seed=42):
    X = dataset[['recency_days', 'frequency', 'monetary']]
    y = dataset['churned']
    if y.nunique() != 2 or y.value_counts().min() < 2:
        raise ValueError('Need at least two samples of each churn class')
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=.25, random_state=seed, stratify=y)
    model = Pipeline([
        ('prep', ColumnTransformer([('num', Pipeline([
            ('imputer', SimpleImputer(strategy='median')),
            ('scale', StandardScaler())]), X.columns.tolist())])),
        ('classifier', LogisticRegression(max_iter=1000, class_weight='balanced', random_state=seed))])
    model.fit(X_train, y_train)
    probabilities = model.predict_proba(X_test)[:, 1]
    predictions = (probabilities >= .5).astype(int)
    metrics = {'roc_auc': float(roc_auc_score(y_test, probabilities)),
               'average_precision': float(average_precision_score(y_test, probabilities)),
               'confusion_matrix': confusion_matrix(y_test, predictions).tolist(),
               'classification_report': classification_report(y_test, predictions, output_dict=True, zero_division=0),
               'test_samples': int(len(y_test)), 'churn_rate_test': float(y_test.mean())}
    return model, metrics


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', type=Path, default=Path('data/sample_transactions.csv'))
    parser.add_argument('--output', type=Path, default=Path('outputs'))
    parser.add_argument('--cutoff', default='2025-07-01')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    df = validate_transactions(pd.read_csv(args.input))
    cohort_retention(df[df['transaction_date'] < pd.Timestamp(args.cutoff)]).to_csv(args.output / 'cohort_retention.csv')
    rfm = rfm_table(df, args.cutoff)
    rfm.to_csv(args.output / 'customer_segments.csv', index=False)
    dataset = make_churn_dataset(df, args.cutoff)
    model, metrics = train_churn_model(dataset)
    joblib.dump(model, args.output / 'churn_model.joblib')
    (args.output / 'metrics.json').write_text(json.dumps(metrics, indent=2), encoding='utf-8')
    dataset.to_csv(args.output / 'model_dataset.csv', index=False)
    fig, ax = plt.subplots(figsize=(8, 4))
    rfm['segment'].value_counts().plot.bar(ax=ax)
    ax.set(title='Customer segments (synthetic data)', ylabel='Customers', xlabel='Segment')
    fig.tight_layout()
    fig.savefig(args.output / 'segments.png', dpi=160)
    plt.close(fig)
    print(json.dumps({k:v for k,v in metrics.items() if k != 'classification_report'}, indent=2))
    print(f'Outputs saved to {args.output}')

if __name__ == '__main__':
    main()
