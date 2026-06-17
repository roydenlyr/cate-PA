import os
import tempfile
import threading
from flask import Flask, request, jsonify

from config import STATION_ID, STATIONS
from wav_parser import is_valid_wav


class HTTPServer:
    def __init__(self, router, playback_state):
        self.app = Flask(__name__)
        self.router = router
        self.playback_state = playback_state
        self._register_routes()

    def _register_routes(self):
        @self.app.route('/status', methods=['GET'])
        def status():
            return jsonify({
                'station': STATION_ID,
                'playing': self.playback_state.is_playing
            })
        
        @self.app.route('/send', methods=['POST'])
        def receive_audio():
            target = request.form.get('target', '').upper()
            if not target:
                return jsonify({'status': 'error', 'message': 'Missing target'}), 400

            audio = request.files.get('audio')
            if not audio:
                return jsonify({'status': 'error', 'message': 'Missing audio file'}), 400
            
            if self.playback_state.is_playing:
                return jsonify({'status': 'busy', 'message': f'{STATION_ID} is currently playing'})
            
            # Save to temp file
            temp_fd, temp_path = tempfile.mkstemp(suffix='.wav')
            os.close(temp_fd)
            audio.save(temp_path)

            # Validate WAV header
            with open(temp_path, 'rb') as f:
                if not is_valid_wav(f.read(44)):
                    os.remove(temp_path)
                    return jsonify({'status': 'error', 'message': 'Invalid WAV file'}), 400
                
            # Route the audio
            def background_task():
                self.router.handle_request(temp_path, target)
                try:
                    os.remove(temp_path)
                except OSError:
                    pass

            threading.Thread(target=background_task, daemon=True).start()
            return jsonify({'status': 'error', 'message': f'Routing to {target}'})
        
        @self.app.route('/stations', methods=['GET'])
        def list_stations():
            return jsonify({
                'stations': list(STATIONS.keys()),
                'self': STATION_ID
            })
        
    def start(self, host, port):
        self.app.run(host=host, port=port, threaded=True)