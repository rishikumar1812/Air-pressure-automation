from datetime import datetime, timedelta
import json, os

CACHE_FILE = "cache.json"

def load_cache():
    if not os.path.exists(CACHE_FILE):
        return None

    with open(CACHE_FILE, "r") as f:
        data = json.load(f)

    t = datetime.fromisoformat(data["timestamp"])

    if datetime.now() - t > timedelta(hours=24):
        return None  # expired

    return data


def save_cache(data):
    data["timestamp"] = datetime.now().isoformat()

    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)