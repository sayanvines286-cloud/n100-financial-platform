import sqlite3

conn = sqlite3.connect("db/n100_financial.db")
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(financial_ratios)")
print(cursor.fetchall())

conn.close()