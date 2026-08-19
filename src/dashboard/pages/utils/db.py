import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st


# Project root:
# n100-financial-platform/
BASE_DIR = Path(__file__).resolve().parents[4]

DB_PATH = BASE_DIR / "db" / "n100_financial.db"


def get_connection():
    """Create a connection to the N100 SQLite database."""
    return sqlite3.connect(DB_PATH)


@st.cache_data(ttl=600)
def run_query(query, params=()):
    """Run a SQL query and return the result as a DataFrame."""
    conn = get_connection()

    try:
        return pd.read_sql_query(query, conn, params=params)
    finally:
        conn.close()


@st.cache_data(ttl=600)
def get_companies():
    """Return all companies."""
    query = """
        SELECT *
        FROM companies
        ORDER BY company_name
    """
    return run_query(query)


@st.cache_data(ttl=600)
def get_ratios(ticker, year=None):
    """Return financial ratios for a company."""
    query = """
        SELECT
            fr.*,
            c.company_name
        FROM financial_ratios fr
        JOIN companies c
            ON fr.company_id = c.company_id
        WHERE c.nse_ticker = ?
    """

    params = [ticker]

    if year is not None:
        query += " AND fr.year = ?"
        params.append(year)

    query += " ORDER BY fr.year DESC"

    return run_query(query, tuple(params))


@st.cache_data(ttl=600)
def get_pl(ticker):
    """Return profit and loss data for a company."""
    query = """
        SELECT
            pl.*,
            c.company_name
        FROM profitandloss pl
        JOIN companies c
            ON pl.company_id = c.company_id
        WHERE c.nse_ticker = ?
        ORDER BY pl.year DESC
    """

    return run_query(query, (ticker,))


@st.cache_data(ttl=600)
def get_bs(ticker):
    """Return balance sheet data for a company."""
    query = """
        SELECT
            bs.*,
            c.company_name
        FROM balancesheet bs
        JOIN companies c
            ON bs.company_id = c.company_id
        WHERE c.nse_ticker = ?
        ORDER BY bs.year DESC
    """

    return run_query(query, (ticker,))


@st.cache_data(ttl=600)
def get_cf(ticker):
    """Return cash flow data for a company."""
    query = """
        SELECT
            cf.*,
            c.company_name
        FROM cashflow cf
        JOIN companies c
            ON cf.company_id = c.company_id
        WHERE c.nse_ticker = ?
        ORDER BY cf.year DESC
    """

    return run_query(query, (ticker,))


@st.cache_data(ttl=600)
def get_sectors():
    """Return sector information for all companies."""
    query = """
        SELECT
            s.*,
            c.company_name,
            c.nse_ticker
        FROM sectors s
        JOIN companies c
            ON s.company_id = c.company_id
        ORDER BY s.broad_sector, c.company_name
    """

    return run_query(query)


@st.cache_data(ttl=600)
def get_peers(group_name):
    """Return companies belonging to a peer group."""
    query = """
        SELECT
            pg.*,
            c.company_name,
            c.nse_ticker
        FROM peer_groups pg
        JOIN companies c
            ON pg.company_id = c.company_id
        WHERE pg.peer_group_name = ?
        ORDER BY pg.is_benchmark DESC, c.company_name
    """

    return run_query(query, (group_name,))


@st.cache_data(ttl=600)
def get_valuation(ticker):
    """
    Return valuation-related data for a company.

    Uses market_cap and financial ratios tables.
    """
    query = """
        SELECT
            c.company_id,
            c.company_name,
            c.nse_ticker,
            mc.year,
            mc.market_cap_crore,
            mc.enterprise_value_crore,
            mc.pe_ratio,
            mc.pb_ratio,
            mc.ev_ebitda,
            mc.dividend_yield_pct
        FROM companies c
        LEFT JOIN market_cap mc
            ON c.company_id = mc.company_id
        WHERE c.nse_ticker = ?
        ORDER BY mc.year DESC
    """

    return run_query(query, (ticker,))