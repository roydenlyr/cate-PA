import socket
from config import TCP_PORT, CHUNK_SIZE

class AudioSender:
    def send_file(self, target_ip, filepath):
        """Sends a WAV file to the specified target IP address over TCP."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect((target_ip, TCP_PORT))

            with open(filepath, 'rb') as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    s.sendall(chunk)
            s.close()
            print(f"File '{filepath}' sent successfully to {target_ip}:{TCP_PORT}")
        except Exception as e:
            print(f"Error sending file '{filepath}' to {target_ip}:{TCP_PORT} - {e}")
