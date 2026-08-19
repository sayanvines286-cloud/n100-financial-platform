from fastapi import FastAPI
import sqlite3
import pandas as pd
from pathlib import Path

app = FastAPI(title="N100 Financial API")

# Database path
BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "db" / "n100_financial.db"


def query(sql):
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql(sql, conn)

    conn.close()

    df = df.replace({float("nan"): None})
    df = df.astype(object)
    df = df.where(pd.notnull(df), None)

    return df.to_dict(orient="records")

@app.get("/")
def home():
    return {"message": "N100 Financial API is running!"}


@app.get("/companies")
def companies():
    sql = """
    SELECT DISTINCT company_id
FROM sectors
ORDER BY company_id
    """
    return query(sql)


@app.get("/market-cap")
def market_cap():
    sql = """
    SELECT *
    FROM market_cap
    LIMIT 20
    """
    return query(sql)


@app.get("/financial-ratios")
def financial_ratios():
    sql = """
    SELECT *
    FROM financial_ratios
    LIMIT 20
    """
    return query(sql)


@app.get("/stock-prices")
def stock_prices():
    sql = """
    SELECT *
    FROM stock_prices
    LIMIT 20
    """
    return query(sql)