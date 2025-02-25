#!/bin/bash

# Path to your SSH private key
SSH_KEY_PATH="$HOME/.ssh/id_rsa_hanwha"

# SSH server details
SSH_USER="fo18103"
SSH_SERVER="10.70.66.2"


mapfile -t CAMERA_IPS < hanwha.txt

# Starting local port number
START_PORT=5554

# Function to open a new terminal with an SSH tunnel
open_ssh_tunnel() {
    local camera_ip=$1
    local local_port=$2

    # SSH command to establish the tunnel
    SSH_COMMAND="ssh -i $SSH_KEY_PATH -L ${local_port}:${camera_ip}:554 -N ${SSH_USER}@${SSH_SERVER}"

    echo "Opening SSH tunnel for camera ${camera_ip} on local port ${local_port}..."

    # Open a new GNOME terminal and run the SSH command
    gnome-terminal -- bash -c "${SSH_COMMAND}; exec bash"
}

# Loop through all cameras and open SSH tunnels
for i in "${!CAMERA_IPS[@]}"; do
    camera_ip=${CAMERA_IPS[$i]}
    local_port=$((START_PORT + i))
    open_ssh_tunnel "$camera_ip" "$local_port"
    sleep 0.5  # Small delay to avoid overwhelming the system
done

echo "All SSH tunnels are being established."
