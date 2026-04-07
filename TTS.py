import os
import asyncio
import edge_tts
from gtts import gTTS
import uuid
import logging
import re
import time
from flask import current_app

# Enterprise Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NEURAL_TTS")

class VoiceEngine:
    """
    ULTRA-MASSIVE NEURAL VOICE ENGINE
    A dual-tier synthesis system providing high-fidelity human-like speech.
    Supports Edge-TTS Neural and gTTS fallback with advanced text sanitization.
    """

    def __init__(self):
        # Universal Default Voice
        self.default_voice = "en-US-ChristopherNeural"
        
        # Audio Quality Constants
        self.RATE = "+0%"
        self.VOLUME = "+0%"
        self.PITCH = "+0Hz"

    async def _execute_synthesis(self, text, output_path, voice):
        """Internal asynchronous handler for Edge-TTS."""
        communicate = edge_tts.Communicate(
            text, 
            voice, 
            rate=self.RATE, 
            volume=self.VOLUME, 
            pitch=self.PITCH
        )
        await communicate.save(output_path)

    def generate_audio(self, text, user_settings=None):
        """
        Synthesizes high-fidelity audio from text.
        Returns the unique filename for the generated asset.
        """
        start_time = time.time()
        
        # 1. GENERATE UNIQUE ASSET IDENTITY
        asset_id = uuid.uuid4().hex[:12]
        filename = f"neural_voice_{asset_id}.mp3"
        
        # 2. FILESYSTEM ORCHESTRATION
        try:
            # Resolve dynamic static path from Flask context
            base_dir = current_app.root_path if current_app else os.getcwd()
            cache_folder = os.path.join(base_dir, 'static', 'audio_cache')
            os.makedirs(cache_folder, exist_ok=True)
            output_path = os.path.join(cache_folder, filename)
        except Exception as e:
            logger.error(f"Critical Filesystem Failure: {e}")
            return None

        # 3. NEURAL VOICE SELECTION
        voice = self.default_voice
        if user_settings and hasattr(user_settings, 'tts_voice') and user_settings.tts_voice:
            voice = user_settings.tts_voice
            logger.info(f"Using User-Defined Voice: {voice}")

        # 4. ADVANCED TEXT SANITIZATION
        # AI models often output Markdown which sounds terrible when read literally.
        processed_text = self._prepare_text_for_human_speech(text)

        # 5. SYNTHESIS EXECUTION (ASYNC BRIDGE)
        try:
            logger.info(f"Initiating Neural Synthesis for asset {asset_id}...")
            
            # Bridge the sync-async gap safely
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._execute_synthesis(processed_text, output_path, voice))
            finally:
                loop.close()
            
            duration = round(time.time() - start_time, 2)
            logger.info(f"Synthesis Complete: {filename} in {duration}s")
            return filename

        except Exception as e:
            logger.error(f"Neural Tier-1 Synthesis Failed: {e}. Falling back to Tier-2 (gTTS).")
            try:
                # Fallback to standard Google TTS if Edge-TTS service is unreachable
                tts = gTTS(text=processed_text, lang='en', slow=False)
                tts.save(output_path)
                return filename
            except Exception as e2:
                logger.error(f"Critical System Failure: All Synthesis Tiers Exhausted. {e2}")
                return None

    def _prepare_text_for_human_speech(self, text):
        """
        Converts raw AI markdown/code output into natural language flow.
        """
        # Remove massive code blocks entirely (cannot be 'read' effectively)
        text = re.sub(r'```.*?```', ' [Source code block omitted] ', text, flags=re.DOTALL)
        
        # Remove bold, italics, and strike-through markers
        text = re.sub(r'[*_~`]', '', text)
        
        # Convert list markers to breath pauses
        text = text.replace('\n-', '... ').replace('\n*', '... ')
        
        # Clean URLs to just the word 'link'
        text = re.sub(r'http\S+', 'website link', text)
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Safety Truncation: Neural engines have limits per request
        if len(text) > 2000:
            text = text[:1997] + "..."
            
        return text

# Global Engine Singleton
voice_engine = VoiceEngine()
