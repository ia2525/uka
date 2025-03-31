# to run this script, you must be working from uka_tracker subfolder. To do this, you must use the code cd uka_tracker
import subprocess

scripts = [
    "indicators/fetch_prices.py",
    "indicators/gas_prices.py",
    "indicators/weather.py",
    "indicators/news_feed.py"
]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run(["python", script])
