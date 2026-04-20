def read_file(file):

    start, end = None, None

    with open(file, "r") as f:
        for line in f:
            line = line.strip()

            if line.startswith("START TEMP"):
                start = int(line.split(":")[1].strip())

            elif line.startswith("END TEMP"):
                end = int(line.split(":")[1].strip())

    return start, end


def calculate_avg(start, end):
    return (start + end) // 2