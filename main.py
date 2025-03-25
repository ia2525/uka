# main.py
from indicators.fetch_prices import get_real_uka_prices
from config import RAW_DATA_PATH

def main():
    print("Starting UKA data pipeline...")

    # Fetch real UKA prices
    df = get_real_uka_prices()
    RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)  # Ensure path exists
    df.to_csv(RAW_DATA_PATH / "uka_prices.csv", index=False)

    print("Saved UKA price data to CSV.")
    print("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
