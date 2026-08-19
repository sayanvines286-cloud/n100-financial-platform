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

profit_loss = pd.read_csv(PROCESSED / "profitandloss.csv")
balance_sheet = pd.read_csv(PROCESSED / "balancesheet.csv")

print("Datasets Loaded Successfully")

# ==========================
# CAGR Function
# ==========================

def calculate_cagr(first, last, years):
    if first <= 0 or years <= 0:
        return None
    return round((((last / first) ** (1 / years)) - 1) * 100, 2)

# ==========================
# Calculate CAGR
# ==========================

results = []

companies = profit_loss["company_id"].unique()

for company in companies:

    pl = (
        profit_loss[profit_loss["company_id"] == company]
        .sort_values("year")
    )

    bs = (
        balance_sheet[balance_sheet["company_id"] == company]
        .sort_values("year")
    )

    if len(pl) < 2:
        continue

    years = len(pl) - 1

    revenue_cagr = calculate_cagr(
        pl.iloc[0]["sales"],
        pl.iloc[-1]["sales"],
        years,
    )

    profit_cagr = calculate_cagr(
        pl.iloc[0]["net_profit"],
        pl.iloc[-1]["net_profit"],
        years,
    )

    eps_cagr = calculate_cagr(
        pl.iloc[0]["eps"],
        pl.iloc[-1]["eps"],
        years,
    )

    asset_cagr = None

    if len(bs) >= 2:
        asset_cagr = calculate_cagr(
            bs.iloc[0]["total_assets"],
            bs.iloc[-1]["total_assets"],
            years,
        )

    results.append(
        {
            "company_id": company,
            "Revenue CAGR (%)": revenue_cagr,
            "Net Profit CAGR (%)": profit_cagr,
            "EPS CAGR (%)": eps_cagr,
            "Asset CAGR (%)": asset_cagr,
        }
    )

# ==========================
# Output
# ==========================

cagr_df = pd.DataFrame(results)

cagr_df = cagr_df.sort_values(
    by="Revenue CAGR (%)",
    ascending=False,
    na_position="last",
)

output_file = OUTPUT / "cagr_analysis.csv"

cagr_df.to_csv(output_file, index=False)

print("\nCAGR Analysis Completed Successfully!\n")

print(cagr_df.head(10))

print(f"\nSaved to:\n{output_file}")

if __name__ == "__main__":
    print("\nCAGR Pipeline Completed Successfully!")