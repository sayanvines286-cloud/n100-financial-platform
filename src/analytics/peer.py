from pathlib import Path
import pandas as pd
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "output"
REPORTS = ROOT / "reports" / "radar_charts"

OUTPUT.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)


# ============================================================
# COLUMN HELPERS
# ============================================================

def find_column(df, candidates):
    """Return the first matching column from a list of possible names."""
    lower_map = {str(c).strip().lower(): c for c in df.columns}

    for candidate in candidates:
        key = str(candidate).strip().lower()
        if key in lower_map:
            return lower_map[key]

    return None


def find_file(filename):
    """Search the project for a required file."""
    direct_locations = [
        ROOT / filename,
        ROOT / "Data" / filename,
        ROOT / "data" / filename,
        ROOT / "config" / filename,
        OUTPUT / filename,
    ]

    for path in direct_locations:
        if path.exists():
            return path

    matches = list(ROOT.rglob(filename))

    if matches:
        return matches[0]

    return None


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    financial_file = OUTPUT / "financial_ratios.csv"

    if not financial_file.exists():
        raise FileNotFoundError(
            f"Missing required file: {financial_file}"
        )

    df = pd.read_csv(financial_file)

    print(f"Loaded financial data: {len(df)} rows")

    return df


def load_peer_groups():
    """
    Load peer_groups.xlsx and detect company/group columns automatically.
    """

    peer_file = find_file("peer_groups.xlsx")

    if peer_file is None:
        raise FileNotFoundError(
            "Could not find peer_groups.xlsx in the project."
        )

    print(f"Loading peer groups from: {peer_file}")

    excel = pd.ExcelFile(peer_file)

    # Try every sheet until we find company/group information.
    for sheet in excel.sheet_names:

        peer_df = pd.read_excel(peer_file, sheet_name=sheet)

        company_col = find_column(
            peer_df,
            [
                "company_id",
                "company",
                "id",
                "ticker"
            ]
        )

        group_col = find_column(
            peer_df,
            [
                "peer_group_name",
                "peer_group",
                "group_name",
                "peer_group_id",
                "group",
                "sector"
            ]
        )

        if company_col and group_col:

            peer_df = peer_df.rename(
                columns={
                    company_col: "company_id",
                    group_col: "peer_group_name"
                }
            )

            name_col = find_column(
                peer_df,
                [
                    "company_name",
                    "name",
                    "company"
                ]
            )

            if name_col and name_col != "company_id":
                peer_df = peer_df.rename(
                    columns={name_col: "company_name"}
                )
            elif "company_name" not in peer_df.columns:
                peer_df["company_name"] = peer_df["company_id"]

            peer_df["company_id"] = (
                peer_df["company_id"]
                .astype(str)
                .str.strip()
                .str.upper()
            )

            peer_df["peer_group_name"] = (
                peer_df["peer_group_name"]
                .astype(str)
                .str.strip()
            )

            print(
                f"Peer groups loaded: "
                f"{peer_df['peer_group_name'].nunique()} groups"
            )

            return peer_df[
                [
                    "company_id",
                    "company_name",
                    "peer_group_name"
                ]
            ].drop_duplicates()

    raise ValueError(
        "Could not identify company_id and peer group columns "
        "inside peer_groups.xlsx."
    )


# ============================================================
# METRIC DEFINITIONS
# ============================================================

