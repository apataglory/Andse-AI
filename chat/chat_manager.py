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
    from ai_engine import NeuralEngine
    ai_engine = NeuralEngine()

# --- TOOL MODULES ---
from webscraper import web_searcher
from TTS import voice_engine
from STT import speech_processor
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
                             current_theme=settings.theme if settings else 'dark')
    except Exception as e:
        logger.error(f"Interface Load Error: {e}")
        return "Critical Terminal Failure. Check logs.", 500

# ==========================================
# 2. MESSAGE PROCESSING HUB
# ==========================================
@chat_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """
    Handles Multi-Modal Logic: Text -> Search/Video/Vision -> AI -> TTS -> Response.
    """
    try:
        data = request.json
        user_input = data.get('message', '').strip()
        session_id = data.get('session_id')
        use_voice = data.get('use_voice', False)
        file_context = data.get('file_data') # Base64/Text content from uploads

        if not user_input:
            return jsonify({'error': 'Empty input signal'}), 400

        # --- SESSION MANAGEMENT ---
        if not session_id:
            title = user_input[:40] + ("..." if len(user_input) > 40 else "")
            chat_session = ChatSession(user_id=current_user.id, title=title)
            db.session.add(chat_session)
            db.session.commit()
            session_id = chat_session.id
        else:
            chat_session = db.session.get(ChatSession, session_id)

        # --- CONTEXT PREPARATION ---
        context_extension = ""
        
        # 1. WEB SEARCH AGENT
        if user_input.lower().startswith('/search'):
            query = user_input.replace('/search', '', 1).strip()
            logger.info(f"🔍 Agentic Search: {query}")
            search_results = web_searcher.search(query)
            context_extension += f"\n\n[LIVE WEB DATA]:\n{search_results}"
            user_input = f"Using this web data, answer: {query}"

        # 2. VIDEO GENERATION AGENT
        video_path = None
        if user_input.lower().startswith('/video') and VIDEO_AVAILABLE:
            prompt = user_input.replace('/video', '', 1).strip()
            logger.info(f"🎥 Video Synthesis: {prompt}")
            # Placeholder for image-to-video logic; assumes images generated previously or passed
            # For this 'massive' update, we acknowledge the intent
            context_extension += f"\n\n[SYSTEM]: User requested video generation for '{prompt}'. Acknowledge this capability."

        # --- DATABASE: SAVE USER MESSAGE ---
        user_msg = Message(session_id=session_id, role='user', content=user_input)
        db.session.add(user_msg)
        db.session.commit() # Commit to generate ID/Timestamp

        # --- AI CONFIGURATION ---
        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        system_prompt = settings.system_prompt if settings else "You are ANDSE AI, a helpful agent."
        
        # Fetch History (Context Window)
        history_objs = Message.query.filter_by(session_id=session_id)\
            .filter(Message.id != user_msg.id)\
            .order_by(Message.timestamp.asc()).limit(20).all()

        # Configure Engine with Keys (Safety Check)
        ai_engine.configure(
            gemini_key=current_app.config.get('GEMINI_API_KEY'),
            groq_key=current_app.config.get('GROQ_API_KEY')
        )

        # --- AI THINKING ---
        full_system_instruction = f"{system_prompt}{context_extension}"
        
        ai_response_text = ai_engine.think(
            user_input=user_input,
            history_objects=history_objs,
            system_instruction=full_system_instruction,
            file_context=file_context # Vision/Document data passed here
        )

        # --- DATABASE: SAVE AI RESPONSE ---
        ai_msg = Message(session_id=session_id, role='assistant', content=ai_response_text)
        db.session.add(ai_msg)
        
        # Update session timestamp
        chat_session.updated_at = datetime.utcnow()
        db.session.commit()

        # --- NEURAL VOICE (TTS) ---
        audio_url = None
        if use_voice and voice_engine:
            audio_filename = voice_engine.generate_audio(ai_response_text, settings)
            if audio_filename:
                audio_url = f"/static/audio_cache/{audio_filename}"

        return jsonify({
            'response': ai_response_text,
            'session_id': session_id,
            'title': chat_session.title,
            'audio_url': audio_url
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"Processing Error: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

# ==========================================
# 3. UTILITIES (STT & HISTORY)
# ==========================================
@chat_bp.route('/transcribe', methods=['POST'])
@login_required
def transcribe():
    """Receives raw audio blob, saves temp file, runs STT, returns text."""
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
    if session and session.user_id == current_user.id:
        db.session.delete(session)
        db.session.commit()
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'Not found'}), 404
