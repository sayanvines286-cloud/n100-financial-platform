import sqlite3
from pathlib import Path
import pandas as pd

# Base project directory
BASE_DIR = Path(__file__).resolve().parents[2]

# Paths
PROCESSED_DATA_DIR = BASE_DIR / "Data" / "processed"
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "n100_financial.db"

TABLES = [
    "analysis",
    "balancesheet",
    "cashflow",
    "companies",
    "documents",
    "profitandloss",
    "prosandcons",

    "financial_ratios",
    "market_cap",
    "peer_groups",
    "sectors",
    "stock_prices",
]


def create_database():
    """
    Create SQLite database from processed CSV files.
    """

    conn = sqlite3.connect(DB_PATH)

    for table in TABLES:
        csv_path = PROCESSED_DATA_DIR / f"{table}.csv"

        print(f"Importing {table}...")

        df = pd.read_csv(csv_path)

        df.to_sql(
            table,
            conn,
            if_exists="replace",
            index=False
        )

        print(f"✓ Imported {table}")

    conn.close()

    print("\nDatabase created successfully!")
    print(f"Location: {DB_PATH}")


if __name__ == "__main__":
    create_database()