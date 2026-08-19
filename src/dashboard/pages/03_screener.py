import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# --------------------------------------------------
# PATH SETUP
# --------------------------------------------------

ROOT = Path(__file__).resolve().parents[3]

if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from src.dashboard.pages.utils.db import get_connection

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Stock Screener | Nifty 100 Analytics",
    page_icon="🔎",
    layout="wide"
)


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🔎 Stock Screener")
st.caption(
    "Filter Nifty 100 companies using financial performance and valuation metrics."
)

st.divider()


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

try:
    conn = get_connection()

    query = """
    SELECT
        c.company_name,
        c.id AS company_id,

        fr.year,
        fr.net_profit_margin_pct AS net_margin_pct,
        fr.operating_profit_margin_pct AS operating_margin_pct,
        fr.return_on_equity_pct,
        fr.debt_to_equity,
        fr.interest_coverage,
        fr.asset_turnover,
        fr.free_cash_flow_cr,
        fr.capex_cr,
        fr.earnings_per_share,
        fr.book_value_per_share,
        fr.dividend_payout_ratio_pct,
        fr.total_debt_cr,
        fr.cash_from_operations_cr

    FROM companies c

    INNER JOIN financial_ratios fr
        ON c.id = fr.company_id

    ORDER BY c.company_name
    """

    df = pd.read_sql_query(query, conn)
    conn.close()

except Exception as e:
    st.error(f"Unable to load financial data: {e}")
    st.stop()


# --------------------------------------------------
# CHECK DATA
# --------------------------------------------------

if df.empty:
    st.warning("No financial data available.")
    st.stop()


# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.header("🎯 Screening Filters")

# Company
companies = sorted(df["company_name"].dropna().unique())

selected_companies = st.sidebar.multiselect(
    "Company",
    companies
)

# Year
years = sorted(df["year"].dropna().unique(), reverse=True)

selected_year = st.sidebar.selectbox(
    "Year",
    years
)

# Minimum ROE
min_roe = st.sidebar.number_input(
    "Minimum ROE (%)",
    min_value=0.0,
    value=0.0,
    step=1.0
)

# Maximum Debt / Equity
max_de = st.sidebar.number_input(
    "Maximum Debt / Equity",
    min_value=0.0,
    value=100.0,
    step=0.5
)

# Minimum Interest Coverage
min_interest = st.sidebar.number_input(
    "Minimum Interest Coverage",
    min_value=0.0,
    value=0.0,
    step=1.0
)

# Minimum EPS
min_eps = st.sidebar.number_input(
    "Minimum EPS",
    value=0.0,
    step=1.0
)


# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------

filtered = df[df["year"] == selected_year].copy()

if selected_companies:
    filtered = filtered[
        filtered["company_name"].isin(selected_companies)
    ]

filtered = filtered[
    (filtered["return_on_equity_pct"] >= min_roe)
    & (filtered["debt_to_equity"] <= max_de)
    & (filtered["interest_coverage"] >= min_interest)
    & (filtered["earnings_per_share"] >= min_eps)
]


# --------------------------------------------------
# RESULTS SUMMARY
# --------------------------------------------------

st.subheader("📊 Screening Results")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Companies Found",
        len(filtered)
    )

with col2:
    st.metric(
        "Selected Year",
        selected_year
    )

with col3:
    total_for_year = len(df[df["year"] == selected_year])

    if total_for_year > 0:
        percentage = (len(filtered) / total_for_year) * 100
    else:
        percentage = 0

    st.metric(
        "Match Rate",
        f"{percentage:.1f}%"
    )


st.divider()


# --------------------------------------------------
# DISPLAY RESULTS
# --------------------------------------------------

if filtered.empty:

    st.info(
        "No companies match the selected screening criteria."
    )

else:

    display_df = filtered[
        [
            "company_name",
            "year",
            "net_margin_pct",
            "return_on_equity_pct",
            "debt_to_equity",
            "interest_coverage",
            "asset_turnover",
            "earnings_per_share",
            "book_value_per_share",
            "free_cash_flow_cr",
            "total_debt_cr"
        ]
    ].copy()

    display_df.columns = [
        "Company",
        "Year",
        "Net Margin %",
        "ROE %",
        "Debt / Equity",
        "Interest Coverage",
        "Asset Turnover",
        "EPS",
        "Book Value / Share",
        "Free Cash Flow (Cr)",
        "Total Debt (Cr)"
    ]

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


    # --------------------------------------------------
    # DOWNLOAD
    # --------------------------------------------------

    csv = display_df.to_csv(index=False)

    st.download_button(
        label="⬇️ Download Screening Results",
        data=csv,
        file_name="nifty100_screening_results.csv",
        mime="text/csv"
    )