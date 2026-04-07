import os
import requests
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify

logger = logging.getLogger(__name__)

# 1. Define the Blueprint that app.py is looking for
image_bp = Blueprint('image_generator', __name__)

class ImageGenerator:
    """
    The Visual Synthesis Engine.
    Interfaces with external DALL-E or Stability APIs.
    """
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.output_dir = "static/uploads/images/output"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate(self, prompt):
        """
        Generates a high-fidelity image based on text description.
        """
        if not self.api_key:
            logger.error("Visual Synthesis API key missing.")
            return None

        try:
            logger.info(f"Generating image for prompt: {prompt[:50]}...")
            
            response = requests.post(
                "https://api.openai.com/v1/images/generations",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": "dall-e-3",
                    "prompt": f"Ultra-realistic, high detail: {prompt}",
                    "n": 1,
                    "size": "1024x1024"
                },
                timeout=60
            )
            response.raise_for_status()
            
            data = response.json()
            image_url = data['data'][0]['url']
            
            # Download and save locally
            img_response = requests.get(image_url)
            filename = f"gen_{int(datetime.now().timestamp())}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(img_response.content)
            
            # Return the URL relative to the web server
            return f"/static/uploads/images/output/{filename}"

        except Exception as e:
            logger.error(f"Visual Synthesis Failure: {e}")
            return None

# 2. Instantiate the generator logic
image_gen = ImageGenerator()

# 3. Add routes to the blueprint so app.py can register them
@image_bp.route('/api/image/generate', methods=['POST'])
def handle_image_request():
    data = request.json
    prompt = data.get('prompt')
    if not prompt:
        return jsonify({"error": "No prompt provided"}), 400
    
    result_url = image_gen.generate(prompt)
    if result_url:
        return jsonify({"url": result_url}), 200
    else:
        return jsonify({"error": "Generation failed"}), 500

@image_bp.route('/api/image/status', methods=['GET'])
def image_status():
    return jsonify({"status": "active", "model": "dall-e-3"})