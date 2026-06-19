import time
import socket
import threading
from config import CHUNK_SIZE, OK_MESSAGE


class AudioSender:
    """Handles sending audio to remote stations over TCP."""

    def send_file(self, target_addr, filepath):
        """Connect, check accept/busy, stream in background. Returns immediately."""
        sock, status = self._connect(target_addr)
        if sock is None:
            return status

        file_data = self._read_file(filepath)
        self._stream_background(sock, file_data, target_addr)
        return {'status': 'ok', 'message': f'Accepted by {target_addr}'}

    def _connect(self, target_addr):
        """Establish TCP connection and check if station is free."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(target_addr)

            response = s.recv(1)
            if response != OK_MESSAGE:
                s.close()
                return None, {'status': 'busy', 'message': f'Target {target_addr} is busy'}

            s.settimeout(None)
            return s, None

        except Exception as e:
            return None, {'status': 'error', 'message': f'Failed to connect to {target_addr}: {e}'}

    def _read_file(self, filepath):
        """Read entire file into memory."""
        with open(filepath, 'rb') as f:
            return f.read()

    def _stream_background(self, sock, file_data, target_addr):
        """Stream audio data in a background thread."""
        def stream():
            try:
                sock.sendall(file_data)
                time.sleep(0.5)
            except Exception as e:
                print(f"Streaming error to {target_addr}: {e}")
            finally:
                sock.close()

        threading.Thread(target=stream, daemon=True).start()