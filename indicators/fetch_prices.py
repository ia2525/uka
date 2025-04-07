import requests
import os
import pandas as pd
from datetime import datetime

def get_real_uka_prices():
    url = "https://www.ice.com/marketdata/DelayedMarkets.shtml?getHistoricalChartDataAsJson=&marketId=6994206&historicalSpan=1"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "application/json",
        "Referer": "https://www.ice.com/products/80216150/UKA-Futures/data?span=1&marketId=6994206"
    }

    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        raise ConnectionError(f"Failed to fetch data. Status code: {response.status_code}")

    data = response.json()
    bars = data.get("bars", [])
    if not bars or not isinstance(bars, list):
        raise ValueError("Unexpected format for 'bars' in the API response.")

    if isinstance(bars[0], list) and isinstance(bars[0][0], list):
        bars = bars[1]
    elif isinstance(bars[0], list):
        bars = bars

    if not all(len(row) == 2 for row in bars):
        raise ValueError("Each row in 'bars' must contain [date, price]")

    df = pd.DataFrame(bars, columns=["date", "uka_price"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date"])
    df = df.sort_values("date")

    # ⚠️ Check age
    latest_date = df["date"].max()
    days_old = (datetime.today() - latest_date).days
    if days_old > 3:
        print(f"⚠️ WARNING: UKA data is {days_old} days old (last update: {latest_date.date()}). ICE may not be updating.")

    print("✅ Fetched UKA prices from ICE JSON API.")
    return df

if __name__ == "__main__":
    df_new = get_real_uka_prices()

    csv_path = "data/raw/uka_prices.csv"
    if os.path.exists(csv_path):
        df_existing = pd.read_csv(csv_path, parse_dates=["date"])
        combined = pd.concat([df_existing, df_new])
        combined = combined.drop_duplicates(subset="date")
        combined = combined.sort_values("date")
    else:
        combined = df_new

    combined.to_csv(csv_path, index=False)
    print("📌 Appended new data to data/raw/uka_prices.csv")
    print(combined.tail(10))
