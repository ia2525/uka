import pandas as pd
from indicators.carbon_intensity_api import fetch_national_carbon_timeseries_2020

print("📥 Fetching carbon intensity data from 2020 to today...")
df = fetch_national_carbon_timeseries_2020(start_date="2020-01-01")

print("📥 Fetching carbon intensity data from 2020 to today...")
df = fetch_national_carbon_timeseries_2020(start_date="2020-01-01")

print("💾 Saving to file: data/carbon_intensity_2020_to_latest.parquet")
df.to_parquet("data/carbon_intensity_2020_to_latest.parquet")

print("✅ Done! Historical carbon intensity saved.")
