import sys
from pathlib import Path
import os 
sys.path.append(str(Path(__file__).resolve().parents[1]))
# uka_tracker/dashboard/tabs.py
import numpy as np
import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from pathlib import Path
import altair as alt
import plotly.express as px


from indicators.gas_prices import fetch_gas_prices
from indicators.weather import fetch_weather_forecasts
from indicators.news_feed import fetch_google_news, fetch_uka_players_news
from indicators.scrape_uka_prices import scrape_and_update_uka_timeseries
from indicators.production_index import reshape_allocation_timeseries

def load_combined_uka_prices():
    # Load your data (replace with your actual logic)
    df1 = pd.read_csv("data/raw/uka_prices.csv")
    df2 = pd.read_csv("data/raw/uka_timeseries.csv")

    combined = pd.concat([df1, df2], ignore_index=True)

    # 🔑 Ensure all dates are consistent datetime type
    combined["date"] = pd.to_datetime(combined["date"], errors="coerce").dt.date

    # Now you can safely sort
    combined = combined.sort_values("date", ascending=True).reset_index(drop=True)
    return combined


def render_uka_prices_tab(_):
    st.header("📈 Historical UKA Prices")

    df = load_combined_uka_prices()

    if st.button("🔄 Fetch Latest UKA Price"):
        try:
            scrape_and_update_uka_timeseries()
            df = load_combined_uka_prices()
            st.success("✅ Data updated successfully.")
        except Exception as e:
            st.error(f"❌ Update failed: {e}")

    df["SMA_7"] = df["uka_price"].rolling(window=7).mean()

    # Melt for Altair
    plot_df = df[["date", "uka_price", "SMA_7"]].melt("date", var_name="Series", value_name="Price")

    color_scale = alt.Scale(domain=["uka_price", "SMA_7"], range=["#1f77b4", "orange"])

    line = alt.Chart(plot_df).mark_line().encode(
        x=alt.X("date:T", title="Date", axis=alt.Axis(format="%m/%d/%Y")),
        y=alt.Y("Price:Q", title="€ Price"),
        color=alt.Color("Series:N", scale=color_scale, title="Legend"),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%m/%d/%Y"),
            alt.Tooltip("Price:Q", title="Price", format=".2f"),
            alt.Tooltip("Series:N", title="Type")
        ]
    )

    points = alt.Chart(plot_df).mark_point(filled=True, size=30).encode(
        x="date:T",
        y="Price:Q",
        color=alt.Color("Series:N", scale=color_scale),
        tooltip=[
            alt.Tooltip("date:T", title="Date", format="%m/%d/%Y"),
            alt.Tooltip("Price:Q", title="Price", format=".2f"),
            alt.Tooltip("Series:N", title="Type")
        ]
    )

    chart = (line + points).properties(height=320)

    st.altair_chart(chart, use_container_width=True)

    # ✅ Latest price section
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) > 1 else None
    delta = latest["uka_price"] - previous["uka_price"] if previous is not None else 0

    st.markdown("### Latest Price")
    st.metric(label=f"{latest['date']}", value=f"€{latest['uka_price']:.2f}", delta=f"{delta:.2f}")


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



