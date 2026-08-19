# ============================================================
# 08_reports.py
# Nifty 100 Financial Analytics Platform
# Annual Reports
# ============================================================

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Annual Reports | Nifty 100",
    page_icon="📄",
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


if conn is None:

    st.error(
        "Database not found.\n\n"
        "Expected database: n100_financial.db"
    )

    st.stop()


# ============================================================
# HELPER — FIND COLUMN CASE-INSENSITIVELY
# ============================================================

def find_column(df, candidates):

    """
    Find a column regardless of capitalization,
    spaces or underscores.
    """

    normalized = {
        str(col)
        .strip()
        .lower()
        .replace(" ", "")
        .replace("_", ""): col
        for col in df.columns
    }

    for candidate in candidates:

        key = (
            candidate
            .strip()
            .lower()
            .replace(" ", "")
            .replace("_", "")
        )

        if key in normalized:
            return normalized[key]

    return None


# ============================================================
# LOAD COMPANIES
# ============================================================

@st.cache_data
def load_companies():

    df = pd.read_sql_query(
        "SELECT * FROM companies",
        conn,
    )

    if df.empty:
        return df

    id_col = find_column(
        df,
        [
            "id",
            "company_id",
            "symbol",
            "code",
        ],
    )

    name_col = find_column(
        df,
        [
            "company_name",
            "companyname",
            "name",
        ],
    )

    if id_col is None:
        raise ValueError(
            "Could not find the company ID column "
            "in the companies table."
        )

    if name_col is None:
        raise ValueError(
            "Could not find the company name column "
            "in the companies table."
        )

    result = df[
        [id_col, name_col]
    ].copy()

    result.columns = [
        "company_id",
        "company_name",
    ]

    result["company_id"] = (
        result["company_id"]
        .astype(str)
        .str.strip()
    )

    result["company_name"] = (
        result["company_name"]
        .astype(str)
        .str.strip()
    )

    return result.drop_duplicates(
        subset=["company_id"]
    )


# ============================================================
# LOAD DOCUMENTS
# ============================================================

