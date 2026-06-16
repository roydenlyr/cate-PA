import threading

from config import TCP_PORT, IP_ADDRESS, WATCH_FOLDER
from playback_state import PlaybackState
from server import AudioServer
from file_watcher import FileWatcher
from router import Router


if __name__ == "__main__":
    state = PlaybackState()
    server = AudioServer(IP_ADDRESS, TCP_PORT, state)
    server_thread = threading.Thread(target=server.start, daemon=True)
    server_thread.start()
    print(f"Audio server started on {IP_ADDRESS}:{TCP_PORT}")

    router = Router(state)
    watcher = FileWatcher(WATCH_FOLDER, router.handle_file)
    try:
        watcher.start()
    except KeyboardInterrupt:
        print("Shutting down...")
