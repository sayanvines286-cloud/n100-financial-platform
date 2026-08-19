from pathlib import Path
import pandas as pd

# Base project directory
BASE_DIR = Path(__file__).resolve().parents[2]

RAW_DATA_DIR = BASE_DIR / "Data" / "raw"
PROCESSED_DATA_DIR = BASE_DIR / "Data" / "processed"
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "analysis": "analysis.xlsx",
    "balancesheet": "balancesheet.xlsx",
    "cashflow": "cashflow.xlsx",
    "companies": "companies.xlsx",
    "documents": "documents.xlsx",
    "profitandloss": "profitandloss.xlsx",
    "prosandcons": "prosandcons.xlsx",

    "financial_ratios": "supporting datasets/financial_ratios.xlsx",
    "market_cap": "supporting datasets/market_cap.xlsx",
    "peer_groups": "supporting datasets/peer_groups.xlsx",
    "sectors": "supporting datasets/sectors.xlsx",
    "stock_prices": "supporting datasets/stock_prices.xlsx",
}


def clean_column_names(df):
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
        .str.replace("-", "_")
        .str.replace(r"[^\w]", "", regex=True)
    )
    return df


def detect_header(file_path):
    preview = pd.read_excel(file_path, header=None, nrows=10)

    for i in range(len(preview)):
        row = preview.iloc[i].astype(str).str.lower()

        if (
            row.str.contains("company").any()
            or row.str.contains("year").any()
            or row.str.contains("sales").any()
            or row.str.contains("revenue").any()
            or row.str.contains("particular").any()
        ):
            return i

    return 0


def load_excel(file_path):
    header_row = detect_header(file_path)

    df = pd.read_excel(file_path, header=header_row)

    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")

    df = clean_column_names(df)

    return df


def process_all_files():

    for name, relative_path in FILES.items():

        file_path = RAW_DATA_DIR / relative_path

        print(f"Loading {name}...")

        df = load_excel(file_path)

        output_file = PROCESSED_DATA_DIR / f"{name}.csv"

        df.to_csv(output_file, index=False)

        print(f"Saved -> {output_file}")

    print("\nAll datasets processed successfully!")


if __name__ == "__main__":
    process_all_files()