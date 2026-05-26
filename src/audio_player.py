import subprocess
class AudioPlayer:
    def __init__(self, channels, sample_rate, bits_per_sample):
        format_map = {8: 'U8', 16: 'S16_LE', 24: 'S24_LE', 32: 'S32_LE'}
        self.process = subprocess.Popen(
            ['aplay', '-f', format_map[bits_per_sample],
             '-r', str(sample_rate),
             '-c', str(channels),
             '-'],
            stdin=subprocess.PIPE
        )

    def play(self, data):
        self.process.stdin.write(data)

    def close(self):
        self.process.stdin.close()
        self.process.wait()