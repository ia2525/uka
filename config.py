# uka_tracker/config.py
from pathlib import Path

# Root directory of your project
BASE_DIR = Path(__file__).resolve().parent

# Data directories
DATA_DIR = BASE_DIR / "data"
RAW_DATA_PATH = DATA_DIR / "raw"
PROCESSED_DATA_PATH = DATA_DIR / "processed"

# URLs or API endpoints (placeholder)
UKA_PRICE_SOURCE = "https://example.com/uka-prices"
