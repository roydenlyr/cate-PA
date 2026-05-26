import os
import subprocess

from config import STATION_ID, PEERS
from sender import AudioSender


class Router:
    def __init__(self):
        self.sender = AudioSender()

    def _parse_target(self, filepath):
        """Extract target prefix from filename. E.g. 'S1_announcement.wav' -> 'S1'"""
        filename = os.path.basename(filepath)
        parts = filename.split('_', 1)
        if len(parts) < 2:
            print(f"Invalid filename format: {filename}. Expected <target>_<name>.wav")
            return None
        return parts[0].upper()

    def _play_local(self, filepath):
        """Play WAV file through 3.5mm jack using aplay."""
        try:
            subprocess.run(['aplay', filepath], check=True)
        except Exception as e:
            print(f"Local playback error: {e}")

    def _send_to_station(self, station_id, filepath):
        """Send WAV file to a specific station."""
        if station_id not in PEERS:
            print(f"Unknown station: {station_id}")
            return
        self.sender.send_file(PEERS[station_id], filepath)

    def handle_file(self, filepath):
        """Main routing logic. Called by FileWatcher when a new file appears."""
        target = self._parse_target(filepath)
        if target is None:
            return

        print(f"Routing {os.path.basename(filepath)} -> target: {target}")

        if target == 'LOCAL':
            # Play on own station only
            self._play_local(filepath)

        elif target == 'ALL':
            # Play locally and send to all other stations
            self._play_local(filepath)
            for station_id in PEERS:
                if station_id != STATION_ID:
                    self._send_to_station(station_id, filepath)

        elif target == STATION_ID:
            # Addressed to own station, play locally
            self._play_local(filepath)

        elif target in PEERS:
            # Addressed to another station, send to it
            self._send_to_station(target, filepath)

        else:
            print(f"Unknown target: {target}")
