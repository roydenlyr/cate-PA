import threading

class PlaybackState:
    def __init__(self):
        self._lock = threading.Lock()
        self._playing = False

    def try_acquire(self):
        with self._lock:
            if self._playing:
                return False
            self._playing = True
            return True
    
    def release(self):
        with self._lock:
            self._playing = False

    @property
    def is_playing(self):
        return self._playing