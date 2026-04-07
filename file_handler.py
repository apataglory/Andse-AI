import os
import uuid
import logging
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 1. Define the Blueprint that app.py is looking for
file_bp = Blueprint('file_handler', __name__)

class FileHandler:
    """
    Secure File Management System.
    Handles uploads, validation, and storage routing.
    """
    
    def __init__(self):
        # Whitelisted extensions for security
        self.ALLOWED_EXTENSIONS = {
            'images': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
            'documents': {'pdf', 'docx', 'txt', 'pptx', 'md', 'csv'},
            'audio': {'mp3', 'wav', 'ogg', 'm4a', 'webm'},
            'video': {'mp4', 'mov', 'avi'}
        }

    def _get_extension(self, filename):
        """Extracts and normalizes the file extension."""
        return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    def _is_allowed(self, filename):
        """Checks if the file type is permitted."""
        ext = self._get_extension(filename)
        for category, extensions in self.ALLOWED_EXTENSIONS.items():
            if ext in extensions:
                return True, category
        return False, None

    def save_file(self, file_object):
        """
        Saves an uploaded file securely.
        """
        if not file_object or file_object.filename == '':
            return {'success': False, 'error': "No file selected"}

        # 1. Validate Extension
        allowed, category = self._is_allowed(file_object.filename)
        if not allowed:
            return {'success': False, 'error': f"File type not allowed."}

        # 2. Secure Filename & UUID Generation
        original_name = secure_filename(file_object.filename)
        ext = self._get_extension(original_name)
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        
        # 3. Determine Storage Path
        # Fallback to 'uploads' if UPLOAD_FOLDER isn't in config yet
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        target_dir = os.path.join(upload_folder, category) 
        
        if not os.path.exists(target_dir):
            os.makedirs(target_dir, exist_ok=True)

        # 4. Save File
        full_path = os.path.join(target_dir, unique_filename)
        try:
            file_object.save(full_path)
            logger.info(f"File saved: {unique_filename} ({category})")
            
            return {
                'success': True,
                'filepath': full_path,
                'filename': unique_filename,
                'type': category,
                'original_name': original_name,
                'url_path': f"/static/uploads/{category}/{unique_filename}"
            }
            
        except Exception as e:
            logger.error(f"File save failed: {e}")
            return {'success': False, 'error': str(e)}

    def get_file_content(self, filepath):
        """Reads text content from basic text files."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

# 2. Global Instance
file_handler = FileHandler()

# 3. Define routes for the Blueprint
@file_bp.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"success": False, "error": "No file part"}), 400
    
    file = request.files['file']
    result = file_handler.save_file(file)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@file_bp.route('/api/files/types', methods=['GET'])
def get_types():
    return jsonify(file_handler.ALLOWED_EXTENSIONS)