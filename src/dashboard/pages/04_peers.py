import streamlit as st
import sqlite3
import pandas as pd


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Peer Comparison | Nifty 100",
    page_icon="👥",
    layout="wide"
)


# ============================================================
# DATABASE
# ============================================================

DB_PATH = "db/n100_financial.db"


@st.cache_data
def load_data():

    conn = sqlite3.connect(DB_PATH)

    query = """
        SELECT
            c.id AS company_id,
            c.company_name,
            s.broad_sector,
            s.sub_sector,
            s.index_weight_pct,
            s.market_cap_category,

            fr.year,
            fr.net_profit_margin_pct,
            fr.operating_profit_margin_pct,
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

        LEFT JOIN sectors s
            ON c.id = s.company_id

        INNER JOIN financial_ratios fr
            ON c.id = fr.company_id

        ORDER BY c.company_name
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


# ============================================================
# LOAD DATA
# ============================================================

try:
    df = load_data()

except Exception as e:
    st.error(f"Unable to load financial data: {e}")
    st.stop()


# ============================================================
# PAGE HEADER
# ============================================================

st.title("👥 Peer Comparison")

st.write(
    "Compare Nifty 100 companies with their sector peers "
    "using key financial and performance metrics."
)

st.divider()


# ============================================================
# BASIC DATA CLEANING
# ============================================================

df["company_name"] = df["company_name"].fillna("Unknown Company")

df["broad_sector"] = df["broad_sector"].fillna("Unknown")

df["sub_sector"] = df["sub_sector"].fillna("Unknown")


# ============================================================
# COMPANY + YEAR FILTERS
# ============================================================

st.subheader("🏢 Selected Company")

company_list = sorted(
    df["company_name"].dropna().unique().tolist()
)

if not company_list:
    st.warning("No companies found in the database.")
    st.stop()


selected_company = st.selectbox(
    "Select Company",
    company_list
)


# Data for selected company
company_df = df[
    df["company_name"] == selected_company
].copy()


if company_df.empty:
    st.warning("No financial data available for this company.")
    st.stop()


# Available years
years = sorted(
    company_df["year"].dropna().unique().tolist(),
    reverse=True
)

if not years:
    st.warning("No financial years available.")
    st.stop()


selected_year = st.selectbox(
    "Select Year",
    years
)


# ============================================================
# SELECTED COMPANY DATA
# ============================================================

selected_row = company_df[
    company_df["year"] == selected_year
].copy()


if selected_row.empty:
    st.warning("No data available for the selected year.")
    st.stop()


selected_row = selected_row.iloc[0]


selected_sector = selected_row["broad_sector"]

selected_sub_sector = selected_row["sub_sector"]


# ============================================================
# COMPANY SUMMARY
# ============================================================

st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.caption("Company")
    st.subheader(selected_company)

with col2:
    st.caption("Sector")
    st.subheader(selected_sector)

with col3:
    st.caption("Year")
    st.subheader(str(selected_year))


# ============================================================
# SECTOR PEERS
# ============================================================

st.divider()

st.subheader("👥 Sector Peers")


# Filter companies belonging to the same broad sector
peer_df = df[
    (df["broad_sector"] == selected_sector) &
    (df["year"] == selected_year)
].copy()


# Remove duplicate company rows
peer_df = peer_df.drop_duplicates(
    subset=["company_id"]
)


# Sort selected company first
peer_df["is_selected"] = (
    peer_df["company_name"] == selected_company
)

peer_df = peer_df.sort_values(
    by=["is_selected", "company_name"],
    ascending=[False, True]
)


# ============================================================
# PEER STATISTICS
# ============================================================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Companies Compared",
        len(peer_df)
    )

with col2:
    st.metric(
        "Selected Company",
        selected_company
    )

with col3:
    st.metric(
        "Sector",
        selected_sector
    )


# ============================================================
# COMPARISON TABLE
# ============================================================

display_columns = {
    "company_name": "Company",
    "year": "Year",
    "net_profit_margin_pct": "Net Margin %",
    "return_on_equity_pct": "ROE %",
    "debt_to_equity": "Debt / Equity",
    "interest_coverage": "Interest Coverage",
    "asset_turnover": "Asset Turnover",
    "earnings_per_share": "EPS",
    "book_value_per_share": "Book Value / Share",
    "free_cash_flow_cr": "Free Cash Flow ₹ Cr",
    "dividend_payout_ratio_pct": "Dividend Payout %",
}


available_columns = [
    col for col in display_columns.keys()
    if col in peer_df.columns
]


display_df = peer_df[available_columns].copy()

display_df = display_df.rename(
    columns={
        col: display_columns[col]
        for col in available_columns
    }
)


# ============================================================
# ROUND NUMERIC VALUES
# ============================================================

for col in display_df.columns:

    if col != "Company" and col != "Year":

        if pd.api.types.is_numeric_dtype(
            display_df[col]
        ):
            display_df[col] = display_df[col].round(2)


# ============================================================
# HIGHLIGHT SELECTED COMPANY
# ============================================================

def highlight_selected(row):

    if row["Company"] == selected_company:
        return [
            "font-weight: bold"
            for _ in row
        ]

    return [""] * len(row)


st.dataframe(
    display_df.style.apply(
        highlight_selected,
        axis=1
    ),
    use_container_width=True,
    hide_index=True
)


# ============================================================
# COMPANY vs PEERS
# ============================================================

st.divider()

st.subheader("📊 Company vs Sector Average")


numeric_metrics = [
    "net_profit_margin_pct",
    "return_on_equity_pct",
    "debt_to_equity",
    "interest_coverage",
    "asset_turnover",
]


comparison_data = []

for metric in numeric_metrics:

    if metric not in peer_df.columns:
        continue

    company_value = selected_row[metric]

    peer_average = peer_df[metric].mean()

    comparison_data.append({
        "Metric": display_columns.get(
            metric,
            metric
        ),
        "Selected Company": company_value,
        "Sector Average": peer_average
    })


if comparison_data:

    comparison_df = pd.DataFrame(
        comparison_data
    )

    comparison_df["Selected Company"] = (
        comparison_df["Selected Company"]
        .round(2)
    )

    comparison_df["Sector Average"] = (
        comparison_df["Sector Average"]
        .round(2)
    )

    st.dataframe(
        comparison_df,
        use_container_width=True,
        hide_index=True
    )


# ============================================================
# DOWNLOAD
# ============================================================

st.divider()

csv = display_df.to_csv(
    index=False
)

st.download_button(
    label="⬇️ Download Peer Comparison",
    data=csv,
    file_name="peer_comparison.csv",
    mime="text/csv"
)