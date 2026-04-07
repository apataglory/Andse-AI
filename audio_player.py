from flask import send_from_directory, Blueprint, current_app
from flask_login import login_required
import os

audio_bp = Blueprint('audio', __name__)

@audio_bp.route('/play/<filename>')
@login_required
def serve_audio(filename):
    """Securely serves generated speech files to the frontend."""
    audio_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'audio')
    return send_from_directory(audio_dir, filename)