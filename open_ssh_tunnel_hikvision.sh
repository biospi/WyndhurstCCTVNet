#!/bin/bash

# Path to your SSH private key
SSH_KEY_PATH="$HOME/.ssh/id_rsa_hanwha"

# SSH server details
SSH_USER="$USER"
SSH_SERVER="10.70.66.2"

# Read the IP and port from file.txt
mapfile -t CAMERA_DETAILS < hikvision.txt

# Function to open a new terminal with an SSH tunnel
open_ssh_tunnel() {
    local camera_ip=$1
    local local_port=$2

    # SSH command to establish the tunnel
    SSH_COMMAND="ssh -i $SSH_KEY_PATH -L ${local_port}:${camera_ip}:554 -N ${SSH_USER}@${SSH_SERVER}"

    echo "Opening SSH ${SSH_COMMAND} tunnel for camera ${camera_ip} on local port ${local_port}..."

    # Open a new GNOME terminal and run the SSH command
    gnome-terminal -- bash -c "${SSH_COMMAND}; exec bash"
}

# Loop through all camera details and open SSH tunnels
for camera_detail in "${CAMERA_DETAILS[@]}"; do
    camera_ip=$(echo $camera_detail | cut -d ' ' -f 1)  # Get the IP (first value)
    local_port=$(echo $camera_detail | cut -d ' ' -f 3)  # Get the port (third value)

    open_ssh_tunnel "$camera_ip" "$local_port"
    sleep 0.5  # Small delay to avoid overwhelming the system
done

echo "All SSH tunnels are being established."
