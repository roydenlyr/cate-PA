import pyaudio

class AudioPlayer:
    def __init__(self, channels, sample_rate, bits_per_sample):
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.p.get_format_from_width(bits_per_sample // 8),
                                  channels=channels,
                                  rate=sample_rate,
                                  output=True)

    def play(self, data):
        self.stream.write(data)
    
    def close(self):
        self.stream.stop_stream()
        self.stream.close()
        self.p.terminate()
