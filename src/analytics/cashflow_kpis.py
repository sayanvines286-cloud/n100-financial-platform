import pandas as pd
from pathlib import Path

# ==========================
# Paths
# ==========================
BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED = BASE_DIR / "Data" / "processed"
OUTPUT = BASE_DIR / "output"

OUTPUT.mkdir(exist_ok=True)

# ==========================
# Load Data
# ==========================

cashflow = pd.read_csv(PROCESSED / "cashflow.csv")
profit_loss = pd.read_csv(PROCESSED / "profitandloss.csv")

print("Datasets Loaded Successfully")

# Merge datasets
df = cashflow.merge(
    profit_loss[["company_id", "year", "net_profit"]],
    on=["company_id", "year"],
    how="left"
)

# ==========================
# KPI Calculations
# ==========================

df["Operating Cash Ratio"] = (
    df["operating_activity"] /
    df["net_profit"].replace(0, pd.NA)
)

df["Operating Cash Ratio"] = (
    pd.to_numeric(df["Operating Cash Ratio"], errors="coerce")
    .fillna(0)
    .round(2)
)
df["Investment Ratio"] = (
    df["investing_activity"] /
    df["operating_activity"].replace(0, pd.NA)
)

df["Investment Ratio"] = (
    pd.to_numeric(df["Investment Ratio"], errors="coerce")
    .fillna(0)
    .round(2)
)

df["Financing Ratio"] = (
    df["financing_activity"] /
    df["operating_activity"].replace(0, pd.NA)
)

df["Financing Ratio"] = (
    pd.to_numeric(df["Financing Ratio"], errors="coerce")
    .fillna(0)
    .round(2)
)

df["Free Cash Flow Indicator"] = (
    df["operating_activity"] -
    abs(df["investing_activity"])
)

# Cash Quality Score
df["Cash Quality Score"] = (
    df["Operating Cash Ratio"].fillna(0) * 40
    +
    (df["Free Cash Flow Indicator"] > 0).astype(int) * 60
)

# ==========================
# Ranking
# ==========================

df["Cashflow Rank"] = (
    df["Cash Quality Score"]
    .rank(ascending=False, method="dense")
    .astype(int)
)

# ==========================
# Output
# ==========================

result = df[
    [
        "company_id",
        "year",
        "Operating Cash Ratio",
        "Investment Ratio",
        "Financing Ratio",
        "Free Cash Flow Indicator",
        "Cash Quality Score",
        "Cashflow Rank",
    ]
]

result = result.sort_values(
    by="Cash Quality Score",
    ascending=False,
)

output_file = OUTPUT / "cashflow_kpis.csv"

result.to_csv(output_file, index=False)

print("\nCashflow KPI Analysis Completed!\n")

print(result.head(10))

print(f"\nSaved to:\n{output_file}")

if __name__ == "__main__":
    print("\nCashflow KPI Pipeline Completed Successfully!")