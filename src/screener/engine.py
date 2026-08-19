import yaml
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]

CONFIG = BASE_DIR / "config" / "screener_config.yaml"
OUTPUT = BASE_DIR / "output"

financial_ratios = pd.read_csv(BASE_DIR / "Data" / "processed" / "financial_ratios.csv")
cagr = pd.read_csv(OUTPUT / "cagr_analysis.csv")
cashflow = pd.read_csv(OUTPUT / "cashflow_kpis.csv")
df = (
    financial_ratios
    .merge(cagr, on="company_id", how="left")
    .merge(cashflow, on=["company_id", "year"], how="left")
)

print(df.columns.tolist())
print(df.head())

with open(CONFIG, "r") as f:
    presets = yaml.safe_load(f)["presets"]
    # Composite Quality Score
df["Composite Score"] = (
    df["return_on_equity_pct"].fillna(0) * 0.35
    + df["Cash Quality Score"].fillna(0) * 0.30
    + df["Revenue CAGR (%)"].fillna(0) * 0.20
    + (100 - df["debt_to_equity"].fillna(100)) * 0.15
)

df["Composite Score"] = df["Composite Score"].round(2)

print(df[["company_id", "Composite Score"]].head())
def apply_filters(df, preset):
    filtered = df.copy()

    if "roe_min" in preset and "return_on_equity_pct" in filtered.columns:
        filtered = filtered[
            filtered["return_on_equity_pct"].fillna(0) >= preset["roe_min"]
        ]

    if "de_max" in preset and "debt_to_equity" in filtered.columns:
        filtered = filtered[
            (filtered["debt_to_equity"] <= preset["de_max"])
            | (filtered["debt_to_equity"] == 0)
        ]

    if "market_cap_min" in preset and "market_cap_cr" in filtered.columns:
        filtered = filtered[
            filtered["market_cap_cr"].fillna(0) >= preset["market_cap_min"]
        ]

    if "dividend_yield_min" in preset:
        if "dividend_yield_pct" in filtered.columns:
            filtered = filtered[
                filtered["dividend_yield_pct"].fillna(0)
                >= preset["dividend_yield_min"]
            ]

    if "fcf_min" in preset and "free_cash_flow_cr" in filtered.columns:
        filtered = filtered[
            filtered["free_cash_flow_cr"].fillna(0) >= preset["fcf_min"]
        ]

    return filtered