@st.cache_data
def load_documents():

    # IMPORTANT:
    # Do NOT select Year directly.
    # We load the whole table and detect the
    # real column names dynamically.

    df = pd.read_sql_query(
        "SELECT * FROM documents",
        conn,
    )

    if df.empty:
        return df

    # --------------------------------------------------------
    # Detect columns
    # --------------------------------------------------------

    company_col = find_column(
        df,
        [
            "company_id",
            "companyid",
            "company",
            "id",
            "symbol",
        ],
    )

    year_col = find_column(
        df,
        [
            "year",
            "financial_year",
            "financialyear",
            "fy",
        ],
    )

    report_col = find_column(
        df,
        [
            "annual_report",
            "annualreport",
            "report",
            "report_url",
            "reporturl",
        ],
    )

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    if company_col is None:

        raise ValueError(
            "Could not find company ID column "
            "in documents table.\n\n"
            f"Available columns: {list(df.columns)}"
        )

    if year_col is None:

        raise ValueError(
            "Could not find year column "
            "in documents table.\n\n"
            f"Available columns: {list(df.columns)}"
        )

    if report_col is None:

        raise ValueError(
            "Could not find annual report column "
            "in documents table.\n\n"
            f"Available columns: {list(df.columns)}"
        )

    # --------------------------------------------------------
    # Standardize names
    # --------------------------------------------------------

    result = df[
        [
            company_col,
            year_col,
            report_col,
        ]
    ].copy()

    result.columns = [
        "company_id",
        "Year",
        "Annual_Report",
    ]

    # --------------------------------------------------------
    # Clean company ID
    # --------------------------------------------------------

    result["company_id"] = (
        result["company_id"]
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Clean year
    # --------------------------------------------------------

    result["Year"] = pd.to_numeric(
        result["Year"],
        errors="coerce",
    )

    result = result.dropna(
        subset=["Year"]
    ).copy()

    result["Year"] = (
        result["Year"]
        .astype(int)
    )

    # --------------------------------------------------------
    # Clean URLs
    # --------------------------------------------------------

    result["Annual_Report"] = (
        result["Annual_Report"]
        .fillna("")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # Remove duplicates
    # --------------------------------------------------------

    result = result.drop_duplicates(
        subset=[
            "company_id",
            "Year",
            "Annual_Report",
        ]
    )

    return result


# ============================================================
# LOAD DATA
# ============================================================

try:

    companies_df = load_companies()
    documents_df = load_documents()

except Exception as e:

    st.error(
        "Unable to load Annual Reports data."
    )

    st.exception(e)

    st.stop()


# ============================================================
# EMPTY DATA CHECK
# ============================================================

if companies_df.empty:

    st.warning(
        "No companies were found in the database."
    )

    st.stop()


if documents_df.empty:

    st.warning(
        "No annual reports were found "
        "in the documents table."
    )

    st.stop()


# ============================================================
# MERGE COMPANY INFORMATION
# ============================================================

# Keep only reports whose company_id exists in the companies table.
# This prevents orphan document IDs from creating invalid company counts
# and keeps all downstream metrics/filters internally consistent.
reports_df = documents_df.merge(
    companies_df,
    on="company_id",
    how="inner",
)


# ============================================================
# PAGE HEADER
# ============================================================

st.title("📄 Annual Reports")

st.caption(
    "Access annual reports of Nifty 100 companies "
    "through the available BSE India PDF links."
)

st.divider()


# ============================================================
# SUMMARY METRICS
# ============================================================

total_companies = (
    companies_df["company_id"]
    .nunique()
)

companies_with_reports = (
    reports_df.loc[
        reports_df["Annual_Report"].ne(""),
        "company_id",
    ]
    .nunique()
)

total_reports = (
    reports_df["Annual_Report"]
    .ne("")
    .sum()
)

latest_year = (
    int(reports_df["Year"].max())
    if not reports_df.empty
    else None
)


m1, m2, m3, m4 = st.columns(4)


with m1:

    st.metric(
        "Companies",
        f"{total_companies:,}",
    )


with m2:

    st.metric(
        "Companies With Reports",
        f"{companies_with_reports:,}",
    )


with m3:

    st.metric(
        "Report Links",
        f"{total_reports:,}",
    )


with m4:

    st.metric(
        "Latest Year",
        str(latest_year)
        if latest_year
        else "N/A",
    )


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.header("🔎 Report Filters")


# ============================================================
# COMPANY FILTER
# ============================================================

company_options = (
    companies_df[
        [
            "company_id",
            "company_name",
        ]
    ]
    .drop_duplicates()
    .sort_values("company_name")
)


company_names = (
    company_options["company_name"]
    .tolist()
)


selected_company = st.sidebar.selectbox(
    "Select Company",
    company_names,
)


selected_company_id = (
    company_options.loc[
        company_options["company_name"]
        == selected_company,
        "company_id",
    ]
    .iloc[0]
)


# ============================================================
# YEAR FILTER
# ============================================================

year_options = sorted(
    reports_df["Year"]
    .dropna()
    .unique()
    .tolist(),
    reverse=True,
)


year_choices = ["All Years"] + [
    str(year)
    for year in year_options
]


selected_year = st.sidebar.selectbox(
    "Select Financial Year",
    year_choices,
)


# ============================================================
# FILTER COMPANY DATA
# ============================================================

company_reports = reports_df[
    reports_df["company_id"]
    == selected_company_id
].copy()


# ============================================================
# COMPANY HEADER
# ============================================================

st.subheader("🏢 Company")


c1, c2, c3 = st.columns(3)


with c1:

    st.caption("Company")

    st.markdown(
        f"### {selected_company}"
    )


with c2:

    available_count = (
        company_reports[
            "Annual_Report"
        ]
        .ne("")
        .sum()
    )

    st.caption("Reports Available")

    st.markdown(
        f"### {available_count}"
    )


with c3:

    if not company_reports.empty:

        first_year = int(
            company_reports["Year"].min()
        )

        last_year = int(
            company_reports["Year"].max()
        )

        st.caption("Report Range")

        st.markdown(
            f"### {first_year} – {last_year}"
        )

    else:

        st.caption("Report Range")

        st.markdown("### N/A")


# ============================================================
# SELECTED YEAR REPORT
# ============================================================

if selected_year != "All Years":

    selected_year_value = int(
        selected_year
    )

    selected_report = company_reports[
        company_reports["Year"]
        == selected_year_value
    ].copy()

    st.divider()

    st.subheader(
        f"📑 Annual Report — {selected_year}"
    )

    valid_reports = selected_report[
        selected_report["Annual_Report"]
        .ne("")
    ]

    if not valid_reports.empty:

        report_url = (
            valid_reports.iloc[0]
            ["Annual_Report"]
        )

        st.success(
            f"Annual report for "
            f"{selected_company} "
            f"({selected_year}) is available."
        )

        st.link_button(
            "📄 Open Annual Report (BSE PDF)",
            report_url,
        )

    else:

        st.warning(
            f"Annual report for "
            f"{selected_company} "
            f"({selected_year}) "
            f"is not available in the database."
        )


# ============================================================
# REPORT REPOSITORY
# ============================================================

st.divider()

st.subheader(
    f"📚 Report Repository — {selected_company}"
)


display_df = company_reports.copy()


if selected_year != "All Years":

    display_df = display_df[
        display_df["Year"]
        == int(selected_year)
    ].copy()


display_df["Status"] = display_df[
    "Annual_Report"
].apply(
    lambda x:
    "Available"
    if str(x).strip()
    else "Missing"
)


display_df = display_df.sort_values(
    "Year",
    ascending=False,
)


if display_df.empty:

    st.info(
        "No report records found "
        "for the selected filter."
    )

else:

    table_df = display_df[
        [
            "Year",
            "Status",
            "Annual_Report",
        ]
    ].copy()

    table_df.columns = [
        "Financial Year",
        "Status",
        "Annual Report",
    ]

    st.dataframe(
        table_df,
        width="stretch",
        hide_index=True,
        column_config={

            "Financial Year":
                st.column_config.NumberColumn(
                    format="%d"
                ),

            "Status":
                st.column_config.TextColumn(
                    width="small"
                ),

            "Annual Report":
                st.column_config.LinkColumn(
                    "Annual Report",
                    display_text="Open PDF ↗",
                ),
        },
    )


# ============================================================
# REPORT COVERAGE
# ============================================================

st.divider()
st.subheader("📊 Report Coverage")

# Coverage is calculated only from valid companies that have a real
# annual-report URL for the given financial year.
coverage_source = reports_df[
    reports_df["Annual_Report"]
    .fillna("")
    .astype(str)
    .str.strip()
    .ne("")
].copy()

coverage_df = (
    coverage_source
    .dropna(subset=["Year", "company_id"])
    .groupby("Year")
    .agg(
        Reports=("Annual_Report", "count"),
        Companies=("company_id", "nunique"),
    )
    .reset_index()
)

coverage_df["Year"] = pd.to_numeric(
    coverage_df["Year"],
    errors="coerce",
)

coverage_df = coverage_df.dropna(
    subset=["Year"]
).copy()

coverage_df["Year"] = coverage_df["Year"].astype(int)

# Never allow the number of reporting companies to exceed the
# actual company universe in the companies table.
coverage_df["Companies"] = coverage_df["Companies"].clip(
    lower=0,
    upper=total_companies,
)

if total_companies > 0:
    coverage_df["Coverage (%)"] = (
        coverage_df["Companies"]
        / total_companies
        * 100
    )
else:
    coverage_df["Coverage (%)"] = 0.0

coverage_df["Coverage (%)"] = coverage_df["Coverage (%)"].clip(
    lower=0,
    upper=100,
)

coverage_df = coverage_df.sort_values(
    "Year",
    ascending=False,
)

coverage_df = coverage_df[
    [
        "Year",
        "Reports",
        "Companies",
        "Coverage (%)",
    ]
]

st.dataframe(
    coverage_df,
    width="stretch",
    hide_index=True,
    column_config={
        "Year": st.column_config.NumberColumn(
            format="%d",
        ),
        "Reports": st.column_config.NumberColumn(
            format="%d",
        ),
        "Companies": st.column_config.NumberColumn(
            format="%d",
        ),
        "Coverage (%)": st.column_config.NumberColumn(
            format="%.1f%%",
        ),
    },
)


# ============================================================
# DOWNLOAD
# ============================================================

st.divider()

st.subheader("⬇️ Export")


download_df = reports_df[
    [
        "company_id",
        "company_name",
        "Year",
        "Annual_Report",
    ]
].copy()


download_df.columns = [
    "Symbol",
    "Company",
    "Year",
    "Annual Report URL",
]


csv_data = download_df.to_csv(
    index=False
).encode("utf-8")


st.download_button(
    label="⬇️ Download Annual Reports CSV",
    data=csv_data,
    file_name="nifty100_annual_reports.csv",
    mime="text/csv",
)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Data source: Nifty 100 financial database. "
    "Annual report links are sourced from "
    "the BSE India annual-report repository."
)