# News tab (consolidated version)
def render_news_tab():
    st.subheader("📲 Policy & Market News")

    news_tabs = st.tabs(["📰 Market News", "📋 Policy Tracker", "🏭 Major UKA Players"])

    # Tab 1 – General Market News
    with news_tabs[0]:
        st.markdown("### 📰 Market News")
        news_df = fetch_google_news()
        if not news_df.empty:
            for _, row in news_df.iterrows():
                st.write(f"**{row['title']}**")
                st.write(f"Source: {row['source']} | Published: {row['published'].strftime('%Y-%m-%d')}")
                st.write(f"[Read more]({row['link']})")
                st.write("-" * 80)
        else:
            st.write("No news articles available at the moment.")

    # Tab 2 – Policy Tracker
    with news_tabs[1]:
        st.markdown("### 📋 Policy Tracker")

        policies = [
            {
                "title": "2030 Extension of UK ETS",
                "description": "The UK government is considering extending the UK ETS to 2030 to align with long-term climate goals.",
                "status": "Under Review",
                "last_updated": "2025-03-15",
                "search_url": "https://www.google.com/search?q=UK+ETS+Extension+news"
            },
            {
                "title": "Possible Linkage with EU ETS",
                "description": "Discussions are ongoing regarding linking the UK ETS with the EU ETS to create a unified carbon market.",
                "status": "In Negotiation",
                "last_updated": "2025-01-28",
                "search_url": "https://www.google.com/search?q=UK+ETS+EU+linkage"
            },
            {
                "title": "Inclusion of Waste Incineration Facilities",
                "description": "The UK government is exploring the inclusion of waste incineration facilities in the UK ETS to reduce emissions.",
                "status": "Proposed",
                "last_updated": "2025-02-10",
                "search_url": "https://www.google.com/search?q=UK+ETS+waste+incineration"
            },
            {
                "title": "Inclusion of Maritime Sector in UK ETS",
                "description": "Following the EU's lead, the UK is considering including maritime emissions in the UK ETS to better regulate the shipping sector.",
                "status": "Under Discussion",
                "last_updated": "2025-03-30",
                "search_url": "https://www.google.com/search?q=UK+ETS+maritime+shipping+inclusion"
            }
        ]

        for policy in policies:
            st.markdown(f"#### **{policy['title']}**")
            st.write(policy["description"])
            st.write(f"**Status:** {policy['status']} | **Last Updated:** {policy['last_updated']}")
            st.markdown(f"[🔍 View Google News]({policy['search_url']})")
            st.markdown("---")

    # Tab 3 – UKA Players + Google Links
    with news_tabs[2]:
        st.markdown("### 🏭 News on Major UKA Buyers & Industries")

        players_news = fetch_uka_players_news()
        if not players_news.empty:
            for _, row in players_news.iterrows():
                st.write(f"**{row['title']}**")
                st.write(f"Source: {row['source']} | Published: {row['published'].strftime('%Y-%m-%d')}")
                st.write(f"[Read more]({row['link']})")
                st.write("-" * 80)
        else:
            st.warning("No recent news found for major UKA players or industries via RSS.")

        st.markdown("---")
        st.markdown("### 🔎 Live Google Search Links")
        st.info("RSS Feed often lags considerably. The below open Google with live news results for top companies and emitting sectors.")

        search_links = {
            "Tata Steel UK Limited": "https://www.google.com/search?q=Tata+Steel+UK+news",
            "British Steel Limited": "https://www.google.com/search?q=British+Steel+news",
            "Phillips 66 Limited": "https://www.google.com/search?q=Phillips+66+news",
            "Oil Refining News": "https://www.google.com/search?q=UK+oil+refining+industry+news",
            "Cement Industry News": "https://www.google.com/search?q=UK+cement+industry+news",
            "Combustion of Fuels News": "https://www.google.com/search?q=UK+combustion+of+fuels+industry+news"
        }

        for label, url in search_links.items():
            st.markdown(f"🔗 [**{label}**]({url})")

#Overlay tab 
def overlays_tab(df):
    st.subheader("🧩 Overlays")

    overlay_options = [
        "UKA vs Natural Gas Prices",
        "UKA vs EU Linkage Announcement",
        "UKA vs UK Industrial Output"  
    ]
    selected_overlay = st.selectbox("Choose an overlay", overlay_options)

    if selected_overlay == "UKA vs Natural Gas Prices":
        render_uka_vs_gas_overlay(df)

    elif selected_overlay == "UKA vs EU Linkage Announcement":
        render_uka_vs_policy_overlay(df)

    elif selected_overlay == "UKA vs UK Industrial Output":
        render_uka_vs_industrial_overlay(df)

    plt.style.use("ggplot")

def render_uka_vs_gas_overlay(df):
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import numpy as np
    from indicators.gas_prices import fetch_gas_prices

    plt.style.use("ggplot")

    # --- Prepare Data ---
    uka_df = df[["date", "uka_price"]].copy()
    gas_df = fetch_gas_prices()[["date", "Close_NG=F"]].copy()

    # 🔧 Make sure both 'date' columns are datetime64[ns]
    uka_df["date"] = pd.to_datetime(uka_df["date"])
    gas_df["date"] = pd.to_datetime(gas_df["date"])

    # --- Merge and drop NaNs ---
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
        "### 📝 *This chart compares UKA prices with US natural gas prices to test whether rising gas prices lead to higher UKA demand (via industries switching to coal).*"
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

