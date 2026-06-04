# DO NOT TOUCH THESE VARIABLES:
#   TCP_PORT
#   IP_ADDRESS
#   CHUNK_SIZE
#   WATCH_FOLDER

TCP_PORT = 8080
IP_ADDRESS = '0.0.0.0'
CHUNK_SIZE = 32768
WATCH_FOLDER = '/home/cate/audio_inbox'

# To be configured for each station before deployment

STATION_ID = 'FS1'
NUMBER_OF_STATIONS = 3


# To be change upon deployment

STATIONS = {
    'FS1': ('128.127.1.50', TCP_PORT),
    'FS2': ('128.127.2.50', TCP_PORT),
    'FS3': ('128.127.3.50', TCP_PORT),
    'WS': ('128.127.4.50', TCP_PORT),
}
