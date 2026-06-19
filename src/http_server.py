import os
import tempfile
from flask import Flask, request, jsonify

from config import STATION_ID, STATIONS
from wav_parser import is_valid_wav


class HTTPServer:
    """HTTP API layer. Validates requests and delegates to the router."""

    def __init__(self, router, playback_state):
        self.app = Flask(__name__)
        self.router = router
        self.playback_state = playback_state
        self._register_routes()

    def _register_routes(self):
        self.app.add_url_rule('/status', view_func=self._status, methods=['GET'])
        self.app.add_url_rule('/stations', view_func=self._list_stations, methods=['GET'])
        self.app.add_url_rule('/send', view_func=self._send, methods=['POST'])

    def _status(self):
        return jsonify({
            'station': STATION_ID,
            'playing': self.playback_state.is_playing
        })

    def _list_stations(self):
        return jsonify({
            'stations': list(STATIONS.keys()),
            'self': STATION_ID
        })

    def _send(self):
        target, error = self._validate_target()
        if error:
            return error

        temp_path, error = self._save_and_validate_audio()
        if error:
            return error

        results = self.router.handle_request(temp_path, target)
        self._cleanup(temp_path)
        return jsonify(results)

    def _validate_target(self):
        """Extract and validate the target field."""
        target = request.form.get('target', '').upper()
        if not target:
            return None, (jsonify({'status': 'error', 'message': 'Missing target'}), 400)
        return target, None

    def _save_and_validate_audio(self):
        """Save uploaded audio to temp file and validate WAV header."""
        audio = request.files.get('audio')
        if not audio:
            return None, (jsonify({'status': 'error', 'message': 'Missing audio file'}), 400)

        temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
        os.close(temp_fd)
        audio.save(temp_path)

        with open(temp_path, 'rb') as f:
            if not is_valid_wav(f.read(44)):
                os.remove(temp_path)
                return None, (jsonify({'status': 'error', 'message': 'Invalid WAV file'}), 400)

        return temp_path, None

    def _cleanup(self, temp_path):
        """Remove temp file, ignoring errors."""
        try:
            os.remove(temp_path)
        except OSError:
            pass

    def start(self, host, port):
        self.app.run(host=host, port=port, threaded=True)