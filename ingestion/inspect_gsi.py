from pathlib import Path
import pandas as pd

DATA_FOLDER = Path("data/raw/gsi")

print("======================================")
print("GSI DATA INSPECTION")
print("======================================")

files = [p for p in DATA_FOLDER.iterdir() if p.is_file()]

print("\nFiles found:")
for file in files:
    print("-", file.name)

csv_files = list(DATA_FOLDER.glob("*.csv"))

if not csv_files:
    print("\nNo CSV file found yet.")
    print("Download the official GSI inventory and place it in:")
    print("data/raw/gsi/")
else:
    for file in csv_files:
        print("\n======================================")
        print("Reading:", file.name)
        print("======================================")

        df = pd.read_csv(file)

        print("Rows:", df.shape[0])
        print("Columns:", df.shape[1])

        print("\nColumn names:")
        for column in df.columns:
            print("-", column)

        print("\nFirst 5 rows:")
        print(df.head().to_string())

        print("\nMissing values:")
        print(df.isnull().sum().to_string())
