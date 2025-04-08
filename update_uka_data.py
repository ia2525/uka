from indicators.scrape_uka_prices import scrape_and_update_uka_timeseries

def run_daily_scrape():
    try:
        df = scrape_and_update_uka_timeseries("data/raw/uka_timeseries.csv")
        print(df.tail())
    except Exception as e:
        import traceback
        traceback.print_exc()
        exit(1)  # Let GitHub Actions know this failed

if __name__ == "__main__":
    run_daily_scrape()
