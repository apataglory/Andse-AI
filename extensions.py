from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_mail import Mail

db = SQLAlchemy()
login_manager = LoginManager()
socketio = SocketIO()
mail = Mail()  # <--- This is the new Real Email Engine