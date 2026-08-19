import streamlit as st
import sqlite3
from pathlib import Path
import pandas as pd


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Nifty 100 Analytics",
    page_icon="📊",
    layout="wide"
)


# --------------------------------------------------
# DATABASE CONNECTION
# --------------------------------------------------

DB_PATH = Path(__file__).resolve().parents[3] / "db" / "n100_financial.db"


@st.cache_data
def load_data():

    conn = sqlite3.connect(DB_PATH)

    companies = pd.read_sql_query(
        "SELECT * FROM companies",
        conn
    )

    sectors = pd.read_sql_query(
        "SELECT * FROM sectors",
        conn
    )

    market_cap = pd.read_sql_query(
        "SELECT * FROM market_cap",
        conn
    )

    financial_ratios = pd.read_sql_query(
        "SELECT * FROM financial_ratios",
        conn
    )

    conn.close()

    return companies, sectors, market_cap, financial_ratios


companies, sectors, market_cap, financial_ratios = load_data()


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("📊 Nifty 100 Analytics")

st.markdown(
    "### Nifty 100 Financial Intelligence Platform"
)

st.write(
    "Explore company fundamentals, financial ratios, "
    "peer comparisons, market trends and sector-level insights."
)

st.divider()


# --------------------------------------------------
# KEY METRICS
# --------------------------------------------------

total_companies = len(companies)

total_sectors = (
    sectors["broad_sector"].nunique()
    if "broad_sector" in sectors.columns
    else 0
)

avg_roe = (
    financial_ratios["return_on_equity_pct"].mean()
    if "return_on_equity_pct" in financial_ratios.columns
    else 0
)

avg_roce = (
    financial_ratios["roce_percentage"].mean()
    if "roce_percentage" in financial_ratios.columns
    else 0
)


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Companies",
        total_companies
    )

with col2:
    st.metric(
        "Sectors",
        total_sectors
    )

with col3:
    st.metric(
        "Average ROE",
        f"{avg_roe:.2f}%"
    )

with col4:
    st.metric(
        "Average ROCE",
        f"{avg_roce:.2f}%"
    )


st.divider()


# --------------------------------------------------
# SECTOR DISTRIBUTION
# --------------------------------------------------

st.subheader("🏭 Sector Distribution")

if "broad_sector" in sectors.columns:

    sector_data = (
        sectors.groupby("broad_sector")
        .size()
        .reset_index(name="companies")
        .sort_values("companies", ascending=False)
    )

    st.bar_chart(
        sector_data.set_index("broad_sector")
    )

else:

    st.info("Sector data is not available.")


# --------------------------------------------------
# MARKET CAP OVERVIEW
# --------------------------------------------------

st.subheader("💰 Market Capitalisation Overview")

if "market_cap_crore" in market_cap.columns:

    market_cap_data = market_cap[
        ["company_id", "market_cap_crore"]
    ].copy()

    market_cap_data = market_cap_data.sort_values(
        "market_cap_crore",
        ascending=False
    ).head(10)

    st.bar_chart(
        market_cap_data.set_index("company_id")
    )

else:

    st.info("Market-cap data is not available.")


# --------------------------------------------------
# COMPANY DATABASE
# --------------------------------------------------

st.subheader("🏢 Companies in Nifty 100")

if "company_name" in companies.columns:

    display_columns = [
        column
        for column in [
            "company_name",
            "face_value",
            "book_value",
            "roce_percentage",
            "roe_percentage"
        ]
        if column in companies.columns
    ]

    if display_columns:

        st.dataframe(
            companies[display_columns],
            use_container_width=True,
            hide_index=True
        )

    else:

        st.dataframe(
            companies,
            use_container_width=True,
            hide_index=True
        )

else:

    st.info("Company data is not available.")


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Nifty 100 Analytics • Financial Intelligence Platform"
)