METRIC_ALIASES = {

    "ROE": [
        "roe",
        "roe_percentage",
        "return_on_equity"
    ],

    "ROCE": [
        "roce",
        "roce_percentage",
        "return_on_capital_employed"
    ],

    "NPM": [
        "npm",
        "npm_percentage",
        "net_profit_margin",
        "net_margin"
    ],

    "Operating Profit Margin": [
        "opm",
        "opm_percentage",
        "operating_profit_margin",
        "operating_margin",
        "operating_margin_percentage"
    ],

    "Debt Equity": [
        "debt_equity",
        "debt_to_equity",
        "debt_equity_ratio"
    ],

    "Interest Coverage": [
        "interest_coverage",
        "interest_cover",
        "icr"
    ],

    "Dividend Yield": [
        "dividend_yield",
        "dividend_yield_pct",
        "dividend_yield_percentage"
    ],

    "FCF": [
        "fcf",
        "free_cash_flow",
        "free_cashflow"
    ],

    "FCF CAGR 5yr": [
        "fcf_cagr_5yr",
        "fcf_cagr_5y",
        "fcf_cagr"
    ],

    "PAT CAGR 5yr": [
        "pat_cagr_5yr",
        "pat_cagr_5y",
        "pat_cagr"
    ],

    "Revenue CAGR 5yr": [
        "revenue_cagr_5yr",
        "revenue_cagr_5y",
        "revenue_cagr"
    ],

    "EPS CAGR 5yr": [
        "eps_cagr_5yr",
        "eps_cagr_5y",
        "eps_cagr"
    ],

    "Asset Turnover": [
        "asset_turnover",
        "asset_turnover_ratio"
    ],

    "Revenue": [
        "revenue",
        "sales"
    ],

    "Net Profit": [
        "net_profit",
        "pat",
        "profit_after_tax"
    ],

    "EPS": [
        "eps",
        "earnings_per_share"
    ],

    "Market Cap": [
        "market_cap",
        "market_capitalization"
    ],

    "Total Assets": [
        "total_assets",
        "assets"
    ],

    "Cashflow to Profit": [
        "cashflow_to_profit",
        "cfo_to_pat",
        "cfo_pat_ratio"
    ],

    "Composite Score": [
        "composite_score",
        "composite_quality_score",
        "quality_score"
    ]
}


RANK_METRICS = [
    "ROE",
    "ROCE",
    "NPM",
    "Debt Equity",
    "FCF CAGR 5yr",
    "PAT CAGR 5yr",
    "Revenue CAGR 5yr",
    "EPS CAGR 5yr",
    "Interest Coverage",
    "Asset Turnover"
]


# ============================================================
# PREPARE FINANCIAL DATA
# ============================================================

