
Ahh yes — I understand. You mean inside the State/District sections, some records are displaying None for things like state/district names.

That is because your dataset has some missing/invalid administrative mappings. We should hide/replace those values in the UI, not modify the underlying GSI data.

For example:

State = None → State = Unknown / Unmapped

District = None → District = Unknown / Unmapped

But for the state selector, we should ideally exclude None entirely, so the dropdown only contains actual states.

Quick fix
In your app.py, wherever the state list is created, use:

states = sorted(
    df["state"]
    .dropna()
    .astype(str)
    .loc[lambda x: x.str.strip().ne("")]
    .loc[lambda x: x.str.lower().ne("none")]
    .unique()
)
And wherever you create the district list:

districts = sorted(
    state_df["district"]
    .dropna()
    .astype(str)
    .loc[lambda x: x.str.strip().ne("")]
    .loc[lambda x: x.str.lower().ne("none")]
    .unique()
)
For displayed values, use:

state_name = str(row.get("state", "Unknown")).strip()

if state_name.lower() in ["none", "nan", ""]:
    state_name = "Unknown / Unmapped"
Same for district:

district_name = str(row.get("district", "Unknown")).strip()

if district_name.lower() in ["none", "nan", ""]:
    district_name = "Unknown / Unmapped"
One thing I'd change too
Your data already has 29,987/29,990 district mappings, so only 3 records are actually unmapped in the merged dataset. That's tiny.

The bigger issue is likely that some UI code converts missing values to the literal string "None" while building the state/district sections.

Don't rebuild the dataset. The data is fine enough; just sanitize the UI values.

If you want, I can give you the entire current app.py with the None issue fixed everywhere, while preserving your current detailed Command Center.


how tp change i cant find manually in app

Yep bro 😭 don't manually find anything. We'll replace the whole app.py, but I need to use your current detailed version, not give you a stripped-down app.

Since your current deployed app is working, the safest way is:

1. Download your current app.py from GitHub
In PowerShell, inside your project folder, run only this command:

git checkout -- app.py
2. Then send me your current app.py
You can simply upload app.py here.

I'll modify the entire file and give you a complete copy-paste replacement that:

removes None from State dropdowns

removes None from District dropdowns

changes missing display values to Unknown / Unmapped

handles NaN too

keeps ALL your current dashboard sections

keeps your maps

keeps exposure

keeps alerts

keeps field reporting

keeps weather scenario

keeps system health

keeps the current styling

Then I'll give you exactly:

git add app.py
git commit -m "Fix state and district display values"
git push origin main --force
Don't try to search through the 2,900+ lines yourself. Upload the current app.py and I'll do the whole thing.



Pasted text(7).txt
Document

Done bro. I took your full current app.py and fixed the State/District None issue without removing any of your dashboard features. 


The fix does 3 things:

Removes None, NaN, null, and blank values from State dropdown

Removes them from District dropdown

Displays missing administrative mappings as Unknown / Unmapped instead of None

1. Replace your app.py
I generated the complete fixed file:

Download the fixed app.py

Important: Don't copy individual sections. Replace your entire existing app.py with this file.

2. Then run these commands
In PowerShell, from your project folder:

Copy-Item "C:\Users\YOUR_NAME\Downloads\app_fixed_none.py" ".\app.py" -Force
If the downloaded file went somewhere else, easiest is to manually copy the downloaded file into your project folder and rename it:

app_fixed_none.py
        ↓
app.py
Then:

git add app.py
git commit -m "Fix None values in state and district views"
git push origin main --force
3. Streamlit
Wait for Streamlit Cloud to redeploy, then refresh the dashboard.

You should now have clean dropdowns like:

🇮🇳 State
ALL STATES
Andhra Pradesh
Arunachal Pradesh
Assam
Manipur
Meghalaya
Mizoram
Nagaland
Sikkim
Tripura
...
instead of:

None
Assam
Manipur
...
And the State → District Command View won't show literal None anymore.

Your maps, alerts, exposure, field reporting, AI risk engine, emergency prioritization, and all the detailed sections remain intact.


app_fixed_none.py
Code


Library
/
LEETCODE PROBLEMS
/
app_fixed_none.py


1
2
3
4
5
6
7
8
9
10
11
12
13
14
15
16
17
18
19
20
21
22
23
24
25
# ============================================================
# SIH26001 - NER LANDSLIDE AI COMMAND CENTER
# FULL FEATURE PROTOTYPE
# ============================================================

import sys
from pathlib import Path

import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk


# ============================================================
# PATHS
# ============================================================

BASE = Path(__file__).resolve().parent

DATA_DIR = BASE / "data" / "processed"
MODEL_DIR = BASE / "model"
SCRIPTS_DIR = BASE / "scripts"

# IMPORTANT:
