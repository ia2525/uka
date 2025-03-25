# analysis/visualize_prices.py

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Load the data
DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "raw" / "uka_prices.csv"
df = pd.read_csv(DATA_PATH)

# Convert date column to datetime
df["date"] = pd.to_datetime(df["date"])
df = df.sort_values("date")

# Plot
plt.figure(figsize=(10, 5))
plt.plot(df["date"], df["uka_price"], marker='o', linestyle='-')
plt.title("UKA Prices Over Time")
plt.xlabel("Date")
plt.ylabel("Price (€)")
plt.grid(True)
plt.tight_layout()
plt.show()
