#!/bin/bash

# Path to your SSH private key
SSH_KEY_PATH="$HOME/.ssh/id_rsa"

# SSH server details
SSH_USER="$USER"
SSH_SERVER="10.70.66.2"

# File containing camera details
CAMERA_FILE="hanwha.txt"

# Check if camera IP is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <camera_ip> [local_port]"
    exit 1
fi

CAMERA_IP="$1"
LOCAL_PORT="$2"

# If no port is provided, find the corresponding local port for the camera IP from the file
if [ -z "$LOCAL_PORT" ]; then
    LOCAL_PORT=$(grep "^$CAMERA_IP " "$CAMERA_FILE" | awk '{print $3}')
    if [ -z "$LOCAL_PORT" ]; then
        echo "Camera IP not found in $CAMERA_FILE and no local port provided"
        exit 1
    fi
fi

# Kill existing tunnel for this camera
EXISTING_TUNNEL_PIDS=$(pgrep -f "ssh -i $SSH_KEY_PATH -L ${LOCAL_PORT}:${CAMERA_IP}:554")
if [ -n "$EXISTING_TUNNEL_PIDS" ]; then
    echo "Closing existing tunnel for $CAMERA_IP on port $LOCAL_PORT..."
    # Loop through each PID and gracefully terminate it
    for PID in $EXISTING_TUNNEL_PIDS; do
        echo "Terminating process $PID"
        kill -TERM "$PID"
        # Wait a little for the process to terminate
        sleep 2
        # Check if the process is still running and force kill if necessary
        if ps -p "$PID" > /dev/null; then
            echo "Process $PID didn't terminate gracefully, force killing..."
            kill -9 "$PID"
        fi
        sleep 1
    done
else
    echo "No existing tunnel found for $CAMERA_IP on port $LOCAL_PORT."
fi

# Open new tunnel
SSH_COMMAND="ssh -i $SSH_KEY_PATH -L ${LOCAL_PORT}:${CAMERA_IP}:554 -N ${SSH_USER}@${SSH_SERVER}"
echo "Opening SSH tunnel for $CAMERA_IP on port $LOCAL_PORT..."
gnome-terminal -- bash -c "${SSH_COMMAND}; exec bash"
