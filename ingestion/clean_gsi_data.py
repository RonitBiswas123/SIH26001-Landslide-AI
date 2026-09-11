import pandas as pd
import re
from pathlib import Path


# ==========================================
# FILE PATHS
# ==========================================

INPUT = Path(
    "data/processed/gsi_inventory_raw.csv"
)

OUTPUT = Path(
    "data/processed/gsi_inventory_clean.csv"
)


# ==========================================
# LOAD DATA
# ==========================================

print("Loading GSI inventory...")

df = pd.read_csv(INPUT)

print("Records loaded:", len(df))


# ==========================================
# EXTRACT DATE
# ==========================================

def extract_date(text):

    pattern = (
        r"\b"
        r"(?:\d{1,2}\s+)?"
        r"(January|February|March|April|May|June|"
        r"July|August|September|October|November|December)"
        r"\s+\d{4}"
        r"\b"
    )

    match = re.search(
        pattern,
        str(text),
        re.IGNORECASE
    )

    if match:

        return match.group(0)

    return None


df["event_date_raw"] = (
    df["source_record"]
    .apply(extract_date)
)


# Convert to proper date

df["event_date"] = pd.to_datetime(
    df["event_date_raw"],
    errors="coerce"
)


# ==========================================
# EXTRACT STATE
# ==========================================

STATES = [
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",
    "Jammu and Kashmir",
    "Ladakh"
]


def extract_state(text):

    text = str(text)

    for state in STATES:

        if state.lower() in text.lower():

            return state

    return None


df["state"] = (
    df["source_record"]
    .apply(extract_state)
)


# ==========================================
# BASIC COORDINATE VALIDATION
# ==========================================

df = df[
    df["latitude"].between(6, 38)
    &
    df["longitude"].between(68, 98)
].copy()


# ==========================================
# REMOVE EXACT DUPLICATES
# ==========================================

df.drop_duplicates(
    inplace=True
)


# ==========================================
# SAVE
# ==========================================

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

df.to_csv(
    OUTPUT,
    index=False
)


# ==========================================
# REPORT
# ==========================================

print()
print("==========================================")
print("GSI CLEANING COMPLETE")
print("==========================================")

print()

print("Records:", len(df))

print(
    "Dates extracted:",
    df["event_date"].notna().sum()
)

print(
    "States detected:",
    df["state"].notna().sum()
)

print()

print("State distribution:")

print(
    df["state"]
    .value_counts(dropna=False)
    .to_string()
)

print()

print("Date range:")

print(
    df["event_date"].min(),
    "to",
    df["event_date"].max()
)

print()

print("Saved to:")

print(OUTPUT)

print()