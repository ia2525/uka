# uka_tracker/dashboard/tabs.py

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

from indicators.gas_prices import fetch_gas_prices
from indicators.weather import fetch_weather_forecasts
from indicators.news_feed import fetch_google_news, summarize_news_with_gemini

# UKA Prices tab
def render_uka_prices_tab(df):
    st.subheader("Historical UKA Prices")
    df = df.sort_values("date")
    st.line_chart(df.set_index("date")["uka_price"])
    st.metric("Latest Price", f"€{df.iloc[-1]['uka_price']:.2f}", delta=f"{df.iloc[-1]['uka_price'] - df.iloc[-2]['uka_price']:.2f}")


# Gas Prices tab
def render_gas_prices_tab():
    gas_df = fetch_gas_prices()
    st.subheader("🔥 Gas Prices")

    TICKER_LABELS = {
        "Close_NG=F": "US Natural Gas (Henry Hub) - Close",
        "Volume_NG=F": "US Natural Gas (Henry Hub) - Volume",
        "Close_BZ=F": "Brent Crude Oil - Close",
        "Volume_BZ=F": "Brent Crude Oil - Volume"
    }

    # Only use these columns
    tab_columns = list(TICKER_LABELS.keys())

    gas_tabs = st.tabs([TICKER_LABELS[col] for col in tab_columns])

    for tab, col in zip(gas_tabs, tab_columns):
        with tab:
            st.subheader(TICKER_LABELS[col])
            st.line_chart(gas_df.set_index("date")[[col]])

# Weather tab
def render_weather_tab():
    weather_data = fetch_weather_forecasts()
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


# News tab
def render_news_tab():
    st.subheader("📢 Policy & Market News")
    news_df = fetch_google_news()

    if not news_df.empty:
        for index, row in news_df.iterrows():
            st.write(f"**{row['title']}**")
            st.write(f"Source: {row['source']}")
            st.write(f"[Read more]({row['link']})")
            st.write("-" * 80)

        st.markdown("### 🔍 Summary of News Headlines")
        summary = summarize_news_with_gemini(news_df)
        st.write(summary)
    else:
        st.write("No news articles available at the moment.")

#Overlay tab 
def overlays_tab(df):
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    from indicators.gas_prices import fetch_gas_prices

    st.subheader("🧩 Overlay: UKA vs Natural Gas Prices")
    plt.style.use("ggplot")

    # --- Prepare Data ---
    uka_df = df[["date", "uka_price"]].copy()
    gas_df = fetch_gas_prices()[["date", "Close_NG=F"]].copy()
    overlay_df = pd.merge(uka_df, gas_df, on="date", how="inner").dropna()

    # --- Overlay Plot ---
    fig, ax1 = plt.subplots(figsize=(4, 2), dpi=150)
    ax1.set_xlabel("Date", fontsize=7)
    ax1.set_ylabel("UKA Price (€)", color="tab:blue", fontsize=8)
    ax1.plot(overlay_df["date"], overlay_df["uka_price"], color="tab:blue", linewidth=1.5)
    ax1.tick_params(axis="y", labelcolor="tab:blue", labelsize=7)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax1.tick_params(axis="x", labelsize=7, rotation=45)

    ax2 = ax1.twinx()
    ax2.set_ylabel("US Natural Gas Price (USD/MMBtu)", color="tab:red", fontsize=8)
    ax2.plot(overlay_df["date"], overlay_df["Close_NG=F"], color="tab:red", linewidth=1.5)
    ax2.tick_params(axis="y", labelcolor="tab:red", labelsize=7)

    fig.tight_layout(pad=2)
    st.pyplot(fig, use_container_width=True)

    # --- Correlation ---
    correlation = np.corrcoef(overlay_df["uka_price"], overlay_df["Close_NG=F"])[0, 1]
    st.markdown(f"📈 **Correlation (Pearson):** `{correlation:.2f}`")

    if correlation > 0.5:
        st.success("UKA and Natural Gas show a strong positive correlation during this period.")
    elif correlation > 0.2:
        st.info("There's a mild positive correlation between UKA and Natural Gas.")
    elif correlation < -0.2:
        st.warning("There's an inverse correlation — they move in opposite directions.")
    else:
        st.error("Little to no correlation in this period — external factors may be dominating.")

    st.markdown(
        "### 📝 *This chart compares UKA prices with US natural gas prices to test whether rising gas prices leads to higher UKA demand (via industries switching to coal to offset higher prices))"
    )

    # --- Rolling Correlation ---
    rolling_corr = overlay_df["uka_price"].rolling(window=7).corr(overlay_df["Close_NG=F"])
    st.subheader("📉 7-Day Rolling Correlation (UKA vs Natural Gas)")

    fig_corr, ax = plt.subplots(figsize=(6, 2.5), dpi=150)
    ax.plot(overlay_df["date"], rolling_corr, color="purple", linewidth=1.5)
    ax.axhline(0, linestyle="--", color="gray", linewidth=1)
    ax.set_title("Rolling Correlation", fontsize=11)
    ax.set_ylabel("Correlation", fontsize=9)
    ax.set_xlabel("Date", fontsize=9)
    ax.tick_params(axis="both", labelsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.tick_params(axis="x", rotation=45)
    fig_corr.tight_layout(pad=2)
    st.pyplot(fig_corr, use_container_width=True)