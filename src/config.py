import socket
import json
import os

# Fixed - never change
TCP_PORT = 8080
HTTP_PORT = 5000
IP_ADDRESS = '0.0.0.0'
CHUNK_SIZE = 32768

BUSY_MESSAGE = b'\x01'
OK_MESSAGE = b'\x00'

# Auto-detected from hostname
hostname = socket.gethostname()
STATION_ID = hostname.split('-')[-1].upper()  # Extract station ID from hostname (e.g., 'FS1', 'WS')

# Loaded from master file
config_path = os.path.join(os.path.dirname(__file__), 'stations.json')
with open(config_path, 'r') as f:
    station_ips = json.load(f)

STATIONS = {sid: (ip, TCP_PORT) for sid, ip in station_ips.items()}
NUMBER_OF_STATIONS = len(STATIONS)
