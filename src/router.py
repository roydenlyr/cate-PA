import os
import subprocess
import threading

from config import STATION_ID, STATIONS
from sender import AudioSender
from wav_parser import is_valid_wav


class Router:
    def __init__(self):
        self.sender = AudioSender()

    def _parse_target(self, filepath):
        """Extract target from filename. E.g. 'S1.wav' -> 'S1', 'Broadcast.wav' -> 'BROADCAST'"""
        filename = os.path.basename(filepath)
        target = os.path.splitext(filename)[0].upper()
        return target

    def _play_local(self, filepath):
        """Play WAV file through 3.5mm jack using aplay."""
        try:
            subprocess.run(['aplay', filepath], check=True)
        except Exception as e:
            print(f"Local playback error: {e}")

    def _send_to_station(self, station_id, filepath):
        """Send WAV file to a specific station."""
        if station_id not in STATIONS:
            print(f"Unknown station: {station_id}")
            return
        self.sender.send_file(STATIONS[station_id], filepath)

    def handle_file(self, filepath):
        """Main routing logic. Called by FileWatcher when a new file appears."""
        if not is_valid_wav(open(filepath, 'rb').read(44)):
            print(f"Invalid WAV file: {os.path.basename(filepath)}, skipping.")
            return

        target = self._parse_target(filepath)
        if target is None:
            return

        print(f"Routing {os.path.basename(filepath)} -> target: {target}")

        if target == 'BROADCAST':
            threads = []
            threads.append(threading.Thread(target=self._play_local, args=(filepath,)))
            for station_id in STATIONS:
                if station_id != STATION_ID:
                    threads.append(threading.Thread(target=self._send_to_station, args=(station_id, filepath)))
            
            for t in threads:
                t.start()
            for t in threads:
                t.join()

        elif target == STATION_ID:
            self._play_local(filepath)

        elif target in STATIONS:
            self._send_to_station(target, filepath)

        else:
            print(f"Unknown target: {target}")
