import speech_recognition as sr
import os
import logging
from pydub import AudioSegment

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SpeechProcessor:
    """
    Advanced Voice-to-Text Processor.
    Supports .webm (Browser Audio), .ogg, .wav, and .mp3 formats.
    """

    def __init__(self):
        self.recognizer = sr.Recognizer()

    def transcribe_audio(self, file_path):
        """
        Converts input audio file to WAV format and performs Google Speech Recognition.
        """
        wav_path = None
        try:
            # 1. Convert to WAV (Standardizes input for SpeechRecognition)
            logger.info(f"Processing audio: {file_path}")
            audio = AudioSegment.from_file(file_path)
            
            # Create a temporary WAV file
            wav_path = file_path + ".wav"
            audio.export(wav_path, format="wav")

            # 2. Perform Transcription
            with sr.AudioFile(wav_path) as source:
                # Adjust for ambient noise for better accuracy
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio_data = self.recognizer.record(source)
                
                # Use Google Web Speech API (Free & High Quality)
                text = self.recognizer.recognize_google(audio_data)
                
            logger.info(f"Transcription successful: {text}")
            return text

        except sr.UnknownValueError:
            logger.warning("STT: Audio unintelligible.")
            return "[Audio Unintelligible]"
        except sr.RequestError as e:
            logger.error(f"STT Service Error: {e}")
            return "[Speech Service Unavailable]"
        except Exception as e:
            logger.error(f"General STT Error: {e}")
            return f"[Error: {str(e)}]"
        finally:
            # 3. Cleanup: Remove the temporary WAV file to save space
            if wav_path and os.path.exists(wav_path):
                try:
                    os.remove(wav_path)
                except:
                    pass

# Global Instance
speech_processor = SpeechProcessor()
