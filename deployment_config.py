import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base Configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-ultra-massive-999'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload Paths
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 500MB limit

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or \
        'sqlite:///' + os.path.join(basedir, 'database', 'instance', 'andse_core.db')

    # API Keys
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY')

class ProductionConfig(Config):
    """Fortress Mode."""
    DEBUG = False
    TESTING = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    # In production, use a robust DB like PostgreSQL
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') 

class DevelopmentConfig(Config):
    """Hacker Mode."""
    DEBUG = True
    TESTING = True
    SESSION_COOKIE_SECURE = False
    
def get_config():
    env = os.environ.get('FLASK_ENV', 'production')
    if env == 'development':
        return DevelopmentConfig
    return ProductionConfig