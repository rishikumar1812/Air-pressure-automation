import os
from datetime import datetime

import config
from cache import save_cache, load_cache, trim
from monitor_temp import read_file, calculate_avg


def is_valid(file):
    return datetime.fromtimestamp(os.path.getmtime(file)).hour >= 12


def process_data():

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

    files = [
        os.path.join(config.LOG_DIR, f)
        for f in os.listdir(config.LOG_DIR)
        if f.endswith(".csv")
    ]

    f_arr = [[] for _ in range(6)]
    r_arr = [[] for _ in range(6)]

    for file in files:

        if not is_valid(file):
            continue

        key = os.path.basename(file)[-7:-4]
        idx = int(os.path.basename(file)[-6:-4]) - 1

        if key in config.front_file:
            f_arr[idx].append(file)

        elif key in config.rear_file:
            r_arr[idx].append(file)

    # PROCESS
    for i in range(6):

        # FRONT
        if f_arr[i]:
            latest = max(f_arr[i], key=os.path.getmtime)

            if config.LAST_FILES.get(f"f{i}") != latest:
                s, e = read_file(latest)

                if s is not None:
                    front_start[i].append(s)
                    front_end[i].append(e)
                    config.LAST_FILES[f"f{i}"] = latest

        # REAR
        if r_arr[i]:
            latest = max(r_arr[i], key=os.path.getmtime)

            if config.LAST_FILES.get(f"r{i}") != latest:
                s, e = read_file(latest)

                if s is not None:
                    rear_start[i].append(s)
                    rear_end[i].append(e)
                    config.LAST_FILES[f"r{i}"] = latest

    # TRIM
    for i in range(6):
        front_start[i] = trim(front_start[i], config.MAX_POINTS)
        front_end[i] = trim(front_end[i], config.MAX_POINTS)
        rear_start[i] = trim(rear_start[i], config.MAX_POINTS)
        rear_end[i] = trim(rear_end[i], config.MAX_POINTS)

    save_cache({
        "front_start": front_start,
        "front_end": front_end,
        "rear_start": rear_start,
        "rear_end": rear_end
    })

    # AVG
    front_avg = [
        calculate_avg(front_start[i][-1], front_end[i][-1])
        if front_start[i] else 0
        for i in range(6)
    ]

    rear_avg = [
        calculate_avg(rear_start[i][-1], rear_end[i][-1])
        if rear_start[i] else 0
        for i in range(6)
    ]

    return front_start, front_end, rear_start, rear_end, front_avg, rear_avg