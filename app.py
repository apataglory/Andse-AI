# --- 1. CRITICAL: GEVENT MONKEY PATCH (MUST BE LINE 1) ---
try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    pass

import os
import sys
import logging
from flask import Flask, render_template, redirect, url_for, jsonify
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

# --- 2. SYSTEM PATH CONFIGURATION ---
# Ensures Python finds modules in the root directory
sys.path.append(os.getcwd())

# --- 3. IMPORT EXTENSIONS & MODELS ---
from extensions import db, socketio, mail
from database.models import User

# --- 4. THE MASSIVE FEATURE IMPORT ENGINE ---
# This logic attempts to load modules from root OR subfolders to prevent crashes
def safe_import(module_name, blueprint_name=None):
    try:
        # Try direct import (e.g. 'import chat_manager')
        mod = __import__(module_name, fromlist=[blueprint_name] if blueprint_name else [])
        return getattr(mod, blueprint_name) if blueprint_name else mod
    except ImportError:
        try:
            # Try package import (e.g. 'import chat.chat_manager')
            # This handles cases where files are moved into folders
            if module_name == 'chat_manager':
                from chat import chat_manager as mod
            elif module_name == 'webscraper':
                from webscraper import web_searcher # Special case for class instance
                return None # The scraper isn't a blueprint, it's a tool
            else:
                return None
            return getattr(mod, blueprint_name) if blueprint_name else mod
        except ImportError as e:
            print(f"⚠️ Warning: Feature '{module_name}' could not be loaded: {e}")
            return None

# Import Blueprints
from auth import auth_bp, configure_oauth
chat_bp = safe_import('chat_manager', 'chat_bp')
settings_bp = safe_import('settings', 'settings_bp')
video_bp = safe_import('video_editor', 'video_bp')
image_bp = safe_import('image_generator', 'image_bp')
file_bp = safe_import('file_handler', 'file_bp')

# Special handling for Scraper (It might be a blueprint or just a class)
try:
    from webscraper import scraper_bp
except ImportError:
    scraper_bp = None

# --- 5. ENVIRONMENT CONFIG ---
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("ANDSE_CORE")

def create_app():
    app = Flask(__name__)
    
    # ==========================================
    # 6. HYPER-CONFIGURATION
    # ==========================================
    db_url = os.getenv('DATABASE_URL', 'sqlite:///andse_neural.db')
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'neural-link-omega-99'),
        SQLALCHEMY_DATABASE_URI=db_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        UPLOAD_FOLDER=os.path.join(app.root_path, 'static', 'uploads'),
        IMAGE_GEN_FOLDER=os.path.join(app.root_path, 'static', 'generated_images'),
        AUDIO_CACHE=os.path.join(app.root_path, 'static', 'audio_cache'),
        VIDEO_CACHE=os.path.join(app.root_path, 'static', 'video_cache'),
        MAX_CONTENT_LENGTH=1024 * 1024 * 1024, # 1GB
        GOOGLE_CLIENT_ID=os.getenv('GOOGLE_CLIENT_ID'),
        GOOGLE_CLIENT_SECRET=os.getenv('GOOGLE_CLIENT_SECRET'),
        GEMINI_API_KEY=os.getenv('GEMINI_API_KEY'),
        GROQ_API_KEY=os.getenv('GROQ_API_KEY'),
        MAIL_SERVER='smtp.gmail.com',
        MAIL_PORT=465,
        MAIL_USE_SSL=True,
        MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
        MAIL_PASSWORD=os.getenv('MAIL_PASSWORD')
    )

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # ==========================================
    # 7. AUTOMATIC DIRECTORY PROVISIONING
    # ==========================================
    directories = [
        app.config['UPLOAD_FOLDER'],
        app.config['IMAGE_GEN_FOLDER'],
        app.config['AUDIO_CACHE'],
        app.config['VIDEO_CACHE'],
        os.path.join(app.config['UPLOAD_FOLDER'], 'docs'),
        os.path.join(app.config['UPLOAD_FOLDER'], 'temp')
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)

    # ==========================================
    # 8. EXTENSION ACTIVATION
    # ==========================================
    CORS(app)
    db.init_app(app)
    # Database Migration Engine (Added as requested)
    migrate = Migrate(app, db)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='gevent')

    # ==========================================
    # 9. LOGIN & SECURITY
    # ==========================================
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # ==========================================
    # 10. REGISTER ALL BLUEPRINTS
    # ==========================================
    configure_oauth(app)
    
    blueprints = [
        (auth_bp, '/auth'),
        (chat_bp, '/chat'),
        (settings_bp, '/settings'),
        (video_bp, '/video'),
        (image_bp, '/generate'),
        (file_bp, '/files'),
        (scraper_bp, '/scrape')
    ]

    for bp, prefix in blueprints:
        if bp:
            app.register_blueprint(bp, url_prefix=prefix)
            logger.info(f"✅ Feature Active: {prefix}")
        elif prefix == '/auth':
            raise RuntimeError("CRITICAL ERROR: Auth blueprint is mandatory!")

    # ==========================================
    # 11. GLOBAL CORE ROUTES
    # ==========================================
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('chat.interface'))
        return render_template('login.html')

    @app.route('/system/status')
    def status():
        return jsonify({
            "status": "online",
            "modules": {
                "vision": bool(image_bp),
                "video": bool(video_bp),
                "scraper": bool(scraper_bp)
            }
        })

    return app

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"DB Init Note: {e}")
    
    # Safe Port Handling (Defaults to 5000 if PORT not set locally)
    port = int(os.environ["PORT"])
    socketio.run(app, host="0.0.0.0", port=port, debug=True)