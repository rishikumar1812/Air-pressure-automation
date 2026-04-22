
def read_temp_complete_avg(start, end):
    return (start + end) // 2

def read_start_temp(df):
    return df["Start Temp"].astype(int).values

def read_end_temp(df):
    return df["End Temp"].astype(int).values