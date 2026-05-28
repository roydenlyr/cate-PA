TCP_PORT = 8080
IP_ADDRESS = '0.0.0.0'
CHUNK_SIZE = 32768
STATION_ID = 'FS1'
WATCH_FOLDER = '/home/cate/audio_inbox'
NUMBER_OF_STATIONS = 3


# To be change upon deployment

STATIONS = {
    'FS1': ('192.168.0.133', 8080),
    'FS2': ('192.168.0.161', 8081),  # For testing, FS2 is the same machine
    'FS3': ('192.168.0.161', 8082),  # For testing, FS3 is the same machine
}
