import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from indicators.gas_prices import fetch_gas_prices
from indicators.weather import fetch_weather_forecasts
from indicators.news_feed import fetch_google_news, summarize_news_with_gemini

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="UKA Dashboard", layout="wide")

# ------------------ Load UKA Prices ------------------
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "uka_prices.csv"
df = pd.read_csv(DATA_PATH)
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

# ------------------ Fetch Data ------------------
gas_df = fetch_gas_prices()
weather_data = fetch_weather_forecasts()
news_df = fetch_google_news()
latest = df.iloc[-1]

# ------------------ Title ------------------
st.title("📊 UK Carbon Allowance (UKA) Dashboard")

# ------------------ Tabs ------------------
tabs = st.tabs([
    "📈 UKA Prices", 
    "🔥 Gas Prices", 
    "🌤️ UK Weather Forecast", 
    "📢 Policy & Market News",
    "🧩 Overlays"
])

# --- UKA Prices TAB ---
with tabs[0]:
    st.subheader("Historical UKA Prices")
    st.line_chart(df.set_index("date")["uka_price"])
    st.metric("Latest Price", f"€{latest['uka_price']:.2f}", delta=f"{latest['uka_price'] - df.iloc[-2]['uka_price']:.2f}")

# --- Gas Prices TAB ---
with tabs[1]:
    st.subheader("🔥 Gas Prices")
    
    gas_df = fetch_gas_prices()

    TICKER_LABELS = {
        "Close_NG=F": "US Natural Gas (Henry Hub) - Close",
        "Volume_NG=F": "US Natural Gas (Henry Hub) - Volume",
        "Close_BZ=F": "Brent Crude Oil - Close",
        "Volume_BZ=F": "Brent Crude Oil - Volume"
    }

    EXPLANATORY_NOTES = {
        "Close_NG=F": "Natural gas is a key fuel for UK power generation. Higher gas prices can lead to coal switching, increasing emissions and demand for UK carbon allowances.",
        "Volume_NG=F": "Volume shows how actively natural gas futures are being traded. High volume may indicate market reactions to weather, storage, or geopolitical shifts that can indirectly affect UKA demand.",
        "Close_BZ=F": "Brent crude reflects broader energy market sentiment. Rising oil prices can signal macroeconomic activity or energy inflation, both of which influence carbon markets.",
        "Volume_BZ=F": "Volume here captures market interest in Brent. While not directly tied to emissions, surges in volume can reflect speculative behavior or energy risk sentiment that spills into carbon pricing."
    }

    selected_columns = [col for col in gas_df.columns if col in TICKER_LABELS]
    display_names = [TICKER_LABELS[col] for col in selected_columns]
    selected_label = st.selectbox("Select indicator", display_names)
    selected_col = [col for col, label in TICKER_LABELS.items() if label == selected_label][0]

    st.subheader(selected_label)
    st.line_chart(gas_df.set_index("date")[[selected_col]])
    st.markdown(f"📝 *{EXPLANATORY_NOTES.get(selected_col, 'No explanation available.')}*")

# --- Weather TAB ---
with tabs[2]:
    st.subheader("UK Weather Forecast")
    city_tabs = st.tabs(weather_data["city"].unique().tolist())
    for tab, city in zip(city_tabs, weather_data["city"].unique()):
        with tab:
            city_data = weather_data[weather_data["city"] == city]
            available_cols = [col for col in ["temp", "wind_speed"] if col in city_data.columns]
            if available_cols:
                st.line_chart(city_data.set_index("date")[available_cols])
            else:
                st.warning(f"No weather data available for {city}.")

# --- Policy & Market News TAB ---
with tabs[3]:
    st.subheader("📢 Policy & Market News")

    if not news_df.empty:
        for index, row in news_df.iterrows():
            st.write(f"**{row['title']}**")
            st.write(f"Source: {row['source']}")
            st.write(f"[Read more]({row['link']})")
            st.write("-" * 80)

        # ✅ Move summary logic here
        st.markdown("### 🔍 Summary of News Headlines")
        summary = summarize_news_with_gemini(news_df)
        st.write(summary)

    else:
        st.write("No news articles available at the moment.")

# --- Overlay TAB ---
with tabs[4]:
    st.subheader("🧩 Overlay: UKA vs Natural Gas Prices")

    # Filter and prepare data
    uka_df = df[["date", "uka_price"]].copy()
    gas_df = fetch_gas_prices()[["date", "Close_NG=F"]].copy()

    # Merge on date
    overlay_df = pd.merge(uka_df, gas_df, on="date", how="inner")

    # Drop NA values if any
    overlay_df.dropna(inplace=True)

    # Plot with matplotlib
    import matplotlib.pyplot as plt

    fig, ax1 = plt.subplots(figsize=(6, 3))

    ax1.set_xlabel("Date")
    ax1.set_ylabel("UKA Price (€)", color="tab:blue")
    ax1.plot(overlay_df["date"], overlay_df["uka_price"], color="tab:blue", label="UKA Price")
    ax1.tick_params(axis="y", labelcolor="tab:blue")

    ax2 = ax1.twinx()  # Create a second y-axis
    ax2.set_ylabel("US Natural Gas Price (USD/MMBtu)", color="tab:red")
    ax2.plot(overlay_df["date"], overlay_df["Close_NG=F"], color="tab:red", label="Natural Gas Price")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    fig.tight_layout()
    st.pyplot(fig)

    st.markdown("📝 *This chart compares UKA prices with US natural gas prices. Rising gas prices can lead to coal switching and higher UKA demand, while falling gas prices may ease carbon pressure.*")