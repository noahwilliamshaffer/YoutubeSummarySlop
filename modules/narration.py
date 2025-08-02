"""
Narration Module
Generates AI voice narration using ElevenLabs API
"""

import os
import requests
from dotenv import load_dotenv
from typing import Optional, Dict, List
import logging
import time

# Load environment variables
load_dotenv()

class NarrationGenerator:
    def __init__(self):
        self.api_key = os.getenv('ELEVENLABS_API_KEY')
        if not self.api_key:
            raise ValueError("ElevenLabs API key not found. Please set ELEVENLABS_API_KEY in .env file")
        
        self.base_url = "https://api.elevenlabs.io/v1"
        self.headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        # Default voice settings
        self.default_voice_id = os.getenv('DEFAULT_VOICE_ID', 'EXAVITQu4vr4xnSDxMaL')  # Bella voice
        self.default_voice_settings = {
            "stability": 0.4,
            "similarity_boost": 0.9,
            "style": 0.2,
            "use_speaker_boost": True
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def get_available_voices(self) -> List[Dict]:
        """
        Get list of available voices from ElevenLabs
        
        Returns:
            List of available voices
        """
        try:
            url = f"{self.base_url}/voices"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            voices_data = response.json()
            voices = voices_data.get('voices', [])
            
            self.logger.info(f"Retrieved {len(voices)} available voices")
            return voices
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching voices: {e}")
            return []
    
    def generate_speech(self, text: str, voice_id: Optional[str] = None, 
                       output_path: str = "./temp/narration.mp3", 
                       voice_settings: Optional[Dict] = None) -> Optional[str]:
        """
        Generate speech from text using ElevenLabs TTS
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID (uses default if None)
            output_path: Path to save the audio file
            voice_settings: Voice configuration settings
            
        Returns:
            Path to generated audio file or None if failed
        """
        try:
            if not voice_id:
                voice_id = self.default_voice_id
            
            if not voice_settings:
                voice_settings = self.default_voice_settings
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            url = f"{self.base_url}/text-to-speech/{voice_id}"
            
            payload = {
                "text": text,
                "voice_settings": voice_settings,
                "model_id": "eleven_multilingual_v2"
            }
            
            self.logger.info(f"Generating speech for {len(text)} characters using voice {voice_id}")
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            # Save the audio file
            with open(output_path, "wb") as f:
                f.write(response.content)
            
            self.logger.info(f"Speech generated successfully: {output_path}")
            return output_path
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error generating speech: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return None
    
    def generate_speech_with_timestamps(self, text: str, voice_id: Optional[str] = None,
                                      output_path: str = "./temp/narration.mp3") -> Optional[Dict]:
        """
        Generate speech with word-level timestamps for caption synchronization
        
        Args:
            text: Text to convert to speech
            voice_id: ElevenLabs voice ID
            output_path: Path to save the audio file
            
        Returns:
            Dictionary with audio path and timing information
        """
        try:
            if not voice_id:
                voice_id = self.default_voice_id
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            url = f"{self.base_url}/text-to-speech/{voice_id}/with-timestamps"
            
            payload = {
                "text": text,
                "voice_settings": self.default_voice_settings,
                "model_id": "eleven_multilingual_v2",
                "enable_timestamps": True
            }
            
            self.logger.info(f"Generating speech with timestamps for {len(text)} characters")
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            
            # Save the audio file
            audio_data = data.get('audio_base64', '')
            if audio_data:
                import base64
                audio_bytes = base64.b64decode(audio_data)
                with open(output_path, "wb") as f:
                    f.write(audio_bytes)
            
            # Extract timing information
            timing_info = {
                'audio_path': output_path,
                'duration': data.get('duration', 0),
                'word_timestamps': data.get('word_timestamps', []),
                'character_timestamps': data.get('character_timestamps', [])
            }
            
            self.logger.info(f"Speech with timestamps generated: {output_path}")
            return timing_info
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error generating speech with timestamps: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return None
    
    def split_text_for_generation(self, text: str, max_chars: int = 2000) -> List[str]:
        """
        Split long text into chunks suitable for TTS generation
        
        Args:
            text: Text to split
            max_chars: Maximum characters per chunk
            
        Returns:
            List of text chunks
        """
        try:
            if len(text) <= max_chars:
                return [text]
            
            chunks = []
            current_chunk = ""
            
            # Split by sentences to maintain natural breaks
            sentences = text.replace('. ', '.|||').replace('? ', '?|||').replace('! ', '!|||').split('|||')
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= max_chars:
                    current_chunk += sentence
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = sentence
            
            if current_chunk:
                chunks.append(current_chunk.strip())
            
            self.logger.info(f"Split text into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            self.logger.error(f"Error splitting text: {e}")
            return [text]
    
    def generate_long_speech(self, text: str, voice_id: Optional[str] = None,
                           output_dir: str = "./temp") -> Optional[List[str]]:
        """
        Generate speech for long text by splitting into chunks
        
        Args:
            text: Long text to convert to speech
            voice_id: ElevenLabs voice ID
            output_dir: Directory to save audio chunks
            
        Returns:
            List of paths to generated audio files
        """
        try:
            chunks = self.split_text_for_generation(text)
            audio_files = []
            
            for i, chunk in enumerate(chunks):
                output_path = os.path.join(output_dir, f"narration_chunk_{i+1:03d}.mp3")
                
                audio_file = self.generate_speech(
                    text=chunk,
                    voice_id=voice_id,
                    output_path=output_path
                )
                
                if audio_file:
                    audio_files.append(audio_file)
                    # Small delay to avoid rate limiting
                    time.sleep(0.5)
                else:
                    self.logger.error(f"Failed to generate audio for chunk {i+1}")
                    return None
            
            self.logger.info(f"Generated {len(audio_files)} audio chunks")
            return audio_files
            
        except Exception as e:
            self.logger.error(f"Error generating long speech: {e}")
            return None
    
    def get_voice_info(self, voice_id: str) -> Optional[Dict]:
        """
        Get information about a specific voice
        
        Args:
            voice_id: ElevenLabs voice ID
            
        Returns:
            Voice information dictionary
        """
        try:
            url = f"{self.base_url}/voices/{voice_id}"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            voice_info = response.json()
            self.logger.info(f"Retrieved info for voice: {voice_info.get('name', 'Unknown')}")
            
            return voice_info
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Error fetching voice info: {e}")
            return None
    
    def optimize_voice_settings(self, voice_id: str, content_type: str = "narrative") -> Dict:
        """
        Get optimized voice settings based on content type
        
        Args:
            voice_id: ElevenLabs voice ID
            content_type: Type of content (narrative, documentary, casual)
            
        Returns:
            Optimized voice settings
        """
        try:
            base_settings = self.default_voice_settings.copy()
            
            if content_type == "narrative":
                # For movie narration
                base_settings.update({
                    "stability": 0.5,
                    "similarity_boost": 0.8,
                    "style": 0.3
                })
            elif content_type == "documentary":
                # For documentary style
                base_settings.update({
                    "stability": 0.7,
                    "similarity_boost": 0.9,
                    "style": 0.1
                })
            elif content_type == "casual":
                # For casual discussion
                base_settings.update({
                    "stability": 0.3,
                    "similarity_boost": 0.7,
                    "style": 0.4
                })
            
            self.logger.info(f"Optimized voice settings for {content_type} content")
            return base_settings
            
        except Exception as e:
            self.logger.error(f"Error optimizing voice settings: {e}")
            return self.default_voice_settings

def main():
    """Test the NarrationGenerator functionality"""
    try:
        narrator = NarrationGenerator()
        
        # Test voice listing
        print("Fetching available voices...")
        voices = narrator.get_available_voices()
        if voices:
            print(f"Found {len(voices)} voices")
            for voice in voices[:3]:  # Show first 3 voices
                print(f"- {voice.get('name', 'Unknown')} ({voice.get('voice_id', '')})")
        
        # Test speech generation with sample text
        sample_text = """
        Welcome to our movie breakdown series. Today we're diving deep into one of cinema's most 
        influential films. Get ready for an incredible journey through storytelling, symbolism, 
        and cinematic excellence.
        """
        
        print(f"\nGenerating speech for sample text...")
        audio_file = narrator.generate_speech(
            text=sample_text.strip(),
            output_path="./temp/test_narration.mp3"
        )
        
        if audio_file:
            print(f"Speech generated successfully: {audio_file}")
        else:
            print("Failed to generate speech")
            
    except Exception as e:
        print(f"Error running NarrationGenerator test: {e}")

if __name__ == "__main__":
    main() 