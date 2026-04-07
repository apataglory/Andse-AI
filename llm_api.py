import os
import logging
from google import genai
from google.genai import types
from groq import Groq

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        # NEW: Google GenAI Client
        self.google_key = os.environ.get("GEMINI_API_KEY")
        self.google_client = genai.Client(api_key=self.google_key) if self.google_key else None
        
        # Groq Client
        self.groq_key = os.environ.get("GROQ_API_KEY")
        self.groq_client = Groq(api_key=self.groq_key) if self.groq_key else None

    def generate_response(self, prompt, history, system_prompt, provider='gemini', image_path=None):
        try:
            if provider == 'gemini' and self.google_client:
                return self._stream_gemini(prompt, history, system_prompt, image_path)
            return self._stream_groq(prompt, history, system_prompt)
        except Exception as e:
            logger.error(f"Brain Sync Error: {e}")
            yield f"Synthesis Interrupted: {str(e)}"

    def _stream_gemini(self, prompt, history, system_prompt, image_path):
        contents = []
        # Construct History
        for msg in history:
            role = "user" if msg.sender == "user" else "model"
            contents.append(types.Content(role=role, parts=[types.Part.from_text(text=msg.content)]))

        # Construct Current Input
        parts = [types.Part.from_text(text=prompt)]
        if image_path and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                parts.append(types.Part.from_bytes(data=f.read(), mime_type="image/jpeg"))

        contents.append(types.Content(role="user", parts=parts))

        # Start Stream
        response = self.google_client.models.generate_content_stream(
            model="gemini-1.5-pro",
            contents=contents,
            config=types.GenerateContentConfig(system_instruction=system_prompt, temperature=0.7)
        )
        for chunk in response:
            if chunk.text: yield chunk.text

    def _stream_groq(self, prompt, history, system_prompt):
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history:
            messages.append({"role": msg.sender, "content": msg.content})
        messages.append({"role": "user", "content": prompt})

        stream = self.groq_client.chat.completions.create(
            model="llama3-70b-8192", messages=messages, stream=True
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

llm_client = LLMClient()