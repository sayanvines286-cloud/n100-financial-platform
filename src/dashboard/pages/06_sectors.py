import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from pathlib import Path


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Sector Analysis | Nifty 100",
    page_icon="🏭",
    layout="wide"
)


# ============================================================
# DATABASE PATH
# ============================================================

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Search upward through the project folders for the database.
DB_NAME = "n100_financial.db"

possible_paths = [
    BASE_DIR / "db" / DB_NAME,
    BASE_DIR.parent / "db" / DB_NAME,
    BASE_DIR.parent.parent / "db" / DB_NAME,
    BASE_DIR.parent.parent.parent / "db" / DB_NAME,
    BASE_DIR.parent.parent.parent.parent / "db" / DB_NAME,
    BASE_DIR.parent.parent.parent.parent.parent / "db" / DB_NAME,
]

DB_PATH = next(
    (path for path in possible_paths if path.exists()),
    None
)


# ============================================================
# ============================================================
# DATABASE CONNECTION
# ============================================================

@st.cache_resource
def get_connection():
    if DB_PATH is None:
        return None

    return sqlite3.connect(
        str(DB_PATH),
        check_same_thread=False
    )


conn = get_connection()

# ============================================================
# HEADER
# ============================================================

st.title("🏭 Sector Analysis")

st.caption(
    "Compare Nifty 100 sectors using revenue, profitability, "
    "financial health, valuation and market-cap metrics."
)

st.divider()


# ============================================================
# DATABASE CHECK
# ============================================================

if conn is None:
    st.error(
        "Database not found.\n\n"
        "Please make sure `n100_financial.db` exists "
        "inside the project's `db` folder."
    )
    st.stop()


# ============================================================
# LOAD SECTOR DATA
# ============================================================

@st.cache_data
def load_sectors():
    query = """
        SELECT
            company_id,
            broad_sector,
            sub_sector,
            index_weight_pct,
            market_cap_category
        FROM sectors
        WHERE broad_sector IS NOT NULL
    """

    return pd.read_sql_query(query, conn)


@st.cache_data
def load_companies():
    query = """
        SELECT
            id AS company_id,
            company_name,
            roce_percentage,
            roe_percentage,
            book_value
        FROM companies
    """

    return pd.read_sql_query(query, conn)


@st.cache_data
def load_profit_loss():
    query = """
        SELECT
            company_id,
            year,
            sales,
            expenses,
            operating_profit,
            opm_percentage,
            other_income,
            interest,
            depreciation,
            profit_before_tax,
            tax_percentage,
            net_profit,
            eps,
            dividend_payout
        FROM profitandloss
    """

    return pd.read_sql_query(query, conn)


@st.cache_data
def load_ratios():
    query = """
        SELECT
            company_id,
            year,
            net_profit_margin_pct,
            operating_profit_margin_pct,
            return_on_equity_pct,
            debt_to_equity,
            interest_coverage,
            asset_turnover,
            free_cash_flow_cr,
            capex_cr,
            earnings_per_share,
            book_value_per_share,
            dividend_payout_ratio_pct,
            total_debt_cr,
            cash_from_operations_cr
        FROM financial_ratios
    """

    return pd.read_sql_query(query, conn)


@st.cache_data
def load_market_cap():
    query = """
        SELECT
            company_id,
            year,
            market_cap_crore,
            enterprise_value_crore,
            pe_ratio,
            pb_ratio,
            ev_ebitda,
            dividend_yield_pct
        FROM market_cap
    """

    return pd.read_sql_query(query, conn)


sectors_df = load_sectors()
companies_df = load_companies()
pl_df = load_profit_loss()
ratios_df = load_ratios()
market_df = load_market_cap()


# ============================================================
# BASIC VALIDATION
# ============================================================

required_tables_loaded = [
    sectors_df,
    companies_df,
    pl_df,
    ratios_df,
    market_df
]

if any(df.empty for df in required_tables_loaded):
    st.warning(
        "Some required financial tables contain no data."
    )
    st.stop()


# ============================================================
# NORMALIZE YEARS
# ============================================================

