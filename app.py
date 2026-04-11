# --- 1. CRITICAL: GEVENT MONKEY PATCH (MUST BE LINE 1) ---
try:
    from gevent import monkey
    monkey.patch_all()
except ImportError:
    pass

import os
import sys
import logging
import importlib.util
from flask import Flask, render_template, redirect, url_for, jsonify
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

# --- 2. SYSTEM PATH CONFIGURATION ---
# We force the root and the chat folder into the system path
BASE_DIR = os.path.abspath(os.getcwd())
sys.path.append(BASE_DIR)
sys.path.append(os.path.join(BASE_DIR, 'chat'))

# --- 3. IMPORT EXTENSIONS & MODELS ---
from extensions import db, socketio, mail
from database.models import User

# --- 4. LOGGING CONFIGURATION ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

def create_app():
    load_dotenv()
    app = Flask(__name__)

    # --- 5. CORE SECURITY & DATABASE CONFIG ---
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev-key-12345")
    
    db_url = os.environ.get("DATABASE_URL", "sqlite:///andse_core.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # OAuth & Mail Config
    app.config['GOOGLE_CLIENT_ID'] = os.environ.get("GOOGLE_CLIENT_ID")
    app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get("GOOGLE_CLIENT_SECRET")
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.environ.get("MAIL_PASSWORD")

    # --- 6. EXTENSION INITIALIZATION ---
    db.init_app(app)
    mail.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='gevent')
    Migrate(app, db)
    CORS(app)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # --- 7. AUTHENTICATION ---
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # --- 8. MANUAL BLUEPRINT REGISTRATION ---
    # Register Auth
    try:
        from auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        logger.info("✅ Auth Blueprint Registered")
        from auth import configure_oauth
        configure_oauth(app)
    except Exception as e:
        logger.error(f"❌ Auth Load Error: {e}")

    # Register Chat (Manual File Discovery)
    chat_bp = None
    chat_path = os.path.join(BASE_DIR, 'chat', 'chat_manager.py')
    
    if os.path.exists(chat_path):
        try:
            # This "spec" method manually loads the file even if it's not a package
            spec = importlib.util.spec_from_file_location("chat_manager", chat_path)
            chat_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(chat_module)
            chat_bp = getattr(chat_module, 'chat_bp')
            app.register_blueprint(chat_bp, url_prefix='/chat')
            logger.info("🚀 SUCCESS: Chat Blueprint loaded manually from chat/chat_manager.py")
        except Exception as e:
            logger.error(f"❌ Manual Chat Load Failed: {e}")
    else:
        logger.error(f"❌ FILE NOT FOUND: Checked {chat_path}")

    # --- 9. GLOBAL CORE ROUTES ---
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            # Double check if the blueprint successfully registered
            if 'chat' in app.blueprints:
                return redirect(url_for('chat.interface'))
            else:
                return f"""
                <body style="background:#050505; color:#fff; font-family:sans-serif; display:flex; align-items:center; justify-content:center; height:100vh; text-align:center; padding: 20px;">
                    <div style="max-width: 500px; border: 1px solid #ef4444; padding: 40px; border-radius: 20px; background: #000;">
                        <h1 style="color:#ef4444; margin-bottom: 10px;">Diagnostic Mode</h1>
                        <p style="font-size: 1.1rem;">The server is alive, but the Chat Module failed to load.</p>
                        <hr style="border: 0; border-top: 1px solid #333; margin: 20px 0;">
                        <p style="color:#a1a1aa; text-align: left;"><b>Debug Info:</b></p>
                        <ul style="color:#666; font-size: 0.8rem; text-align: left;">
                            <li>Directory: {BASE_DIR}</li>
                            <li>Chat File Exists: {os.path.exists(chat_path)}</li>
                            <li>Path Searched: {chat_path}</li>
                        </ul>
                    </div>
                </body>
                """
        return render_template('login.html')

    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
