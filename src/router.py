import os
import subprocess
import threading

from config import STATION_ID, STATIONS
from sender import AudioSender
from wav_parser import is_valid_wav


class Router:
    def __init__(self, playback_state):
        self.sender = AudioSender()
        self.playback_state = playback_state

    def _play_local(self, filepath):
        """Play WAV file through 3.5mm jack using aplay."""
        if not self.playback_state.try_acquire():
            return {'status': 'busy', 'message': f'{STATION_ID} is currently playing'}

        try:
            subprocess.run(['aplay', filepath], check=True)
        except Exception as e:
            return {'status': 'error', 'message': f'Local playback error: {e}'}
        finally:
            self.playback_state.release()

    def _send_to_station(self, station_id, filepath):
        """Send WAV file to a specific station."""
        if station_id not in STATIONS:
            return {'status': 'error', 'message': f'Unknown station: {station_id}'}
        return self.sender.send_file(STATIONS[station_id], filepath)

    def handle_request(self, filepath, target):
        """Main routing logic. Called by FileWatcher when a new file appears."""
        print(f"Routing {os.path.basename(filepath)} -> target: {target}")

        if target == 'BROADCAST':
            threads = []
            results = {}

            def play_local():
                results['local'] = self._play_local(filepath)

            def send_to(sid):
                results[sid] = self._send_to_station(sid, filepath)

            threads.append(threading.Thread(target=play_local))
            for station_id in STATIONS:
                if station_id != STATION_ID:
                    threads.append(threading.Thread(target=send_to, args=(station_id,)))
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            return {'status': 'ok', 'message': 'Broadcast complete', 'details': results}

        elif target == STATION_ID:
            return self._play_local(filepath)

        elif target in STATIONS:
            return self._send_to_station(target, filepath)

        else:
            return {'status': 'error', 'message': f'Unknown target: {target}'}
