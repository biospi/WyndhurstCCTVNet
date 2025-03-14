import rstp_playback
import concurrent.futures
import queue


def process_cctv(ip, is_fisheye, port):
    print(ip, is_fisheye, port)
    rstp_playback.main(ip, is_fisheye, port)


def main(ip_file):
    cctvs = [line.strip() for line in open(ip_file).readlines()]

    cctv_queue = queue.Queue()
    for i, l in enumerate(cctvs):
        ip, is_fisheye, port = l.split(" ")
        try:
            cctv_queue.put((ip, int(is_fisheye), int(port)))
        except ValueError as e:
            print(e)

    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as executor:
        while not cctv_queue.empty():
            ip, is_fisheye, port = cctv_queue.get()
            executor.submit(process_cctv, ip, is_fisheye, port)

if __name__ == "__main__":
    main("hanwha.txt")
