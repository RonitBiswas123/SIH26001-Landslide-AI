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
if not (BASE / 'data').exists() and (BASE.parent / 'data').exists():
    BASE = BASE.parent`r`nif not (BASE / "data").exists() and (BASE.parent / "data").exists():`r`n    BASE = BASE.parent

DATA_DIR = BASE / "data" / "processed"
MODEL_DIR = BASE / "model"
SCRIPTS_DIR = BASE / "scripts"

# IMPORTANT:
# This is the merged dataset containing:
# GSI + terrain + district
MASTER_FILE = (
    DATA_DIR /
    "master_landslide_dataset_with_districts.csv"
)

# Fallback if merged file does not exist
OLD_MASTER_FILE = (
    DATA_DIR /
    "master_landslide_dataset_with_districts.csv"
)

EXPOSURE_FILE = (
    DATA_DIR /
    "landslide_exposure_priority.csv"
)

ALERT_FILE = (
    DATA_DIR /
    "active_alerts.csv"
)

WEATHER_FILE = (
    DATA_DIR /
    "imd_weather.csv"
)

MODEL_FILE = (
    MODEL_DIR /
    "landslide_susceptibility_model.pkl"
)

FIELD_REPORT_DIR = (
    DATA_DIR /
    "field_reports"
)

FIELD_REPORT_FILE = (
    FIELD_REPORT_DIR /
    "field_reports.csv"
)


# ============================================================
# IMPORT RISK ENGINE
# ============================================================

sys.path.append(str(SCRIPTS_DIR))

try:
    from risk_engine import calculate_risk
    RISK_ENGINE_AVAILABLE = True
except Exception:
    RISK_ENGINE_AVAILABLE = False


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="NER Landslide AI Command Center",
    page_icon="🌋",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS
# ============================================================

