import os
import random
import string
import logging
import traceback
from datetime import datetime
from threading import Thread

from flask import (
    Blueprint, 
    render_template, 
    request, 
    redirect, 
    url_for, 
    flash, 
    session, 
    current_app, 
    send_from_directory,
    jsonify
)
from flask_login import (
    login_user, 
    logout_user, 
    login_required, 
    current_user
)
from werkzeug.security import generate_password_hash
from flask_mail import Message

# Internal Module Imports
from extensions import db, mail
from database.models import User, UserSettings
from authlib.integrations.flask_client import OAuth

# ==========================================
# AUTH CONFIGURATION & CORE INITIALIZATION
# ==========================================

auth_bp = Blueprint('auth', __name__)
oauth = OAuth()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def configure_oauth(app):
    """
    Initializes OAuth registry with Google as the primary provider.
    Ensures secure communication via OpenID Connect.
    """
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config.get('GOOGLE_CLIENT_ID'),
        client_secret=app.config.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
    logger.info("🔐 OAuth Configuration Initialized: Google provider active.")

# ==========================================
# SYSTEM ASSETS & UTILITIES
# ==========================================

@auth_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'favicon.ico', 
        mimetype='image/vnd.microsoft.icon'
    )

def send_async_email(app, msg, user_email, code):
    """Background task to send email so it doesn't freeze the UI."""
    with app.app_context():
        try:
            mail.send(msg)
            logger.info(f"✅ Security Code Successfully Delivered to {user_email}")
        except Exception as e:
            logger.error(f"❌ CRITICAL EMAIL FAILURE: {str(e)}")
            # Fallback: Print to Render console so you can still log in!
            print(f"\n==========================================")
            print(f" FALLBACK LOG: CODE FOR {user_email} IS [{code}]")
            print(f"==========================================\n")

