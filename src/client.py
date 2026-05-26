import socket
import wave
import time

from config import CHUNK_SIZE, TCP_PORT, IP_ADDRESS

filename = '../audio/CATE.wav'
wf = wave.open(filename, 'rb')

bytes_per_second = wf.getframerate() * wf.getsampwidth() * wf.getnchannels()

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.0.133', TCP_PORT))


with open(filename, 'rb') as f:
    header = f.read(44)
    client_socket.sendall(header)

    data = wf.readframes(CHUNK_SIZE)
    while data:
        client_socket.sendall(data)
        data = wf.readframes(CHUNK_SIZE)

time.sleep(0.5)
wf.close()
client_socket.close()
