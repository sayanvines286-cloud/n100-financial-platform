# ============================================================
# 07_capital.py
# Nifty 100 Financial Analytics Platform
# Capital Allocation Dashboard
# ============================================================

import re
import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Capital Allocation | Nifty 100",
    page_icon="💰",
    layout="wide",
)


# ============================================================
# DATABASE PATH
# ============================================================

BASE_DIR = Path(__file__).resolve().parent
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
    None,
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

@st.cache_resource
def get_connection():
    if DB_PATH is None:
        return None

    return sqlite3.connect(
        str(DB_PATH),
        check_same_thread=False,
    )


conn = get_connection()


# ============================================================
# DATABASE CHECK
# ============================================================

if conn is None:
    st.error(
        "Database not found.\n\n"
        "Please make sure `n100_financial.db` exists inside "
        "the project's `db` folder."
    )
    st.stop()


# ============================================================
# DATA LOADERS
# ============================================================

@st.cache_data
def load_companies():
    query = """
        SELECT
            id AS company_id,
            company_name
        FROM companies
    """

    df = pd.read_sql_query(query, conn)
    return df


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
    """

    df = pd.read_sql_query(query, conn)
    return df


@st.cache_data
def load_cashflow():
    query = """
        SELECT
            company_id,
            year,
            operating_activity,
            investing_activity,
            financing_activity,
            net_cash_flow
        FROM cashflow
    """

    df = pd.read_sql_query(query, conn)
    return df


@st.cache_data
def load_profit_loss():
    query = """
        SELECT
            company_id,
            year,
            sales,
            net_profit,
            operating_profit,
            opm_percentage
        FROM profitandloss
    """

    df = pd.read_sql_query(query, conn)
    return df


@st.cache_data
def load_ratios():
    query = """
        SELECT
            company_id,
            year,
            free_cash_flow_cr,
            cash_from_operations_cr,
            return_on_equity_pct
        FROM financial_ratios
    """

    df = pd.read_sql_query(query, conn)
    return df


# ============================================================
# LOAD DATA
# ============================================================

try:
    companies_df = load_companies()
    sectors_df = load_sectors()
    cashflow_df = load_cashflow()
    pl_df = load_profit_loss()
    ratios_df = load_ratios()

except Exception as exc:
    st.error("Unable to load capital allocation data.")
    st.exception(exc)
    st.stop()


# ============================================================
# BASIC VALIDATION
# ============================================================

if cashflow_df.empty:
    st.error("No cash-flow data is available in the database.")
    st.stop()

if sectors_df.empty:
    st.error("No sector mapping is available in the database.")
    st.stop()


# ============================================================
# NORMALISATION HELPERS
# ============================================================

def normalize_company_id(series):
    """
    Normalise ticker/company IDs before every join.

    This prevents joins such as:
        'VEDL'
        'vedl '
        ' VEDL'
    from being treated as different companies.
    """
    return (
        series.astype("string")
        .str.strip()
        .str.upper()
    )


def extract_year(value):
    """
    Extract a four-digit year from values such as:
        Mar-24
        Mar 2024
        Dec 2023
        2024
    """
    if pd.isna(value):
        return None

    match = re.search(r"(19\d{2}|20\d{2})", str(value))

    if match:
        return int(match.group(1))

    return None


def sign_label(value):
    """
    Convert a numeric cash-flow value into + / -.

    Zero is treated as positive/neutral for the 8-pattern
    capital allocation matrix so every company receives a
    deterministic pattern.
    """
    if pd.isna(value):
        return None

    return "+" if float(value) >= 0 else "-"


# ============================================================
# NORMALISE IDS
# ============================================================

companies_df["company_id"] = normalize_company_id(
    companies_df["company_id"]
)

sectors_df["company_id"] = normalize_company_id(
    sectors_df["company_id"]
)

cashflow_df["company_id"] = normalize_company_id(
    cashflow_df["company_id"]
)

pl_df["company_id"] = normalize_company_id(
    pl_df["company_id"]
)

ratios_df["company_id"] = normalize_company_id(
    ratios_df["company_id"]
)


# ============================================================
# CLEAN COMPANY MASTER
# ============================================================

companies_df["company_name"] = (
    companies_df["company_name"]
    .astype("string")
    .str.strip()
)

# Remove duplicate company master rows.
companies_df = (
    companies_df
    .drop_duplicates(subset=["company_id"], keep="first")
)


# ============================================================
# CLEAN SECTOR MASTER
# ============================================================

for col in [
    "broad_sector",
    "sub_sector",
    "market_cap_category",
]:
    if col in sectors_df.columns:
        sectors_df[col] = (
            sectors_df[col]
            .astype("string")
            .str.strip()
        )

sectors_df = (
    sectors_df
    .drop_duplicates(subset=["company_id"], keep="first")
)


# ============================================================
# NORMALISE YEARS
# ============================================================

cashflow_df["financial_year"] = (
    cashflow_df["year"].apply(extract_year)
)

pl_df["financial_year"] = (
    pl_df["year"].apply(extract_year)
)

ratios_df["financial_year"] = (
    ratios_df["year"].apply(extract_year)
)


# ============================================================
# NUMERIC CLEANING
# ============================================================

cashflow_numeric = [
    "operating_activity",
    "investing_activity",
    "financing_activity",
    "net_cash_flow",
]

for col in cashflow_numeric:
    cashflow_df[col] = pd.to_numeric(
        cashflow_df[col],
        errors="coerce",
    )


for col in [
    "sales",
    "net_profit",
    "operating_profit",
    "opm_percentage",
]:
    if col in pl_df.columns:
        pl_df[col] = pd.to_numeric(
            pl_df[col],
            errors="coerce",
        )


# ============================================================
# LATEST RECORD FOR SELECTED YEAR
# ============================================================

def latest_record_for_year(df, selected_year):
    """
    Select the latest available record per company for the
    requested financial year.

    Handles year values such as:
        Mar-24
        Sep-24
        Dec-24
    """

    temp = df[
        df["financial_year"] == selected_year
    ].copy()

    if temp.empty:
        return temp

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
        "Dec": 12,
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
        keep="last",
    )

    return temp.drop(
        columns=["month_number"],
        errors="ignore",
    )


# ============================================================
# AVAILABLE YEARS
# ============================================================

available_years = sorted(
    set(
        cashflow_df["financial_year"]
        .dropna()
        .astype(int)
        .tolist()
    ),
    reverse=True,
)

if not available_years:
    st.error("No valid financial years were found.")
    st.stop()


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Capital Allocation Filters")

selected_year = st.sidebar.selectbox(
    "Select Financial Year",
    available_years,
)

sector_values = sorted(
    sectors_df["broad_sector"]
    .dropna()
    .astype(str)
    .unique()
    .tolist()
)

sector_options = ["All Sectors"] + sector_values

selected_sector = st.sidebar.selectbox(
    "Select Sector",
    sector_options,
)


# ============================================================
# PREPARE SELECTED YEAR
# ============================================================

cashflow_year = latest_record_for_year(
    cashflow_df,
    selected_year,
)

pl_year = latest_record_for_year(
    pl_df,
    selected_year,
)

ratios_year = latest_record_for_year(
    ratios_df,
    selected_year,
)


# ============================================================
# MERGE CASH FLOW + COMPANY MASTER + SECTOR MASTER
# ============================================================
# IMPORTANT FIX:
# The previous version could lose company/sector metadata when
# joining only through financial-ratio data. The correct source
# of sector/sub-sector is the `sectors` table, which has a
# 1:1 mapping with companies.
# ============================================================

capital_df = cashflow_year[
    [
        "company_id",
        "year",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "net_cash_flow",
    ]
].copy()


# Company metadata
capital_df = capital_df.merge(
    companies_df[
        [
            "company_id",
            "company_name",
        ]
    ],
    on="company_id",
    how="left",
)


# Sector metadata
capital_df = capital_df.merge(
    sectors_df[
        [
            "company_id",
            "broad_sector",
            "sub_sector",
            "index_weight_pct",
            "market_cap_category",
        ]
    ],
    on="company_id",
    how="left",
)


# Profitability / FCF supporting data
if not pl_year.empty:
    capital_df = capital_df.merge(
        pl_year[
            [
                "company_id",
                "sales",
                "net_profit",
                "operating_profit",
                "opm_percentage",
            ]
        ],
        on="company_id",
        how="left",
    )

if not ratios_year.empty:
    capital_df = capital_df.merge(
        ratios_year[
            [
                "company_id",
                "free_cash_flow_cr",
                "cash_from_operations_cr",
                "return_on_equity_pct",
            ]
        ],
        on="company_id",
        how="left",
    )


# ============================================================
# METADATA FALLBACKS
# ============================================================
# Never display literal None/NaN for a company identifier.
# If a company-master name is missing, use its ticker.
# Sector/sub-sector still come from the sectors table.
# ============================================================

capital_df["company_name"] = (
    capital_df["company_name"]
    .fillna(capital_df["company_id"])
    .replace("", pd.NA)
    .fillna(capital_df["company_id"])
)

capital_df["broad_sector"] = (
    capital_df["broad_sector"]
    .fillna("Unclassified")
    .replace("", "Unclassified")
)

capital_df["sub_sector"] = (
    capital_df["sub_sector"]
    .fillna("Unclassified")
    .replace("", "Unclassified")
)


# ============================================================
# CASH FLOW PATTERN
# ============================================================

capital_df["CFO Sign"] = capital_df[
    "operating_activity"
].apply(sign_label)

capital_df["CFI Sign"] = capital_df[
    "investing_activity"
].apply(sign_label)

capital_df["CFF Sign"] = capital_df[
    "financing_activity"
].apply(sign_label)


capital_df["Cash Flow Pattern"] = (
    "("
    + capital_df["CFO Sign"].fillna("?")
    + ", "
    + capital_df["CFI Sign"].fillna("?")
    + ", "
    + capital_df["CFF Sign"].fillna("?")
    + ")"
)


# ============================================================
# CAPITAL ALLOCATION LABELS
# ============================================================

PATTERN_LABELS = {
    "(+, +, +)": "Cash Accumulation",
    "(+, +, -)": "Asset Monetiser",
    "(+, -, +)": "Growth Financed",
    "(+, -, -)": "Reinvestor / Shareholder Returns",
    "(-, +, +)": "External Funding",
    "(-, +, -)": "Cash Recovery / Deleveraging",
    "(-, -, +)": "Distress Signal",
    "(-, -, -)": "Cash Burn",
}


capital_df["Capital Allocation"] = (
    capital_df["Cash Flow Pattern"]
    .map(PATTERN_LABELS)
    .fillna("Unclassified")
)


# ============================================================
# FREE CASH FLOW
# ============================================================

capital_df["FCF (₹ Cr)"] = (
    capital_df["operating_activity"]
    + capital_df["investing_activity"]
)


# ============================================================
# DISTRESS SIGNAL
# ============================================================

capital_df["Distress Signal"] = (
    (capital_df["operating_activity"] < 0)
    & (capital_df["financing_activity"] > 0)
)


# ============================================================
# FILTER BY SECTOR
# ============================================================

if selected_sector != "All Sectors":
    capital_df = capital_df[
        capital_df["broad_sector"] == selected_sector
    ].copy()


# ============================================================
# REMOVE INVALID CASH FLOW ROWS
# ============================================================

capital_df = capital_df[
    capital_df[
        [
            "operating_activity",
            "investing_activity",
            "financing_activity",
        ]
    ]
    .notna()
    .any(axis=1)
].copy()


if capital_df.empty:
    st.warning(
        f"No capital allocation data is available for "
        f"{selected_year}"
        + (
            f" in the {selected_sector} sector."
            if selected_sector != "All Sectors"
            else "."
        )
    )
    st.stop()


# ============================================================
# HEADER
# ============================================================

st.title("💰 Capital Allocation")

st.caption(
    "Analyze how Nifty 100 companies allocate cash between "
    "operations, investment and financing."
)


# ============================================================
# KPI CARDS
# ============================================================

total_companies = capital_df["company_id"].nunique()

positive_cfo = (
    capital_df["operating_activity"] > 0
).sum()

positive_fcf = (
    capital_df["FCF (₹ Cr)"] > 0
).sum()

negative_cfo = (
    capital_df["operating_activity"] < 0
).sum()

distress_count = (
    capital_df["Distress Signal"]
).sum()


st.divider()

k1, k2, k3, k4, k5 = st.columns(5)

with k1:
    st.metric(
        "Companies",
        f"{total_companies:,}",
    )

with k2:
    st.metric(
        "Positive CFO",
        f"{positive_cfo:,}",
    )

with k3:
    st.metric(
        "Positive FCF",
        f"{positive_fcf:,}",
    )

with k4:
    st.metric(
        "Negative CFO",
        f"{negative_cfo:,}",
    )

with k5:
    st.metric(
        "Distress Signals",
        f"{distress_count:,}",
    )


# ============================================================
# CAPITAL ALLOCATION MAP
# ============================================================

st.divider()

st.subheader("🗺️ Capital Allocation Map")

st.caption(
    "Companies are grouped according to the sign of "
    "Operating Cash Flow (CFO), Investing Cash Flow (CFI) "
    "and Financing Cash Flow (CFF)."
)


pattern_summary = (
    capital_df
    .groupby(
        [
            "Capital Allocation",
            "Cash Flow Pattern",
        ],
        dropna=False,
    )
    .agg(
        Companies=("company_id", "nunique"),
    )
    .reset_index()
)


pattern_order = [
    "Reinvestor / Shareholder Returns",
    "Growth Financed",
    "Distress Signal",
    "Asset Monetiser",
    "Cash Recovery / Deleveraging",
    "Cash Burn",
    "External Funding",
    "Cash Accumulation",
]

pattern_summary["sort_order"] = (
    pattern_summary["Capital Allocation"]
    .map(
        {
            label: index
            for index, label in enumerate(pattern_order)
        }
    )
    .fillna(999)
)

pattern_summary = (
    pattern_summary
    .sort_values("sort_order")
    .drop(columns=["sort_order"])
)


if not pattern_summary.empty:

    fig_tree = px.treemap(
        pattern_summary,
        path=["Capital Allocation"],
        values="Companies",
        color="Capital Allocation",
        hover_data={
            "Companies": True,
        },
    )

    fig_tree.update_traces(
        textinfo="label+value",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Companies=%{value}<extra></extra>"
        ),
    )

    fig_tree.update_layout(
        title=f"Capital Allocation Patterns — {selected_year}",
        height=520,
        margin=dict(
            l=10,
            r=10,
            t=60,
            b=10,
        ),
    )

    st.plotly_chart(
        fig_tree,
        use_container_width=True,
    )


# ============================================================
# CAPITAL ALLOCATION PATTERN TABLE
# ============================================================

st.subheader("📊 Capital Allocation Patterns")

pattern_table = (
    capital_df
    .groupby(
        [
            "Capital Allocation",
            "Cash Flow Pattern",
        ],
        dropna=False,
    )
    .agg(
        Companies=("company_id", "nunique"),
        Total_CFO=("operating_activity", "sum"),
        Total_CFI=("investing_activity", "sum"),
        Total_CFF=("financing_activity", "sum"),
        Total_FCF=("FCF (₹ Cr)", "sum"),
    )
    .reset_index()
)

pattern_table["sort_order"] = (
    pattern_table["Capital Allocation"]
    .map(
        {
            label: index
            for index, label in enumerate(pattern_order)
        }
    )
    .fillna(999)
)

pattern_table = (
    pattern_table
    .sort_values("sort_order")
    .drop(columns=["sort_order"])
)


pattern_display = pattern_table.rename(
    columns={
        "Capital Allocation": "Capital Allocation",
        "Cash Flow Pattern": "Pattern",
        "Companies": "Companies",
        "Total_CFO": "Total CFO (₹ Cr)",
        "Total_CFI": "Total CFI (₹ Cr)",
        "Total_CFF": "Total CFF (₹ Cr)",
        "Total_FCF": "Total FCF (₹ Cr)",
    }
)


st.dataframe(
    pattern_display,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Companies": st.column_config.NumberColumn(
            format="%d",
        ),
        "Total CFO (₹ Cr)": st.column_config.NumberColumn(
            format="%,.0f",
        ),
        "Total CFI (₹ Cr)": st.column_config.NumberColumn(
            format="%,.0f",
        ),
        "Total CFF (₹ Cr)": st.column_config.NumberColumn(
            format="%,.0f",
        ),
        "Total FCF (₹ Cr)": st.column_config.NumberColumn(
            format="%,.0f",
        ),
    },
)


# ============================================================
# COMPANY DRILL-DOWN
# ============================================================

st.divider()

st.subheader("🏢 Company Drill-Down")

drill_options = [
    "All Patterns"
] + [
    label
    for label in pattern_order
    if label in capital_df["Capital Allocation"].unique()
]

selected_pattern = st.selectbox(
    "Select Capital Allocation Pattern",
    drill_options,
)


drill_df = capital_df.copy()

if selected_pattern != "All Patterns":
    drill_df = drill_df[
        drill_df["Capital Allocation"]
        == selected_pattern
    ].copy()


drill_df = drill_df.sort_values(
    ["Capital Allocation", "company_name"]
)


drill_display = drill_df[
    [
        "company_id",
        "company_name",
        "broad_sector",
        "sub_sector",
        "Cash Flow Pattern",
        "Capital Allocation",
        "operating_activity",
        "investing_activity",
        "financing_activity",
        "FCF (₹ Cr)",
    ]
].rename(
    columns={
        "company_id": "Symbol",
        "company_name": "Company",
        "broad_sector": "Sector",
        "sub_sector": "Sub Sector",
        "Cash Flow Pattern": "Cash Flow Pattern",
        "Capital Allocation": "Capital Allocation",
        "operating_activity": "CFO (₹ Cr)",
        "investing_activity": "CFI (₹ Cr)",
        "financing_activity": "CFF (₹ Cr)",
    }
)


st.dataframe(
    drill_display,
    use_container_width=True,
    hide_index=True,
    height=480,
    column_config={
        "CFO (₹ Cr)": st.column_config.NumberColumn(
            format="%,.0f",
        ),
        "CFI (₹ Cr)": st.column_config.NumberColumn(
            format="%,.0f",
        ),
        "CFF (₹ Cr)": st.column_config.NumberColumn(
            format="%,.0f",
        ),
        "FCF (₹ Cr)": st.column_config.NumberColumn(
            format="%,.0f",
        ),
    },
)


# ============================================================
# CASH FLOW COMPONENTS
# ============================================================

st.divider()

st.subheader("💵 Cash Flow Components")

st.caption(
    f"CFO vs CFI vs CFF — {selected_year}"
)


chart_df = capital_df[
    [
        "company_id",
        "company_name",
        "operating_activity",
        "investing_activity",
        "financing_activity",
    ]
].copy()


# Use ticker on the X-axis to prevent 99 long company names
# from overlapping. Full company name is retained in hover.
chart_df = chart_df.sort_values(
    "company_id"
)


chart_long = chart_df.melt(
    id_vars=[
        "company_id",
        "company_name",
    ],
    value_vars=[
        "operating_activity",
        "investing_activity",
        "financing_activity",
    ],
    var_name="Cash Flow Type",
    value_name="Cash Flow (₹ Cr)",
)


chart_long["Cash Flow Type"] = (
    chart_long["Cash Flow Type"]
    .replace(
        {
            "operating_activity": "CFO",
            "investing_activity": "CFI",
            "financing_activity": "CFF",
        }
    )
)


fig_cash = px.bar(
    chart_long,
    x="company_id",
    y="Cash Flow (₹ Cr)",
    color="Cash Flow Type",
    barmode="group",
    hover_data={
        "company_name": True,
        "company_id": True,
        "Cash Flow (₹ Cr)": ":,.0f",
        "Cash Flow Type": True,
    },
    labels={
        "company_id": "Company",
        "Cash Flow (₹ Cr)": "Cash Flow (₹ Cr)",
        "Cash Flow Type": "Cash Flow Type",
    },
)


fig_cash.update_layout(
    height=560,
    bargap=0.18,
    xaxis=dict(
        tickangle=-45,
        type="category",
        automargin=True,
    ),
    yaxis=dict(
        zeroline=True,
        title="Cash Flow (₹ Cr)",
    ),
    legend_title="Cash Flow Type",
    margin=dict(
        l=20,
        r=20,
        t=30,
        b=100,
    ),
)


st.plotly_chart(
    fig_cash,
    use_container_width=True,
)


# ============================================================
# DISTRESS SIGNALS
# ============================================================

st.divider()

st.subheader("🚨 Distress Signals")

st.caption(
    "A distress signal is flagged when operating cash flow "
    "is negative while financing cash flow is positive."
)


distress_df = capital_df[
    capital_df["Distress Signal"]
].copy()


if distress_df.empty:

    st.success(
        "No distress signals found for the selected "
        "financial year and sector."
    )

else:

    distress_display = distress_df[
        [
            "company_id",
            "company_name",
            "broad_sector",
            "sub_sector",
            "operating_activity",
            "investing_activity",
            "financing_activity",
            "FCF (₹ Cr)",
        ]
    ].rename(
        columns={
            "company_id": "Symbol",
            "company_name": "Company",
            "broad_sector": "Sector",
            "sub_sector": "Sub Sector",
            "operating_activity": "CFO (₹ Cr)",
            "investing_activity": "CFI (₹ Cr)",
            "financing_activity": "CFF (₹ Cr)",
        }
    )

    distress_display = distress_display.sort_values(
        "CFO (₹ Cr)"
    )

    st.dataframe(
        distress_display,
        use_container_width=True,
        hide_index=True,
        height=430,
        column_config={
            "CFO (₹ Cr)": st.column_config.NumberColumn(
                format="%,.0f",
            ),
            "CFI (₹ Cr)": st.column_config.NumberColumn(
                format="%,.0f",
            ),
            "CFF (₹ Cr)": st.column_config.NumberColumn(
                format="%,.0f",
            ),
            "FCF (₹ Cr)": st.column_config.NumberColumn(
                format="%,.0f",
            ),
        },
    )


# ============================================================
# DOWNLOAD
# ============================================================

st.divider()

download_columns = [
    "company_id",
    "company_name",
    "broad_sector",
    "sub_sector",
    "Cash Flow Pattern",
    "Capital Allocation",
    "operating_activity",
    "investing_activity",
    "financing_activity",
    "FCF (₹ Cr)",
    "Distress Signal",
]

download_df = capital_df[
    download_columns
].copy()

download_df = download_df.rename(
    columns={
        "company_id": "Symbol",
        "company_name": "Company",
        "broad_sector": "Sector",
        "sub_sector": "Sub Sector",
        "operating_activity": "CFO (₹ Cr)",
        "investing_activity": "CFI (₹ Cr)",
        "financing_activity": "CFF (₹ Cr)",
    }
)

csv_data = download_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇️ Download Capital Allocation CSV",
    data=csv_data,
    file_name=(
        f"capital_allocation_{selected_year}"
        + (
            f"_{selected_sector.lower().replace(' ', '_')}"
            if selected_sector != "All Sectors"
            else ""
        )
        + ".csv"
    ),
    mime="text/csv",
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Data source: Nifty 100 financial database "
    "(`n100_financial.db`)."
)
