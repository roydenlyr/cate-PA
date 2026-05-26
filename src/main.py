from config import TCP_PORT, IP_ADDRESS
from server import AudioServer

if __name__ == "__main__":
    server = AudioServer(IP_ADDRESS, TCP_PORT)
    server.start()
