import streamlit as st
import sqlite3
from pathlib import Path
import pandas as pd


# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------

st.set_page_config(
    page_title="Company Profile",
    page_icon="🏢",
    layout="wide"
)


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

DB_PATH = Path(__file__).resolve().parents[3] / "db" / "n100_financial.db"


@st.cache_data
def load_companies():

    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        "SELECT * FROM companies",
        conn
    )

    conn.close()

    return df


companies = load_companies()


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🏢 Company Profile")

st.markdown(
    "Explore detailed information about companies in the Nifty 100."
)

st.divider()


# --------------------------------------------------
# COMPANY SELECTOR
# --------------------------------------------------

company_names = companies["company_name"].dropna().tolist()

selected_company = st.selectbox(
    "Select a Company",
    company_names
)


# --------------------------------------------------
# SELECT COMPANY DATA
# --------------------------------------------------

company = companies[
    companies["company_name"] == selected_company
].iloc[0]


# --------------------------------------------------
# COMPANY HEADER
# --------------------------------------------------

col1, col2 = st.columns([1, 4])


with col1:

    if "company_logo" in companies.columns:

        logo = company["company_logo"]

        if pd.notna(logo) and str(logo).strip():

            try:
                st.image(
                    logo,
                    width=120
                )
            except Exception:
                st.write("🏢")

        else:
            st.write("🏢")

    else:
        st.write("🏢")


with col2:

    st.subheader(company["company_name"])

    if "about_company" in companies.columns:

        about = company["about_company"]

        if pd.notna(about):
            st.write(about)


st.divider()


# --------------------------------------------------
# COMPANY DETAILS
# --------------------------------------------------

st.subheader("📋 Company Details")


details_col1, details_col2, details_col3 = st.columns(3)


with details_col1:

    if "face_value" in companies.columns:

        value = company["face_value"]

        st.metric(
            "Face Value",
            f"₹{value:.2f}" if pd.notna(value) else "N/A"
        )


with details_col2:

    if "book_value" in companies.columns:

        value = company["book_value"]

        st.metric(
            "Book Value",
            f"₹{value:.2f}" if pd.notna(value) else "N/A"
        )


with details_col3:

    if "roce_percentage" in companies.columns:

        value = company["roce_percentage"]

        st.metric(
            "ROCE",
            f"{value:.2f}%" if pd.notna(value) else "N/A"
        )


# --------------------------------------------------
# ROE
# --------------------------------------------------

if "roe_percentage" in companies.columns:

    st.metric(
        "ROE",
        (
            f"{company['roe_percentage']:.2f}%"
            if pd.notna(company["roe_percentage"])
            else "N/A"
        )
    )


st.divider()


# --------------------------------------------------
# COMPANY LINKS
# --------------------------------------------------

st.subheader("🔗 Company Resources")

link_col1, link_col2, link_col3 = st.columns(3)


with link_col1:

    if "website" in companies.columns:

        website = company["website"]

        if pd.notna(website) and str(website).strip():

            st.link_button(
                "🌐 Company Website",
                website,
                width="stretch"
            )


with link_col2:

    if "nse_profile" in companies.columns:

        nse = company["nse_profile"]

        if pd.notna(nse) and str(nse).strip():

            st.link_button(
                "📈 NSE Profile",
                nse,
                width="stretch"
            )


with link_col3:

    if "bse_profile" in companies.columns:

        bse = company["bse_profile"]

        if pd.notna(bse) and str(bse).strip():

            st.link_button(
                "📊 BSE Profile",
                bse,
                width="stretch"
            )


# --------------------------------------------------
# MARKET INFORMATION
# --------------------------------------------------

st.divider()

st.subheader("📊 Additional Information")


available_columns = [
    "id",
    "company_name",
    "face_value",
    "book_value",
    "roce_percentage",
    "roe_percentage"
]


available_columns = [
    column
    for column in available_columns
    if column in companies.columns
]


if available_columns:

    profile_data = pd.DataFrame(
        {
            "Field": available_columns,
            "Value": [
                company[column]
                for column in available_columns
            ]
        }
    )

    st.dataframe(
        profile_data,
        width="stretch",
        hide_index=True
    )


# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.caption(
    "Nifty 100 Analytics • Company Intelligence"
)