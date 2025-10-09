from gtts import gTTS
from deep_translator import GoogleTranslator
import base64
from io import BytesIO
from config import Config

class MultilingualTTS:
    @staticmethod
    def text_to_speech(text, language='en'):
        """
        Convert text to speech in multiple languages
        """
        try:
            # Translate if not English
            if language != 'en':
                translator = GoogleTranslator(source='en', target=language)
                text = translator.translate(text)
            
            # Generate speech
            tts = gTTS(text=text, lang=language, slow=False)
            
            # Convert to base64
            audio_buffer = BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            
            audio_base64 = base64.b64encode(audio_buffer.read()).decode('utf-8')
            
            return {
                "success": True,
                "audio_base64": audio_base64,
                "language": language,
                "format": "mp3"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def get_supported_languages():
        """Return list of supported languages"""
        return Config.SUPPORTED_LANGUAGES