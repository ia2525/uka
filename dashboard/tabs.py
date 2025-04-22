import sys
import pandas as pd
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[1]))
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path
import altair as alt
import plotly.express as px
import plotly.graph_objects as go


from indicators.carbon_intensity_api import fetch_carbon_intensity, fetch_national_carbon_timeseries, fetch_national_carbon_timeseries_2020
from indicators.scrape_uka_prices import scrape_and_update_uka_timeseries
from indicators.production_index import reshape_allocation_timeseries
from indicators.policy_data import get_policies


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


# Carbon Intensity tab
def render_carbon_tab():
    import pandas as pd
    import plotly.express as px

    st.subheader("🌍 UK Carbon Intensity")

    # 🔹 LIVE SNAPSHOT
    intensity = fetch_carbon_intensity()
    if intensity["actual"] is not None:
        st.metric("Actual Intensity (gCO₂/kWh)", intensity["actual"])
        st.metric("Forecast Intensity (gCO₂/kWh)", intensity["forecast"])
        st.text(f"Intensity Index: {intensity['index']}")
    else:
        st.warning("Could not fetch carbon intensity data at this time.")

    st.markdown("---")

    # 🔹 HISTORICAL NATIONAL TIME SERIES
    st.subheader("📈 Historical Carbon Intensity Since Jan 1, 2025")
    with st.spinner("Fetching time series..."):
        df = fetch_national_carbon_timeseries()

    if not df.empty:
        df["from"] = pd.to_datetime(df["from"])
        df = df.set_index("from").sort_index()

        # 12h & 30d smoothing
        df["12h_avg"] = df["actual"].rolling("12h").mean()
        df["30d_avg"] = df["actual"].rolling("30d").mean()

        df_plot = df[["12h_avg", "30d_avg"]].dropna().reset_index()
        df_melted = df_plot.melt(id_vars="from", var_name="Smoothing", value_name="Intensity")

        fig = px.line(
            df_melted,
            x="from",
            y="Intensity",
            color="Smoothing",
            title="📉 Historical Carbon Intensity – Since Jan 1, 2025",
            labels={"from": "Date", "Intensity": "gCO₂/kWh"},
            height=450
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Carbon Intensity (gCO₂/kWh)",
            margin=dict(l=40, r=40, t=40, b=20),
            legend_title_text="Rolling Avg",
            template="plotly_white",
            xaxis=dict(
                rangeselector=dict(
                    buttons=[
                        dict(count=7, label="1w", step="day", stepmode="backward"),
                        dict(count=14, label="2w", step="day", stepmode="backward"),
                        dict(count=1, label="1m", step="month", stepmode="backward"),
                        dict(step="all")
                    ]
                ),
                rangeslider=dict(visible=True),  # 👈 this enables the horizontal slider!
                type="date"
            )
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No historical data could be loaded.")

    # SECOND - LONGER HISTORICAL GRAPH
    st.subheader("📈 Historical Carbon Intensity Since Jan 1, 2020")
    with st.spinner("Fetching time series..."):
        df = fetch_national_carbon_timeseries_2020()

    if not df.empty:
        df["from"] = pd.to_datetime(df["from"])
        df = df.set_index("from").sort_index()

        # Create rolling averages
        df["48h_avg"] = df["actual"].rolling("48h").mean()
        df["30d_avg"] = df["actual"].rolling("30D").mean()

        # Drop NaNs introduced by rolling
        df_plot = df[["48h_avg", "30d_avg"]].dropna().reset_index()

        # Plot with both lines
        fig = px.line(
            df_plot,
            x="from",
            y=["48h_avg", "30d_avg"],
            title="📉 Historical Carbon Intensity (48h & 30d Avg) – Since Jan 1, 2020",
            labels={
                "from": "Date",
                "value": "Carbon Intensity (gCO₂/kWh)",
                "variable": "Average Type"
            },
            height=450
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Carbon Intensity (gCO₂/kWh)",
            margin=dict(l=40, r=40, t=40, b=20),
            template="plotly_white",
            xaxis=dict(
                rangeselector=dict(
                    buttons=[
                        dict(count=6, label="6m", step="month", stepmode="backward"),
                        dict(count=1, label="1yr", step="year", stepmode="backward"),
                        dict(count=3, label="3yr", step="year", stepmode="backward"),
                        dict(step="all")
                    ]
                ),
                rangeslider=dict(visible=True),
                type="date"
            )
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No historical data could be loaded.")


# News tab (consolidated version)

def render_news_tab():
    st.subheader("📲 Policy & Market News")

    news_tabs = st.tabs(["📋 Policy Tracker", "🏭 Major UKA Players"])

    # Tab 1 – Policy Tracker

    with news_tabs[0]:
        st.markdown("### 📋 Policy Tracker")
        policies = get_policies()

        for policy in policies:
            st.markdown(f"#### **{policy['title']}**")
            st.write(policy["description"])
            st.write(f"**Status:** {policy.get('status', 'N/A')} | **Last Updated:** {policy.get('last_updated', 'N/A')}")

            excluded_keys = {"title", "description", "status", "last_updated", "search_url"}
            for key, value in policy.items():
                if key not in excluded_keys:
                    if isinstance(value, str) and value.startswith("http"):
                        st.markdown(f"**{key}:** [Link]({value})")
                    else:
                        st.markdown(f"**{key}:** {value}")

            for url in policy.get("search_url", []):
                st.markdown(f"🔍 [View Google News]({url})")

            st.markdown("---")

    # Tab 2 – UKA Players + Google Links
    with news_tabs[1]:
        st.markdown("### 🏭 News on Major UKA Buyers & Industries")

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
        "UKA vs EU Linkage Announcement" 
    ]
    selected_overlay = st.selectbox("Choose an overlay", overlay_options)

    if selected_overlay == "UKA vs EU Linkage Announcement":
        render_uka_vs_policy_overlay(df)


    plt.style.use("ggplot")

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