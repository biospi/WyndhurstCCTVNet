import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import subprocess
import socket
import configparser
import getpass
config = configparser.ConfigParser()
config.read("config.cfg")

CAMERA_LIST_FILE = Path("hanwha_ip_study.txt")
BASE_OUTPUT_DIR = Path("/mnt/storage/cctvnet/")
CHUNK_DURATION = 20 * 60  # 20 minutes
SSH_KEY_PATH = "~/.ssh/id_rsa_hanwha"
SSH_USER = getpass.getuser()
SSH_SERVER = "10.70.66.2"


def wait_for_port(port, timeout=10):
    start_time = time.time()
    while time.time() - start_time < timeout:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(("localhost", port))
            if result == 0:
                return True
        time.sleep(0.5)
    raise TimeoutError(f"Port {port} did not open within {timeout} seconds.")



def create_ssh_tunnel(local_port, camera_ip):
    """
    Establish an SSH tunnel to forward the RTSP port from the remote server to the local machine.
    Prints the SSH command output for debugging purposes.
    """
    ssh_command = [
        "ssh",
        "-i", str(SSH_KEY_PATH),
        #"-o", "ControlMaster=no",  # Uncomment if you want to force new connections
        "-L", f"{local_port}:{camera_ip}:554",
        "-f",  # Run SSH in the background after connection
        f"{SSH_USER}@{SSH_SERVER}",
        "sleep 1"
    ]

    print(f"Executing SSH command: {' '.join(ssh_command)}")

    # Capture the output and error
    process = subprocess.Popen(
        ssh_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # Read the output and error
    stdout, stderr = process.communicate()

    if stdout:
        print(f"SSH stdout: {stdout.decode().strip()}")
    if stderr:
        print(f"SSH stderr: {stderr.decode().strip()}")

    return process


def get_camera_directory(rtsp_url):
    """Generate a directory path based on the last two elements of the IP and the current date."""
    ip_address = rtsp_url.split("@")[-1].split(":")[0]  # Extract IP address
    ip_suffix = ".".join(ip_address.split(".")[-2:])  # Last two elements of the IP
    date_str = datetime.now().strftime("%Y%b%d")  # Format date as 09Jan2025
    return BASE_OUTPUT_DIR / ip_suffix / date_str / "videos"


def get_output_filename(output_dir, start_time):
    """Generate a filename in the format startofvideo_endofvideo.mp4."""
    end_time = start_time + timedelta(seconds=CHUNK_DURATION)
    start_str = start_time.strftime("%Y%m%dT%H%M%S")
    end_str = end_time.strftime("%Y%m%dT%H%M%S")
    return output_dir / f"{start_str}_{end_str}.mp4"


def record_camera(rtsp_url, local_port):
    """Record video from the IP camera in chunks using FFmpeg."""
    while True:
        output_dir = get_camera_directory(rtsp_url)
        output_dir.mkdir(parents=True, exist_ok=True)
        start_time = datetime.now()
        output_file = get_output_filename(output_dir, start_time)
        print(f"Recording started: {output_file}")

        command = [
            "ffmpeg",
            "-y",  # Overwrite output file if it exists
            "-rtsp_transport", "tcp",  # Use TCP for RTSP
            "-i", f"rtsp://admin:{config['AUTH']['password_hanwha']}@localhost:{local_port}/profile2/media.smp",  # Local tunneled RTSP stream
            "-t", str(CHUNK_DURATION),  # Duration of the video chunk
            "-c:v", "libx264",  # Re-encode video using H.264
            "-preset", "fast",  # Speed-quality tradeoff
            "-crf", "28",  # Constant Rate Factor
            "-r", "16",  # Frame rate
            "-an",  # Disable audio
            str(output_file)  # Output file
        ]

        try:
            subprocess.run(command, check=True)
            print(f"Recording saved: {output_file}")
        except subprocess.CalledProcessError as e:
            print(f"Error recording {rtsp_url}: {e}")
            break


def main():
    """Main function to read camera list, establish SSH tunnels, and start recording."""
    with CAMERA_LIST_FILE.open("r") as file:
        camera_ips = [line.strip() for line in file if line.strip()]

    ssh_tunnels = []

    with ThreadPoolExecutor() as executor:
        for idx, camera_ip in enumerate(camera_ips):
            local_port = 5554 + idx  # Assign a unique local port for each camera

            # Establish SSH tunnel
            # tunnel = create_ssh_tunnel(local_port, camera_ip)
            # ssh_tunnels.append(tunnel)

            # # Wait for tunnel to be ready
            # try:
            #     wait_for_port(local_port)
            # except TimeoutError as e:
            #     print(f"Error establishing SSH tunnel for {camera_ip}: {e}")
            #     continue  # Skip this camera if tunnel doesn't establish

            # Start recording
            rtsp_url = f"rtsp://admin:{config['AUTH']['password_hanwha']}@{camera_ip}:554/profile2/media.smp"
            executor.submit(record_camera, rtsp_url, local_port)

    # Cleanup on exit
    for tunnel in ssh_tunnels:
        tunnel.terminate()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Recording stopped.")

#"#fo18103@it106570:~$ ssh -L 5554:10.70.66.16:554 fo18103@10.70.66.2

#ssh -i ~/.ssh/id_rsa_hanwha fo18103@10.70.66.2
#ssh-keygen -t rsa -b 4096 -C "fo18103@it106570"
#ssh-copy-id fo18103@10.70.66.2
#ssh fo18103@10.70.66.2
