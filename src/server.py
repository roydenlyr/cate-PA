import socket
import threading

from config import CHUNK_SIZE, NUMBER_OF_STATIONS, BUSY_MESSAGE, OK_MESSAGE
from wav_parser import read_header
from audio_player import AudioPlayer
from config import REPEAT, DELAY


class AudioServer:
    """TCP server that receives audio from other stations and plays it."""

    def __init__(self, ip_address, tcp_port, playback_state):
        self.ip_address = ip_address
        self.tcp_port = tcp_port
        self.playback_state = playback_state
        self.player = AudioPlayer(repeat=REPEAT, delay=DELAY)

    def start(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.s.bind((self.ip_address, self.tcp_port))
        self.s.listen(NUMBER_OF_STATIONS)

        try:
            while True:
                client_socket, addr = self.s.accept()
                threading.Thread(target=self._handle_client, args=(client_socket, addr)).start()
        except KeyboardInterrupt:
            print("Shutting down server...")
            self.s.close()

    def _handle_client(self, client_socket, addr):
        """Accept or reject connection, receive audio, play it."""
        print(f"Connection from {addr}")

        if not self.playback_state.try_acquire():
            print(f"Busy - rejecting {addr}")
            client_socket.sendall(BUSY_MESSAGE)
            client_socket.close()
            return

        client_socket.sendall(OK_MESSAGE)

        try:
            audio_data = self._receive_audio(client_socket)
            self.player.play_data(audio_data)
        finally:
            self.playback_state.release()
            client_socket.close()

    def _receive_audio(self, client_socket):
        """Buffer all incoming audio data and return as bytes."""
        header = read_header(client_socket)
        chunks = [header]

        while True:
            data = client_socket.recv(CHUNK_SIZE)
            if not data:
                break
            chunks.append(data)

        return b''.join(chunks)