def send_verification_email(user_email, code):
    """
    Builds the email message and spawns a background thread to send it.
    """
    logger.info(f"📧 Dispatching security protocol to: {user_email}")
    
    msg = Message(
        subject="🔐 Your ANDSE Security Code",
        sender=current_app.config.get('MAIL_USERNAME'),
        recipients=[user_email]
    )
    
    msg.html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 40px; background: #030303; color: white; text-align: center;">
        <div style="max-width: 550px; margin: 0 auto; background: #0f172a; padding: 50px; border-radius: 24px; border: 1px solid #1e293b; box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);">
            <h1 style="color: #38bdf8; font-size: 28px; margin-bottom: 5px; letter-spacing: -1px;">ANDSE AI</h1>
            <p style="color: #94a3b8; font-size: 14px; margin-bottom: 30px; text-transform: uppercase; letter-spacing: 2px;">Neural Identity Verification</p>
            
            <div style="padding: 20px; border: 1px dashed #334155; border-radius: 12px; background: #020617; margin: 30px 0;">
                <p style="color: #64748b; font-size: 12px; margin-bottom: 10px;">YOUR ACCESS CODE:</p>
                <span style="color: #0ea5e9; font-size: 42px; font-weight: 800; letter-spacing: 12px; font-family: monospace;">{code}</span>
            </div>
            
            <p style="color: #475569; font-size: 12px; line-height: 1.6;">
                If you did not request this code, your neural link might be compromised. 
                Please ignore this message or contact security.
            </p>
            <div style="margin-top: 40px; border-top: 1px solid #1e293b; padding-top: 20px;">
                <small style="color: #334155;">© 2026 ANDSE AI | Protocol: Secure-L3</small>
            </div>
        </div>
    </div>
    """
    
    # Grab the true Flask app instance
    app = current_app._get_current_object()
    # Start the email process in the background
    Thread(target=send_async_email, args=(app, msg, user_email, code)).start()
    return True

# ==========================================
# OAUTH / GOOGLE FLOW
# ==========================================

@auth_bp.route('/login/google')
def google_login():
    scheme = 'https' if os.environ.get('RENDER') or request.headers.get('X-Forwarded-Proto') == 'https' else 'http'
    redirect_uri = url_for('auth.google_callback', _external=True, _scheme=scheme)
    return oauth.google.authorize_redirect(redirect_uri, prompt='consent')

@auth_bp.route('/login/google/callback')
def google_callback():
    try:
        token = oauth.google.authorize_access_token()
        user_info = oauth.google.userinfo()
        email = user_info['email']
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.info(f"🆕 Provisioning new Google User: {email}")
            secure_pwd_stub = generate_password_hash(f"OAUTH_SECURE_{random.getrandbits(256)}")
            user = User(email=email, password_hash=secure_pwd_stub, is_verified=True)
            db.session.add(user)
            db.session.commit()
            
            db.session.add(UserSettings(user_id=user.id))
            db.session.commit()
            
        login_user(user)
        logger.info(f"✅ User {email} authenticated via Google OAuth.")
        return redirect(url_for('chat.interface'))
        
    except Exception as e:
        logger.error(f"❌ Google Login Error: {traceback.format_exc()}")
        flash(f"Neural verification failed: {str(e)}", "error")
        return redirect(url_for('auth.login'))

# ==========================================
# STANDARD AUTHENTICATION FLOW (PASSWORDLESS)
# ==========================================

@auth_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('chat.interface'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        
        if not email:
            flash("Email field is mandatory.")
            return redirect(url_for('auth.signup'))

        if User.query.filter_by(email=email).first():
            flash('Identity already exists. Access Terminal instead.')
            return redirect(url_for('auth.login'))
        
        verification_code = ''.join(random.choices(string.digits, k=6))
        secure_pwd_stub = generate_password_hash(f"PWDLESS_{random.getrandbits(256)}")
        
        new_user = User(
            email=email, 
            password_hash=secure_pwd_stub, 
            is_verified=False, 
            verification_code=verification_code
        )
        
        try:
            db.session.add(new_user)
            db.session.commit()
            
            db.session.add(UserSettings(user_id=new_user.id))
            db.session.commit()
            
            send_verification_email(email, verification_code)
            
            session['pending_email'] = email
            logger.info(f"📝 User Created: {email}. Verification pending.")
            return redirect(url_for('auth.verify_page'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"🔥 Database Critical: {str(e)}")
            flash("System error during initialization. Try again.")
            
    return render_template('signup.html')

@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify_page():
    if 'pending_email' not in session:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        submitted_code = request.form.get('code')
        email = session.get('pending_email')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.verification_code == submitted_code:
            user.is_verified = True
            user.verification_code = None
            
            if hasattr(user, 'last_login'):
                user.last_login = datetime.utcnow() 
                
            db.session.commit()
            
            login_user(user)
            session.pop('pending_email', None)
            logger.info(f"⚡ Identity Verified & Session Started: {email}")
            return redirect(url_for('chat.interface'))
        
        flash("❌ Invalid Verification Protocol. Access Denied.")
        
    return render_template('verify.html', email=session.get('pending_email'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('chat.interface'))
        
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        
        if user:
            session['pending_email'] = email
            new_otp = ''.join(random.choices(string.digits, k=6))
            user.verification_code = new_otp
            db.session.commit()
            
            send_verification_email(email, new_otp)
            flash("Verification code dispatched to your neural link.")
            return redirect(url_for('auth.verify_page'))
            
        logger.warning(f"🛡️ Unauthorized Access attempt: {email}")
        flash("❌ Identity not found. Please create a protocol.")
        
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    user_email = current_user.email
    logout_user()
    session.clear() 
    logger.info(f"🔒 Session Terminated: {user_email}")
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/status')
@login_required
def get_user_stats():
    return jsonify({
        "identity": current_user.email,
        "verified": current_user.is_verified,
        "session_active": True,
        "timestamp": datetime.utcnow().isoformat()
    })
