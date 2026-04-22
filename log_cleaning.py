import os
import config
import pandas as pd
from datetime import datetime

from monitor_temp import read_start_temp, read_end_temp


def is_12_pm(file):
    return datetime.fromtimestamp(os.path.getmtime(file)).hour >= 12


def read_latest_dfile(files):

    model_name = []
    start_temp = []
    end_temp = []
    update_time = []

    for file in files:
        with open(file, "r") as f:
            for line in f:
                line = line.strip()

                if line.startswith("MODEL"):
                    model_name.append(line.split(":")[1].strip())

                elif line.startswith("START TEMP"):
                    start_temp.append(int(line.split(":")[1].strip()))

                elif line.startswith("END TEMP"):
                    end_temp.append(int(line.split(":")[1].strip()))

                elif line.startswith("UPDATE TIME"):
                    update_time.append(line.split(":")[1].strip())

    if not model_name:
        return None

    return pd.DataFrame({
        "modelname": model_name,
        "Start Temp": start_temp,
        "End Temp": end_temp,
        "Update Time": update_time
    })


def read_latest_array_file(file_array):
    if not file_array:
        return None

    file_array = sorted(file_array, key=os.path.getmtime)
    return read_latest_dfile(file_array)


def read_latest_start_array_file(file_arr, data_points=20):

    arrays = []

    for arr in file_arr:
        df = read_latest_array_file(arr)

        if df is not None:
            x = read_start_temp(df)

            if len(x) > data_points:
                x = x[-data_points:]

            arrays.append(x)
        else:
            arrays.append([])

    return arrays


def read_latest_end_array_file(file_arr, data_points=20):

    arrays = []

    for arr in file_arr:
        df = read_latest_array_file(arr)

        if df is not None:
            x = read_end_temp(df)

            if len(x) > data_points:
                x = x[-data_points:]

            arrays.append(x)
        else:
            arrays.append([])

    return arrays


def processlog(directory):

    front_rack = []
    rear_rack = []

    # RESET ARRAYS
    config.f_arr = [[] for _ in range(6)]
    config.r_arr = [[] for _ in range(6)]

    files = [
        os.path.join(directory, f)
        for f in os.listdir(directory)
        if f.endswith(".csv")
    ]

    for file in files:

        key = os.path.basename(file)[-7:-4]
        key1 = os.path.basename(file)[-5:-4]

        if key in config.front_file:

            if is_12_pm(file):

                front_rack.append(file)

                if key1 in ['1']:
                    config.f_arr[0].append(file)
                elif key1 in ['2']:
                    config.f_arr[1].append(file)
                elif key1 in ['3']:
                    config.f_arr[2].append(file)
                elif key1 in ['4']:
                    config.f_arr[3].append(file)
                elif key1 in ['5']:
                    config.f_arr[4].append(file)
                elif key1 in ['6']:
                    config.f_arr[5].append(file)

        elif key in config.wear_file:

            if is_12_pm(file):

                rear_rack.append(file)

                if key1 in ['1']:
                    config.r_arr[0].append(file)
                elif key1 in ['2']:
                    config.r_arr[1].append(file)
                elif key1 in ['3']:
                    config.r_arr[2].append(file)
                elif key1 in ['4']:
                    config.r_arr[3].append(file)
                elif key1 in ['5']:
                    config.r_arr[4].append(file)
                elif key1 in ['6']:
                    config.r_arr[5].append(file)

    front_start = read_latest_start_array_file(config.f_arr)
    front_end = read_latest_end_array_file(config.f_arr)

    rear_start = read_latest_start_array_file(config.r_arr)
    rear_end = read_latest_end_array_file(config.r_arr)

    return front_start, front_end, rear_start, rear_end