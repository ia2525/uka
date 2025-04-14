import requests
import pandas as pd

def fetch_carbon_intensity():
    """
    Fetch current national carbon intensity data.
    Returns a dictionary with actual, forecast, and index values.
    """
    try:
        url = "https://api.carbonintensity.org.uk/intensity"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # The response has data["data"] as a list
        intensity = data["data"][0]["intensity"]

        return {
            "actual": intensity.get("actual"),
            "forecast": intensity.get("forecast"),
            "index": intensity.get("index")
        }
    except Exception as e:
        print(f"❌ Error fetching carbon intensity: {e}")
        return {
            "actual": None,
            "forecast": None,
            "index": None
        }
def fetch_national_carbon_timeseries(start_date="2025-01-01", end_date=None):
    import requests
    import pandas as pd
    from datetime import datetime, timedelta

    if end_date is None:
        end_date = datetime.utcnow().strftime("%Y-%m-%d")

    start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    all_data = []

    while start_dt < end_dt:
        segment_start = start_dt.strftime("%Y-%m-%dT%H:%MZ")
        segment_end = (start_dt + timedelta(days=30)).strftime("%Y-%m-%dT%H:%MZ")
        url = f"https://api.carbonintensity.org.uk/intensity/{segment_start}/{segment_end}"

        response = requests.get(url)
        if response.status_code != 200:
            print(f"❌ Failed segment: {segment_start} to {segment_end}")
            break

        batch = response.json()["data"]
        all_data.extend(batch)
        start_dt += timedelta(days=30)

    df = pd.DataFrame(all_data)
    df["from"] = pd.to_datetime(df["from"])
    df["to"] = pd.to_datetime(df["to"])

    intensity_df = df.dropna().assign(
        actual=lambda d: d["intensity"].apply(lambda x: x.get("actual")),
        forecast=lambda d: d["intensity"].apply(lambda x: x.get("forecast")),
        index=lambda d: d["intensity"].apply(lambda x: x.get("index")),
    )

    return intensity_df[["from", "to", "actual", "forecast", "index"]]

REGION_COORDS = {
    "North Scotland": (57.5, -4.2),
    "South Scotland": (55.8, -3.9),
    "North West England": (53.6, -2.8),
    "North East England": (54.9, -1.5),
    "Yorkshire": (53.9, -1.0),
    "North Wales & Merseyside": (53.3, -3.0),
    "South Wales": (51.8, -3.0),
    "West Midlands": (52.5, -2.0),
    "East Midlands": (52.8, -0.9),
    "East England": (52.3, 0.8),
    "South West England": (51.0, -3.7),
    "South England": (50.9, -1.3),
    "London": (51.5, -0.1),
    "South East England": (51.3, 0.4)
}

CUSTOM_INDEX_COLORS = {
    "very low": "green",
    "low": "#a6d96a",
    "moderate": "yellow",
    "high": "orange",
    "very high": "red"
}

def fetch_regional_carbon_intensity():
    import requests
    import pandas as pd

    url = "https://api.carbonintensity.org.uk/regional"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()["data"][0]  # latest snapshot
        regions = data["regions"]

        records = []
        for r in regions:
            region_name = r.get("shortname", "Unknown")
            lat, lon = REGION_COORDS.get(region_name, (None, None))

            records.append({
                "region": region_name,
                "intensity": r.get("intensity", {}).get("actual"),
                "index": r.get("intensity", {}).get("index"),
                "lat": lat,
                "lon": lon
            })

        df = pd.DataFrame(records)

        # Debug: Check how many valid rows you got
        print(f"✅ Regional records fetched: {len(df)}")
        print(df[["region", "lat", "lon"]])  # Optional: inspect coords

        return df

    except Exception as e:
        print(f"❌ Error fetching regional data: {e}")
        return pd.DataFrame()
