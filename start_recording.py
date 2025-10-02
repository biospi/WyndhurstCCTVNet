import subprocess
import time

from utils import SOURCE_PATH


def main():
    ssh_tunnel_script = (SOURCE_PATH / f"open_ssh_tunnel.sh").as_posix()
    print("Starting SSH tunnels...")
    print(ssh_tunnel_script)
    subprocess.run(ssh_tunnel_script, shell=True, check=True)
    subprocess.run((SOURCE_PATH / f"open_ssh_tunnel_hikvision.sh").as_posix(), shell=True, check=True)

    print("Starting report_email.py in background...")
    subprocess.Popen(["python3", (SOURCE_PATH / f"report_email.py").as_posix()])
    time.sleep(2)

    print("Starting transfer_from_farm_pc.py in background...")
    subprocess.Popen(["python3", (SOURCE_PATH / f"transfer_from_farm_pc.py").as_posix()])
    time.sleep(2)

    print("Starting hanwha_rtsp_multi.py...")
    subprocess.run(["python3", (SOURCE_PATH / f"hanwha_rtsp_multi.py").as_posix()])

if __name__ == '__main__':
    main()

