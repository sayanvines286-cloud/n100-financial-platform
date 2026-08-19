import pandas as pd
from pathlib import Path

# -----------------------------
# Project Paths
# -----------------------------
BASE_DIR = Path(__file__).resolve().parents[2]

PROCESSED = BASE_DIR / "Data" / "processed"
OUTPUT = BASE_DIR / "output"

OUTPUT.mkdir(exist_ok=True)

# -----------------------------
# Load Processed CSVs
# -----------------------------
profit_loss = pd.read_csv(PROCESSED / "profitandloss.csv")
balance_sheet = pd.read_csv(PROCESSED / "balancesheet.csv")
cashflow = pd.read_csv(PROCESSED / "cashflow.csv")

print("Datasets Loaded Successfully")

# -----------------------------
# Merge Datasets
# -----------------------------
df = profit_loss.merge(
    balance_sheet,
    on=["company_id", "year"],
    how="inner",
    suffixes=("_pl", "_bs")
)

df = df.merge(
    cashflow,
    on=["company_id", "year"],
    how="left"
)

print(f"Merged Shape : {df.shape}")

# -----------------------------
# Clean Missing Values
# -----------------------------
numeric_cols = df.select_dtypes(include="number").columns

df[numeric_cols] = df[numeric_cols].fillna(0)

# Avoid divide-by-zero
df.replace([float("inf"), float("-inf")], 0, inplace=True)

print("Data Cleaned")

# -----------------------------
# Ratio Functions
# -----------------------------
def safe_divide(a, b):
    if b == 0:
        return 0
    return a / b


def percentage(x):
    return round(x * 100, 2)
# =====================================================
# Financial Ratio Calculations
# =====================================================

print("\nCalculating Financial Ratios...")

# -----------------------------
# Profitability Ratios
# -----------------------------

df["net_profit_margin"] = (
    df.apply(
        lambda x: percentage(
            safe_divide(x["net_profit"], x["sales"])
        ),
        axis=1,
    )
)

df["operating_profit_margin"] = (
    df.apply(
        lambda x: percentage(
            safe_divide(x["operating_profit"], x["sales"])
        ),
        axis=1,
    )
)

# -----------------------------
# Return on Equity
# -----------------------------

df["roe"] = (
    df.apply(
        lambda x: percentage(
            safe_divide(
                x["net_profit"],
                x["equity_capital"] + x["reserves"]
            )
        ),
        axis=1,
    )
)

# -----------------------------
# Debt to Equity
# -----------------------------

df["debt_to_equity"] = (
    df.apply(
        lambda x: round(
            safe_divide(
                x["borrowings"],
                x["equity_capital"] + x["reserves"]
            ),
            2,
        ),
        axis=1,
    )
)

# -----------------------------
# Asset Turnover
# -----------------------------

df["asset_turnover"] = (
    df.apply(
        lambda x: round(
            safe_divide(
                x["sales"],
                x["total_assets"]
            ),
            2,
        ),
        axis=1,
    )
)

# -----------------------------
# Interest Coverage Ratio
# -----------------------------

df["interest_coverage"] = (
    df.apply(
        lambda x: round(
            safe_divide(
                x["operating_profit"],
                x["interest"]
            ),
            2,
        ),
        axis=1,
    )
)

# -----------------------------
# Cash Flow to Profit Ratio
# -----------------------------

df["cashflow_to_profit"] = (
    df.apply(
        lambda x: round(
            safe_divide(
                x["operating_activity"],
                x["net_profit"]
            ),
            2,
        ),
        axis=1,
    )
)

print("Financial Ratios Calculated Successfully")
# =====================================================
# Financial Health Score
# =====================================================

print("\nCalculating Financial Health Score...")

df["financial_health_score"] = (
    (df["roe"] * 0.30)
    + (df["net_profit_margin"] * 0.25)
    + (df["operating_profit_margin"] * 0.20)
    + (df["asset_turnover"] * 15)
    - (df["debt_to_equity"] * 5)
)

# Round score
df["financial_health_score"] = df["financial_health_score"].round(2)

# =====================================================
# Company Ranking
# =====================================================

df["company_rank"] = (
    df["financial_health_score"]
    .rank(ascending=False, method="dense")
    .astype(int)
)

# =====================================================
# Select Final Columns
# =====================================================

final_df = df[
    [
        "company_id",
        "year",
        "sales",
        "net_profit",
        "operating_profit",
        "equity_capital",
        "borrowings",
        "total_assets",
        "operating_activity",
        "net_profit_margin",
        "operating_profit_margin",
        "roe",
        "debt_to_equity",
        "asset_turnover",
        "interest_coverage",
        "cashflow_to_profit",
        "financial_health_score",
        "company_rank",
    ]
]

# =====================================================
# Sort Ranking
# =====================================================

final_df = final_df.sort_values(
    by="financial_health_score",
    ascending=False,
)

# =====================================================
# Save Output
# =====================================================

output_file = OUTPUT / "financial_ratios.csv"

final_df.to_csv(output_file, index=False)

print("\nFinancial Ratios Saved Successfully!")
print(output_file)

print("\n========== TOP 10 COMPANIES ==========")
print(
    final_df[
        [
            "company_id",
            "financial_health_score",
            "company_rank",
        ]
    ].head(10)
)

# =====================================================
# Main
# =====================================================

if __name__ == "__main__":
    print("\nAnalytics Pipeline Completed Successfully!")