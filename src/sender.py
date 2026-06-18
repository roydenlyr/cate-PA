import time
import socket
import threading
from config import CHUNK_SIZE, OK_MESSAGE

class AudioSender:
    def send_file(self, target_ip, filepath):
        """Sends a WAV file to the specified target IP address over TCP."""

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(target_ip)

            response = s.recv(1)
            if response != OK_MESSAGE:
                s.close()
                return {'status': 'busy', 'message': f'Target {target_ip} is busy'}
            
            s.settimeout(None)

            with open(filepath, 'rb') as f:
                file_data = f.read()
            
            def stream():
                try:
                    s.sendall(file_data)
                    time.sleep(0.5)
                except Exception as e:
                    print(f"Streaming error to {target_ip}: {e}")
                finally:
                    s.close()
            
            threading.Thread(target=stream, daemon=True).start()
            return {'status': 'ok', 'message': f'Sent to {target_ip}'}
        
        except Exception as e:
            return {'status': 'error', 'message': f'Failed to send to {target_ip}: {e}'}
