import json
import os
from datetime import datetime

CACHE_FILE = "temp_cache.json"


def save_cache(data):
    data["timestamp"] = datetime.now().isoformat()
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)


def load_cache():
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE, "r") as f:
        return json.load(f)


def trim(arr, max_points):
    return arr[-max_points:] if len(arr) > max_points else arr