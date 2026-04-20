import os
import config
import pandas as pd
from datetime import datetime

from cache import save_cache, load_cache, trim_24hr, LAST_FILES
from temp_DL_graph import Temp_graph


def is_12_pm(file):
    mod_time = datetime.fromtimestamp(os.path.getmtime(file))
    return mod_time.hour >= 12


def read_latest_dfile(files):

    model_name = []
    start_temp = []
    end_temp = []
    update_time = []

    for file in files:
        with open(file, "r") as f:
            for line in f:
                line = line.strip()

                if line.startswith("MODEL :"):
                    model_name.append(line.split(":")[1].strip())

                elif line.startswith("START TEMP :"):
                    start_temp.append(int(line.split(":")[1].strip()))

                elif line.startswith("END TEMP :"):
                    end_temp.append(int(line.split(":")[1].strip()))

                elif line.startswith("UPDATE TIME :"):
                    update_time.append(line.split(":")[1].strip())

    if not model_name:
        return None

    return pd.DataFrame({
        "model": model_name,
        "Start Temp": start_temp,
        "End Temp": end_temp,
        "Update Time": update_time
    })


def process_and_plot(log_dir):

    # LOAD CACHE
    cache = load_cache()

    if cache:
        front_start = cache["front_start"]
        front_end = cache["front_end"]
        rear_start = cache["rear_start"]
        rear_end = cache["rear_end"]
    else:
        front_start = [[] for _ in range(6)]
        front_end = [[] for _ in range(6)]
        rear_start = [[] for _ in range(6)]
        rear_end = [[] for _ in range(6)]

    # CLEAR FILE ARRAYS
    for i in range(6):
        config.f_arr[i].clear()
        config.r_arr[i].clear()

    # READ FILES
    csv_files = [
        os.path.join(log_dir, f)
        for f in os.listdir(log_dir)
        if f.endswith(".csv")
    ]

    for file in csv_files:

        if not is_12_pm(file):
            continue

        key = os.path.basename(file)[-7:-4]
        key1 = os.path.basename(file)[-6:-4]

        idx = int(key1) - 1

        if key in config.front_file:
            if 0 <= idx < 6:
                config.f_arr[idx].append(file)

        elif key in config.rear_file:
            if 0 <= idx < 6:
                config.r_arr[idx].append(file)

    # PROCESS LATEST FILE PER RACK
    for i in range(6):

        # FRONT
        if config.f_arr[i]:
            latest_file = max(config.f_arr[i], key=os.path.getmtime)
            df = read_latest_dfile([latest_file])

            if df is not None and not df.empty:
                s = int(df["Start Temp"].values[-1])
                e = int(df["End Temp"].values[-1])

                if LAST_FILES.get(f"front_{i}") != latest_file:
                    front_start[i].append(s)
                    front_end[i].append(e)
                    LAST_FILES[f"front_{i}"] = latest_file

        # REAR
        if config.r_arr[i]:
            latest_file = max(config.r_arr[i], key=os.path.getmtime)
            df = read_latest_dfile([latest_file])

            if df is not None and not df.empty:
                s = int(df["Start Temp"].values[-1])
                e = int(df["End Temp"].values[-1])

                if LAST_FILES.get(f"rear_{i}") != latest_file:
                    rear_start[i].append(s)
                    rear_end[i].append(e)
                    LAST_FILES[f"rear_{i}"] = latest_file

    # TRIM 24 HOURS
    for i in range(6):
        front_start[i] = trim_24hr(front_start[i])
        front_end[i] = trim_24hr(front_end[i])
        rear_start[i] = trim_24hr(rear_start[i])
        rear_end[i] = trim_24hr(rear_end[i])

    # SAVE CACHE
    save_cache({
        "front_start": front_start,
        "front_end": front_end,
        "rear_start": rear_start,
        "rear_end": rear_end
    })

    # GRAPH
    Temp_graph(front_start, front_end, rear_start, rear_end)