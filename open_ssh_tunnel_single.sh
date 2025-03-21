#!/bin/bash

# Path to your SSH private key
SSH_KEY_PATH="$HOME/.ssh/id_rsa_hanwha"

# SSH server details
SSH_USER="fo18103"
SSH_SERVER="10.70.66.2"

# File containing camera details
CAMERA_FILE="hanwha.txt"

# Check if camera IP is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <camera_ip>"
    exit 1
fi

CAMERA_IP="$1"

# Find the corresponding local port for the camera IP
LOCAL_PORT=$(grep "^$CAMERA_IP " "$CAMERA_FILE" | awk '{print $3}')

if [ -z "$LOCAL_PORT" ]; then
    echo "Camera IP not found in $CAMERA_FILE"
    exit 1
fi

# Kill existing tunnel for this camera
EXISTING_TUNNEL_PID=$(pgrep -f "ssh -i $SSH_KEY_PATH -L ${LOCAL_PORT}:${CAMERA_IP}:554")
if [ -n "$EXISTING_TUNNEL_PID" ]; then
    echo "Closing existing tunnel for $CAMERA_IP on port $LOCAL_PORT..."
    kill "$EXISTING_TUNNEL_PID"
    sleep 1
fi

# Open new tunnel
SSH_COMMAND="ssh -i $SSH_KEY_PATH -L ${LOCAL_PORT}:${CAMERA_IP}:554 -N ${SSH_USER}@${SSH_SERVER}"
echo "Opening SSH tunnel for $CAMERA_IP on port $LOCAL_PORT..."
gnome-terminal -- bash -c "${SSH_COMMAND}; exec bash"
