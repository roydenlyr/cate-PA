import os
import threading

from config import STATION_ID, STATIONS
from sender import AudioSender
from audio_player import AudioPlayer


class Router:
    """Routes audio to local playback or remote stations."""

    REPEAT = 2

    def __init__(self, playback_state):
        self.sender = AudioSender()
        self.playback_state = playback_state
        self.player = AudioPlayer(repeat=self.REPEAT)

    def handle_request(self, filepath, target):
        """Route audio to the correct destination."""
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
        """Send to all stations simultaneously. Returns immediately."""
        results = {}
        file_data = self._read_file(filepath)

        self._broadcast_local(results, file_data)
        self._broadcast_remote(results, filepath)

        return {'status': 'ok', 'message': 'Broadcast complete', 'details': results}

    def _broadcast_local(self, results, file_data):
        """Check local availability and start background playback."""
        if not self.playback_state.try_acquire():
            results['local'] = {'status': 'busy', 'message': f'{STATION_ID} is currently playing'}
            return

        results['local'] = {'status': 'ok', 'message': f'{STATION_ID} accepted'}
        threading.Thread(
            target=self._play_and_release,
            args=(file_data,),
            daemon=True
        ).start()

    def _broadcast_remote(self, results, filepath):
        """Connect to all remote stations in parallel. Returns when all have responded."""
        threads = []

        for sid in STATIONS:
            if sid != STATION_ID:
                t = threading.Thread(target=lambda s=sid: self._collect_result(results, s, filepath))
                threads.append(t)
                t.start()

        for t in threads:
            t.join()

    def _collect_result(self, results, station_id, filepath):
        """Send to a station and store the result."""
        results[station_id] = self._send_to_station(station_id, filepath)

    def _play_local(self, filepath):
        """Play audio locally (blocking)."""
        if not self.playback_state.try_acquire():
            return {'status': 'busy', 'message': f'{STATION_ID} is currently playing'}

        try:
            self.player.play_file(filepath)
            return {'status': 'ok', 'message': 'Local playback complete'}
        except Exception as e:
            return {'status': 'error', 'message': f'Local playback error: {e}'}
        finally:
            self.playback_state.release()

    def _play_and_release(self, file_data):
        """Background playback. Lock already held, released when done."""
        try:
            self.player.play_data(file_data)
        except Exception as e:
            print(f"Local playback error: {e}")
        finally:
            self.playback_state.release()

    def _send_to_station(self, station_id, filepath):
        """Send audio to a remote station."""
        if station_id not in STATIONS:
            return {'status': 'error', 'message': f'Unknown station: {station_id}'}
        return self.sender.send_file(STATIONS[station_id], filepath)

    def _read_file(self, filepath):
        with open(filepath, 'rb') as f:
            return f.read()