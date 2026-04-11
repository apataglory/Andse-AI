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
sys.path.append(os.getcwd())

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
    # We are manually importing these because we now know exactly where they are.
    try:
        from auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
        logger.info("✅ Auth Blueprint Registered")
        
        # Try to configure OAuth if it's available in auth.py
        try:
            from auth import configure_oauth
            configure_oauth(app)
        except Exception:
            logger.warning("⚠️ OAuth configuration skipped.")
            
    except ImportError as e:
        logger.error(f"❌ CRITICAL: Could not load Auth module: {e}")

    try:
        # LOOKING IN THE 'chat' FOLDER FOR 'chat_manager'
        from chat.chat_manager import chat_bp
        app.register_blueprint(chat_bp, url_prefix='/chat')
        logger.info("✅ Chat Blueprint Registered from chat/chat_manager.py")
    except ImportError as e:
        logger.error(f"⚠️ Chat module not found in chat/chat_manager.py: {e}")

    # ==========================================
    # 9. GLOBAL CORE ROUTES
    # ==========================================
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            # CHECK: If chat is connected, go there. Otherwise, show diagnostic.
            if 'chat.interface' in [rule.endpoint for rule in app.url_map.iter_rules()]:
                return redirect(url_for('chat.interface'))
            else:
                return """
                <body style="background:#050505; color:#fff; font-family:sans-serif; display:flex; align-items:center; justify-content:center; height:100vh; text-align:center; padding: 20px;">
                    <div style="max-width: 500px; border: 1px solid #22c55e; padding: 40px; border-radius: 20px; background: #000;">
                        <h1 style="color:#22c55e; margin-bottom: 10px;">✔ System Online</h1>
                        <p style="font-size: 1.1rem;">Your identity is verified and the server is running.</p>
                        <hr style="border: 0; border-top: 1px solid #333; margin: 20px 0;">
                        <p style="color:#a1a1aa;">The app is still looking for <b>chat/chat_manager.py</b>.</p>
                        <p style="color:#666; font-size: 0.9rem;">Make sure the file name is exactly lowercase and inside the 'chat' folder on GitHub.</p>
                    </div>
                </body>
                """
        return render_template('login.html')

    # Database creation
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    socketio.run(app, host="0.0.0.0", port=port, debug=True)