def prepare_financial_data(df):

    company_col = find_column(
        df,
        ["company_id", "company", "id", "ticker"]
    )

    if company_col is None:
        raise ValueError(
            "No company identifier column found in financial_ratios.csv"
        )

    year_col = find_column(
        df,
        ["year", "fy", "financial_year"]
    )

    working = df.copy()

    working[company_col] = (
        working[company_col]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Keep latest year per company.
    if year_col:

        working[year_col] = working[year_col].astype(str)

        working = (
            working
            .sort_values([company_col, year_col])
            .drop_duplicates(
                subset=[company_col],
                keep="last"
            )
        )

    result = pd.DataFrame()

    result["company_id"] = working[company_col]

    company_name_col = find_column(
        working,
        [
            "company_name",
            "name"
        ]
    )

    if company_name_col:
        result["company_name"] = (
            working[company_name_col]
            .astype(str)
        )
    else:
        result["company_name"] = result["company_id"]

    if year_col:
        result["year"] = working[year_col]

    # Add all required 20 metrics.
    for metric, aliases in METRIC_ALIASES.items():

        source_col = find_column(
            working,
            aliases
        )

        if source_col:

            result[metric] = pd.to_numeric(
                working[source_col],
                errors="coerce"
            )

        else:

            result[metric] = np.nan

    return result


# ============================================================
# PERCENTILE RANKING
# ============================================================

def calculate_percentile_ranks(df):

    result = df.copy()

    for metric in RANK_METRICS:

        if metric not in result.columns:
            continue

        values = pd.to_numeric(
            result[metric],
            errors="coerce"
        )

        if values.notna().sum() == 0:

            result[f"{metric} Percentile Rank"] = np.nan
            continue

        percentile = (
            values.rank(
                method="average",
                pct=True
            ) * 100
        )

        # Lower Debt/Equity is better.
        if metric == "Debt Equity":

            percentile = 100 - percentile + (
                100 / max(values.notna().sum(), 1)
            )

        result[f"{metric} Percentile Rank"] = percentile.round(2)

    return result


# ============================================================
# BUILD PEER COMPARISON
# ============================================================

def build_peer_comparison(financial_df, peer_df):

    financial = prepare_financial_data(financial_df)

    peer = peer_df.copy()

    peer["company_id"] = (
        peer["company_id"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Load CAGR analysis data.
    cagr_file = OUTPUT / "cagr_analysis.csv"
    cagr = pd.read_csv(cagr_file)

    # Normalize the company ID column.
    cagr_id_col = cagr.columns[0]
    cagr[cagr_id_col] = (
        cagr[cagr_id_col]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # Rename the first column to company_id if necessary.
    if cagr_id_col != "company_id":
        cagr = cagr.rename(columns={cagr_id_col: "company_id"})

    # Map the actual CAGR-analysis column names to peer-comparison names.
    cagr_mapping = {
        "Revenue CAGR (%)": "Revenue CAGR 5yr",
        "Net Profit CAGR (%)": "PAT CAGR 5yr",
        "EPS CAGR (%)": "EPS CAGR 5yr",
    }

    for source_col, target_col in cagr_mapping.items():
        if source_col in cagr.columns:
            cagr[target_col] = pd.to_numeric(
                cagr[source_col],
                errors="coerce"
            )

    # Keep company ID and the CAGR metrics actually supplied by cagr_analysis.csv.
    cagr_metrics = [
        "company_id",
        "PAT CAGR 5yr",
        "Revenue CAGR 5yr",
        "EPS CAGR 5yr",
    ]
    cagr = cagr[cagr_metrics].copy()

    # Merge financial data first.
    merged = peer.merge(
        financial,
        on="company_id",
        how="left",
        suffixes=("", "_financial")
    )

    # Merge CAGR data.
    merged = merged.merge(
        cagr,
        on="company_id",
        how="left",
        suffixes=("", "_cagr")
    )

    # Prefer peer-group company name.
    if "company_name" not in merged.columns:
        merged["company_name"] = merged["company_id"]

    merged["company_name"] = (
        merged["company_name"]
        .fillna(merged["company_id"])
    )

    # Calculate ranks inside each peer group.
    output_parts = []

    for group_name, group_df in merged.groupby(
        "peer_group_name",
        dropna=False
    ):

        ranked = calculate_percentile_ranks(
            group_df.copy()
        )

        output_parts.append(ranked)

    if not output_parts:
        raise ValueError(
            "No peer groups were created."
        )

    result = pd.concat(
        output_parts,
        ignore_index=True
    )

    return result
# ============================================================
# EXCEL EXPORT
# ============================================================

def safe_sheet_name(name):

    name = str(name)

    invalid = [
        "\\",
        "/",
        "*",
        "?",
        ":",
        "[",
        "]"
    ]

    for char in invalid:
        name = name.replace(char, "_")

    return name[:31] or "Peer Group"


def save_peer_comparison(result):
    print(">>> ENTERED save_peer_comparison()")
    csv_file = OUTPUT / "peer_comparison.csv"
    xlsx_file = OUTPUT / "peer_comparison.xlsx"

    result.to_csv(
        csv_file,
        index=False
    )

    print(f"Saved CSV: {csv_file}")

    try:

        with pd.ExcelWriter(
            xlsx_file,
            engine="xlsxwriter"
        ) as writer:

            workbook = writer.book

            header_format = workbook.add_format(
                {
                    "bold": True,
                    "bg_color": "#1F4E78",
                    "font_color": "white",
                    "border": 1
                }
            )

            green_format = workbook.add_format(
                {
                    "bg_color": "#C6EFCE",
                    "font_color": "#006100"
                }
            )

            yellow_format = workbook.add_format(
                {
                    "bg_color": "#FFEB9C",
                    "font_color": "#9C6500"
                }
            )

            red_format = workbook.add_format(
                {
                    "bg_color": "#FFC7CE",
                    "font_color": "#9C0006"
                }
            )

            benchmark_format = workbook.add_format(
                {
                    "bg_color": "#FFD966",
                    "bold": True
                }
            )

            # One sheet per peer group.
            groups = list(
                result["peer_group_name"]
                .dropna()
                .astype(str)
                .unique()
            )

            print("DEBUG GROUPS:", groups)
            print("DEBUG RESULT ROWS:", len(result))
            print("DEBUG RESULT COLUMNS:", result.columns.tolist())

            print(
                f"Creating {len(groups)} peer-group sheets..."
            )

            used_names = set()

            for group_name in groups:

                sheet_name = safe_sheet_name(
                    group_name
                )

                original_name = sheet_name
                counter = 2

                while sheet_name in used_names:

                    suffix = f"_{counter}"
                    sheet_name = (
                        original_name[:31 - len(suffix)]
                        + suffix
                    )

                    counter += 1

                used_names.add(sheet_name)

                group_df = result[
                    result["peer_group_name"].astype(str)
                    == str(group_name)
                ].copy()

                # Remove internal peer group column from report.
                report_df = group_df.drop(
                    columns=["peer_group_name"],
                    errors="ignore"
                )

                report_df.to_excel(
                    writer,
                    sheet_name=sheet_name,
                    index=False
                )

                worksheet = writer.sheets[
                    sheet_name
                ]

                # Header formatting.
                for col_num, value in enumerate(
                    report_df.columns
                ):

                    worksheet.write(
                        0,
                        col_num,
                        value,
                        header_format
                    )

                # Freeze header.
                worksheet.freeze_panes(
                    1,
                    0
                )

                # Autofilter.
                worksheet.autofilter(
                    0,
                    0,
                    len(report_df),
                    len(report_df.columns) - 1
                )

                # Width.
                worksheet.set_column(
                    0,
                    len(report_df.columns) - 1,
                    16
                )

                # Find percentile columns.
                for col_num, column in enumerate(
                    report_df.columns
                ):

                    if "Percentile Rank" not in str(column):
                        continue

                    if len(report_df) == 0:
                        continue

                    first_row = 1
                    last_row = len(report_df)

                    worksheet.conditional_format(
                        first_row,
                        col_num,
                        last_row,
                        col_num,
                        {
                            "type": "cell",
                            "criteria": ">=",
                            "value": 75,
                            "format": green_format
                        }
                    )

                    worksheet.conditional_format(
                        first_row,
                        col_num,
                        last_row,
                        col_num,
                        {
                            "type": "cell",
                            "criteria": "between",
                            "minimum": 25,
                            "maximum": 75,
                            "format": yellow_format
                        }
                    )

                    worksheet.conditional_format(
                        first_row,
                        col_num,
                        last_row,
                        col_num,
                        {
                            "type": "cell",
                            "criteria": "<",
                            "value": 25,
                            "format": red_format
                        }
                    )

                # Highlight first company as benchmark if available.
                if len(report_df) > 0:

                    worksheet.set_row(
                        1,
                        None,
                        benchmark_format
                    )

                # Add median summary row.
                numeric_columns = report_df.select_dtypes(
                    include=np.number
                ).columns

                if len(numeric_columns) > 0:

                    summary = {}

                    for column in report_df.columns:

                        if column in numeric_columns:

                            summary[column] = (
                                pd.to_numeric(
                                    report_df[column],
                                    errors="coerce"
                                ).median()
                            )

                        elif column == "company_id":

                            summary[column] = "PEER GROUP MEDIAN"

                        else:

                            summary[column] = ""

                    summary_row = len(report_df) + 2

                    for col_num, column in enumerate(
                        report_df.columns
                    ):

                        worksheet.write(
                            summary_row,
                            col_num,
                            summary.get(column, "")
                        )

        print(
            f"Saved Excel: {xlsx_file}"
        )

        print(
            f"Excel sheets created: {len(used_names)}"
        )

    except ImportError:

        print(
            "xlsxwriter is not installed."
        )

        print(
            "Run: python -m pip install xlsxwriter"
        )

    except Exception as exc:

        print(
            f"Excel export failed: {exc}"
        )

    return result


# ============================================================
# RADAR CHART
# ============================================================

def generate_radar_chart(
    company_row,
    peer_group_df,
    company_id
):

    try:
        import matplotlib.pyplot as plt

    except ImportError:

        print(
            "matplotlib is not installed; "
            "radar charts skipped."
        )

        return

    radar_metrics = [
        "ROE",
        "ROCE",
        "NPM",
        "Debt Equity",
        "FCF CAGR 5yr",
        "PAT CAGR 5yr",
        "Revenue CAGR 5yr",
        "Composite Score"
    ]

    available = [
        metric
        for metric in radar_metrics
        if metric in peer_group_df.columns
    ]

    if len(available) < 5:
        return

    data = peer_group_df.copy()

    for metric in available:

        data[metric] = pd.to_numeric(
            data[metric],
            errors="coerce"
        )

    data = data.dropna(
        subset=available,
        how="all"
    )

    if data.empty:
        return

    company_values = []

    peer_values = []

    for metric in available:

        values = data[metric]

        min_value = values.min()
        max_value = values.max()

        company_value = pd.to_numeric(
            company_row.get(metric),
            errors="coerce"
        )

        peer_average = values.mean()

        if pd.isna(company_value):
            company_value = peer_average

        if pd.isna(min_value) or pd.isna(max_value):
            company_values.append(0)
            peer_values.append(0)

        elif max_value == min_value:

            company_values.append(50)
            peer_values.append(50)

        else:

            company_values.append(
                (
                    company_value - min_value
                )
                /
                (
                    max_value - min_value
                )
                * 100
            )

            peer_values.append(
                (
                    peer_average - min_value
                )
                /
                (
                    max_value - min_value
                )
                * 100
            )

    angles = np.linspace(
        0,
        2 * np.pi,
        len(available),
        endpoint=False
    ).tolist()

    angles += angles[:1]

    company_values += company_values[:1]
    peer_values += peer_values[:1]

    fig, ax = plt.subplots(
        figsize=(8, 8),
        subplot_kw={"polar": True}
    )

    ax.plot(
        angles,
        company_values,
        linewidth=2,
        label=str(company_id)
    )

    ax.fill(
        angles,
        company_values,
        alpha=0.15
    )

    ax.plot(
        angles,
        peer_values,
        linestyle="--",
        linewidth=2,
        label="Peer Group Average"
    )

    ax.set_xticks(
        angles[:-1]
    )

    ax.set_xticklabels(
        available,
        fontsize=9
    )

    ax.set_ylim(
        0,
        100
    )

    ax.set_title(
        f"{company_id} - Peer Comparison Radar",
        pad=25
    )

    ax.legend(
        loc="upper right",
        bbox_to_anchor=(1.30, 1.15)
    )

    filename = (
        f"{str(company_id)}_radar.png"
        .replace("/", "_")
        .replace("\\", "_")
    )

    output_file = REPORTS / filename

    plt.tight_layout()

    plt.savefig(
        output_file,
        dpi=200,
        bbox_inches="tight"
    )

    plt.close()

    print(
        f"Radar saved: {output_file}"
    )


# ============================================================
# GENERATE ALL RADAR CHARTS
# ============================================================

def generate_all_radar_charts(result):

    if "peer_group_name" not in result.columns:
        return

    total = 0

    for group_name, group_df in result.groupby(
        "peer_group_name"
    ):

        for _, company_row in group_df.iterrows():

            company_id = company_row[
                "company_id"
            ]

            generate_radar_chart(
                company_row,
                group_df,
                company_id
            )

            total += 1

    print(
        f"Radar chart generation completed: {total} companies"
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_peer_analysis(
    company_id=None,
    top_n=10
):

    print("\n" + "=" * 70)
    print("SPRINT 3 - PEER COMPARISON ANALYSIS")
    print("=" * 70)

    financial_df = load_data()

    peer_df = load_peer_groups()

    result = build_peer_comparison(
        financial_df,
        peer_df
    )

    print(
        f"Companies in comparison: {len(result)}"
    )

    print(
        f"Peer groups found: "
        f"{result['peer_group_name'].nunique()}"
    )

    # Optional target-company display.
    if company_id is not None:

        target = result[
            result["company_id"].astype(str).str.upper()
            == str(company_id).upper()
        ]

        if target.empty:

            print(
                f"Warning: {company_id} not found."
            )

        else:

            print(
                f"Target company found: {company_id}"
            )
    print(">>> ABOUT TO CALL SAVE:", save_peer_comparison)
    print(">>> SAVE FUNCTION LINE:", save_peer_comparison.__code__.co_firstlineno)
    save_peer_comparison(
        result
    )

    generate_all_radar_charts(
        result
    )

    print("\n" + "=" * 70)
    print("SPRINT 3 PEER ENGINE COMPLETED SUCCESSFULLY!")
    print("=" * 70)

    return result


if __name__ == "__main__":
    run_peer_analysis()