def extract_year(value):
    """
    Extract a four-digit financial year from values such as:

    Dec 2012
    Mar 2024
    Sep 2024
    Mar 2023 15
    TTM

    TTM is treated as unavailable for year-based sector analysis.
    """

    if pd.isna(value):
        return None

    value = str(value)

    import re

    match = re.search(r"(20\d{2}|19\d{2})", value)

    if match:
        return int(match.group(1))

    return None


pl_df["financial_year"] = pl_df["year"].apply(extract_year)
ratios_df["financial_year"] = ratios_df["year"].apply(extract_year)

market_df["financial_year"] = pd.to_numeric(
    market_df["year"],
    errors="coerce"
)


# ============================================================
# AVAILABLE YEARS
# ============================================================

pl_years = set(
    pl_df["financial_year"]
    .dropna()
    .astype(int)
)

ratio_years = set(
    ratios_df["financial_year"]
    .dropna()
    .astype(int)
)

market_years = set(
    market_df["financial_year"]
    .dropna()
    .astype(int)
)

available_years = sorted(
    pl_years & ratio_years & market_years,
    reverse=True
)


if not available_years:
    st.warning("No valid financial years found.")
    st.stop()


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🔎 Sector Filters")

sector_list = sorted(
    sectors_df["broad_sector"]
    .dropna()
    .unique()
    .tolist()
)

selected_sector = st.sidebar.selectbox(
    "Select Sector",
    sector_list
)


selected_year = st.sidebar.selectbox(
    "Select Financial Year",
    available_years
)


# ============================================================
# HELPER FUNCTION
# ============================================================

def latest_record_for_year(df, year, value_column="financial_year"):
    """
    Returns the latest available financial record for each company
    within the selected calendar/financial year.

    This handles data such as:
        Mar 2024
        Sep 2024
        etc.
    """

    temp = df[df[value_column] == year].copy()

    if temp.empty:
        return temp

    # Extract month ordering where possible
    month_map = {
        "Jan": 1,
        "Feb": 2,
        "Mar": 3,
        "Apr": 4,
        "May": 5,
        "Jun": 6,
        "Jul": 7,
        "Aug": 8,
        "Sep": 9,
        "Oct": 10,
        "Nov": 11,
        "Dec": 12
    }

    if "year" in temp.columns:
        temp["month_number"] = (
            temp["year"]
            .astype(str)
            .str[:3]
            .map(month_map)
            .fillna(0)
        )
    else:
        temp["month_number"] = 0

    temp = temp.sort_values(
        ["company_id", "month_number"]
    )

    temp = temp.drop_duplicates(
        subset=["company_id"],
        keep="last"
    )

    return temp.drop(columns=["month_number"], errors="ignore")


# ============================================================
# PREPARE YEAR DATA
# ============================================================

pl_year_df = latest_record_for_year(
    pl_df,
    selected_year
)

ratio_year_df = latest_record_for_year(
    ratios_df,
    selected_year
)

market_year_df = market_df[
    market_df["financial_year"] == selected_year
].copy()

market_year_df = market_year_df.drop_duplicates(
    subset=["company_id"],
    keep="last"
)


# ============================================================
# MERGE ALL FINANCIAL DATA
# ============================================================

financial_df = sectors_df.merge(
    companies_df,
    on="company_id",
    how="left"
)

financial_df = financial_df.merge(
    pl_year_df,
    on="company_id",
    how="left",
    suffixes=("", "_pl")
)

financial_df = financial_df.merge(
    ratio_year_df,
    on="company_id",
    how="left",
    suffixes=("", "_ratio")
)

financial_df = financial_df.merge(
    market_year_df[
        [
            "company_id",
            "market_cap_crore",
            "enterprise_value_crore",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct"
        ]
    ],
    on="company_id",
    how="left"
)


# ============================================================
# SELECTED SECTOR DATA
# ============================================================

sector_data = financial_df[
    financial_df["broad_sector"] == selected_sector
].copy()


if sector_data.empty:
    st.warning(
        f"No companies found for the {selected_sector} sector."
    )
    st.stop()


# ============================================================
# SECTOR SUMMARY
# ============================================================

st.subheader(
    f"{selected_sector} — FY {selected_year}"
)

st.caption(
    f"Financial analysis for companies classified under "
    f"the {selected_sector} sector."
)


