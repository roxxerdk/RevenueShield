"""Database initial seeder for RevenueShield.

Reads raw transaction data (without modifying raw CSVs) and populates the SQLite database
with initial evaluated recovery cases so the dashboard and API have rich initial data.
"""
from pathlib import Path
import pandas as pd
from database import init_db, get_db_session
from models.db_models import RecoveryCase
from recovery_workflow import recovery_workflow
from config import settings

def seed_database(limit: int = 60) -> int:
    """Seed the database with sample failed transactions from raw data."""
    init_db()

    with get_db_session() as session:
        existing_count = session.query(RecoveryCase).count()
        if existing_count > 0:
            print(f"Database already contains {existing_count} recovery cases. Skipping seed.")
            return existing_count

    csv_path = settings.resolved_data_dir / "raw" / "transactions.csv"
    if not csv_path.exists():
        print(f"Transactions CSV not found at {csv_path}")
        return 0

    print(f"Loading raw transactions from {csv_path}...")
    df = pd.read_csv(csv_path)

    # Filter failed transactions for recovery evaluation
    failed_df = df[df["status"].isin(["failed", "subscription_failed", "abandoned"])].head(limit)
    print(f"Seeding {len(failed_df)} failed transactions into RevenueShield...")

    count = 0
    for _, row in failed_df.iterrows():
        txn = row.to_dict()
        # Clean nan values
        for k, v in list(txn.items()):
            if pd.isna(v):
                txn[k] = None

        try:
            recovery_workflow.run(txn)
            count += 1
        except Exception as e:
            print(f"Error seeding transaction {txn.get('transaction_id')}: {e}")

    print(f"Successfully seeded {count} transactions into RevenueShield SQLite database.")
    return count

if __name__ == "__main__":
    seed_database()
