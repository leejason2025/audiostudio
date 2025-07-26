import os
import logging
from typing import Optional
from openai import OpenAI
from app.config import settings

# Set up logging
logger = logging.getLogger(__name__)

class TranscriptionService:
    """Service for transcribing audio files using OpenAI Whisper API"""
    
    def __init__(self):
        """Initialize the transcription service with OpenAI client"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    def transcribe_audio(self, file_path: str) -> str:
        """
        Transcribe an audio file using OpenAI Whisper API.
        
        Args:
            file_path: Path to the audio file to transcribe
            
        Returns:
            str: The transcribed text
            
        Raises:
            FileNotFoundError: If the audio file doesn't exist
            ValueError: If the file format is not supported
            Exception: For API failures or other transcription errors
        """
        # Validate file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Validate file format (basic check)
        if not file_path.lower().endswith(('.mp3', '.wav', '.m4a', '.flac')):
            raise ValueError(f"Unsupported audio format: {file_path}")
        
        try:
            logger.info(f"Starting transcription for file: {file_path}")
            
            # Open and transcribe the audio file
            with open(file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            # The transcript is returned as a string when response_format="text"
            transcription_text = transcript.strip()
            
            if not transcription_text:
                logger.warning(f"Empty transcription result for file: {file_path}")
                return "No speech detected in the audio file."
            
            logger.info(f"Transcription completed successfully for file: {file_path}")
            return transcription_text
            
        except Exception as e:
            logger.error(f"Transcription failed for file {file_path}: {str(e)}")
            
            # Handle specific OpenAI API errors
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                status_code = e.response.status_code
                if status_code == 401:
                    raise Exception("Invalid OpenAI API key")
                elif status_code == 429:
                    raise Exception("OpenAI API rate limit exceeded. Please try again later.")
                elif status_code == 413:
                    raise Exception("Audio file is too large for processing")
                elif status_code >= 500:
                    raise Exception("OpenAI API service is temporarily unavailable")
            
            # Re-raise the original exception if it's not an API error
            raise Exception(f"Transcription failed: {str(e)}")
    
    def validate_api_key(self) -> bool:
        """
        Validate that the OpenAI API key is working.
        
        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            # Make a simple API call to test the key
            models = self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False


# Factory function to create transcription service instance
def get_transcription_service() -> TranscriptionService:
    """Get a transcription service instance"""
    return TranscriptionService()