import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from models.forecast import generate_forecast
from indicators.gas_prices import fetch_gas_prices
from indicators.weather import fetch_weather_forecasts
from indicators.news_feed import fetch_google_news

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
forecast, model = generate_forecast(df)
forecast_tail = forecast[forecast["ds"] > df["date"].max()]
latest = df.iloc[-1]

# ------------------ Title ------------------
st.title("📊 UK Carbon Allowance (UKA) Dashboard")

# ------------------ Tabs ------------------
tabs = st.tabs([
    "📈 UKA Prices", 
    "🔮 Forecast", 
    "🔥 Gas Prices", 
    "🌤️ UK Weather Forecast", 
    "📢 Policy & Market News"
])

# --- UKA Prices TAB ---
with tabs[0]:
    st.subheader("Historical UKA Prices")
    st.line_chart(df.set_index("date")["uka_price"])
    st.metric("Latest Price", f"€{latest['uka_price']:.2f}", delta=f"{latest['uka_price'] - df.iloc[-2]['uka_price']:.2f}")

# --- Forecast TAB ---
with tabs[1]:
    st.subheader("7-Day Forecast")
    st.line_chart(forecast_tail.set_index("ds")[["yhat", "yhat_lower", "yhat_upper"]])

# --- Gas Prices TAB ---
with tabs[2]:
    st.subheader("Gas Prices")
    gas_tabs = st.tabs([col for col in gas_df.columns if col != "date"])
    for tab, col in zip(gas_tabs, [c for c in gas_df.columns if c != "date"]):
        with tab:
            st.subheader(col)
            st.line_chart(gas_df.set_index("date")[[col]])

# --- Weather TAB ---
with tabs[3]:
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
with tabs[4]:
    st.subheader("📢 Policy & Market News")

    # Display news articles in the Streamlit app
    if not news_df.empty:
        for index, row in news_df.iterrows():
            st.write(f"**{row['title']}**")
            st.write(f"Source: {row['source']}")
            st.write(f"[Read more]({row['link']})")
            st.write("-" * 80)
    else:
        st.write("No news articles available at the moment.")