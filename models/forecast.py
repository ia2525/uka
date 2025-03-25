# models/forecast.py

from prophet import Prophet
import pandas as pd

def generate_forecast(df, days_ahead=7):
    # Prophet expects columns named 'ds' and 'y'
    df_prophet = df.rename(columns={"date": "ds", "uka_price": "y"})

    model = Prophet(daily_seasonality=True)
    model.fit(df_prophet)

    future = model.make_future_dataframe(periods=days_ahead)
    forecast = model.predict(future)

    return forecast, model
