import threading

from config import TCP_PORT, HTTP_PORT, IP_ADDRESS
from playback_state import PlaybackState
from server import AudioServer
from http_server import HTTPServer
from router import Router


if __name__ == "__main__":
    state = PlaybackState()

    # Start TCP server for receiving audio from other Pis
    server = AudioServer(IP_ADDRESS, TCP_PORT, state)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    print(f"Audio server started on {IP_ADDRESS}:{TCP_PORT}")

    router = Router(state)
    http = HTTPServer(router, state)
    print(f"HTTP server starting on {IP_ADDRESS}:{HTTP_PORT}")

    try:
        http.start(IP_ADDRESS, HTTP_PORT)
    except KeyboardInterrupt:
        print("Shutting down...")
