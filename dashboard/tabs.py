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


from indicators.carbon_intensity_api import fetch_carbon_intensity, fetch_national_carbon_timeseries, fetch_regional_carbon_intensity
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


# Carbon Intensity tab
def render_carbon_tab():
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
        df = df.set_index("from")[["actual", "forecast"]].resample("h").mean().reset_index()
        st.line_chart(df.set_index("from")[["actual", "forecast"]])
    else:
        st.warning("No historical data could be loaded.")

    st.markdown("---")

    # 🔹 REGIONAL MAP
    st.subheader("🗺️ Regional Carbon Intensity – UK Map")

    regional_df = fetch_regional_carbon_intensity()
    regional_df = regional_df.dropna(subset=["lat", "lon"])

    # ✅ Define custom color mapping
    CUSTOM_INDEX_COLORS = {
        "very low": "green",
        "low": "#a6d96a",
        "moderate": "yellow",
        "high": "orange",
        "very high": "red"
    }

    # ✅ Map index → color
    regional_df["color"] = regional_df["index"].map(CUSTOM_INDEX_COLORS)

    if not regional_df.empty:
        fig = go.Figure()

        for _, row in regional_df.iterrows():
            fig.add_trace(go.Scattermapbox(
                lat=[row["lat"]],
                lon=[row["lon"]],
                mode="markers",
                marker=go.scattermapbox.Marker(
                    size=20,
                    color=row["color"]
                ),
                name=row["region"],
                hovertext=f"{row['region']}<br>Index: {row['index']}",
                hoverinfo="text"
            ))

        fig.update_layout(
            mapbox=dict(
                style="carto-positron",
                zoom=5,
                center={"lat": 54.0, "lon": -2.5}
            ),
            margin={"r": 0, "t": 0, "l": 0, "b": 0},
            showlegend=False
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("No regional data available to display.")

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
                "status": "Under Review; UK Gov Consultation closed on 9 April 2025",
                "Latest Developments": "The UK ETS Authority published a consultation paper setting out its proposals for extending the UK ETS scheme based on stakeholder feedback, beyond the end of Phase I to follow directly into a second phase from 1 January 2031 onward. There are three options: (1) 2031-2037, (2) 2031-2040, and (3) 2031-2042. The consultation also seeks views on the length of the proposed Phase II and whether banking of emissions allowances between Phase I and Phase II should be permitted. Responses were submitted by 23:59 BST on 9 April 2025 & UK Gov response is expected by end of 2025.",
                "9 April 2025 Consultation": "https://assets.publishing.service.gov.uk/media/67abe55a0f72884e1756aa6f/extending-the-ukets-cap-beyond-2030.pdf",
                "Other Notable Developments": "The UK ETS free allocation period has been extended beyond 2025 to 2026, with the latter being treated as an extension of the 2021–2025 period. The second allocation period will commence in 2027 and run through 2030. This period may introduce revised rules and allocation methodologies based on the outcomes of the ongoing Free Allocation Review. The Authority intends to publish its response to this review by the end of 2025. Link: https://assets.publishing.service.gov.uk/media/676000e81857548bccbcfa2a/ukets-moving-second-free-allocation-period-authority-response.pdf",
                "last_updated": "2025-04-14",
                "search_url": ["https://www.google.com/search?q=UK+ETS+Extension+news"]
            },
            {
                "title": "Possible Linkage with EU ETS",
                "description": "In March 2025, reports emerged that the UK government is considering linking its ETS with the EU's carbon market. As of April 2025, such developments have not progressed beyond this expression of interest. Notably, this consideration is part of a broader strategy to enhance cooperation with the EU, including discussions anticipated at a UK-EU Summit in May 2025. Additionally, Labour Party leader Sir Keir Starmer has expressed intentions to relink the UK and EU emission trading schemes as part of efforts to reset relations with Brussels.",
                "status": "Interest Expressed; Formal Talks Pending",
                "Key Dates to Watch": "UK-EU Summit (May 2025): This summit is expected to address broader post-Brexit relations, including potential cooperation on emissions trading.",
                "Latest Developments": "The EU-UK Parliamentary Partnership Assembly (PPA) took place on 17 March 2025. A document was published, called 'Recommendation on strengthening the EU-UK relationship', which included a section calling for serious consideration of linking UK & EU ETS. The PPA is a body that allows for dialogue between the UK and EU on various issues, and is expected to meet again in autumn 2025 in London, although no formal date has yet been set. Link to Meeting Document: https://www.europarl.europa.eu/cmsdata/293904/5th%20PPA%20Recommendation%2017.03.25.pdf",
                "PPA Meeting": "https://www.europarl.europa.eu/delegations/en/5th-eu-uk-parliamentary-partnership-asse/product-details/20250224DPU39839",
                "last_updated": "2025-04-14",
                "search_url": ["https://www.google.com/search?q=UK+ETS+EU+linkage"]
            },
            {
                "title": "Inclusion of Waste Incineration Facilities & Maritime Sector in UK ETS",
                "description": "The UK government is exploring the inclusion of waste incineration facilities and the Maritime Sector in the UK ETS to reduce emissions and better regulate the shipping sector.",
                "status": "Proposed",
                "last_updated": "2025-04-14",
                "search_url": [
                    "https://www.google.com/search?q=UK+ETS+waste+incineration",
                    "https://www.google.com/search?q=UK+ETS+maritime+shipping"
                ]
            }
        ]

        for policy in policies:
            st.markdown(f"#### **{policy['title']}**")
            st.write(policy["description"])
            st.write(f"**Status:** {policy.get('status', 'N/A')} | **Last Updated:** {policy.get('last_updated', 'N/A')}")

            # Display additional fields
            excluded_keys = {"title", "description", "status", "last_updated", "search_url"}
            for key, value in policy.items():
                if key not in excluded_keys:
                    if isinstance(value, str) and value.startswith("http"):
                        st.markdown(f"**{key}:** [Link]({value})")
                    else:
                        st.markdown(f"**{key}:** {value}")

            # Handle one or more search links
            search_links = policy.get("search_url", [])
            if isinstance(search_links, str):
                search_links = [search_links]
            for url in search_links:
                st.markdown(f"🔍 [View Google News]({url})")

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