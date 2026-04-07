import os
import time
import random
import logging
from google import genai
from google.genai import types

# Robust Groq Import
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

# Configure Logger for real-time monitoring in your terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NeuralEngine:
    def __init__(self):
        self.client = None
        self.groq_client = None
        self.is_active = False
        
        # Using explicit version IDs to bypass the "404 Not Found" alias issues
        # your logs showed earlier.
        self.gemini_models = [
            "gemini-2.0-flash",       
            "gemini-1.5-flash-002",   
            "gemini-1.5-pro-002",     
            "gemini-1.0-pro"          
        ]
        
        # Groq Models (Primary for Text to ensure reliability)
        self.groq_models = [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ]

    def configure(self, gemini_key, groq_key=None):
        """Initializes API clients and sets readiness state."""
        success = False
        
        # Configure Gemini
        if gemini_key:
            try:
                self.client = genai.Client(api_key=gemini_key, http_options={'api_version': 'v1beta'})
                success = True
                logger.info("✅ Gemini Neural Path: ACTIVE")
            except Exception as e:
                logger.error(f"❌ Gemini Setup Failed: {e}")

        # Configure Groq
        if groq_key and GROQ_AVAILABLE:
            try:
                self.groq_client = Groq(api_key=groq_key)
                success = True
                logger.info("✅ Groq High-Speed Path: ACTIVE")
            except Exception as e:
                logger.error(f"❌ Groq Setup Failed: {e}")
        
        self.is_active = success
        return success

    def think(self, user_input, history_objects=[], system_instruction="You are ANDSE AI."):
        """Main entry point for AI logic. Handles failover between providers."""
        if not self.is_active:
            return "❌ **NEURAL OFFLINE:** Please verify API keys in your .env file and restart the server."

        # Handle Image Synthesis Requests
        if any(t in user_input.lower() for t in ["draw", "generate image", "visualize", "paint"]):
            return self._generate_image(user_input)

        # 1. PRIMARY: Try Groq (Fastest and avoids Gemini's 429/404 issues)
        if self.groq_client:
            resp = self._try_groq(user_input, history_objects, system_instruction)
            if resp: return resp

        # 2. BACKUP: Try Gemini if Groq is unavailable or fails
        if self.client:
            resp = self._try_gemini(user_input, history_objects, system_instruction)
            if resp: return resp

        return "❌ **Neural Critical Failure:** All providers (Groq/Gemini) are unresponsive. Check logs for details."

    def _try_groq(self, prompt, history, instr):
        """Attempts text generation via Groq LPUs."""
        msgs = [{"role": "system", "content": instr}]
        for m in history:
            # history_objects are SQLAlchemy models from chat_manager.py
            msgs.append({"role": "user" if m.role == 'user' else "assistant", "content": m.content})
        msgs.append({"role": "user", "content": prompt})

        for model in self.groq_models:
            try:
                logger.info(f"⚡ Engaging Groq LPU: {model}")
                chat = self.groq_client.chat.completions.create(
                    model=model, messages=msgs, temperature=0.7, max_tokens=4096
                )
                return f"{chat.choices[0].message.content}"
            except Exception as e:
                logger.warning(f"⚠️ Groq {model} failed: {e}")
                continue
        return None

    def _try_gemini(self, prompt, history, instr):
        """Attempts text generation via Google Gemini nodes."""
        contents = []
        for msg in history:
            role = "user" if msg.role == 'user' else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))
        contents.append(types.Content(role="user", parts=[types.Part.from_text(text=prompt)]))

        config = types.GenerateContentConfig(temperature=0.7, system_instruction=instr)

        for model in self.gemini_models:
            try:
                logger.info(f"📡 Engaging Gemini Node: {model}")
                response = self.client.models.generate_content(model=model, contents=contents, config=config)
                if response.text: return response.text
            except Exception as e:
                logger.warning(f"⚠️ Gemini {model} failed: {str(e)[:100]}")
                continue
        return None

    def _generate_image(self, prompt):
        """Redirects visual requests to Pollinations API."""
        clean = prompt.lower().replace("draw", "").replace("generate image", "").strip()
        seed = random.randint(1, 1000000)
        url = f"https://image.pollinations.ai/prompt/{clean}?seed={seed}&model=flux&nologo=true"
        return f"![Output]({url})\n\n**Visual Synthesis:** *{clean}*"

# Global instance for the Flask app to import
engine = NeuralEngine()