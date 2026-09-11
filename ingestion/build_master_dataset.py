import pandas as pd
import re
from pathlib import Path


# ==========================================
# PATHS
# ==========================================

INPUT = Path(
    "data/processed/gsi_inventory_raw.csv"
)

OUTPUT = Path(
    "data/processed/gsi_master_dataset.csv"
)


# ==========================================
# LOAD
# ==========================================

print("Loading GSI data...")

df = pd.read_csv(INPUT)

print("Records:", len(df))


# ==========================================
# EXTRACT YEAR FROM SLIDE ID
# ==========================================

def extract_year(slide_no):

    if pd.isna(slide_no):
        return None

    text = str(slide_no)

    # Find 4-digit year
    years = re.findall(
        r"(?:19|20)\d{2}",
        text
    )

    if years:
        return int(years[0])

    return None


df["year"] = (
    df["slide_no"]
    .apply(extract_year)
)


# ==========================================
# STATE LIST
# ==========================================

states = [

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


# ==========================================
# EXTRACT STATE
# ==========================================

def extract_state(text):

    if pd.isna(text):
        return None

    text = str(text)

    for state in states:

        if re.search(
            r"\b"
            + re.escape(state)
            + r"\b",
            text,
            re.IGNORECASE
        ):

            return state

    return None


df["state"] = (
    df["source_record"]
    .apply(extract_state)
)


# ==========================================
# EXTRACT EVENT DATE
# ==========================================

def extract_date(text):

    if pd.isna(text):
        return None

    text = str(text)

    months = (
        "January|February|March|April|May|June|"
        "July|August|September|October|November|December"
    )

    patterns = [

        rf"\b\d{{1,2}}\s+({months})\s+(19|20)\d{{2}}\b",

        rf"\b({months})\s+\d{{1,2}},?\s+(19|20)\d{{2}}\b"

    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            return match.group(0)

    return None


df["event_date_raw"] = (
    df["source_record"]
    .apply(extract_date)
)


df["event_date"] = pd.to_datetime(
    df["event_date_raw"],
    errors="coerce"
)


# ==========================================
# EXTRACT MOVEMENT TYPE
# ==========================================

movement_types = [

    "Debris Slide",
    "Earth Slide",
    "Rock Slide",
    "Debris Flow",
    "Rock Fall",
    "Earth Flow",
    "Mud Flow",
    "Mud Slide",
    "Topple",
    "Fall",
    "Flow",
    "Slide"

]


def extract_movement(text):

    if pd.isna(text):
        return None

    text = str(text)

    # Check longer names first

    for movement in sorted(
        movement_types,
        key=len,
        reverse=True
    ):

        if re.search(
            r"\b"
            + re.escape(movement)
            + r"\b",
            text,
            re.IGNORECASE
        ):

            return movement

    return None


df["movement_type"] = (
    df["source_record"]
    .apply(extract_movement)
)


# ==========================================
# COORDINATE VALIDATION
# ==========================================

df["latitude"] = pd.to_numeric(
    df["latitude"],
    errors="coerce"
)

df["longitude"] = pd.to_numeric(
    df["longitude"],
    errors="coerce"
)


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
print("GSI MASTER DATASET CREATED")
print("==========================================")

print()

print("Records:", len(df))

print()

print(
    "States detected:",
    df["state"].notna().sum()
)

print(
    "Dates detected:",
    df["event_date"].notna().sum()
)

print(
    "Movement types detected:",
    df["movement_type"].notna().sum()
)

print()

print("State distribution:")

print(
    df["state"]
    .value_counts(
        dropna=False
    )
    .to_string()
)

print()

print("Year distribution:")

print(
    df["year"]
    .value_counts()
    .sort_index()
    .tail(30)
    .to_string()
)

print()

print("Saved:")

print(OUTPUT)

print()