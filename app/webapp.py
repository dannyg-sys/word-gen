import os
from flask import Flask, request, jsonify
from .word_service import WordService

app = Flask(__name__, static_folder='../static')
word_service = None


def _read_version():
    """Read the application version from the VERSION file at the repo root."""
    version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'VERSION')
    try:
        with open(version_file, 'r') as f:
            return f.read().strip()
    except OSError:
        return 'unknown'


VERSION = _read_version()

@app.route('/', methods=['GET'])
def index():
    return app.send_static_file('index.html')

@app.route('/version', methods=['GET'])
def version():
    return jsonify({'version': VERSION})

def init_word_service(service):
    global word_service
    word_service = service

@app.route('/words', methods=['POST'])
def get_words():
    try:
        if not word_service:
            return jsonify({'error': 'Word service not initialized. Please restart the application.'}), 500

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        word_length = int(data.get('wordLength', 5))
        word_count = int(data.get('numberOfWords', 1))
        
        if word_length < 1:
            return jsonify({'error': 'Word length must be positive'}), 400
        if word_count < 1:
            return jsonify({'error': 'Number of words must be positive'}), 400

        words = word_service.get_random_words(word_length, word_count)
        if not words:
            return jsonify({'error': 'No words found matching criteria'}), 404

        return jsonify({
            'words': '-'.join(words) if words else 'No words found'
        })
    except Exception as e:
        print(f"Error processing request: {str(e)}")  # Add logging
        return jsonify({'error': str(e)}), 400 