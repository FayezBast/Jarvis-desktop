import os
import logging
import tempfile
import pygame
import os
import logging
import tempfile
import pygame
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try to import ElevenLabs
try:
    from elevenlabs.client import ElevenLabs
    from elevenlabs import VoiceSettings, Voice
    import elevenlabs
    ELEVENLABS_AVAILABLE = True
except ImportError as e:
    ELEVENLABS_AVAILABLE = False
    logging.warning(f"ElevenLabs not available: {e}. Using fallback TTS.")

# Fallback TTS
import pyttsx3

# ElevenLabs Configuration
ELEVENLABS_VOICE_ID = 'JBFqnCBsd6RMkjVDRZzb'  # Your specific voice ID
ELEVENLABS_MODEL = 'eleven_turbo_v2'  # Fast, high-quality model

class JarvisSpeech:
    """Enhanced speech system with ElevenLabs support"""
    
    def __init__(self):
        self.use_elevenlabs = False
        self.elevenlabs_api_key = None
        self.voice_id = ELEVENLABS_VOICE_ID
        self.model = ELEVENLABS_MODEL
        self.client = None
        self.fallback_engine = None
        
        # Initialize pygame mixer for audio playback
        pygame.mixer.init()
        
        # Try to initialize ElevenLabs
        self._init_elevenlabs()
        
        # Initialize fallback TTS
        self._init_fallback()
        
    def _init_elevenlabs(self):
        """Initialize ElevenLabs TTS"""
        if not ELEVENLABS_AVAILABLE:
            print("❌ ElevenLabs library not available")
            return
            
        # Get API key from environment or use hardcoded fallback
        self.elevenlabs_api_key = os.getenv("ELEVEN_API_KEY")
        
        # Fallback to hardcoded API key if env var not found (for packaged app)
        if not self.elevenlabs_api_key:
            # SECURITY: Never hardcode API keys! Use environment variables only.
            print("❌ No API key found. Please set ELEVEN_API_KEY environment variable.")
            return
        else:
            print(f"✅ Found API key from environment: {self.elevenlabs_api_key[:10]}...")
        
        if self.elevenlabs_api_key:
            try:
                print("🔄 Initializing ElevenLabs client...")
                # Initialize ElevenLabs client
                self.client = ElevenLabs(api_key=self.elevenlabs_api_key)
                
                # Use your configured voice ID
                self.voice_id = ELEVENLABS_VOICE_ID
                self.use_elevenlabs = True
                print(f"✅ ElevenLabs initialized successfully with voice ID: {self.voice_id}")
                return
                    
            except Exception as e:
                print(f"❌ ElevenLabs initialization failed: {e}")
                self.use_elevenlabs = False
        else:
            print("💡 ElevenLabs API key not found in environment variables")
            print("💡 Add ELEVEN_API_KEY to .env file or environment")
            
    def _init_fallback(self):
        """Initialize fallback pyttsx3 TTS"""
        try:
            self.fallback_engine = pyttsx3.init()
            
            # Try to set a good voice
            voices = self.fallback_engine.getProperty('voices')
            for voice in voices:
                if 'jamie' in voice.name.lower() or 'daniel' in voice.name.lower():
                    self.fallback_engine.setProperty('voice', voice.id)
                    break
                    
            # Set speech rate and volume
            self.fallback_engine.setProperty('rate', 180)
            self.fallback_engine.setProperty('volume', 1.0)
            
            logging.info("✅ Fallback TTS (pyttsx3) initialized")
            
        except Exception as e:
            logging.error(f"❌ Fallback TTS initialization failed: {e}")
            
    def speak(self, text: str) -> bool:
        """
        Speak text using ElevenLabs or fallback TTS
        Returns True if successful, False otherwise
        """
        if not text or not text.strip():
            return False
            
        print(f"🎤 Speaking: '{text[:50]}...' (ElevenLabs: {self.use_elevenlabs})")
            
        try:
            if self.use_elevenlabs and self.voice_id:
                print("🎵 Using ElevenLabs TTS...")
                return self._speak_elevenlabs(text)
            else:
                print("🔊 Using fallback TTS...")
                return self._speak_fallback(text)
                
        except Exception as e:
            print(f"❌ Speech error: {e}")
            # Try fallback if ElevenLabs fails
            if self.use_elevenlabs:
                print("🔄 Falling back to pyttsx3...")
                return self._speak_fallback(text)
            return False
            
    def _speak_elevenlabs(self, text: str) -> bool:
        """Speak using ElevenLabs TTS"""
        try:
            print(f"🎵 Generating ElevenLabs audio for: '{text[:30]}...'")
            # Generate audio using the client
            audio = self.client.text_to_speech.convert(
                voice_id=self.voice_id,
                text=text,
                model_id=self.model,
                voice_settings=VoiceSettings(
                    stability=0.75,      # Higher = more stable/consistent
                    similarity_boost=0.8, # Higher = closer to original voice
                    style=0.2,           # Lower = more neutral
                    use_speaker_boost=True
                )
            )
            
            print("🎵 Audio generated, saving to temp file...")
            # Save audio stream to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                # Write the audio stream to file
                for chunk in audio:
                    temp_file.write(chunk)
                temp_path = temp_file.name
                
            print(f"🎵 Playing audio from: {temp_path}")
            # Play audio using pygame
            pygame.mixer.music.load(temp_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
                
            print("🎵 Audio playback finished")
            # Clean up temporary file
            try:
                os.unlink(temp_path)
            except:
                pass
                
            return True
            
        except Exception as e:
            print(f"❌ ElevenLabs TTS error: {e}")
            return False
            
    def _speak_fallback(self, text: str) -> bool:
        """Speak using fallback pyttsx3 TTS"""
        try:
            if self.fallback_engine:
                self.fallback_engine.say(text)
                self.fallback_engine.runAndWait()
                return True
            return False
            
        except Exception as e:
            logging.error(f"❌ Fallback TTS error: {e}")
            return False
            
    def stop_speech(self) -> bool:
        """Stop current speech playback"""
        try:
            # Stop pygame audio playback
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                print("🛑 Speech playback stopped")
                return True
            
            # Stop fallback TTS if running
            if self.fallback_engine:
                try:
                    self.fallback_engine.stop()
                    print("🛑 Fallback TTS stopped")
                    return True
                except:
                    pass
                    
            return False
        except Exception as e:
            print(f"❌ Error stopping speech: {e}")
            return False
            
    def get_status(self) -> str:
        """Get current TTS status"""
        if self.use_elevenlabs:
            return "🎙️ ElevenLabs (High Quality)"
        elif self.fallback_engine:
            return "🔊 System TTS (Fallback)"
        else:
            return "❌ No TTS Available"
            
    def list_available_voices(self) -> list:
        """List available ElevenLabs voices"""
        if not self.use_elevenlabs or not self.client:
            return []
            
        try:
            available_voices = self.client.voices.get_all()
            return [(voice.name, voice.voice_id) for voice in available_voices.voices]
        except:
            return []
            
    def set_voice(self, voice_id: str) -> bool:
        """Set ElevenLabs voice by ID"""
        if self.use_elevenlabs:
            self.voice_id = voice_id
            return True
        return False


# Global instance
jarvis_speech = JarvisSpeech()

def speak_text(text: str):
    """Main function to speak text - drop-in replacement for existing speak_text"""
    return jarvis_speech.speak(text)

def stop_speech():
    """Stop current speech playback"""
    return jarvis_speech.stop_speech()

def get_speech_status():
    """Get current speech system status"""
    return jarvis_speech.get_status()

def list_voices():
    """List available voices"""
    return jarvis_speech.list_available_voices()

def set_voice(voice_id: str):
    """Set voice by ID"""
    return jarvis_speech.set_voice(voice_id)
