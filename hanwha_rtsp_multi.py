import rstp_playback
import concurrent.futures
import queue
import pandas as pd
from pathlib import Path
from datetime import datetime
import time


def process_cctv(ip, is_fisheye, port):
    print(ip, is_fisheye, port)
    rstp_playback.main(ip, is_fisheye, port)


def main(ip_file):
    cctvs = [line.strip() for line in open(ip_file).readlines()]

    cctv_queue = queue.Queue()
    for i, l in enumerate(cctvs):
        if l == "":
            continue
        ip, is_fisheye, port = l.split(" ")
        try:
            cctv_queue.put((ip, int(is_fisheye), int(port)))
        except ValueError as e:
            print(e)

    with concurrent.futures.ThreadPoolExecutor(max_workers=35) as executor:
        while not cctv_queue.empty():
            ip, is_fisheye, port = cctv_queue.get()
            executor.submit(process_cctv, ip, is_fisheye, port)

if __name__ == "__main__":
    metadata_dir = Path("metadata")
    metadata_dir.mkdir(exist_ok=True)
    while True:
        start_time = time.time()
        main("hanwha_ip_study.txt")
        duration = time.time() - start_time
        timestamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        csv_file = metadata_dir / f"iteration_{timestamp}.csv"
        df = pd.DataFrame({"Timestamp": [timestamp], "Duration (s)": [duration]})
        df["Duration (days)"] = df["Duration (s)"] / 86400
        df.to_csv(csv_file, index=False)
        print(f"Iteration completed in {duration:.2f} seconds. Saved to {csv_file}")
