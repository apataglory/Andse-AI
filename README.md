# ANDSE AI - Ultra Massive Intelligence System v2.0

The Advanced Neural Digital Sensory Engine (ANDSE) is a multimodal AI operating system capable of:
* **Vision:** Image analysis & generation (Gemini Vision)
* **Hearing:** Real-time Voice Transcription (MediaRecorder + STT)
* **Speech:** Neural Text-to-Speech (Edge TTS)
* **Action:** Automated Email Reporting & Background Tasks
* **Memory:** Long-term vector-based memory retention

## 🚀 Quick Start

1.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Environment:**
    * Rename `.env.example` to `.env`.
    * Add your API Keys (Gemini, Groq, Google OAuth).

3.  **Launch System:**
    ```bash
    python app.py
    ```

## 📂 File Structure

* `app.py` - The Core Executable.
* `reasoning_engine.py` - The Brain (Logic & Tool Use).
* `ai_engine.py` - The Voice (Gemini/Groq Integration).
* `automation_engine.py` - The Background Worker.
* `static/` - Frontend Assets (JS/CSS).

* `templates/` - HTML Views.
