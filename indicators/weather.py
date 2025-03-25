# uka_tracker/indicators/weather.py

import requests
import pandas as pd

API_KEY = "c912c42333e0456ccce7724a8f788970"

CITIES = {
    "London": (51.5074, -0.1278),
    "Edinburgh": (55.9533, -3.1883),
    "Glasgow": (55.8642, -4.2518),
    "Belfast": (54.5973, -5.9301),
    "Manchester": (53.4808, -2.2426),
}

def fetch_weather_forecasts():
    all_data = []

    for city, (lat, lon) in CITIES.items():
        url = (
            f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&units=metric&appid={API_KEY}"
        )
        response = requests.get(url)
        data = response.json()

        if response.status_code != 200 or "list" not in data:
            print(f"❌ Failed to fetch weather for {city}: {data}")
            continue

        # Aggregate daily forecasts from 3-hour intervals
        df = pd.DataFrame(data["list"])
        df["dt"] = pd.to_datetime(df["dt"], unit="s")
        df["date"] = df["dt"].dt.date
        df["temp"] = df["main"].apply(lambda x: x["temp"])
        df["wind_speed"] = df["wind"].apply(lambda x: x["speed"])

        # Daily averages
        daily = df.groupby("date")[["temp", "wind_speed"]].mean().reset_index()
        daily["city"] = city
        all_data.append(daily)

    if not all_data:
        return pd.DataFrame()  # avoid crashing if all cities fail

    return pd.concat(all_data, ignore_index=True)