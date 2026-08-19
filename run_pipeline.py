import subprocess
import sys

steps = [
    "src/etl/loader.py",
    "src/etl/database.py",
    "src/analytics/ratios.py",
    "src/analytics/cagr.py",
    "src/analytics/cashflow_kpis.py",
]

print("=" * 60)
print("N100 Financial Intelligence Platform")
print("=" * 60)

for step in steps:
    print(f"\nRunning: {step}")

    result = subprocess.run([sys.executable, step])

    if result.returncode != 0:
        print(f"\nERROR while running {step}")
        sys.exit(1)

print("\n" + "=" * 60)
print("ALL PIPELINES COMPLETED SUCCESSFULLY!")
print("=" * 60)