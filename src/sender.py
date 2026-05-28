import time
import socket
from config import CHUNK_SIZE

class AudioSender:
    def send_file(self, target_ip, filepath):
        """Sends a WAV file to the specified target IP address over TCP."""

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # s.settimeout(5)
            s.connect(target_ip)

            with open(filepath, 'rb') as f:
                header = f.read(44)
                s.sendall(header)
                
                data = f.read(CHUNK_SIZE)

                while data:
                    s.sendall(data)
                    data = f.read(CHUNK_SIZE)

            time.sleep(0.5)
            s.close()
            print(f"File '{filepath}' sent successfully to {target_ip}")
        except Exception as e:
            print(f"Error sending file '{filepath}' to {target_ip}: - {e}")
