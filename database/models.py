from extensions import db
from flask_login import UserMixin
from datetime import datetime
import uuid
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    """
    MASTER USER IDENTITY: 
    Supports Secure Password Auth, Google OAuth, and Multi-Factor Verification.
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    
    # Advanced Verification System
    is_verified = db.Column(db.Boolean, default=False)
    verification_code = db.Column(db.String(10), nullable=True) # Optimized for 6-digit codes
    account_status = db.Column(db.String(20), default='active') # active, suspended, maintenance
    
    # Neural Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships (Orphan removal ensures neural database remains clean and high-speed)
    settings = db.relationship('UserSettings', backref='user', uselist=False, cascade="all, delete-orphan")
    sessions = db.relationship('ChatSession', backref='user', lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class UserSettings(db.Model):
    """
    NEURAL PREFERENCES:
    Customizes the AI experience per individual user.
    """
    __tablename__ = 'user_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Interface Customization
    theme = db.Column(db.String(20), default='dark')
    accent_color = db.Column(db.String(20), default='#3b82f6')
    
    # AI Engine Logic
    preferred_model = db.Column(db.String(50), default='gemini-2.0-flash')
    system_prompt = db.Column(db.Text, default="You are ANDSE, a highly advanced AI.")
    
    # Master Toggle Suite
    voice_enabled = db.Column(db.Boolean, default=True)
    search_enabled = db.Column(db.Boolean, default=True)
    vision_enabled = db.Column(db.Boolean, default=True)

class ChatSession(db.Model):
    """
    CHRONOLOGICAL NEURAL LINKS:
    Organizes user interactions into discrete, retrievable, and searchable sessions.
    """
    __tablename__ = 'chat_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    # Unique Public Identifier for secure routing and session sharing
    session_uuid = db.Column(db.String(36), default=lambda: str(uuid.uuid4()), unique=True, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    title = db.Column(db.String(200), default='New Neural Link')
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to individual messages
    messages = db.relationship('Message', backref='session', lazy='dynamic', cascade="all, delete-orphan")

class Message(db.Model):
    """
    NEURAL DATAPOINTS:
    Individual exchanges between the User and the Neural Engine.
    """
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_sessions.id'), nullable=False)
    
    # Messaging Identities
    role = db.Column(db.String(20), nullable=False) # 'user', 'assistant', or 'system'
    content = db.Column(db.Text, nullable=False)
    
    # Technical Analytics & Token Tracking
    model_used = db.Column(db.String(50), nullable=True)
    tokens_count = db.Column(db.Integer, default=0)
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
