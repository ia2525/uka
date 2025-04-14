import sys
from pathlib import Path
import streamlit as st

# Set up app layout
st.set_page_config(page_title="UK Carbon Allowance (UKA) Dashboard", layout="wide")

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parents[1]))

# ✅ Now import tabs after sys.path is set
from tabs import (
    load_combined_uka_prices,  # ✅ newly added function
    render_uka_prices_tab,
    render_carbon_tab,
    render_weather_tab,
    render_news_tab,
    render_industrial_output_tab,
    overlays_tab
)
# Load UKA price data
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "uka_prices.csv"
df = load_combined_uka_prices()

tabs = st.tabs([
    "📈 UKA Prices",
    " Live UK Carbon Intensity Data",
    " UK Weather Forecast",
    " Policy & Market News",
    " Industrial Output",
    " Overlays"
])

with tabs[0]: render_uka_prices_tab(df)
with tabs[1]: render_carbon_tab()
with tabs[2]: render_weather_tab()
with tabs[3]: render_news_tab()
with tabs[4]: render_industrial_output_tab()
with tabs[5]: overlays_tab(df)