# to run this script, you must be working from uka_tracker subfolder. To do this, you must use the code cd uka_tracker
import subprocess
import sys
import os

base_path = os.path.dirname(__file__)
venv_python = sys.executable  # This gets the current Python interpreter (your .venv one)

scripts = [
    "indicators/fetch_prices.py",
    "indicators/gas_prices.py",
    "indicators/weather.py",
    "indicators/news_feed.py"
]

for script in scripts:
    print(f"Running {script}...")
    subprocess.run([venv_python, os.path.join(base_path, script)], check=False)
