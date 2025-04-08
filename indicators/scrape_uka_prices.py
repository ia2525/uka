from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from datetime import date  #
import os
import time

def scrape_and_update_uka_timeseries(csv_path="data/raw/uka_timeseries.csv"):
    # ✅ Setup Selenium and headless Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")

    # ✅ Path to your chromedriver
    driver_path = r"C:\Users\Intern\chromedriver-win64\chromedriver-win64\chromedriver.exe"
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # ✅ Target URL
    url = "https://www.ice.com/products/80216150/UKA-Futures/data?marketId=7977905&span=1"
    driver.get(url)
    driver.execute_script("window.scrollBy(0, 300);")

    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "table"))
        )
    except:
        print("⚠️ Table not found after waiting.")
        driver.quit()
        return

    soup = BeautifulSoup(driver.page_source, "html.parser")
    driver.quit()

    with open("debug_ice.html", "w", encoding="utf-8") as f:
        f.write(soup.prettify())

    table = soup.find("table")
    if not table:
        raise ValueError("Contract table not found.")

    rows = table.find_all("tr")[1:]
    print("\n🧪 Extracted contracts:")
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 3:
            contract = cols[0].text.strip()
            price_str = cols[1].text.strip()

            print("-", contract)

            # ✅ Try to convert price to float
            try:
                last_price = float(price_str.replace(',', '').strip())
            except ValueError:
                continue

            last_price = float(price_str)
            today = date.today()

            if contract == "Dec25":
                new_row = pd.DataFrame([{
                    "date": today,
                    "uka_price": last_price
                }])

                if not os.path.exists(csv_path):
                    new_row.to_csv(csv_path, index=False)
                    print(f"📈 Timeseries started using contract {contract}")
                    return new_row

                existing = pd.read_csv(csv_path)
                existing["date"] = pd.to_datetime(existing["date"]).dt.date  # Ensures dtype is date
                
                if today not in existing["date"].values:
                    updated = pd.concat([existing, new_row])
                    updated.to_csv(csv_path, index=False)
                    print(f"✅ New price appended for contract {contract}")
                    return updated
                else:
                    print("⏸️ No update needed — already recorded.")
                    return existing

    raise ValueError("⚠️ No valid contracts found in table.")

if __name__ == "__main__":
    df = scrape_and_update_uka_timeseries()
    print(df.tail())
