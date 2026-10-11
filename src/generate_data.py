"""Generate a reproducible fictional dataset; no real customer records."""
from pathlib import Path
from src.pipeline import generate_transactions

if __name__ == '__main__':
    path = Path('data/sample_transactions.csv')
    path.parent.mkdir(exist_ok=True)
    generate_transactions().to_csv(path, index=False, date_format='%Y-%m-%d')
    print(f'Created {path}')
