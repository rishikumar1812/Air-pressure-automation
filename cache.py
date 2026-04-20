import json
import os
from datetime import datetime

CACHE_FILE = "temp_cache.json"
MAX_POINTS = 360  # 24 hours (4 min interval)

# Track last processed file per rack
LAST_FILES = {}

def save_cache(data):
    data["timestamp"] = datetime.now().isoformat()
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE, "r") as f:
        return json.load(f)

def trim_24hr(arr):
    return arr[-MAX_POINTS:] if len(arr) > MAX_POINTS else arr