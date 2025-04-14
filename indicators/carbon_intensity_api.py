import requests

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

def fetch_national_carbon_timeseries_2020(start_date="2020-01-01", end_date=None):
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


