import os
import logging
from flask import Blueprint, request, jsonify

# MOVIEPY 2.0 COMPATIBLE IMPORTS
from moviepy import VideoFileClip, ImageClip, concatenate_videoclips, AudioFileClip
from moviepy.video.fx import Resize, FadeIn, FadeOut

logger = logging.getLogger(__name__)

# 1. Define the Blueprint that app.py expects
video_bp = Blueprint('video_editor', __name__)

class VideoEditor:
    def __init__(self):
        self.output_dir = "static/uploads/videos"
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)

    def generate_ai_video(self, image_list, audio_path, output_filename="generated_clip.mp4"):
        """
        Creates a video from a list of images + audio track using MoviePy 2.0.
        """
        try:
            logger.info(f"Synthesizing video: {output_filename}")
            
            if not image_list or not os.path.exists(audio_path):
                raise ValueError("Missing images or audio source.")

            audio_clip = AudioFileClip(audio_path)
            duration_per_image = audio_clip.duration / len(image_list)
            
            clips = []
            for img_path in image_list:
                if os.path.exists(img_path):
                    # MoviePy 2.0 Method Chaining
                    clip = (ImageClip(img_path)
                            .with_duration(duration_per_image)
                            .with_effects([Resize(height=1080), FadeIn(0.5)]))
                    clips.append(clip)
            
            if not clips:
                raise ValueError("No valid images processed.")

            final_video = concatenate_videoclips(clips, method="compose")
            final_video = final_video.with_audio(audio_clip)
            
            target_path = os.path.join(self.output_dir, output_filename)
            
            # Render settings optimized for web
            final_video.write_videofile(
                target_path, 
                fps=24, 
                codec="libx264", 
                audio_codec="aac",
                threads=4,
                logger=None
            )
            
            return target_path
            
        except Exception as e:
            logger.error(f"Video Rendering Critical Failure: {e}")
            return None

# 2. Instantiate the editor logic
video_editor = VideoEditor()

# 3. Add routes to the blueprint so the web app can actually use the logic
@video_bp.route('/api/video/status', methods=['GET'])
def video_status():
    return jsonify({
        "status": "ready",
        "engine": "MoviePy 2.0",
        "output_directory": video_editor.output_dir
    })

# Example route to trigger processing (you can customize this)
@video_bp.route('/api/video/generate', methods=['POST'])
def handle_generate():
    data = request.json
    # Logic to call video_editor.generate_ai_video(...) would go here
    return jsonify({"message": "Endpoint reached"}), 200