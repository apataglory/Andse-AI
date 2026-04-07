import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """The Ultimate Configuration Blueprint for ANDSE AI."""
    # Core Security
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'ultra-massive-secure-fallback-key-999'
    
    # Database Setup
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'database', 'instance', 'andse_core.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # API Keys & Third-Party Integration
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')
    
    # Mail Engine (SMTP)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # File Management
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # Increased to 100MB for Video support
    
    # Sub-folders for Multimodal storage
    UPLOAD_SUBFOLDERS = ['images', 'audio', 'videos', 'docs']

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    OAUTHLIB_INSECURE_TRANSPORT = '0'

class DevelopmentConfig(Config):
    DEBUG = True
    OAUTHLIB_INSECURE_TRANSPORT = '1'