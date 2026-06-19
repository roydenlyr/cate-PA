import os
import threading

from config import STATION_ID, STATIONS, REPEAT, DELAY
from sender import AudioSender
from audio_player import AudioPlayer

class Router:
    """Routes audio to local playback or remote stations."""

    def __init__(self, playback_state):
        self.sender = AudioSender()
        self.playback_state = playback_state
        self.player = AudioPlayer(repeat=REPEAT, delay=DELAY)

    def handle_request(self, filepath, target):
        print(f"Routing {os.path.basename(filepath)} -> {target}")

        if target == 'BROADCAST':
            return self._broadcast(filepath)
        elif target == STATION_ID:
            return self._play_local(filepath)
        elif target in STATIONS:
            return self._send_to_station(target, filepath)
        else:
            return {'status': 'error', 'message': f'Unknown target: {target}'}

    def _broadcast(self, filepath):
        results = {}
        results['local'] = self._play_local(filepath)
        self._broadcast_remote(results, filepath)
        return {'status': 'ok', 'message': 'Broadcast complete', 'details': results}

    def _broadcast_remote(self, results, filepath):
        threads = []
        for sid in STATIONS:
            if sid != STATION_ID:
                t = threading.Thread(target=lambda s=sid: self._collect_result(results, s, filepath))
                threads.append(t)
                t.start()
        for t in threads:
            t.join()

    def _collect_result(self, results, station_id, filepath):
        results[station_id] = self._send_to_station(station_id, filepath)

    def _play_local(self, filepath):
        """Check availability, start background playback, return immediately."""
        if not self.playback_state.try_acquire():
            return {'status': 'busy', 'message': f'{STATION_ID} is currently playing'}

        file_data = self._read_file(filepath)
        threading.Thread(target=self._play_and_release, args=(file_data,), daemon=True).start()
        return {'status': 'ok', 'message': f'{STATION_ID} accepted'}

    def _play_and_release(self, file_data):
        """Background playback. Lock already held, released when done."""
        try:
            self.player.play_data(file_data)
        except Exception as e:
            print(f"Local playback error: {e}")
        finally:
            self.playback_state.release()

    def _send_to_station(self, station_id, filepath):
        if station_id not in STATIONS:
            return {'status': 'error', 'message': f'Unknown station: {station_id}'}
        return self.sender.send_file(STATIONS[station_id], filepath)

    def _read_file(self, filepath):
        with open(filepath, 'rb') as f:
            return f.read()
