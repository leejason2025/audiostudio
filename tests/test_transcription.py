import pytest
import os
import tempfile
from unittest.mock import Mock, patch, mock_open
from app.services.transcription import TranscriptionService


class TestTranscriptionService:
    """Test cases for the TranscriptionService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Mock the OpenAI client entirely to avoid dependency issues
        with patch('app.services.transcription.settings') as mock_settings, \
             patch('app.services.transcription.OpenAI') as mock_openai:
            mock_settings.OPENAI_API_KEY = 'test-api-key'
            self.mock_client = Mock()
            mock_openai.return_value = self.mock_client
            self.service = TranscriptionService()
    
    def test_init_without_api_key(self):
        """Test that service initialization fails without API key"""
        with patch('app.services.transcription.settings') as mock_settings, \
             patch('app.services.transcription.OpenAI'):
            mock_settings.OPENAI_API_KEY = None
            with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is required"):
                TranscriptionService()
    
    def test_transcribe_audio_file_not_found(self):
        """Test transcription fails when file doesn't exist"""
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            self.service.transcribe_audio("/nonexistent/file.mp3")
    
    def test_transcribe_audio_unsupported_format(self):
        """Test transcription fails with unsupported file format"""
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_path = temp_file.name
        
        try:
            with pytest.raises(ValueError, match="Unsupported audio format"):
                self.service.transcribe_audio(temp_path)
        finally:
            os.unlink(temp_path)
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake audio data')
    @patch('os.path.exists')
    def test_transcribe_audio_success(self, mock_exists, mock_file):
        """Test successful transcription"""
        mock_exists.return_value = True
        
        # Mock the OpenAI client response
        mock_transcript = "This is a test transcription."
        self.mock_client.audio.transcriptions.create.return_value = mock_transcript
        
        result = self.service.transcribe_audio("/fake/path/test.mp3")
        
        assert result == "This is a test transcription."
        mock_file.assert_called_once_with("/fake/path/test.mp3", "rb")
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake audio data')
    @patch('os.path.exists')
    def test_transcribe_audio_empty_result(self, mock_exists, mock_file):
        """Test handling of empty transcription result"""
        mock_exists.return_value = True
        
        # Mock empty transcription result
        self.mock_client.audio.transcriptions.create.return_value = "   "
        
        result = self.service.transcribe_audio("/fake/path/test.mp3")
        
        assert result == "No speech detected in the audio file."
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake audio data')
    @patch('os.path.exists')
    def test_transcribe_audio_api_error(self, mock_exists, mock_file):
        """Test handling of API errors"""
        mock_exists.return_value = True
        
        # Mock API error
        api_error = Exception("API Error")
        api_error.response = Mock()
        api_error.response.status_code = 401
        
        self.mock_client.audio.transcriptions.create.side_effect = api_error
        
        with pytest.raises(Exception, match="Invalid OpenAI API key"):
            self.service.transcribe_audio("/fake/path/test.mp3")
    
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake audio data')
    @patch('os.path.exists')
    def test_transcribe_audio_rate_limit_error(self, mock_exists, mock_file):
        """Test handling of rate limit errors"""
        mock_exists.return_value = True
        
        # Mock rate limit error
        api_error = Exception("Rate limit exceeded")
        api_error.response = Mock()
        api_error.response.status_code = 429
        
        self.mock_client.audio.transcriptions.create.side_effect = api_error
        
        with pytest.raises(Exception, match="OpenAI API rate limit exceeded"):
            self.service.transcribe_audio("/fake/path/test.mp3")
    
    def test_validate_api_key_success(self):
        """Test successful API key validation"""
        self.mock_client.models.list.return_value = Mock()
        assert self.service.validate_api_key() is True
    
    def test_validate_api_key_failure(self):
        """Test failed API key validation"""
        self.mock_client.models.list.side_effect = Exception("Invalid key")
        assert self.service.validate_api_key() is False