# ============================================================
# KEY METRICS
# ============================================================

total_companies = sector_data["company_id"].nunique()

total_revenue = sector_data["sales"].sum(
    min_count=1
)

total_profit = sector_data["net_profit"].sum(
    min_count=1
)

total_market_cap = sector_data["market_cap_crore"].sum(
    min_count=1
)

avg_opm = sector_data["opm_percentage"].mean()

avg_npm = sector_data["net_profit_margin_pct"].mean()

avg_roe = sector_data["return_on_equity_pct"].mean()

avg_de = sector_data["debt_to_equity"].mean()


col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Companies",
        f"{total_companies:,}"
    )

with col2:
    if pd.notna(total_revenue):
        st.metric(
            "Total Revenue",
            f"₹{total_revenue:,.0f} Cr"
        )
    else:
        st.metric("Total Revenue", "N/A")

with col3:
    if pd.notna(total_profit):
        st.metric(
            "Total Net Profit",
            f"₹{total_profit:,.0f} Cr"
        )
    else:
        st.metric("Total Net Profit", "N/A")

with col4:
    if pd.notna(total_market_cap):
        st.metric(
            "Market Cap",
            f"₹{total_market_cap:,.0f} Cr"
        )
    else:
        st.metric("Market Cap", "N/A")


st.divider()


# ============================================================
# PROFITABILITY / FINANCIAL HEALTH
# ============================================================

st.subheader("📊 Profitability & Financial Health")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Avg. Operating Margin",
        f"{avg_opm:.2f}%"
        if pd.notna(avg_opm)
        else "N/A"
    )

with col2:
    st.metric(
        "Avg. Net Profit Margin",
        f"{avg_npm:.2f}%"
        if pd.notna(avg_npm)
        else "N/A"
    )

with col3:
    st.metric(
        "Avg. ROE",
        f"{avg_roe:.2f}%"
        if pd.notna(avg_roe)
        else "N/A"
    )

with col4:
    st.metric(
        "Avg. Debt / Equity",
        f"{avg_de:.2f}"
        if pd.notna(avg_de)
        else "N/A"
    )


# ============================================================
# SECTOR COMPARISON TABLE
# ============================================================

st.divider()

st.subheader(
    f"📈 Nifty 100 Sector Comparison — {selected_year}"
)


# Aggregate all sectors
sector_summary = (
    financial_df
    .groupby("broad_sector", dropna=False)
    .agg(
        Companies=("company_id", "nunique"),
        Revenue_Cr=("sales", "sum"),
        Net_Profit_Cr=("net_profit", "sum"),
        Market_Cap_Cr=("market_cap_crore", "sum"),
        Avg_OPM=("opm_percentage", "mean"),
        Avg_NPM=("net_profit_margin_pct", "mean"),
        Avg_ROE=("return_on_equity_pct", "mean"),
        Avg_Debt_Equity=("debt_to_equity", "mean"),
        Avg_PE=("pe_ratio", "mean")
    )
    .reset_index()
)


sector_summary = sector_summary.sort_values(
    "Market_Cap_Cr",
    ascending=False,
    na_position="last"
)


display_df = sector_summary.copy()

display_df.columns = [
    "Sector",
    "Companies",
    "Revenue (₹ Cr)",
    "Net Profit (₹ Cr)",
    "Market Cap (₹ Cr)",
    "Avg OPM (%)",
    "Avg NPM (%)",
    "Avg ROE (%)",
    "Avg D/E",
    "Avg P/E"
]