def render_uka_vs_policy_overlay(df):
    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates
    import pandas as pd

    eu_linkage_announcement = pd.to_datetime("2025-01-28") #Source: https://www.reuters.com/sustainability/climate-energy/uk-carbon-prices-close-135-higher-eu-linking-talks-report-2025-01-28/
    eu_linkage_update = pd.to_datetime("2025-03-20") #Source: https://carbon-pulse.com/380168/

    fig, ax = plt.subplots(figsize=(6, 2.5), dpi=150)
    ax.plot(df["date"], df["uka_price"], label="UKA Price", color="steelblue", linewidth=1.5)
    ax.axvline(eu_linkage_announcement, color="green", linestyle="--", linewidth=2, label="Possible Linkage Announced")
    ax.axvline(eu_linkage_update, color="orange", linestyle="--", linewidth=2, label="EU Linkage Update")

    ax.set_xlabel("Date", fontsize=9)
    ax.set_ylabel("UKA Price (€)", fontsize=9)
    ax.set_title("UKA Prices vs Policy Events", fontsize=11)
    ax.legend(fontsize=8)
    ax.tick_params(axis="both", labelsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.tick_params(axis="x", rotation=45)

    fig.tight_layout(pad=2)
    st.pyplot(fig, use_container_width=True)

    st.markdown(
        "📝 *This chart visualizes how UKA prices moved in response to policy announcements. "
        "The dashed lines mark policy updates."
        "Update on March 20, 2025: The UK government formally confirmed it is considering the case for linking the country's carbon market to the EU ETS in an update published late on Thursday.*"""
        "However, the UK government cautioned that this does not anticipate any outcome of key talks in May with the block.*"
    )

def render_industrial_output_tab():
    st.subheader("🏭 UK ETS Allocation Time Series")

    companies_long, industries_long = reshape_allocation_timeseries()

    company_tab, industry_tab = st.tabs(["🏢 Top 10 Companies", "🏗️ Top 10 Industries"])

    with company_tab:
        st.markdown("### 🧱 UK ETS Allocation: Top 10 Companies")

        # Horizontal bar chart
        fig1 = px.bar(
            companies_long,
            x="Allocation",
            y="Company",
            color="Year",  # color stack by year
            orientation="h",
            title="Top 10 Companies by Total ETS Allocation (Stacked by Year)",
            labels={"Allocation": "UKA Allocation (€)", "Company": "Company"},
            height=500
        )

        # Ensure consistent ordering by total allocation
        total_allocation = companies_long.groupby("Company")["Allocation"].sum().sort_values(ascending=True)
        fig1.update_layout(
            yaxis=dict(categoryorder="array", categoryarray=total_allocation.index.tolist()),
            barmode="stack"
        )

        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("### 📉 Allocation Over Time – Top 3 Companies")

        top_3_companies = total_allocation.tail(3).index.tolist()
        top_3_df = companies_long[companies_long["Company"].isin(top_3_companies)]

        fig3 = px.line(
            top_3_df,
            x="Year", y="Allocation", color="Company",
            markers=True,
            title="ETS Allocation Over Time – Top 3 Companies"
        )
        st.plotly_chart(fig3, use_container_width=True)

    with industry_tab:
        st.markdown("### 🏗️ UK ETS Allocation: Top 10 Industries")

        # Horizontal stacked bar chart for industries
        fig2 = px.bar(
            industries_long,
            x="Allocation",
            y="Industries",
            color="Year",  # Stack by year
            orientation="h",
            title="Top 10 Industries by Total ETS Allocation (Stacked by Year)",
            labels={"Allocation": "UKA Allocation (€)", "Industries": "Industry"},
            height=500
        )

        # Consistent ordering by total allocation
        total_industry_allocation = industries_long.groupby("Industries")["Allocation"].sum().sort_values(ascending=True)
        fig2.update_layout(
            yaxis=dict(categoryorder="array", categoryarray=total_industry_allocation.index.tolist()),
            barmode="stack"
        )

        st.plotly_chart(fig2, use_container_width=True)

        st.markdown("### 📉 Allocation Over Time – Top 3 Industries")

        top_3_industries = total_industry_allocation.tail(3).index.tolist()
        top_3_industry_df = industries_long[industries_long["Industries"].isin(top_3_industries)]

        fig4 = px.line(
            top_3_industry_df,
            x="Year", y="Allocation", color="Industries",
            markers=True,
            title="ETS Allocation Over Time – Top 3 Industries"
        )
        st.plotly_chart(fig4, use_container_width=True)