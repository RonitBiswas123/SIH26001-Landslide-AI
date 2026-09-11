import pandas as pd
import re
from pathlib import Path


INPUT = Path(
    "data/processed/gsi_master_dataset.csv"
)

OUTPUT = Path(
    "data/processed/gsi_master_dataset_v2.csv"
)


df = pd.read_csv(INPUT)


# ==========================================
# DISTRICT EXTRACTION
# ==========================================

def extract_district(text):

    if pd.isna(text):
        return None

    text = str(text)

    # Remove the beginning serial number and slide ID
    text = re.sub(
        r"^\d+\s+\S+\s*",
        "",
        text
    )

    # State names
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

    # Remove state from beginning
    for state in states:

        text = re.sub(
            r"^" + re.escape(state) + r"\s*",
            "",
            text,
            flags=re.IGNORECASE
        )

    # The first meaningful word/phrase after the state
    # is usually the district in the GSI record.
    #
    # We take text before the next known location/feature
    # only when a clean boundary is available.

    words = text.split()

    if not words:
        return None

    # Basic first-token district candidate.
    # We preserve the original record so this can be
    # manually/algorithmically improved later.
    return words[0]


df["district_candidate"] = (
    df["source_record"]
    .apply(extract_district)
)


# ==========================================
# SAVE
# ==========================================

df.to_csv(
    OUTPUT,
    index=False
)


# ==========================================
# REPORT
# ==========================================

print()
print("==========================================")
print("DISTRICT EXTRACTION COMPLETE")
print("==========================================")

print()

print(
    "Total records:",
    len(df)
)

print()

print(
    "District candidates:",
    df["district_candidate"].notna().sum()
)

print()

print(
    df["district_candidate"]
    .value_counts()
    .head(50)
    .to_string()
)

print()

print("Saved to:")
print(OUTPUT)