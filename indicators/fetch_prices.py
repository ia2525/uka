import requests
import pandas as pd

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
    print("API Response:", data)  # Debugging: Print the full response

    bars = data.get("bars", [])
    if not bars or not isinstance(bars, list):
        raise ValueError("Unexpected format for 'bars' in the API response.")

    # Adjust logic based on the structure of 'bars'
    if isinstance(bars[0], list) and isinstance(bars[0][0], list):
        bars = bars[1]  # Second entry is the real timeseries
    elif isinstance(bars[0], list):
        bars = bars

    # Validate the shape of the data
    if not all(len(row) == 2 for row in bars):
        raise ValueError("Each row in 'bars' must contain [date, price]")

    df = pd.DataFrame(bars, columns=["date", "uka_price"])
    df["date"] = pd.to_datetime(df["date"], errors="coerce")  # Handle invalid dates
    df = df.dropna(subset=["date"])  # Drop rows with invalid dates
    df = df.sort_values("date")

    print("✅ Fetched UKA prices from ICE JSON API.")
    return df