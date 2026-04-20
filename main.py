import time
from log_cleaning import process_and_plot

LOG_DIR = "YOUR_LOG_FOLDER_PATH"

while True:
    process_and_plot(LOG_DIR)
    time.sleep(240)