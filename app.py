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
def safe_import(module_name, blueprint_name=None):
    try:
        mod = __import__(module_name, fromlist=[blueprint_name] if blueprint_name else [])
        return getattr(mod, blueprint_name) if blueprint_name else mod
    except ImportError:
        try:
            if module_name == 'chat_manager':
                from chat.chat_manager import chat_bp
                return chat_bp
            if module_name == 'auth':
                from auth import auth_bp
                return auth_bp
            return None
        except ImportError:
            return None

# --- 5. LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def create_app():
    load_dotenv()
    app = Flask(__name__)

    # --- 6. CORE SECURITY & DATABASE CONFIG ---
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-key-12345")
    
    # Handle Database URL (PostgreSQL Support for Render/Neon)
    db_url = os.environ.get("DATABASE_URL", "sqlite:///andse_core.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # OAuth Config - FIXED: Pull from Environment variables
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get("GOOGLE_CLIENT_ID")
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get("GOOGLE_CLIENT_SECRET")

    # Mail Config
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get("EMAIL_USER")
    app.config['MAIL_PASSWORD'] = os.environ.get("EMAIL_PASS")
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get("EMAIL_USER")

    # --- 7. EXTENSION INITIALIZATION ---
    db.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='gevent')
    Migrate(app, db)
    CORS(app)
    
    # Essential for Render/Proxies
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # --- 8. AUTHENTICATION (FLASK-LOGIN) ---
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- 9. OAUTH CONFIGURATION ---
    from auth import configure_oauth
    configure_oauth(app)

    # --- 10. DYNAMIC BLUEPRINT REGISTRATION ---
    auth_bp = safe_import('auth', 'auth_bp')
    chat_bp = safe_import('chat_manager', 'chat_bp')
    settings_bp = safe_import('settings', 'settings_bp')
    video_bp = safe_import('video_gen', 'video_bp')
    image_bp = safe_import('image_gen', 'image_bp')
    file_bp = safe_import('file_manager', 'file_bp')
    scraper_bp = safe_import('scraper', 'scraper_bp')

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
            # Safely check if the chat module is active before redirecting
            if 'chat.interface' in [rule.endpoint for rule in app.url_map.iter_rules()]:
                return redirect(url_for('chat.interface'))
            else:
                return "<h1>System Active</h1><p>You are logged in, but the Chat Interface module is not connected yet.</p>"
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

    # CRITICAL PRODUCTION FIX: Create tables within the app context for Gunicorn/Render
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ Database tables verified/created in Neon PostgreSQL.")
        except Exception as e:
            logger.error(f"❌ Database creation error: {e}")

    # --- DIAGNOSTIC MODE: CATCH ALL ERRORS AND DISPLAY THEM ---
    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        error_trace = traceback.format_exc()
        return f"""
        <div style="background:#0f0f11; color:#fff; font-family:monospace; padding:40px; border-radius:10px; height: 100vh;">
            <h2 style="color:#ef4444;">🚨 Application Crash Detected 🚨</h2>
            <p style="color:#a1a1aa;">The server encountered an error. Please copy the green text below and show it to the AI:</p>
            <hr style="border-color:#27272a;">
            <pre style="color:#22c55e; overflow-x:auto; background:#000; padding: 20px;">{error_trace}</pre>
        </div>
        """, 500

    return app

# Initialize the application instance
app = create_app()

if __name__ == '__main__':
    # Local execution (ignored by Gunicorn on Render)
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
