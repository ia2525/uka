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
    data = response.json()

    # 👇 Check which 'bars' entry has the actual price data (usually second one)
    bars = data.get("bars", [])
    if isinstance(bars[0], list) and isinstance(bars[0][0], list):
        bars = bars[1]  # Second entry is the real timeseries
    elif isinstance(bars[0], list):
        bars = bars

    # Double-check shape of the first entry
    if not all(len(row) == 2 for row in bars):
        raise ValueError("Each row in 'bars' must contain [date, price]")

    df = pd.DataFrame(bars, columns=["date", "uka_price"])
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")

    print("✅ Fetched UKA prices from ICE JSON API.")
    return df
