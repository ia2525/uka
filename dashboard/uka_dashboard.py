import sys
from pathlib import Path
import pandas as pd
import streamlit as st
st.set_page_config(page_title="UK Carbon Allowance (UKA) Dashboard", layout="wide")

# Ensure root project path is on sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from dashboard.tabs import (
    render_uka_prices_tab,
    render_gas_prices_tab,
    render_weather_tab,
    render_news_tab,
    render_industrial_output_tab,
    overlays_tab
)

# Load UKA price data
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "uka_prices.csv"
df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"])

tabs = st.tabs([
    "📈 UKA Prices",
    "🔥 Gas Prices",
    "🌤️ UK Weather Forecast",
    "📢 Policy & Market News",
    "🏭 Industrial Output",
    "🧩 Overlays"
])

with tabs[0]: render_uka_prices_tab(df)
with tabs[1]: render_gas_prices_tab()
with tabs[2]: render_weather_tab()
with tabs[3]: render_news_tab()
with tabs[4]: render_industrial_output_tab()
with tabs[5]: overlays_tab(df)