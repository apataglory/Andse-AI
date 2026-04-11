import os
import json
import traceback
import logging
from datetime import datetime

from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required, current_user

# --- SYSTEM IMPORTS ---
from extensions import db, socketio
from database.models import ChatSession, Message, UserSettings

# --- NEURAL ENGINES ---
try:
    from ai_engine import engine as ai_engine
except ImportError:
    try:
        from ai_engine import NeuralEngine
        ai_engine = NeuralEngine()
    except ImportError:
        ai_engine = None
        logging.error("❌ CRITICAL: AI Engine module not found.")

# --- TOOL MODULES WITH SAFETY GUARDS ---
# We wrap these in try-except to prevent the entire server from crashing 
# if a specific dependency (like edge_tts) is missing.

try:
    from webscraper import web_searcher
except ImportError:
    web_searcher = None
    logging.warning("⚠️ WebScraper not available.")

try:
    from TTS import voice_engine
    TTS_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    voice_engine = None
    TTS_AVAILABLE = False
    logging.warning(f"⚠️ TTS Module failed to load: {e}")

try:
    from STT import speech_processor
    STT_AVAILABLE = True
except (ImportError, ModuleNotFoundError) as e:
    speech_processor = None
    STT_AVAILABLE = False
    logging.warning(f"⚠️ STT Module failed to load: {e}")

try:
    from video_editor import video_editor
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False

# Configure Logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

chat_bp = Blueprint('chat', __name__)

# ==========================================
# 1. INTERFACE ROUTE
# ==========================================
@chat_bp.route('/')
@login_required
def interface():
    """
    Renders the Neural Terminal.
    Loads session history and user-specific visual themes.
    """
    try:
        # Fetch sessions ordered by last update
        sessions = ChatSession.query.filter_by(user_id=current_user.id)\
            .order_by(ChatSession.updated_at.desc())\
            .limit(50).all()
        
        # Fetch or Create Settings
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.session.add(settings)
            db.session.commit()

        return render_template('chat.html', 
                               sessions=sessions, 
                               settings=settings,
                               current_theme=settings.theme,
                               stt_enabled=STT_AVAILABLE,
                               tts_enabled=TTS_AVAILABLE)
    except Exception as e:
        logger.error(f"Interface Load Error: {e}")
        return "Internal System Error", 500

# ==========================================
# 2. VOICE & MEDIA HANDLERS
# ==========================================

@chat_bp.route('/transcribe', methods=['POST'])
@login_required
def transcribe():
    """Receives audio blob, saves temp file, runs STT, returns text."""
    if not STT_AVAILABLE:
        return jsonify({'error': 'Speech-to-Text module is currently offline'}), 503

    if 'file' not in request.files:
        return jsonify({'error': 'No audio file received'}), 400
    
    file = request.files['file']
    # Save to a temp location
    upload_path = os.path.join(current_app.static_folder, 'uploads', f'speech_{current_user.id}.webm')
    os.makedirs(os.path.dirname(upload_path), exist_ok=True)
    file.save(upload_path)
    
    try:
        text = speech_processor.transcribe_audio(upload_path)
        return jsonify({'text': text})
    except Exception as e:
        logger.error(f"STT Error: {e}")
        return jsonify({'error': 'Transcription failed'}), 500

@chat_bp.route('/session/<int:id>/history')
@login_required
def get_history(id):
    session = db.session.get(ChatSession, id)
    if not session or session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    messages = Message.query.filter_by(session_id=id).order_by(Message.timestamp.asc()).all()
    history = [{'role': m.role, 'content': m.content} for m in messages]
    return jsonify({'history': history, 'title': session.title})

@chat_bp.route('/session/<int:id>/delete', methods=['POST', 'DELETE'])
@login_required
def delete_session(id):
    session = db.session.get(ChatSession, id)
    if not session or session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        db.session.delete(session)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