st.dataframe(
    display_df,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# CHART 1 — MARKET CAP BY SECTOR
# ============================================================

st.subheader("🏦 Market Capitalisation by Sector")

chart_market = sector_summary.dropna(
    subset=["Market_Cap_Cr"]
).copy()

chart_market = chart_market.sort_values(
    "Market_Cap_Cr",
    ascending=True
)

if not chart_market.empty:

    fig_market = px.bar(
        chart_market,
        x="Market_Cap_Cr",
        y="broad_sector",
        orientation="h",
        labels={
            "Market_Cap_Cr": "Market Cap (₹ Cr)",
            "broad_sector": "Sector"
        },
        title=f"Sector Market Capitalisation — {selected_year}"
    )

    fig_market.update_layout(
        height=500,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    st.plotly_chart(
        fig_market,
        use_container_width=True
    )


# ============================================================
# CHART 2 — REVENUE VS NET PROFIT
# ============================================================

st.subheader("💰 Revenue vs Net Profit")

chart_profit = sector_summary.dropna(
    subset=["Revenue_Cr", "Net_Profit_Cr"]
).copy()

if not chart_profit.empty:

    fig_profit = px.scatter(
        chart_profit,
        x="Revenue_Cr",
        y="Net_Profit_Cr",
        size="Market_Cap_Cr",
        hover_name="broad_sector",
        labels={
            "Revenue_Cr": "Revenue (₹ Cr)",
            "Net_Profit_Cr": "Net Profit (₹ Cr)",
            "Market_Cap_Cr": "Market Cap (₹ Cr)"
        },
        title=f"Revenue vs Net Profit — {selected_year}"
    )

    fig_profit.update_layout(
        height=500
    )

    st.plotly_chart(
        fig_profit,
        use_container_width=True
    )


# ============================================================
# CHART 3 — PROFITABILITY
# ============================================================

st.subheader("📈 Sector Profitability")

profitability_df = sector_summary[
    [
        "broad_sector",
        "Avg_OPM",
        "Avg_NPM"
    ]
].copy()

profitability_df = profitability_df.dropna(
    subset=["Avg_OPM", "Avg_NPM"],
    how="all"
)

if not profitability_df.empty:

    profitability_long = profitability_df.melt(
        id_vars="broad_sector",
        value_vars=["Avg_OPM", "Avg_NPM"],
        var_name="Metric",
        value_name="Percentage"
    )

    profitability_long["Metric"] = (
        profitability_long["Metric"]
        .replace(
            {
                "Avg_OPM": "Operating Margin",
                "Avg_NPM": "Net Profit Margin"
            }
        )
    )

    fig_profitability = px.bar(
        profitability_long,
        x="broad_sector",
        y="Percentage",
        color="Metric",
        barmode="group",
        labels={
            "broad_sector": "Sector",
            "Percentage": "Percentage (%)",
            "Metric": "Metric"
        },
        title=f"Average Profitability by Sector — {selected_year}"
    )

    fig_profitability.update_layout(
        height=550,
        xaxis_tickangle=-35
    )

    st.plotly_chart(
        fig_profitability,
        use_container_width=True
    )


# ============================================================
# SELECTED SECTOR — COMPANY BREAKDOWN
# ============================================================

st.divider()

st.subheader(
    f"🏢 Companies in {selected_sector}"
)


company_columns = [
    "company_id",
    "company_name",
    "sub_sector",
    "index_weight_pct",
    "market_cap_category",
    "sales",
    "net_profit",
    "opm_percentage",
    "net_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "market_cap_crore",
    "pe_ratio",
    "pb_ratio"
]

company_columns = [
    col
    for col in company_columns
    if col in sector_data.columns
]

company_table = sector_data[company_columns].copy()


rename_map = {
    "company_id": "Symbol",
    "company_name": "Company",
    "sub_sector": "Sub Sector",
    "index_weight_pct": "Index Weight (%)",
    "market_cap_category": "Market Cap Category",
    "sales": "Revenue (₹ Cr)",
    "net_profit": "Net Profit (₹ Cr)",
    "opm_percentage": "OPM (%)",
    "net_profit_margin_pct": "NPM (%)",
    "return_on_equity_pct": "ROE (%)",
    "debt_to_equity": "D/E",
    "market_cap_crore": "Market Cap (₹ Cr)",
    "pe_ratio": "P/E",
    "pb_ratio": "P/B"
}

company_table = company_table.rename(
    columns=rename_map
)


st.dataframe(
    company_table,
    use_container_width=True,
    hide_index=True
)


# ============================================================
# DOWNLOAD DATA
# ============================================================

csv_data = company_table.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇️ Download Sector Data CSV",
    data=csv_data,
    file_name=(
        f"{selected_sector.lower().replace(' ', '_')}"
        f"_{selected_year}.csv"
    ),
    mime="text/csv"
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Data source: Nifty 100 financial database "
    "(`n100_financial.db`)."
)