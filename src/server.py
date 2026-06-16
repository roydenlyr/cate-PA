import socket
import threading
import time

from config import CHUNK_SIZE, NUMBER_OF_STATIONS
from wav_parser import parse_wav_header, read_header
from audio_player import AudioPlayer

BUSY_MESSAGE = b'\x01'
OK_MESSAGE = b'\x00'

class AudioServer:
    def __init__(self, ip_address, tcp_port, playback_state):
        self.ip_address = ip_address
        self.tcp_port = tcp_port
        self.playback_state = playback_state

    def start(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.ip_address, self.tcp_port))
        self.s.listen(NUMBER_OF_STATIONS)

        try:
            while True:
                client_socket, addr = self.s.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_thread.start()

        except KeyboardInterrupt:
            print("Shutting down server...")
            self.s.close()

    def handle_client(self, client_socket, addr):
        print(f"Connection from {addr} has been established.")

        if not self.playback_state.try_acquire():
            print(f"Busy - rejecting connection from {addr}.")
            client_socket.sendall(BUSY_MESSAGE)
            client_socket.close()
            return

        client_socket.sendall(OK_MESSAGE)

        try:
            header = read_header(client_socket)
            channels, sample_rate, bits_per_sample = parse_wav_header(header)
            audio_player = AudioPlayer(channels, sample_rate, bits_per_sample)

            while True:
                data = client_socket.recv(CHUNK_SIZE)
                if not data:
                    break
                audio_player.play(data)

            time.sleep(0.5)  # Ensure all audio is played before closing
            audio_player.close()
        finally:
            self.playback_state.release()
            client_socket.close()
