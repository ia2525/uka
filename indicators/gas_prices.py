def fetch_gas_prices():
    import yfinance as yf
    import pandas as pd

    ticker_labels = {
        "NG=F": "US Natural Gas (Henry Hub)",
        "BZ=F": "Brent Crude Oil"
    }

    df = yf.download(list(ticker_labels.keys()), period="3mo", interval="1d", auto_adjust=True)

    # Flatten MultiIndex (e.g., ('NG=F', 'Close') → 'NG=F_Close')
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [f"{ticker}_{metric}" for ticker, metric in df.columns]

    df.reset_index(inplace=True)
    df.rename(columns={"Date": "date"}, inplace=True)
    return df
