def fetch_gas_prices():
    import yfinance as yf
    import pandas as pd

    tickers = {
        "NG=F": "US Natural Gas (Henry Hub)",
        "BZ=F": "Brent Crude Oil"
    }

    df = yf.download(list(tickers.keys()), period="3mo", interval="1d", auto_adjust=True)

    # Reset columns if it's a MultiIndex (fix!)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [f"{col[0]}_{col[1]}" for col in df.columns]  # e.g., NG=F_Close

    df.reset_index(inplace=True)
    df.rename(columns={"Date": "date"}, inplace=True)
    return df
