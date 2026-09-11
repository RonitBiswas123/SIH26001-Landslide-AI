from pathlib import Path
import pandas as pd

INPUT_DIR = Path("data/raw/gsi")
OUTPUT_DIR = Path("data/processed")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# This script intentionally does not assume GSI column names.
# Inspect the downloaded official file first, then map its actual
# fields into a canonical schema.

csv_files = list(INPUT_DIR.glob("*.csv"))

if not csv_files:
    print("No GSI CSV found in data/raw/gsi/")
    print("Place the official inventory there and run inspect_gsi.py first.")
    raise SystemExit(0)

file = csv_files[0]
df = pd.read_csv(file)

print("Loaded:", file)
print("Shape:", df.shape)
print("Actual columns:")
print(list(df.columns))

print("\nNo automatic renaming has been applied.")
print("Create the source-to-canonical column mapping only after")
print("confirming the actual GSI schema.")

# Preserve a raw-normalized copy without changing source values.
out = OUTPUT_DIR / "gsi_inventory_inspected.csv"
df.to_csv(out, index=False)

print("\nSaved inspection copy:", out)
