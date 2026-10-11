import pandas as pd
import pytest
from src.pipeline import generate_transactions, validate_transactions, rfm_table, cohort_retention, make_churn_dataset, train_churn_model


def test_generator_reproducible():
    assert generate_transactions(20).equals(generate_transactions(20))


def test_validation_rejects_duplicate_ids():
    df = generate_transactions(10)
    df.loc[1, 'transaction_id'] = df.loc[0, 'transaction_id']
    with pytest.raises(ValueError):
        validate_transactions(df)


def test_rfm_and_cohort():
    df = validate_transactions(generate_transactions(60))
    rfm = rfm_table(df, '2025-07-01')
    assert rfm['recency_days'].ge(1).all()
    assert rfm['rfm_score'].between(3, 15).all()
    retention = cohort_retention(df)
    assert (retention[0] == 100).all()


def test_churn_features_do_not_include_future():
    df = validate_transactions(generate_transactions(100))
    dataset = make_churn_dataset(df, '2025-07-01')
    historical = rfm_table(df, '2025-07-01')
    pd.testing.assert_frame_equal(dataset[historical.columns], historical)
    assert dataset['churned'].isin([0, 1]).all()


def test_model_trains():
    df = validate_transactions(generate_transactions(300))
    dataset = make_churn_dataset(df, '2025-07-01')
    model, metrics = train_churn_model(dataset)
    assert 0 <= metrics['roc_auc'] <= 1
    assert len(model.predict(dataset[['recency_days','frequency','monetary']].head())) == 5
