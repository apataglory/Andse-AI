from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from database.models import UserSettings

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/')
@login_required
def index():
    # Ensure settings exist
    settings = UserSettings.query.filter_by(user_id=current_user.id).first()
    if not settings:
        settings = UserSettings(user_id=current_user.id)
        db.session.add(settings)
        db.session.commit()

    # List of Neural Voices for dropdown
    voices = [
        {"id": "en-US-ChristopherNeural", "name": "Male (US - Christopher)"},
        {"id": "en-US-JennyNeural", "name": "Female (US - Jenny)"},
        {"id": "en-GB-SoniaNeural", "name": "Female (UK - Sonia)"},
        {"id": "en-AU-WilliamNeural", "name": "Male (Australian - William)"},
        {"id": "en-NG-EzinneNeural", "name": "Female (Nigerian - Ezinne)"}
    ]
    
    return render_template('settings.html', 
                         settings=settings, 
                         voices=voices,
                         current_theme=settings.theme if settings else 'dark')

@settings_bp.route('/update', methods=['POST'])
@login_required
def update():
    try:
        theme = request.form.get('theme')
        system_prompt = request.form.get('system_prompt')
        tts_voice = request.form.get('tts_voice')

        settings = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not settings:
            settings = UserSettings(user_id=current_user.id)
            db.session.add(settings)

        settings.theme = theme
        settings.system_prompt = system_prompt
        if hasattr(settings, 'tts_voice'): # Check if model has this column
            settings.tts_voice = tts_voice
        
        db.session.commit()
        flash("Neural preferences synchronized successfully.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Update failed: {e}", "error")
        
    return redirect(url_for('settings.index'))
