TCP_PORT = 8080
IP_ADDRESS = '0.0.0.0'
CHUNK_SIZE = 32768
STATION_ID = 'FS1'
WATCH_FOLDER = '/home/cate/audio_inbox'
NUMBER_OF_STATIONS = 3


# To be change upon deployment

STATIONS = {
    'FS1': ('cate-PA-FS1.local', TCP_PORT),
    'FS2': ('cate-PA-FS2.local', TCP_PORT),
    'WS': ('cate-PA-WS.local', TCP_PORT),
}
