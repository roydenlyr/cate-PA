import struct

def read_header(client_socket):
    header = b''
    while len(header) < 44:
        header += client_socket.recv(44 - len(header))
    return header

def is_valid_wav(header_bytes):
    return header_bytes[0:4] == b'RIFF' and header_bytes[8:12] == b'WAVE'

def parse_wav_header(header_bytes):
    if not is_valid_wav(header_bytes):
        raise ValueError("Not a valid WAV file")
    
    
    
    channels = struct.unpack('<H', header_bytes[22:24])[0]
    sample_rate = struct.unpack('<I', header_bytes[24:28])[0]
    bits_per_sample = struct.unpack('<H', header_bytes[34:36])[0]
    return channels, sample_rate, bits_per_sample