st.markdown(
    """
    <style>
    /* =========================================================
       NER COMMAND CENTER — ULTRA POLISHED UI
       ========================================================= */

    :root {
        --ink: #0f172a;
        --muted: #64748b;
        --line: #e2e8f0;
        --panel: #ffffff;
        --soft: #f8fafc;
        --navy: #0b1220;
        --cyan: #0891b2;
    }

    .stApp {
        background:
            radial-gradient(circle at 85% 0%, rgba(8,145,178,.07), transparent 28%),
            linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
        color: var(--ink);
    }

    [data-testid="stHeader"] {
        background: rgba(248,250,252,.82);
        backdrop-filter: blur(12px);
    }

    [data-testid="stAppViewContainer"] > .main {
        padding-top: 1.25rem;
    }

    .block-container {
        max-width: 1500px;
        /* Extra top breathing room so Streamlit's fixed toolbar
           never overlaps/cuts the command-center header. */
        padding: 4.6rem 2.2rem 3rem 2.2rem !important;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, #0b1220 0%, #111827 55%, #0f172a 100%);
        border-right: 1px solid rgba(255,255,255,.08);
    }

    [data-testid="stSidebar"] * {
        color: #e5e7eb;
    }

    [data-testid="stSidebar"] .stMarkdown p {
        color: #94a3b8;
    }

    [data-testid="stSidebar"] [data-baseweb="select"] > div,
    [data-testid="stSidebar"] input {
        background: #182235 !important;
        border-color: #334155 !important;
        color: #f8fafc !important;
    }

    [data-testid="stSidebar"] [data-testid="stSlider"] {
        padding-bottom: .35rem;
    }

    /* Main header */
    .main-title {
        font-size: clamp(2rem, 3.2vw, 3rem);
        line-height: 1.12;
        letter-spacing: -.045em;
        font-weight: 850;
        color: #f8fafc;
        margin: 0 0 .5rem;
        padding-top: .15rem;
        position: relative;
        z-index: 2;
    }

    .subtitle {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: .65rem;
    }

    .section-title {
        font-size: 1.45rem;
        font-weight: 800;
        color: #0f172a;
        letter-spacing: -.02em;
        margin-top: 1.45rem;
        margin-bottom: .65rem;
    }

    /* Hero */
    .hero {
        position: relative;
        overflow: hidden;
        padding: 1.35rem 1.55rem;
        border-radius: 20px;
        margin: .75rem 0 1rem;
        color: white;
        background:
            radial-gradient(circle at 95% 5%, rgba(34,211,238,.24), transparent 30%),
            linear-gradient(135deg, #0b1220 0%, #172033 62%, #0e7490 130%);
        box-shadow: 0 18px 45px rgba(15,23,42,.14);
        border: 1px solid rgba(255,255,255,.08);
    }

    .hero:after {
        content: "";
        position: absolute;
        right: -90px;
        bottom: -120px;
        width: 300px;
        height: 300px;
        border: 1px solid rgba(255,255,255,.12);
        border-radius: 50%;
    }

    .hero h3 {
        color: white !important;
        margin: 0 0 .25rem !important;
        font-size: 1.35rem;
    }

    .hero p {
        color: #cbd5e1 !important;
    }

    /* Metrics */
    [data-testid="stMetric"] {
        background: rgba(255,255,255,.9);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: .85rem 1rem;
        min-height: 108px;
        box-shadow: 0 8px 24px rgba(15,23,42,.055);
        transition: transform .18s ease, box-shadow .18s ease;
    }

    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 32px rgba(15,23,42,.09);
    }

    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-weight: 650 !important;
    }

    [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 850 !important;
        letter-spacing: -.035em;
    }

    /* Cards / alerts */
    .critical-box,
    .high-box,
    .moderate-box,
    .low-box {
        padding: 1rem 1.15rem;
        border-radius: 16px;
        margin: .8rem 0;
        box-shadow: 0 8px 24px rgba(15,23,42,.055);
    }

    .critical-box {
        background: linear-gradient(135deg,#fff1f2,#ffe4e6);
        border: 1px solid #fecdd3;
        border-left: 6px solid #dc2626;
    }

    .high-box {
        background: linear-gradient(135deg,#fff7ed,#ffedd5);
        border: 1px solid #fed7aa;
        border-left: 6px solid #ea580c;
    }

    .moderate-box {
        background: linear-gradient(135deg,#fefce8,#fef3c7);
        border: 1px solid #fde68a;
        border-left: 6px solid #ca8a04;
    }

    .low-box {
        background: linear-gradient(135deg,#f0fdf4,#dcfce7);
        border: 1px solid #bbf7d0;
        border-left: 6px solid #16a34a;
    }

    /* Native Streamlit containers */
    [data-testid="stVerticalBlockBorderWrapper"] {
        border-radius: 16px !important;
        border-color: var(--line) !important;
        background: rgba(255,255,255,.72);
    }

    /* Buttons */
    .stButton > button,
    .stDownloadButton > button,
    button[kind="primary"] {
        border-radius: 10px !important;
        font-weight: 700 !important;
        border: 1px solid #cbd5e1 !important;
        min-height: 2.5rem;
        transition: all .18s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        border-color: #0891b2 !important;
        box-shadow: 0 7px 18px rgba(8,145,178,.14);
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: .3rem;
        padding: .35rem;
        border-radius: 14px;
        background: rgba(226,232,240,.62);
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        font-weight: 700;
        padding: .55rem .85rem;
    }

    .stTabs [aria-selected="true"] {
        background: white;
        box-shadow: 0 4px 14px rgba(15,23,42,.08);
    }

    /* Tables */
    [data-testid="stDataFrame"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        overflow: hidden;
        box-shadow: 0 8px 24px rgba(15,23,42,.04);
    }

    /* Expanders */
    [data-testid="stExpander"] {
        border: 1px solid var(--line);
        border-radius: 14px;
        background: rgba(255,255,255,.7);
    }

    /* Alerts / messages */
    [data-testid="stAlert"] {
        border-radius: 13px;
    }

    /* Maps */
    [data-testid="stDeckGlJsonChart"] {
        border-radius: 18px;
        overflow: hidden;
        border: 1px solid var(--line);
        box-shadow: 0 12px 32px rgba(15,23,42,.09);
    }

    /* Inputs */
    [data-baseweb="select"] > div,
    [data-baseweb="input"] > div,
    textarea {
        border-radius: 10px !important;
    }

    /* Dividers */
    hr {
        border: 0 !important;
        border-top: 1px solid #e2e8f0 !important;
        margin: 1.35rem 0 !important;
    }

    .small-muted {
        color: #64748b;
        font-size: .8rem;
    }

    /* Compact status pills */
    .status-strip {
        display: flex;
        flex-wrap: wrap;
        gap: .55rem;
        margin: .75rem 0 1.1rem;
        position: relative;
        z-index: 2;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: .35rem;
        padding: .4rem .7rem;
        border-radius: 999px;
        background: rgba(255,255,255,.85);
        border: 1px solid #dbe3ec;
        color: #334155;
        font-size: .78rem;
        font-weight: 750;
        box-shadow: 0 4px 12px rgba(15,23,42,.04);
    }

    .status-dot {
        width: .45rem;
        height: .45rem;
        border-radius: 50%;
        background: #16a34a;
        box-shadow: 0 0 0 3px rgba(22,163,74,.12);
    }

    @media (max-width: 900px) {
        .block-container {
            padding: 1rem .8rem 2rem;
        }
        .main-title {
            font-size: 2rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🌋 NER Landslide AI Command Center</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "AI-powered landslide susceptibility, dynamic risk, exposure intelligence "
    "and emergency prioritization"
    "</div>",
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="top-badges">
        <span class="badge online">● GSI INVENTORY</span>
        <span class="badge online">● DEM / TERRAIN</span>
        <span class="badge online">● DISTRICT GIS</span>
        <span class="badge online">● AI RANDOM FOREST</span>
        <span class="badge proto">◐ WEATHER PROTOTYPE</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    "SIH26001 • AI-Based Early Warning and Landslide Risk Monitoring System"
)


# LOAD FUNCTIONS
# ============================================================

@st.cache_data
def load_master():

    if MASTER_FILE.exists():
        return pd.read_csv(MASTER_FILE)

    if OLD_MASTER_FILE.exists():
        return pd.read_csv(OLD_MASTER_FILE)

    return pd.DataFrame()


@st.cache_data
def load_exposure():

    if not EXPOSURE_FILE.exists():
        return pd.DataFrame()

    return pd.read_csv(EXPOSURE_FILE)


@st.cache_data
def load_alerts():

    if not ALERT_FILE.exists():
        return pd.DataFrame()

    return pd.read_csv(ALERT_FILE)


@st.cache_data
def load_weather():

    if not WEATHER_FILE.exists():
        return pd.DataFrame()

    return pd.read_csv(WEATHER_FILE)


@st.cache_resource
def load_model():

    if not MODEL_FILE.exists():
        return None

    try:
        import joblib
        return joblib.load(MODEL_FILE)

    except Exception:
        return None


# ============================================================
# LOAD EVERYTHING
# ============================================================

df = load_master()
exposure_df = load_exposure()
alerts_df = load_alerts()
weather_df = load_weather()
model = load_model()


# ============================================================
# VALIDATION
# ============================================================

if df.empty:

    st.error(
        "❌ Master dataset not found.\n\n"
        "Expected:\n"
        "data/processed/"
        "master_landslide_dataset_with_districts.csv"
    )

    st.stop()


terrain_columns = [
    "elevation_m",
    "slope_deg",
    "aspect_sin",
    "aspect_cos",
]


missing_columns = [
    c for c in terrain_columns
    if c not in df.columns
]


if missing_columns:

    st.error(
        "❌ Required terrain columns are missing:\n\n"
        + ", ".join(missing_columns)
    )

    st.info(
        "Use the merged terrain dataset generated by "
        "merge_district_terrain.py."
    )

    st.stop()


terrain_df = df.dropna(
    subset=terrain_columns
).copy()


if terrain_df.empty:

    st.error(
        "❌ No terrain-enabled locations available."
    )

    st.stop()


# ============================================================
# WEATHER MODE
# ============================================================

weather_mode = "PROTOTYPE SCENARIO"

if not weather_df.empty:

    try:

        status = str(
            weather_df.iloc[0].get(
                "status",
                "UNKNOWN",
            )
        )

        if status.upper() == "ONLINE":
            weather_mode = "IMD LIVE"

    except Exception:

        weather_mode = "PROTOTYPE SCENARIO"


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("🎛️ Control Panel")

st.sidebar.markdown(
    "Configure the current landslide-risk scenario."
)

# ------------------------------------------------------------
# STATE
# ------------------------------------------------------------

states = []

if "state" in df.columns:

    states = sorted(
        df["state"]
        .dropna()
        .astype(str)
        .unique()
    )


selected_state = "ALL STATES"

if states:

    selected_state = st.sidebar.selectbox(
        "🇮🇳 State",
        ["ALL STATES"] + states,
    )


# ------------------------------------------------------------
# DISTRICT
# ------------------------------------------------------------

district_options = []

if selected_state != "ALL STATES":

    temp_state = df[
        df["state"].astype(str)
        == selected_state
    ]

    if "district" in temp_state.columns:

        district_options = sorted(
            temp_state["district"]
            .dropna()
            .astype(str)
            .unique()
        )


selected_district = "ALL DISTRICTS"

if district_options:

    selected_district = st.sidebar.selectbox(
        "📍 District",
        ["ALL DISTRICTS"] + district_options,
    )


# ------------------------------------------------------------
# SCENARIO INPUTS
# ------------------------------------------------------------

st.sidebar.markdown("---")

st.sidebar.subheader(
    "🌧️ Weather Scenario"
)

rainfall_24h = st.sidebar.slider(
    "Rainfall — Last 24 Hours (mm)",
    min_value=0,
    max_value=300,
    value=150,
    step=5,
)

rainfall_7d = st.sidebar.slider(
    "Rainfall — Last 7 Days (mm)",
    min_value=0,
    max_value=1000,
    value=500,
    step=10,
)

soil_moisture = st.sidebar.slider(
    "Soil Moisture (%)",
    min_value=0,
    max_value=100,
    value=67,
    step=1,
)


if weather_mode == "IMD LIVE":

    st.sidebar.success(
        "🟢 Weather Source: IMD LIVE"
    )

else:

    st.sidebar.warning(
        "🟡 Weather Source: Prototype Scenario"
    )


st.sidebar.caption(
    "Rainfall and soil-moisture values are "
    "currently scenario inputs."
)


# ============================================================
# FILTER DATA
# ============================================================

filtered_df = terrain_df.copy()


if selected_state != "ALL STATES":

    filtered_df = filtered_df[
        filtered_df["state"].astype(str)
        == selected_state
    ]


if selected_district != "ALL DISTRICTS":

    if "district" in filtered_df.columns:

        filtered_df = filtered_df[
            filtered_df["district"].astype(str)
            == selected_district
        ]


if filtered_df.empty:

    st.warning(
        "No terrain-enabled locations found "
        "for the selected region."
    )

    st.stop()


# ============================================================
# REGIONAL RISK ENGINE
# ============================================================

@st.cache_data
def calculate_regional_risk(
    input_df,
    rainfall24,
    rainfall7,
    soil,
):

    output = input_df.copy()

    x = output[
        [
            "elevation_m",
            "slope_deg",
            "aspect_sin",
            "aspect_cos",
        ]
    ].copy()

    x = x.fillna(0)

    if model is not None:

        probabilities = (
            model.predict_proba(x)[:, 1]
            * 100
        )

    else:

        probabilities = np.clip(
            (
                output["slope_deg"] * 1.5
                + output["elevation_m"] / 100
            ),
            0,
            100,
        )

    r24 = np.clip(
        rainfall24 / 150,
        0,
        1,
    )

    r7 = np.clip(
        rainfall7 / 500,
        0,
        1,
    )

    rainfall_score = (
        0.60 * r24
        + 0.40 * r7
    ) * 100

    soil_score = np.clip(
        (soil - 40) / 50,
        0,
        1,
    ) * 100

    risk = (
        0.55 * probabilities
        + 0.30 * rainfall_score
        + 0.15 * soil_score
    )

    risk = np.clip(
        risk,
        0,
        100,
    )

    levels = np.select(
        [
            risk >= 85,
            risk >= 65,
            risk >= 40,
        ],
        [
            "CRITICAL",
            "HIGH",
            "MODERATE",
        ],
        default="LOW",
    )

    output["susceptibility"] = probabilities
    output["rainfall_trigger"] = rainfall_score
    output["soil_trigger"] = soil_score
    output["risk"] = risk
    output["risk_level"] = levels.astype(str)

    return output


regional_df = calculate_regional_risk(
    filtered_df,
    rainfall_24h,
    rainfall_7d,
    soil_moisture,
)


# ============================================================
# COMMAND CENTER METRICS
# ============================================================

critical_count = int(
    (
        regional_df["risk_level"]
        == "CRITICAL"
    ).sum()
)

high_count = int(
    (
        regional_df["risk_level"]
        == "HIGH"
    ).sum()
)

moderate_count = int(
    (
        regional_df["risk_level"]
        == "MODERATE"
    ).sum()
)

low_count = int(
    (
        regional_df["risk_level"]
        == "LOW"
    ).sum()
)

average_risk = float(
    regional_df["risk"].mean()
)


# ============================================================
# TOP COMMAND CENTER
# ============================================================

st.markdown(
    '<div class="hero">',
    unsafe_allow_html=True,
)

st.markdown(
    "### 🎛️ NER Disaster Command Center"
)

region_text = selected_state

if selected_district != "ALL DISTRICTS":

    region_text = (
        f"{selected_district}, "
        f"{selected_state}"
    )

st.write(
    f"Current operational view: **{region_text}**"
)

st.markdown(
    "</div>",
    unsafe_allow_html=True,
)


m1, m2, m3, m4, m5 = st.columns(5)

m1.metric(
    "📚 GSI Locations",
    f"{len(df):,}",
)

m2.metric(
    "🚨 Critical",
    f"{critical_count:,}",
)

m3.metric(
    "🔴 High",
    f"{high_count:,}",
)

m4.metric(
    "🟡 Moderate",
    f"{moderate_count:,}",
)

m5.metric(
    "📊 Average Risk",
    f"{average_risk:.1f}%",
)


# ============================================================
# SYSTEM STATUS
# ============================================================

st.subheader("📡 System Status")

s1, s2, s3, s4, s5 = st.columns(5)

with s1:
    st.success(
        f"🟢 GSI Inventory\n{len(df):,} records"
    )

with s2:
    st.success(
        f"🟢 DEM / Terrain\n"
        f"{len(terrain_df):,} complete"
    )

with s3:
    if "district" in df.columns:
        district_count = int(
            df["district"].notna().sum()
        )
    else:
        district_count = 0

    st.success(
        f"🟢 District GIS\n"
        f"{district_count:,} mapped"
    )

with s4:

    if model is not None:

        st.success(
            "🟢 AI Model\nRandom Forest"
        )

    else:

        st.error(
            "🔴 AI Model\nUnavailable"
        )

with s5:

    if weather_mode == "IMD LIVE":

        st.success(
            "🟢 Weather\nIMD LIVE"
        )

    else:

        st.warning(
            "🟡 Weather\nPrototype"
        )


# ============================================================
# DATA COVERAGE
# ============================================================

st.subheader(
    "📡 Data & Trigger Coverage"
)

c1, c2, c3, c4 = st.columns(4)

terrain_coverage = (
    len(terrain_df)
    / max(len(df), 1)
    * 100
)

district_coverage = 0

if "district" in df.columns:

    district_coverage = (
        df["district"].notna().sum()
        / max(len(df), 1)
        * 100
    )

c1.metric(
    "⛰️ Terrain Coverage",
    f"{terrain_coverage:.1f}%",
)

c2.metric(
    "🗺️ District Coverage",
    f"{district_coverage:.1f}%",
)

c3.metric(
    "🌧️ 24h Rainfall",
    f"{rainfall_24h} mm",
)

c4.metric(
    "🌧️ 7-day Rainfall",
    f"{rainfall_7d} mm",
)


# ============================================================
# COMMAND ALERT
# ============================================================

if critical_count > 0:

    st.error(
        f"""
        🚨 **COMMAND CENTER ALERT**

        **{critical_count:,} locations** are currently
        classified as **CRITICAL** under the selected scenario.

        Recommended:
        - Prioritize field verification
        - Inspect nearby road corridors
        - Review evacuation requirements
        - Prepare disaster-response resources
        """
    )

elif high_count > 0:

    st.warning(
        f"""
        ⚠️ **HIGH-RISK SITUATION**

        **{high_count:,} locations** are currently
        classified as **HIGH** risk.
        """
    )

else:

    st.success(
        "🟢 No immediate high-risk situation "
        "detected under the selected scenario."
    )


# ============================================================
# EMERGENCY PRIORITIZATION
# ============================================================

st.subheader(
    "🚑 Emergency Prioritization"
)

emergency = regional_df.copy()

if not exposure_df.empty:

    exposure_unique = (
        exposure_df
        .drop_duplicates(
            subset=[
                "latitude",
                "longitude",
            ]
        )
        .copy()
    )

    risk_merge = regional_df[
        [
            "latitude",
            "longitude",
            "risk",
            "susceptibility",
        ]
    ].copy()

    emergency = exposure_unique.merge(
        risk_merge,
        on=[
            "latitude",
            "longitude",
        ],
        how="left",
    )

else:

    emergency["exposure_score"] = 0


emergency["risk"] = (
    pd.to_numeric(
        emergency["risk"],
        errors="coerce",
    ).fillna(0)
)

if "exposure_score" not in emergency.columns:

    emergency["exposure_score"] = 0

emergency["exposure_score"] = (
    pd.to_numeric(
        emergency["exposure_score"],
        errors="coerce",
    ).fillna(0)
)

emergency["priority_score"] = (
    0.65 * emergency["risk"]
    + 0.35 * emergency["exposure_score"]
)

emergency["command_score"] = (
    0.60 * emergency["risk"]
    + 0.25 * emergency["exposure_score"]
    + 0.15 * emergency["priority_score"]
)

emergency["command_score"] = (
    emergency["command_score"]
    .clip(0, 100)
)

emergency["command_level"] = np.select(
    [
        emergency["command_score"] >= 75,
        emergency["command_score"] >= 50,
        emergency["command_score"] >= 25,
    ],
    [
        "IMMEDIATE ACTION",
        "HIGH PRIORITY",
        "MONITOR",
    ],
    default="ROUTINE",
)


immediate = int(
    (
        emergency["command_level"]
        == "IMMEDIATE ACTION"
    ).sum()
)

high_priority = int(
    (
        emergency["command_level"]
        == "HIGH PRIORITY"
    ).sum()
)

monitor = int(
    (
        emergency["command_level"]
        == "MONITOR"
    ).sum()
)

routine = int(
    (
        emergency["command_level"]
        == "ROUTINE"
    ).sum()
)


e1, e2, e3, e4 = st.columns(4)

e1.metric(
    "🚨 Immediate",
    f"{immediate:,}",
)

e2.metric(
    "🔴 High Priority",
    f"{high_priority:,}",
)

e3.metric(
    "🟡 Monitor",
    f"{monitor:,}",
)

e4.metric(
    "🟢 Routine",
    f"{routine:,}",
)


# ============================================================
# RISK DISTRIBUTION
# ============================================================

st.subheader(
    "📊 Risk Distribution"
)

distribution = pd.DataFrame(
    {
        "Risk Level": [
            "CRITICAL",
            "HIGH",
            "MODERATE",
            "LOW",
        ],
        "Locations": [
            critical_count,
            high_count,
            moderate_count,
            low_count,
        ],
    }
)

st.bar_chart(
    distribution.set_index(
        "Risk Level"
    )
)


# ============================================================
# DYNAMIC RISK MAP
# ============================================================

st.subheader(
    "🗺️ Dynamic Landslide Risk Heatmap"
)

risk_map = regional_df[
    [
        "latitude",
        "longitude",
        "risk",
        "risk_level",
        "slope_deg",
        "elevation_m",
    ]
].dropna().copy()


def get_rgb(level):

    if level == "CRITICAL":
        return [210, 0, 0]

    if level == "HIGH":
        return [255, 100, 0]

    if level == "MODERATE":
        return [240, 190, 0]

    return [0, 150, 0]


risk_map["color"] = (
    risk_map["risk_level"]
    .apply(get_rgb)
)


if len(risk_map) > 8000:

    risk_display = (
        risk_map
        .nlargest(8000, "risk")
    )

else:

    risk_display = risk_map


if not risk_display.empty:

    risk_layer = pdk.Layer(
        "ScatterplotLayer",
        data=risk_display,
        get_position="[longitude, latitude]",
        get_fill_color="color",
        get_radius=1300,
        pickable=True,
        opacity=0.65,
    )

    risk_view = pdk.ViewState(
        latitude=float(
            risk_display["latitude"].mean()
        ),
        longitude=float(
            risk_display["longitude"].mean()
        ),
        zoom=4.5,
    )

    risk_deck = pdk.Deck(
        layers=[risk_layer],
        initial_view_state=risk_view,
        tooltip={
            "html": """
            <b>Risk:</b> {risk}%<br/>
            <b>Level:</b> {risk_level}<br/>
            <b>Slope:</b> {slope_deg}°<br/>
            <b>Elevation:</b> {elevation_m} m
            """
        },
    )

    st.pydeck_chart(
        risk_deck,
        use_container_width=True,
    )


st.caption(
    "Dynamic scenario risk combines AI susceptibility "
    "with rainfall and soil-moisture triggers."
)


# ============================================================
# HISTORICAL GSI MAP
# ============================================================

st.subheader(
    "📚 Historical GSI Landslide Inventory"
)

hist_map = df[
    [
        "latitude",
        "longitude",
    ]
].dropna().drop_duplicates().copy()

hist_map["color"] = [
    [190, 30, 30]
] * len(hist_map)


if len(hist_map) > 12000:

    hist_display = hist_map.sample(
        12000,
        random_state=42,
    )

else:

    hist_display = hist_map


if not hist_display.empty:

    hist_layer = pdk.Layer(
        "ScatterplotLayer",
        data=hist_display,
        get_position="[longitude, latitude]",
        get_fill_color="color",
        get_radius=800,
        pickable=True,
    )

    hist_view = pdk.ViewState(
        latitude=float(
            hist_display["latitude"].mean()
        ),
        longitude=float(
            hist_display["longitude"].mean()
        ),
        zoom=4.5,
    )

    hist_deck = pdk.Deck(
        layers=[hist_layer],
        initial_view_state=hist_view,
        tooltip={
            "html": """
            <b>Historical GSI Landslide</b><br/>
            Latitude: {latitude}<br/>
            Longitude: {longitude}
            """
        },
    )

    st.pydeck_chart(
        hist_deck,
        use_container_width=True,
    )


st.caption(
    f"Displaying {len(hist_display):,} historical GSI locations."
)


# ============================================================
# TOP 10 RISK LOCATIONS
# ============================================================

st.subheader(
    "🚨 Top 10 Highest-Risk Locations"
)

top_risk = regional_df.nlargest(
    10,
    "risk",
).copy()


top_columns = [
    "latitude",
    "longitude",
    "state",
    "district",
    "risk",
    "risk_level",
    "susceptibility",
    "slope_deg",
    "elevation_m",
]

top_columns = [
    c for c in top_columns
    if c in top_risk.columns
]


st.dataframe(
    top_risk[
        top_columns
    ].round(2),
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# LOCATION RISK ANALYSIS
# ============================================================

st.subheader(
    "📍 Location Risk Analysis"
)

location_labels = [
    (
        f"{row.latitude:.5f}, "
        f"{row.longitude:.5f}"
    )
    for _, row in regional_df.iterrows()
]


selected_location_index = st.selectbox(
    "Select location",
    range(len(location_labels)),
    format_func=lambda x:
        location_labels[x],
)


selected = regional_df.iloc[
    selected_location_index
]


elevation = float(
    selected["elevation_m"]
)

slope = float(
    selected["slope_deg"]
)

aspect_sin = float(
    selected["aspect_sin"]
)

aspect_cos = float(
    selected["aspect_cos"]
)

aspect_deg = (
    np.degrees(
        np.arctan2(
            aspect_sin,
            aspect_cos,
        )
    )
    + 360
) % 360


# ============================================================
# SELECTED LOCATION RISK
# ============================================================

if RISK_ENGINE_AVAILABLE:

    try:

        risk_result = calculate_risk(
            elevation_m=elevation,
            slope_deg=slope,
            aspect_deg=aspect_deg,
            rainfall_24h=rainfall_24h,
            rainfall_7d=rainfall_7d,
            soil_moisture=soil_moisture,
        )

        susceptibility = float(
            risk_result["susceptibility"]
        )

        rainfall_trigger = float(
            risk_result["rainfall_trigger"]
        )

        soil_trigger = float(
            risk_result["soil_moisture_trigger"]
        )

        final_risk = float(
            risk_result["final_risk"]
        )

        risk_level = str(
            risk_result["risk_level"]
        )

        risk_message = str(
            risk_result["message"]
        )

    except Exception:

        susceptibility = float(
            selected["susceptibility"]
        )

        rainfall_trigger = float(
            selected["rainfall_trigger"]
        )

        soil_trigger = float(
            selected["soil_trigger"]
        )

        final_risk = float(
            selected["risk"]
        )

        risk_level = str(
            selected["risk_level"]
        )

        risk_message = (
            "Risk calculated using prototype "
            "regional risk engine."
        )

else:

    susceptibility = float(
        selected["susceptibility"]
    )

    rainfall_trigger = float(
        selected["rainfall_trigger"]
    )

    soil_trigger = float(
        selected["soil_trigger"]
    )

    final_risk = float(
        selected["risk"]
    )

    risk_level = str(
        selected["risk_level"]
    )

    risk_message = (
        "Risk calculated using prototype "
        "regional risk engine."
    )


# ============================================================
# RISK CARDS
# ============================================================

r1, r2, r3, r4, r5 = st.columns(5)

r1.metric(
    "🧠 AI Susceptibility",
    f"{susceptibility:.1f}%",
)

r2.metric(
    "🌧️ Rain Trigger",
    f"{rainfall_trigger:.1f}",
)

r3.metric(
    "💧 Soil Trigger",
    f"{soil_trigger:.1f}",
)

r4.metric(
    "⚠️ Final Risk",
    f"{final_risk:.1f}%",
)

r5.metric(
    "Risk Level",
    risk_level,
)


# ============================================================
# RISK MESSAGE
# ============================================================

if risk_level == "CRITICAL":

    st.markdown(
        f"""
        <div class="critical-box">
        <h3>🚨 CRITICAL LANDSLIDE RISK</h3>
        <b>{risk_message}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

elif risk_level == "HIGH":

    st.markdown(
        f"""
        <div class="high-box">
        <h3>⚠️ HIGH LANDSLIDE RISK</h3>
        <b>{risk_message}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

elif risk_level == "MODERATE":

    st.markdown(
        f"""
        <div class="moderate-box">
        <h3>🟡 MODERATE LANDSLIDE RISK</h3>
        <b>{risk_message}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

else:

    st.markdown(
        f"""
        <div class="low-box">
        <h3>🟢 LOW LANDSLIDE RISK</h3>
        <b>{risk_message}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LOCATION DETAILS
# ============================================================

st.subheader(
    "📌 Location Details"
)

l1, l2, l3, l4, l5 = st.columns(5)

l1.metric(
    "Latitude",
    f"{float(selected['latitude']):.5f}",
)

l2.metric(
    "Longitude",
    f"{float(selected['longitude']):.5f}",
)

l3.metric(
    "Elevation",
    f"{elevation:.1f} m",
)

l4.metric(
    "Slope",
    f"{slope:.1f}°",
)

if "state" in selected.index:

    l5.metric(
        "State",
        str(selected["state"]),
    )


if "district" in selected.index:

    st.write(
        f"**District:** {selected['district']}"
    )


st.write(
    f"**Coordinates:** "
    f"{float(selected['latitude']):.6f}, "
    f"{float(selected['longitude']):.6f}"
)


# ============================================================
# RISK BREAKDOWN
# ============================================================

st.subheader(
    "🧠 Risk Breakdown"
)

breakdown_df = pd.DataFrame(
    {
        "Factor": [
            "AI Susceptibility",
            "Rainfall Trigger",
            "Soil Moisture",
        ],
        "Score": [
            susceptibility,
            rainfall_trigger,
            soil_trigger,
        ],
    }
)

st.bar_chart(
    breakdown_df.set_index(
        "Factor"
    )
)

st.caption(
    "Prototype risk composition: "
    "55% terrain susceptibility + "
    "30% rainfall trigger + "
    "15% soil-moisture trigger."
)


# ============================================================
# SELECTED LOCATION MAP
# ============================================================

st.subheader(
    "🗺️ Selected Location Map"
)

selected_map = pd.DataFrame(
    {
        "latitude": [
            float(selected["latitude"])
        ],
        "longitude": [
            float(selected["longitude"])
        ],
        "risk": [
            final_risk
        ],
        "risk_level": [
            risk_level
        ],
        "color": [
            get_rgb(risk_level)
        ],
    }
)


selected_layer = pdk.Layer(
    "ScatterplotLayer",
    data=selected_map,
    get_position="[longitude, latitude]",
    get_fill_color="color",
    get_radius=3000,
    pickable=True,
)


selected_view = pdk.ViewState(
    latitude=float(
        selected["latitude"]
    ),
    longitude=float(
        selected["longitude"]
    ),
    zoom=7,
)


selected_deck = pdk.Deck(
    layers=[selected_layer],
    initial_view_state=selected_view,
    tooltip={
        "html": """
        <b>Risk:</b> {risk}%<br/>
        <b>Level:</b> {risk_level}
        """
    },
)


st.pydeck_chart(
    selected_deck,
    use_container_width=True,
)


# ============================================================
# TERRAIN ANALYSIS
# ============================================================

st.subheader(
    "⛰️ Terrain Analysis"
)

t1, t2, t3, t4 = st.columns(4)

t1.metric(
    "Elevation",
    f"{elevation:.1f} m",
)

t2.metric(
    "Slope",
    f"{slope:.1f}°",
)

t3.metric(
    "Aspect",
    f"{aspect_deg:.1f}°",
)

if "historical_landslide_count" in selected.index:

    historical_count = pd.to_numeric(
        selected["historical_landslide_count"],
        errors="coerce",
    )

    if pd.isna(historical_count):
        historical_count = 0

else:

    historical_count = 0


t4.metric(
    "Historical Nearby",
    f"{int(historical_count)}",
)


terrain_summary = pd.DataFrame(
    {
        "Terrain Feature": [
            "Elevation (m)",
            "Slope (degrees)",
            "Aspect (degrees)",
        ],
        "Value": [
            elevation,
            slope,
            aspect_deg,
        ],
    }
)

st.dataframe(
    terrain_summary.round(2),
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# HISTORICAL INTELLIGENCE
# ============================================================

st.subheader(
    "📚 Historical Intelligence"
)

if "historical_landslide_count" in regional_df.columns:

    historical_series = pd.to_numeric(
        regional_df[
            "historical_landslide_count"
        ],
        errors="coerce",
    ).fillna(0)

    h1, h2, h3 = st.columns(3)

    h1.metric(
        "Historical Locations",
        f"{int((historical_series > 0).sum()):,}",
    )

    h2.metric(
        "Max Historical Count",
        f"{int(historical_series.max()):,}",
    )

    h3.metric(
        "Avg Historical Count",
        f"{historical_series.mean():.2f}",
    )

else:

    st.info(
        "Historical count field unavailable."
    )


# ============================================================
# WEATHER & TRIGGER MONITOR
# ============================================================

st.subheader(
    "🌧️ Weather & Trigger Monitor"
)

w1, w2, w3 = st.columns(3)

w1.metric(
    "24h Rainfall",
    f"{rainfall_24h} mm",
)

w2.metric(
    "7-day Rainfall",
    f"{rainfall_7d} mm",
)

w3.metric(
    "Trigger Intensity",
    f"{rainfall_trigger:.1f}%",
)


if rainfall_24h >= 150:

    st.error(
        "🚨 High short-term rainfall scenario."
    )

elif rainfall_24h >= 100:

    st.warning(
        "⚠️ Elevated short-term rainfall scenario."
    )

else:

    st.info(
        "🟢 Short-term rainfall below prototype "
        "high-trigger level."
    )


if rainfall_7d >= 500:

    st.warning(
        "⚠️ High cumulative rainfall scenario."
    )


st.caption(
    "Prototype weather layer. Connect official IMD "
    "feeds for operational deployment."
)


# ============================================================
# WHAT-IF SCENARIO SIMULATOR
# ============================================================

st.subheader(
    "🔮 What-If Scenario Simulator"
)

projected_rainfall = st.slider(
    "Projected next 24-hour rainfall (mm)",
    min_value=0,
    max_value=500,
    value=min(
        250,
        rainfall_24h + 50,
    ),
    step=10,
    key="projected_rain",
)


scenario_regional = calculate_regional_risk(
    filtered_df,
    projected_rainfall,
    rainfall_7d,
    soil_moisture,
)


current_average = float(
    regional_df["risk"].mean()
)

scenario_average = float(
    scenario_regional["risk"].mean()
)

change = (
    scenario_average
    - current_average
)


q1, q2, q3 = st.columns(3)

q1.metric(
    "Current Average Risk",
    f"{current_average:.1f}%",
)

q2.metric(
    "Scenario Risk",
    f"{scenario_average:.1f}%",
)

q3.metric(
    "Risk Change",
    f"{change:+.1f}%",
)


if change > 10:

    st.error(
        "🚨 Significant increase in projected risk."
    )

elif change > 0:

    st.warning(
        "⚠️ Increased rainfall raises projected risk."
    )

else:

    st.success(
        "🟢 Projected scenario does not increase "
        "average regional risk."
    )


# ============================================================
# STATE / DISTRICT COMMAND VIEW
# ============================================================

st.subheader(
    "🗺️ State → District Command View"
)

if "state" in regional_df.columns:

    command_states = sorted(
        regional_df["state"]
        .dropna()
        .astype(str)
        .unique()
    )

    if command_states:

        command_state = st.selectbox(
            "Command State",
            command_states,
            key="command_state",
        )

        state_df = regional_df[
            regional_df["state"].astype(str)
            == command_state
        ].copy()

        command_districts = []

        if "district" in state_df.columns:

            command_districts = sorted(
                state_df["district"]
                .dropna()
                .astype(str)
                .unique()
            )

        command_district = "ALL DISTRICTS"

        if command_districts:

            command_district = st.selectbox(
                "Command District",
                [
                    "ALL DISTRICTS"
                ]
                + command_districts,
                key="command_district",
            )

        if (
            command_district
            != "ALL DISTRICTS"
            and "district" in state_df.columns
        ):

            area_df = state_df[
                state_df["district"].astype(str)
                == command_district
            ].copy()

            area_name = (
                f"{command_district}, "
                f"{command_state}"
            )

        else:

            area_df = state_df.copy()

            area_name = command_state

        if not area_df.empty:

            avg_area_risk = float(
                area_df["risk"].mean()
            )

            max_area_risk = float(
                area_df["risk"].max()
            )

            high_area = int(
                (
                    area_df["risk"]
                    >= 65
                ).sum()
            )

            a1, a2, a3, a4 = st.columns(4)

            a1.metric(
                "Locations",
                f"{len(area_df):,}",
            )

            a2.metric(
                "Average Risk",
                f"{avg_area_risk:.1f}%",
            )

            a3.metric(
                "Maximum Risk",
                f"{max_area_risk:.1f}%",
            )

            a4.metric(
                "High + Critical",
                f"{high_area:,}",
            )

            st.markdown(
                f"### Top Risk Locations — {area_name}"
            )

            area_top = area_df.nlargest(
                10,
                "risk",
            )

            area_columns = [
                "latitude",
                "longitude",
                "risk",
                "risk_level",
                "slope_deg",
                "elevation_m",
            ]

            area_columns = [
                c for c in area_columns
                if c in area_top.columns
            ]

            st.dataframe(
                area_top[
                    area_columns
                ].round(2),
                use_container_width=True,
                hide_index=True,
            )

            area_map = area_df[
                [
                    "latitude",
                    "longitude",
                    "risk",
                    "risk_level",
                ]
            ].dropna().copy()

            area_map["color"] = (
                area_map["risk_level"]
                .apply(get_rgb)
            )

            if len(area_map) > 5000:

                area_map = (
                    area_map
                    .nlargest(5000, "risk")
                )

            if not area_map.empty:

                area_layer = pdk.Layer(
                    "ScatterplotLayer",
                    data=area_map,
                    get_position="[longitude, latitude]",
                    get_fill_color="color",
                    get_radius=1100,
                    pickable=True,
                    opacity=0.7,
                )

                area_view = pdk.ViewState(
                    latitude=float(
                        area_map["latitude"].mean()
                    ),
                    longitude=float(
                        area_map["longitude"].mean()
                    ),
                    zoom=7,
                )

                area_deck = pdk.Deck(
                    layers=[area_layer],
                    initial_view_state=area_view,
                    tooltip={
                        "html": """
                        <b>Risk:</b> {risk}%<br/>
                        <b>Level:</b> {risk_level}
                        """
                    },
                )

                st.pydeck_chart(
                    area_deck,
                    use_container_width=True,
                )


# ============================================================
# ROAD + SETTLEMENT EXPOSURE
# ============================================================

st.subheader(
    "🛣️ Road & Settlement Exposure"
)

if not exposure_df.empty:

    exposure_unique = (
        exposure_df
        .drop_duplicates(
            subset=[
                "latitude",
                "longitude",
            ]
        )
        .copy()
    )

    x1, x2, x3, x4 = st.columns(4)

    x1.metric(
        "Landslide Locations",
        f"{len(exposure_unique):,}",
    )

    if "nearest_road_km" in exposure_unique.columns:

        x2.metric(
            "Avg Road Distance",
            f"{exposure_unique['nearest_road_km'].mean():.2f} km",
        )

    else:

        x2.metric(
            "Road Distance",
            "N/A",
        )

    if "nearest_settlement_km" in exposure_unique.columns:

        x3.metric(
            "Avg Settlement Distance",
            f"{exposure_unique['nearest_settlement_km'].mean():.2f} km",
        )

    else:

        x3.metric(
            "Settlement Distance",
            "N/A",
        )

    if "exposure_score" in exposure_unique.columns:

        x4.metric(
            "Avg Exposure",
            f"{exposure_unique['exposure_score'].mean():.1f}",
        )

    else:

        x4.metric(
            "Exposure",
            "N/A",
        )

    st.info(
        "A landslide is not equally dangerous everywhere. "
        "The system prioritizes locations where susceptibility "
        "overlaps with roads and settlements."
    )

else:

    st.warning(
        "Exposure dataset unavailable."
    )


# ============================================================
# HIGHEST PRIORITY INTERVENTIONS
# ============================================================

st.subheader(
    "🚑 Highest Priority Intervention Locations"
)

priority_columns = [
    "latitude",
    "longitude",
    "risk",
    "susceptibility",
    "exposure_score",
    "priority_score",
    "command_score",
    "command_level",
    "nearest_road_km",
    "nearest_settlement_km",
]

priority_columns = [
    c for c in priority_columns
    if c in emergency.columns
]


emergency_top = emergency.nlargest(
    15,
    "command_score",
)


st.dataframe(
    emergency_top[
        priority_columns
    ].round(2),
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# AUTOMATED ALERT CENTER
# ============================================================

st.subheader(
    "🚨 Automated Early-Warning Alert Center"
)

if not alerts_df.empty:

    alert_view = (
        alerts_df
        .drop_duplicates(
            subset=[
                "latitude",
                "longitude",
            ]
        )
        .copy()
    )

    if "alert_level" in alert_view.columns:

        alert_counts = (
            alert_view["alert_level"]
            .value_counts()
        )

        z1, z2, z3, z4 = st.columns(4)

        z1.metric(
            "🚨 Immediate",
            int(
                alert_counts.get(
                    "IMMEDIATE ACTION",
                    0,
                )
            ),
        )

        z2.metric(
            "🔴 High",
            int(
                alert_counts.get(
                    "HIGH PRIORITY",
                    0,
                )
            ),
        )

        z3.metric(
            "🟡 Monitor",
            int(
                alert_counts.get(
                    "MONITOR",
                    0,
                )
            ),
        )

        z4.metric(
            "🟢 Routine",
            int(
                alert_counts.get(
                    "ROUTINE",
                    0,
                )
            ),
        )

    st.markdown(
        """
        Alert engine combines:

        **AI susceptibility + rainfall trigger +
        soil moisture + exposure + emergency priority**
        """
    )

    alert_columns = [
        "latitude",
        "longitude",
        "risk_level",
        "alert_level",
        "risk_score",
        "exposure_score",
        "nearest_road_km",
        "nearest_settlement_km",
    ]

    alert_columns = [
        c for c in alert_columns
        if c in alert_view.columns
    ]

    sort_column = None

    if "command_priority" in alert_view.columns:

        sort_column = "command_priority"

    elif "risk_score" in alert_view.columns:

        sort_column = "risk_score"

    if sort_column:

        alert_view = alert_view.sort_values(
            sort_column,
            ascending=False,
        )

    st.dataframe(
        alert_view[
            alert_columns
        ].head(20),
        use_container_width=True,
        hide_index=True,
    )

else:

    st.info(
        "Alert engine ready for live integration."
    )


# ============================================================
# ACTIVE ALERT MAP
# ============================================================

st.subheader(
    "🗺️ Active Alert Map"
)

if not alerts_df.empty:

    alert_map = alerts_df[
        [
            "latitude",
            "longitude",
        ]
    ].dropna().drop_duplicates().copy()

    if "alert_level" in alerts_df.columns:

        levels = (
            alerts_df[
                [
                    "latitude",
                    "longitude",
                    "alert_level",
                ]
            ]
            .drop_duplicates(
                subset=[
                    "latitude",
                    "longitude",
                ]
            )
        )

        alert_map = alert_map.merge(
            levels,
            on=[
                "latitude",
                "longitude",
            ],
            how="left",
        )

    else:

        alert_map["alert_level"] = (
            "MONITOR"
        )

    def alert_color(level):

        if level == "IMMEDIATE ACTION":
            return [210, 0, 0]

        if level == "HIGH PRIORITY":
            return [255, 100, 0]

        if level == "MONITOR":
            return [240, 190, 0]

        return [0, 150, 0]

    alert_map["color"] = (
        alert_map["alert_level"]
        .apply(alert_color)
    )

    if len(alert_map) > 10000:

        alert_display = alert_map.sample(
            10000,
            random_state=42,
        )

    else:

        alert_display = alert_map

    if not alert_display.empty:

        alert_layer = pdk.Layer(
            "ScatterplotLayer",
            data=alert_display,
            get_position="[longitude, latitude]",
            get_fill_color="color",
            get_radius=1000,
            pickable=True,
            opacity=0.7,
        )

        alert_view = pdk.ViewState(
            latitude=float(
                alert_display["latitude"].mean()
            ),
            longitude=float(
                alert_display["longitude"].mean()
            ),
            zoom=4.5,
        )

        alert_deck = pdk.Deck(
            layers=[alert_layer],
            initial_view_state=alert_view,
            tooltip={
                "html": """
                <b>Alert:</b> {alert_level}<br/>
                Latitude: {latitude}<br/>
                Longitude: {longitude}
                """
            },
        )

        st.pydeck_chart(
            alert_deck,
            use_container_width=True,
        )


# ============================================================
# DECISION SUPPORT
# ============================================================

st.subheader(
    "🧠 Decision Support"
)

decision = regional_df.copy()


if "historical_landslide_count" in decision.columns:

    historical = pd.to_numeric(
        decision[
            "historical_landslide_count"
        ],
        errors="coerce",
    ).fillna(0)

    historical_score = (
        np.clip(
            historical,
            0,
            10,
        )
        / 10
        * 100
    )

else:

    historical_score = np.zeros(
        len(decision)
    )


decision["historical_score"] = (
    historical_score
)

decision["priority_score"] = (
    0.65 * decision["risk"]
    + 0.20 * decision["susceptibility"]
    + 0.15 * decision["historical_score"]
)

decision["priority_score"] = (
    decision["priority_score"]
    .clip(0, 100)
)


decision["action"] = np.select(
    [
        decision["priority_score"] >= 75,
        decision["priority_score"] >= 50,
        decision["priority_score"] >= 25,
    ],
    [
        "IMMEDIATE ACTION",
        "HIGH PRIORITY",
        "MONITOR",
    ],
    default="ROUTINE",
)


def explain_risk(row):

    reasons = []

    if row["slope_deg"] >= 35:

        reasons.append(
            "Very steep terrain"
        )

    elif row["slope_deg"] >= 25:

        reasons.append(
            "Steep terrain"
        )

    if row["susceptibility"] >= 75:

        reasons.append(
            "High AI susceptibility"
        )

    if rainfall_24h >= 150:

        reasons.append(
            "Heavy 24-hour rainfall scenario"
        )

    elif rainfall_24h >= 100:

        reasons.append(
            "Elevated short-term rainfall"
        )

    if rainfall_7d >= 500:

        reasons.append(
            "High cumulative rainfall"
        )

    if soil_moisture >= 75:

        reasons.append(
            "High soil moisture"
        )

    if row["historical_score"] >= 50:

        reasons.append(
            "Historical landslide evidence"
        )

    if not reasons:

        reasons.append(
            "No dominant trigger detected"
        )

    return ", ".join(reasons)


decision["reason"] = decision.apply(
    explain_risk,
    axis=1,
)


priority_view = decision.nlargest(
    15,
    "priority_score",
)


decision_columns = [
    "latitude",
    "longitude",
    "state",
    "district",
    "priority_score",
    "action",
    "risk",
    "susceptibility",
    "slope_deg",
    "reason",
]

decision_columns = [
    c for c in decision_columns
    if c in priority_view.columns
]


st.dataframe(
    priority_view[
        decision_columns
    ].round(2),
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# FIELD VERIFICATION / CITIZEN REPORTING
# ============================================================

st.subheader(
    "📱 Field Verification & Citizen Reporting"
)

st.markdown(
    """
    Report fresh ground-level evidence such as:

    **cracks • road blockages • rockfalls • soil movement •
    active landslides • flooding**

    The report is combined with the AI risk score to
    prioritize field response.
    """
)


with st.form(
    "field_report_form"
):

    st.markdown(
        "### 📍 Incident Information"
    )

    f1, f2 = st.columns(2)

    with f1:

        report_latitude = st.number_input(
            "Latitude",
            value=float(
                selected["latitude"]
            ),
            format="%.6f",
        )

    with f2:

        report_longitude = st.number_input(
            "Longitude",
            value=float(
                selected["longitude"]
            ),
            format="%.6f",
        )

    f3, f4 = st.columns(2)

    with f3:

        report_type = st.selectbox(
            "Incident Type",
            [
                "Fresh crack",
                "Road blockage",
                "Rockfall",
                "Soil movement",
                "Active landslide",
                "Flooding",
                "Other",
            ],
        )

    with f4:

        report_severity = st.selectbox(
            "Observed Severity",
            [
                "LOW",
                "MODERATE",
                "HIGH",
                "CRITICAL",
            ],
        )

    reporter_type = st.selectbox(
        "Reporter Type",
        [
            "Citizen",
            "Field Officer",
            "Disaster Response Team",
        ],
    )

    report_description = st.text_area(
        "Description",
        placeholder=(
            "Describe what is happening "
            "at the location..."
        ),
        height=100,
    )

    uploaded_photo = st.file_uploader(
        "📷 Upload Evidence Photo",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
        ],
    )

    submitted = st.form_submit_button(
        "🚨 Submit Field Report",
        use_container_width=True,
    )


# ============================================================
# FIELD REPORT PROCESSING
# ============================================================

if submitted:

    FIELD_REPORT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    try:

        distances = (
            (
                terrain_df["latitude"]
                - report_latitude
            ) ** 2
            +
            (
                terrain_df["longitude"]
                - report_longitude
            ) ** 2
        )

        nearest_index = distances.idxmin()

        nearest = terrain_df.loc[
            nearest_index
        ]

        nearest_elevation = float(
            nearest["elevation_m"]
        )

        nearest_slope = float(
            nearest["slope_deg"]
        )

        nearest_aspect_sin = float(
            nearest["aspect_sin"]
        )

        nearest_aspect_cos = float(
            nearest["aspect_cos"]
        )

        nearest_aspect = (
            np.degrees(
                np.arctan2(
                    nearest_aspect_sin,
                    nearest_aspect_cos,
                )
            )
            + 360
        ) % 360

        if RISK_ENGINE_AVAILABLE:

            field_risk_result = calculate_risk(
                elevation_m=nearest_elevation,
                slope_deg=nearest_slope,
                aspect_deg=nearest_aspect,
                rainfall_24h=rainfall_24h,
                rainfall_7d=rainfall_7d,
                soil_moisture=soil_moisture,
            )

            field_ai_risk = float(
                field_risk_result[
                    "final_risk"
                ]
            )

            field_susceptibility = float(
                field_risk_result[
                    "susceptibility"
                ]
            )

        else:

            field_ai_risk = 0.0
            field_susceptibility = 0.0

    except Exception:

        field_ai_risk = 0.0
        field_susceptibility = 0.0
        nearest_slope = 0.0
        nearest_elevation = 0.0


    severity_scores = {
        "LOW": 20,
        "MODERATE": 45,
        "HIGH": 70,
        "CRITICAL": 100,
    }


    evidence_score = (
        severity_scores[
            report_severity
        ]
    )


    incident_boost = {
        "Fresh crack": 10,
        "Road blockage": 15,
        "Rockfall": 15,
        "Soil movement": 10,
        "Active landslide": 25,
        "Flooding": 10,
        "Other": 5,
    }


    evidence_score = min(
        100,
        evidence_score
        + incident_boost.get(
            report_type,
            0,
        ),
    )


    combined_priority = (
        0.50 * field_ai_risk
        + 0.50 * evidence_score
    )


    combined_priority = np.clip(
        combined_priority,
        0,
        100,
    )


    if combined_priority >= 75:

        field_alert = "IMMEDIATE ACTION"

    elif combined_priority >= 50:

        field_alert = "HIGH PRIORITY"

    elif combined_priority >= 25:

        field_alert = "MONITOR"

    else:

        field_alert = "ROUTINE"


    report_data = {
        "timestamp":
            pd.Timestamp.now().isoformat(),

        "latitude":
            report_latitude,

        "longitude":
            report_longitude,

        "report_type":
            report_type,

        "severity":
            report_severity,

        "reporter_type":
            reporter_type,

        "description":
            report_description,

        "ai_risk":
            round(
                field_ai_risk,
                2,
            ),

        "ai_susceptibility":
            round(
                field_susceptibility,
                2,
            ),

        "evidence_score":
            round(
                evidence_score,
                2,
            ),

        "combined_priority":
            round(
                combined_priority,
                2,
            ),

        "alert_level":
            field_alert,

        "nearest_slope_deg":
            round(
                nearest_slope,
                2,
            ),

        "nearest_elevation_m":
            round(
                nearest_elevation,
                2,
            ),

        "photo_uploaded":
            uploaded_photo is not None,
    }


    new_report = pd.DataFrame(
        [report_data]
    )


    if FIELD_REPORT_FILE.exists():

        old_reports = pd.read_csv(
            FIELD_REPORT_FILE
        )

        new_report = pd.concat(
            [
                old_reports,
                new_report,
            ],
            ignore_index=True,
        )


    new_report.to_csv(
        FIELD_REPORT_FILE,
        index=False,
    )


    # --------------------------------------------------------
    # SAVE PHOTO
    # --------------------------------------------------------

    if uploaded_photo is not None:

        timestamp_name = (
            pd.Timestamp.now()
            .strftime(
                "%Y%m%d_%H%M%S"
            )
        )

        extension = (
            uploaded_photo.name
            .split(".")[-1]
        )

        photo_name = (
            f"field_report_"
            f"{timestamp_name}."
            f"{extension}"
        )

        photo_path = (
            FIELD_REPORT_DIR
            / photo_name
        )

        with open(
            photo_path,
            "wb",
        ) as f:

            f.write(
                uploaded_photo.getbuffer()
            )


    st.success(
        "✅ Field report submitted successfully."
    )


    st.markdown(
        "### 🚨 Field Verification Result"
    )


    fr1, fr2, fr3, fr4 = st.columns(4)

    fr1.metric(
        "AI Risk",
        f"{field_ai_risk:.1f}%",
    )

    fr2.metric(
        "Evidence Score",
        f"{evidence_score:.1f}",
    )

    fr3.metric(
        "Combined Priority",
        f"{combined_priority:.1f}",
    )

    fr4.metric(
        "Alert Level",
        field_alert,
    )


    if field_alert == "IMMEDIATE ACTION":

        st.error(
            """
            🚨 **IMMEDIATE ACTION RECOMMENDED**

            Recommended:
            - Dispatch field verification team
            - Inspect nearby road corridors
            - Assess evacuation requirements
            - Notify disaster management authorities
            """
        )

    elif field_alert == "HIGH PRIORITY":

        st.warning(
            """
            ⚠️ **HIGH PRIORITY**

            Recommended:
            - Send field team
            - Inspect slope and infrastructure
            - Continue rainfall monitoring
            """
        )

    elif field_alert == "MONITOR":

        st.info(
            """
            🟡 **MONITOR**

            Track the report and re-evaluate if
            rainfall or ground movement increases.
            """
        )

    else:

        st.success(
            """
            🟢 **ROUTINE**

            Report recorded for future monitoring.
            """
        )


# ============================================================
# FIELD REPORT HISTORY
# ============================================================

st.subheader(
    "📋 Field Report History"
)

if FIELD_REPORT_FILE.exists():

    try:

        previous_reports = pd.read_csv(
            FIELD_REPORT_FILE
        )

        st.metric(
            "Total Field Reports",
            f"{len(previous_reports):,}",
        )

        report_columns = [
            "timestamp",
            "latitude",
            "longitude",
            "report_type",
            "severity",
            "reporter_type",
            "ai_risk",
            "evidence_score",
            "combined_priority",
            "alert_level",
        ]

        report_columns = [
            c for c in report_columns
            if c in previous_reports.columns
        ]

        if "timestamp" in previous_reports.columns:

            previous_reports = (
                previous_reports
                .sort_values(
                    "timestamp",
                    ascending=False,
                )
            )

        st.dataframe(
            previous_reports[
                report_columns
            ],
            use_container_width=True,
            hide_index=True,
        )

        field_csv = (
            previous_reports
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            "📥 Download Field Reports",
            data=field_csv,
            file_name="field_reports.csv",
            mime="text/csv",
        )

    except Exception as e:

        st.warning(
            f"Could not read field reports: {e}"
        )

else:

    st.info(
        "No field reports submitted yet."
    )


# ============================================================
# EMERGENCY DATA EXPORT
# ============================================================

st.subheader(
    "📥 Emergency Data Export"
)

export_df = decision.copy()


export_columns = [
    "latitude",
    "longitude",
    "state",
    "district",
    "risk",
    "risk_level",
    "susceptibility",
    "slope_deg",
    "elevation_m",
    "historical_score",
    "priority_score",
    "action",
    "reason",
]

export_columns = [
    c for c in export_columns
    if c in export_df.columns
]


csv_data = (
    export_df[
        export_columns
    ]
    .to_csv(index=False)
    .encode("utf-8")
)


st.download_button(
    label="⬇️ Download Emergency Priority CSV",
    data=csv_data,
    file_name="NER_landslide_emergency_priority.csv",
    mime="text/csv",
)


# ============================================================
# WEATHER STATUS
# ============================================================

st.subheader(
    "🌦️ Weather Data Status"
)

if not weather_df.empty:

    st.dataframe(
        weather_df,
        use_container_width=True,
        hide_index=True,
    )

    if weather_mode == "IMD LIVE":

        st.success(
            "🟢 Weather integration operating in live mode."
        )

    else:

        st.warning(
            "🟡 Dashboard is using clearly-labelled "
            "prototype scenario values."
        )

else:

    st.warning(
        "Weather status file unavailable."
    )


# ============================================================
# SYSTEM HEALTH
# ============================================================

st.subheader(
    "🟢 System Health"
)

health_items = [
    (
        "GSI Landslide Inventory",
        not df.empty,
    ),
    (
        "Terrain / DEM Features",
        not terrain_df.empty,
    ),
    (
        "AI Susceptibility Model",
        model is not None,
    ),
    (
        "Risk Engine",
        RISK_ENGINE_AVAILABLE,
    ),
    (
        "Road / Settlement Exposure",
        not exposure_df.empty,
    ),
    (
        "Automated Alerts",
        not alerts_df.empty,
    ),
    (
        "Weather Integration",
        not weather_df.empty,
    ),
    (
        "District GIS",
        "district" in df.columns,
    ),
]


health_cols = st.columns(4)

for i, (name, status) in enumerate(
    health_items
):

    with health_cols[i % 4]:

        if status:

            st.success(
                f"🟢 {name}: ONLINE"
            )

        else:

            st.warning(
                f"🟡 {name}: PROTOTYPE / UNAVAILABLE"
            )


# ============================================================
# DECISION PIPELINE
# ============================================================

st.subheader(
    "🧠 Decision Pipeline"
)

pipeline = [
    "1 • GSI Historical Inventory",
    "2 • DEM + Terrain Analysis",
    "3 • AI Susceptibility",
    "4 • Rainfall Trigger",
    "5 • Soil Moisture Trigger",
    "6 • Exposure Intelligence",
    "7 • Risk Engine",
    "8 • Emergency Prioritization",
    "9 • Automated Alerts",
    "10 • Field Verification",
]


pcols = st.columns(5)

for i, step in enumerate(pipeline):

    with pcols[i % 5]:

        st.info(step)


# ============================================================
# DATA / MODEL PROVENANCE
# ============================================================

with st.expander(
    "📚 Data & Model Provenance"
):

    st.markdown(
        """
        ### Historical Landslide Evidence

        Geological Survey of India (GSI)
        field-validated landslide inventory.

        ### Terrain

        DEM-derived:

        - Elevation
        - Slope
        - Aspect

        ### AI

        Random Forest susceptibility model
        trained using landslide inventory locations
        and terrain-matched background samples.

        ### Exposure

        Road and settlement proximity information
        is used for exposure prioritization.

        ### Dynamic Triggers

        - 24-hour rainfall
        - 7-day cumulative rainfall
        - Soil moisture

        ### Field Verification

        Citizen and field-officer reports can be
        combined with AI risk for response prioritization.

        ### Important Prototype Limitation

        Weather values are currently scenario inputs
        unless a live weather dataset is available.

        Prototype model validation should not be
        presented as operational real-world prediction
        accuracy.
        """
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.markdown(
    """
    <div class="footer">
        <b>SIH26001 — AI-Based Early Warning and Landslide Risk Monitoring System</b><br>
        NER Landslide AI Command Center<br>
        GSI Inventory • DEM Terrain • AI/ML • GIS • Exposure Intelligence •
        Emergency Prioritization • Field Verification • Early Warning<br>
        <span class="small-muted">
        Prototype decision-support system. Weather inputs are scenario-based unless a live feed is available.
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)




