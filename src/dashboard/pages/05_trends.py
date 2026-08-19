# ============================================================
# 05_trends.py
# Nifty 100 Financial Analytics Platform
# Trend Analysis Dashboard
# ============================================================

import sqlite3
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Trends | Nifty 100 Analytics",
    page_icon="📈",
    layout="wide"
)


# ============================================================
# DATABASE
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DB_PATH = PROJECT_ROOT / "db" / "n100_financial.db"


def get_connection():
    return sqlite3.connect(str(DB_PATH))


# ============================================================
# DATA LOADING
# ============================================================

@st.cache_data
def load_companies():

    conn = get_connection()

    query = """
        SELECT
            id,
            company_name
        FROM companies
        ORDER BY company_name
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


@st.cache_data
def load_stock_prices():

    conn = get_connection()

    query = """
        SELECT
            company_id,
            date,
            open_price,
            high_price,
            low_price,
            close_price,
            volume,
            adjusted_close
        FROM stock_prices
        ORDER BY date
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")

    numeric_columns = [
        "open_price",
        "high_price",
        "low_price",
        "close_price",
        "volume",
        "adjusted_close"
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


@st.cache_data
def load_financial_ratios():

    conn = get_connection()

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

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


@st.cache_data
def load_market_cap():

    conn = get_connection()

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
        ORDER BY year
    """

    df = pd.read_sql_query(query, conn)

    conn.close()

    return df


@st.cache_data
def load_sectors():

    conn = get_connection()

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

    conn.close()

    return df


# ============================================================
# LOAD DATA
# ============================================================

try:

    companies_df = load_companies()
    stock_df = load_stock_prices()
    ratios_df = load_financial_ratios()
    market_df = load_market_cap()
    sectors_df = load_sectors()

except Exception as e:

    st.error("Unable to load dashboard data.")

    st.exception(e)

    st.stop()


# ============================================================
# VALIDATION
# ============================================================

if companies_df.empty:

    st.error("No company data found in the database.")

    st.stop()


# ============================================================
# PAGE HEADER
# ============================================================

st.title("📈 Trends")

st.caption(
    "Analyze historical stock performance, profitability, "
    "financial ratios and valuation trends across Nifty 100 companies."
)

st.divider()


# ============================================================
# SIDEBAR FILTERS
# ============================================================

st.sidebar.header("🔎 Trend Filters")


company_names = companies_df["company_name"].dropna().tolist()

default_company = "Abbott India Ltd"

if default_company in company_names:
    default_index = company_names.index(default_company)
else:
    default_index = 0


selected_company = st.sidebar.selectbox(
    "Select Company",
    company_names,
    index=default_index
)


selected_company_id = companies_df.loc[
    companies_df["company_name"] == selected_company,
    "id"
].iloc[0]


# ------------------------------------------------------------
# Convert ID to string because supporting tables use symbols
# ------------------------------------------------------------

selected_company_id = str(selected_company_id)


# ============================================================
# COMPANY INFORMATION
# ============================================================

company_sector = "Unknown"
company_sub_sector = "Unknown"
market_category = "Unknown"

sector_match = sectors_df[
    sectors_df["company_id"].astype(str).str.upper()
    == selected_company_id.upper()
]

if not sector_match.empty:

    company_sector = sector_match.iloc[0]["broad_sector"]

    company_sub_sector = sector_match.iloc[0]["sub_sector"]

    market_category = sector_match.iloc[0]["market_cap_category"]


# ============================================================
# SELECTED COMPANY HEADER
# ============================================================

st.subheader("🏢 Selected Company")

info_col1, info_col2, info_col3 = st.columns(3)

with info_col1:

    st.caption("Company")

    st.markdown(
        f"### {selected_company}"
    )

with info_col2:

    st.caption("Sector")

    st.markdown(
        f"### {company_sector}"
    )

with info_col3:

    st.caption("Market Category")

    st.markdown(
        f"### {market_category}"
    )


st.divider()


# ============================================================
# FILTER COMPANY DATA
# ============================================================

company_stock = stock_df[
    stock_df["company_id"].astype(str).str.upper()
    == selected_company_id.upper()
].copy()


company_ratios = ratios_df[
    ratios_df["company_id"].astype(str).str.upper()
    == selected_company_id.upper()
].copy()


company_market = market_df[
    market_df["company_id"].astype(str).str.upper()
    == selected_company_id.upper()
].copy()


# ============================================================
# NO DATA CHECK
# ============================================================

if company_stock.empty and company_ratios.empty and company_market.empty:

    st.warning(
        f"No historical trend data was found for {selected_company}."
    )

    st.stop()


# ============================================================
# KEY PERFORMANCE METRICS
# ============================================================

st.subheader("📊 Performance Summary")


metric1, metric2, metric3, metric4 = st.columns(4)


# ------------------------------------------------------------
# Latest Price
# ------------------------------------------------------------

latest_price = None

if not company_stock.empty:

    company_stock = company_stock.sort_values("date")

    latest_price = company_stock["close_price"].dropna().iloc[-1]


with metric1:

    st.metric(
        "Latest Price",
        f"₹{latest_price:,.2f}" if latest_price is not None else "N/A"
    )


# ------------------------------------------------------------
# Price Change
# ------------------------------------------------------------

price_change = None

if len(company_stock) >= 2:

    first_price = company_stock["close_price"].dropna().iloc[0]

    last_price = company_stock["close_price"].dropna().iloc[-1]

    if first_price != 0:

        price_change = (
            (last_price - first_price)
            / first_price
        ) * 100


with metric2:

    st.metric(
        "Historical Price Change",
        f"{price_change:+.2f}%"
        if price_change is not None
        else "N/A"
    )


# ------------------------------------------------------------
# Latest ROE
# ------------------------------------------------------------

latest_roe = None

if not company_ratios.empty:

    ratio_temp = company_ratios.copy()

    ratio_temp["year_sort"] = ratio_temp["year"].astype(str)

    ratio_temp = ratio_temp.sort_values("year_sort")

    roe_values = ratio_temp[
        "return_on_equity_pct"
    ].dropna()

    if not roe_values.empty:

        latest_roe = roe_values.iloc[-1]


with metric3:

    st.metric(
        "Latest ROE",
        f"{latest_roe:.2f}%"
        if latest_roe is not None
        else "N/A"
    )


# ------------------------------------------------------------
# Latest Market Cap
# ------------------------------------------------------------

latest_market_cap = None

if not company_market.empty:

    market_temp = company_market.sort_values("year")

    market_values = market_temp[
        "market_cap_crore"
    ].dropna()

    if not market_values.empty:

        latest_market_cap = market_values.iloc[-1]


with metric4:

    st.metric(
        "Latest Market Cap",
        f"₹{latest_market_cap:,.0f} Cr"
        if latest_market_cap is not None
        else "N/A"
    )


st.divider()


# ============================================================
# TREND ANALYSIS
# ============================================================
st.subheader("📊 Trend Analysis")

trend_source = pd.DataFrame()
trend_metric_options = {}

if not company_ratios.empty:
    trend_metric_options.update({
        "Net Profit Margin %": "net_profit_margin_pct",
        "Operating Profit Margin %": "operating_profit_margin_pct",
        "ROE %": "return_on_equity_pct",
        "Debt / Equity": "debt_to_equity",
        "Interest Coverage": "interest_coverage",
        "Asset Turnover": "asset_turnover",
        "EPS": "earnings_per_share",
        "Book Value / Share": "book_value_per_share",
    })

if not company_market.empty:
    trend_metric_options.update({
        "P/E Ratio": "pe_ratio",
        "P/B Ratio": "pb_ratio",
        "EV / EBITDA": "ev_ebitda",
        "Dividend Yield %": "dividend_yield_pct",
        "Market Cap (₹ Cr)": "market_cap_crore",
    })

if trend_metric_options:
    trend_col1, trend_col2, trend_col3 = st.columns([1.2, 1.8, 1])

    with trend_col1:
        selected_trend_metric = st.selectbox(
            "Select Metric",
            list(trend_metric_options.keys()),
            key="trend_metric"
        )

    with trend_col2:
        overlay_options = [m for m in trend_metric_options if m != selected_trend_metric]
        selected_overlays = st.multiselect(
            "Compare With (optional)",
            overlay_options,
            default=[],
            key="trend_overlay"
        )

    with trend_col3:
        trend_years = st.selectbox(
            "Trend Period",
            [5, 10],
            index=1,
            format_func=lambda x: f"Last {x} Years",
            key="trend_years"
        )

    # Build a common year-based dataframe from ratios and market data.
    ratio_trend = company_ratios.copy()
    market_trend = company_market.copy()

    ratio_trend["year"] = pd.to_numeric(ratio_trend["year"], errors="coerce")
    market_trend["year"] = pd.to_numeric(market_trend["year"], errors="coerce")

    metric_frames = []
    ratio_metrics = {v: k for k, v in trend_metric_options.items() if v in ratio_trend.columns}
    market_metrics = {v: k for k, v in trend_metric_options.items() if v in market_trend.columns}

    if ratio_metrics:
        r = ratio_trend[["year"] + list(ratio_metrics.keys())].copy()
        r = r.melt(id_vars="year", var_name="metric_key", value_name="value")
        r["Metric"] = r["metric_key"].map(ratio_metrics)
        metric_frames.append(r[["year", "Metric", "value"]])

    if market_metrics:
        m = market_trend[["year"] + list(market_metrics.keys())].copy()
        m = m.melt(id_vars="year", var_name="metric_key", value_name="value")
        m["Metric"] = m["metric_key"].map(market_metrics)
        metric_frames.append(m[["year", "Metric", "value"]])

    if metric_frames:
        trend_data = pd.concat(metric_frames, ignore_index=True)
        trend_data["value"] = pd.to_numeric(trend_data["value"], errors="coerce")
        trend_data = trend_data.dropna(subset=["year", "value", "Metric"])
        trend_data = trend_data[trend_data["Metric"].isin([selected_trend_metric] + selected_overlays)]
        trend_data = trend_data.sort_values(["Metric", "year"])

        if not trend_data.empty:
            available_years = sorted(trend_data["year"].dropna().unique())
            if available_years:
                cutoff_year = available_years[-1] - trend_years + 1
                trend_data = trend_data[trend_data["year"] >= cutoff_year]

            trend_data["year_label"] = trend_data["year"].astype(int).astype(str)

            fig_trend = px.line(
                trend_data,
                x="year_label",
                y="value",
                color="Metric",
                markers=True,
                title=f"{selected_company} - {selected_trend_metric} Trend",
                labels={
                    "year_label": "Year",
                    "value": selected_trend_metric
                }
            )

            fig_trend.update_layout(
                height=500,
                hovermode="x unified",
                legend_title="Metric"
            )

            st.plotly_chart(fig_trend, use_container_width=True)

            # YoY change for the selected primary metric.
            primary = trend_data[trend_data["Metric"] == selected_trend_metric].copy()
            primary = primary.sort_values("year")
            if len(primary) >= 2:
                primary["YoY %"] = primary["value"].pct_change() * 100
                latest_yoy = primary["YoY %"].dropna().iloc[-1] if not primary["YoY %"].dropna().empty else None
                if latest_yoy is not None:
                    st.caption(f"Latest YoY change in {selected_trend_metric}: {latest_yoy:+.2f}%")
        else:
            st.info("No trend data is available for the selected metric.")
else:
    st.info("No trend metrics are available for this company.")

st.divider()

# ============================================================
# STOCK PRICE TREND
# ============================================================

st.subheader("📈 Stock Price Trend")


if company_stock.empty:

    st.info("No stock price data available.")

else:

    price_data = company_stock[
        [
            "date",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "adjusted_close"
        ]
    ].copy()

    price_data = price_data.dropna(
        subset=["date"]
    )

    price_data = price_data.sort_values("date")

    fig_price = px.line(
        price_data,
        x="date",
        y="close_price",
        markers=True,
        title=f"{selected_company} - Historical Closing Price",
        labels={
            "date": "Date",
            "close_price": "Closing Price (₹)"
        }
    )

    fig_price.update_layout(
        height=500,
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title="Closing Price (₹)"
    )

    st.plotly_chart(
        fig_price,
        use_container_width=True
    )


# ============================================================
# PRICE RANGE / OHLC
# ============================================================

if not company_stock.empty:

    st.subheader("📊 Price Range")

    ohlc_data = company_stock[
        [
            "date",
            "open_price",
            "high_price",
            "low_price",
            "close_price"
        ]
    ].dropna(
        subset=["date"]
    )

    if not ohlc_data.empty:

        fig_ohlc = px.line(
            ohlc_data,
            x="date",
            y=[
                "open_price",
                "high_price",
                "low_price",
                "close_price"
            ],
            title=f"{selected_company} - OHLC Trend",
            labels={
                "date": "Date",
                "value": "Price (₹)",
                "variable": "Price Type"
            }
        )

        fig_ohlc.update_layout(
            height=450,
            hovermode="x unified"
        )

        st.plotly_chart(
            fig_ohlc,
            use_container_width=True
        )


st.divider()


# ============================================================
# PROFITABILITY TRENDS
# ============================================================

st.subheader("💰 Profitability Trends")


if company_ratios.empty:

    st.info("No financial ratio data available.")

else:

    profitability = company_ratios[
        [
            "year",
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct"
        ]
    ].copy()

    profitability["year"] = profitability["year"].astype(str)

    profitability_long = profitability.melt(
        id_vars=["year"],
        value_vars=[
            "net_profit_margin_pct",
            "operating_profit_margin_pct",
            "return_on_equity_pct"
        ],
        var_name="Metric",
        value_name="Value"
    )

    metric_names = {
        "net_profit_margin_pct": "Net Profit Margin %",
        "operating_profit_margin_pct": "Operating Profit Margin %",
        "return_on_equity_pct": "ROE %"
    }

    profitability_long["Metric"] = (
        profitability_long["Metric"]
        .map(metric_names)
    )

    profitability_long = profitability_long.dropna(
        subset=["Value"]
    )

    fig_profitability = px.line(
        profitability_long,
        x="year",
        y="Value",
        color="Metric",
        markers=True,
        title=f"{selected_company} - Profitability Trends",
        labels={
            "year": "Year",
            "Value": "Percentage (%)"
        }
    )

    fig_profitability.update_layout(
        height=500,
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_profitability,
        use_container_width=True
    )


# ============================================================
# FINANCIAL HEALTH TRENDS
# ============================================================
st.subheader("🏦 Financial Health")

if not company_ratios.empty:
    health_data = company_ratios[
        [
            "year",
            "debt_to_equity",
            "interest_coverage",
            "asset_turnover"
        ]
    ].copy()

    health_data["year"] = pd.to_numeric(health_data["year"], errors="coerce")
    health_data = health_data.sort_values("year")

    if not health_data.dropna(how="all", subset=["debt_to_equity", "interest_coverage", "asset_turnover"]).empty:
        fig_health = go.Figure()

        fig_health.add_trace(go.Scatter(
            x=health_data["year"],
            y=health_data["debt_to_equity"],
            name="Debt / Equity",
            mode="lines+markers",
            yaxis="y"
        ))

        fig_health.add_trace(go.Scatter(
            x=health_data["year"],
            y=health_data["interest_coverage"],
            name="Interest Coverage",
            mode="lines+markers",
            yaxis="y2"
        ))

        fig_health.add_trace(go.Scatter(
            x=health_data["year"],
            y=health_data["asset_turnover"],
            name="Asset Turnover",
            mode="lines+markers",
            yaxis="y2"
        ))

        fig_health.update_layout(
            title=f"{selected_company} - Financial Health Trends",
            height=500,
            hovermode="x unified",
            xaxis_title="Year",
            yaxis=dict(title="Debt / Equity"),
            yaxis2=dict(
                title="Interest Coverage / Asset Turnover",
                overlaying="y",
                side="right"
            ),
            legend_title="Metric"
        )

        st.plotly_chart(fig_health, use_container_width=True)
    else:
        st.info("No financial health trend data available.")


st.divider()

# ============================================================
# EPS & BOOK VALUE
# ============================================================
st.subheader("📚 EPS & Book Value Trends")

if not company_ratios.empty:
    eps_data = company_ratios[
        [
            "year",
            "earnings_per_share",
            "book_value_per_share"
        ]
    ].copy()

    eps_data["year"] = pd.to_numeric(eps_data["year"], errors="coerce")
    eps_data = eps_data.sort_values("year")

    if not eps_data.dropna(how="all", subset=["earnings_per_share", "book_value_per_share"]).empty:
        fig_eps = go.Figure()

        fig_eps.add_trace(go.Scatter(
            x=eps_data["year"],
            y=eps_data["earnings_per_share"],
            name="EPS",
            mode="lines+markers",
            yaxis="y"
        ))

        fig_eps.add_trace(go.Scatter(
            x=eps_data["year"],
            y=eps_data["book_value_per_share"],
            name="Book Value / Share",
            mode="lines+markers",
            yaxis="y2"
        ))

        fig_eps.update_layout(
            title=f"{selected_company} - EPS & Book Value",
            height=450,
            hovermode="x unified",
            xaxis_title="Year",
            yaxis=dict(title="EPS (₹)"),
            yaxis2=dict(
                title="Book Value / Share (₹)",
                overlaying="y",
                side="right"
            ),
            legend_title="Metric"
        )

        st.plotly_chart(fig_eps, use_container_width=True)
    else:
        st.info("No EPS or book value data available.")


# ============================================================
# MARKET CAP & VALUATION
# ============================================================

st.subheader("💹 Market Cap & Valuation")


if company_market.empty:

    st.info("No market valuation data available.")

else:

    valuation_data = company_market[
        [
            "year",
            "market_cap_crore",
            "enterprise_value_crore",
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda",
            "dividend_yield_pct"
        ]
    ].copy()

    valuation_data = valuation_data.sort_values("year")


    # --------------------------------------------------------
    # Market Cap
    # --------------------------------------------------------

    fig_market_cap = px.line(
        valuation_data,
        x="year",
        y="market_cap_crore",
        markers=True,
        title=f"{selected_company} - Market Capitalization",
        labels={
            "year": "Year",
            "market_cap_crore": "Market Cap (₹ Cr)"
        }
    )

    fig_market_cap.update_layout(
        height=450,
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_market_cap,
        use_container_width=True
    )


    # --------------------------------------------------------
    # Valuation Multiples
    # --------------------------------------------------------

    valuation_long = valuation_data.melt(
        id_vars=["year"],
        value_vars=[
            "pe_ratio",
            "pb_ratio",
            "ev_ebitda"
        ],
        var_name="Metric",
        value_name="Value"
    )

    valuation_names = {
        "pe_ratio": "P/E Ratio",
        "pb_ratio": "P/B Ratio",
        "ev_ebitda": "EV / EBITDA"
    }

    valuation_long["Metric"] = (
        valuation_long["Metric"]
        .map(valuation_names)
    )

    valuation_long = valuation_long.dropna(
        subset=["Value"]
    )

    fig_valuation = px.line(
        valuation_long,
        x="year",
        y="Value",
        color="Metric",
        markers=True,
        title=f"{selected_company} - Valuation Multiples",
        labels={
            "year": "Year",
            "Value": "Multiple"
        }
    )

    fig_valuation.update_layout(
        height=450,
        hovermode="x unified"
    )

    st.plotly_chart(
        fig_valuation,
        use_container_width=True
    )


st.divider()


# ============================================================
# TRADING VOLUME
# ============================================================

st.subheader("📦 Trading Volume")


if company_stock.empty:

    st.info("No trading volume data available.")

else:

    volume_data = company_stock[
        [
            "date",
            "volume"
        ]
    ].dropna(
        subset=["date", "volume"]
    )

    if not volume_data.empty:

        fig_volume = px.bar(
            volume_data,
            x="date",
            y="volume",
            title=f"{selected_company} - Trading Volume",
            labels={
                "date": "Date",
                "volume": "Volume"
            }
        )

        fig_volume.update_layout(
            height=400,
            xaxis_title="Date",
            yaxis_title="Trading Volume"
        )

        st.plotly_chart(
            fig_volume,
            use_container_width=True
        )


# ============================================================
# RAW TREND DATA
# ============================================================

st.divider()

st.subheader("📋 Historical Data")

data_tab1, data_tab2, data_tab3 = st.tabs(
    [
        "Stock Prices",
        "Financial Ratios",
        "Market Data"
    ]
)


with data_tab1:

    if company_stock.empty:

        st.info("No stock price data available.")

    else:

        display_stock = company_stock.copy()

        display_stock["date"] = (
            display_stock["date"]
            .dt.strftime("%Y-%m-%d")
        )

        st.dataframe(
            display_stock,
            use_container_width=True,
            hide_index=True
        )


with data_tab2:

    if company_ratios.empty:

        st.info("No financial ratio data available.")

    else:

        st.dataframe(
            company_ratios,
            use_container_width=True,
            hide_index=True
        )


with data_tab3:

    if company_market.empty:

        st.info("No market data available.")

    else:

        st.dataframe(
            company_market,
            use_container_width=True,
            hide_index=True
        )


# ============================================================
# DOWNLOAD
# ============================================================

st.divider()

st.subheader("⬇️ Download Trend Data")


download_col1, download_col2, download_col3 = st.columns(3)


with download_col1:

    if not company_stock.empty:

        csv_stock = company_stock.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Stock Data",
            data=csv_stock,
            file_name=f"{selected_company}_stock_prices.csv",
            mime="text/csv"
        )


with download_col2:

    if not company_ratios.empty:

        csv_ratios = company_ratios.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Financial Data",
            data=csv_ratios,
            file_name=f"{selected_company}_financial_ratios.csv",
            mime="text/csv"
        )


with download_col3:

    if not company_market.empty:

        csv_market = company_market.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Market Data",
            data=csv_market,
            file_name=f"{selected_company}_market_data.csv",
            mime="text/csv"
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Nifty 100 Financial Analytics Platform • Trend Analysis"
)