import socket
import wave
import time

filename = '../../audio/CATE.wav'
chunk = 1024
wf = wave.open(filename, 'rb')

bytes_per_second = wf.getframerate() * wf.getsampwidth() * wf.getnchannels()
chunk_duration = (chunk * wf.getsampwidth()) / bytes_per_second

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('localhost', 8080))


with open(filename, 'rb') as f:
    header = f.read(44) 
    client_socket.sendall(header)

    data = wf.readframes(chunk)
    while data:
        client_socket.sendall(data)
        data = wf.readframes(chunk)
        # time.sleep(chunk_duration)

time.sleep(0.5)
wf.close()
client_socket.close()
