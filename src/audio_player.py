import subprocess
import time


class AudioPlayer:
    """Handles all local audio playback through aplay."""

    def __init__(self, repeat=1, delay=1.0):
        self.repeat = repeat
        self.delay = delay

    def play_file(self, filepath):
        """Play a WAV file from disk (blocking)."""
        for i in range(self.repeat):
            subprocess.run(['aplay', filepath], check=True)
            if i < self.repeat - 1:
                time.sleep(self.delay) 

    def play_data(self, data):
        """Play raw WAV data from memory (blocking)."""
        for i in range(self.repeat):
            proc = subprocess.Popen(['aplay', '-'], stdin=subprocess.PIPE)
            proc.stdin.write(data)
            proc.stdin.close()
            proc.wait()
            if i < self.repeat - 1:
                time.sleep(self.delay)

    def play_stream(self, channels, sample_rate, bits_per_sample):
        """Return a StreamPlayer for chunk-by-chunk playback."""
        return StreamPlayer(channels, sample_rate, bits_per_sample)


class StreamPlayer:
    """Plays audio chunks as they arrive over TCP."""

    FORMAT_MAP = {8: 'U8', 16: 'S16_LE', 24: 'S24_LE', 32: 'S32_LE'}

    def __init__(self, channels, sample_rate, bits_per_sample):
        self.process = subprocess.Popen(
            ['aplay', '-f', self.FORMAT_MAP[bits_per_sample],
             '-r', str(sample_rate),
             '-c', str(channels),
             '-'],
            stdin=subprocess.PIPE
        )

    def write(self, data):
        self.process.stdin.write(data)

    def close(self):
        self.process.stdin.close()
        self.process.wait()