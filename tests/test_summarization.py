import pytest
from unittest.mock import Mock, patch
from app.services.summarization import SummarizationService, get_summarization_service


class TestSummarizationService:
    """Test cases for the SummarizationService"""
    
    def setup_method(self):
        """Set up test fixtures"""
        with patch('app.services.summarization.settings.OPENAI_API_KEY', 'test-key'):
            self.service = SummarizationService()
    
    def test_initialization_without_api_key(self):
        """Test that service raises error when API key is missing"""
        with patch('app.services.summarization.settings.OPENAI_API_KEY', None):
            with pytest.raises(ValueError, match="OPENAI_API_KEY environment variable is required"):
                SummarizationService()
    
    def test_summarize_text_empty_input(self):
        """Test that empty text raises ValueError"""
        with pytest.raises(ValueError, match="Text cannot be empty"):
            self.service.summarize_text("")
        
        with pytest.raises(ValueError, match="Text cannot be empty"):
            self.service.summarize_text("   ")
    
    def test_summarize_text_too_short(self):
        """Test that text shorter than minimum length raises ValueError"""
        short_text = "Short"
        with pytest.raises(ValueError, match="Text is too short for summarization"):
            self.service.summarize_text(short_text)
    
    def test_summarize_text_too_long(self):
        """Test that text longer than maximum length raises ValueError"""
        long_text = "x" * 100001  # Exceeds max_text_length
        with pytest.raises(ValueError, match="Text is too long for summarization"):
            self.service.summarize_text(long_text)
    
    @patch('app.services.summarization.OpenAI')
    def test_summarize_text_success(self, mock_openai):
        """Test successful text summarization"""
        # Mock the OpenAI client response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test summary."
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create service with mocked client
        with patch('app.services.summarization.settings.OPENAI_API_KEY', 'test-key'):
            service = SummarizationService()
        
        test_text = "This is a longer text that needs to be summarized. " * 5
        result = service.summarize_text(test_text)
        
        assert result == "This is a test summary."
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('app.services.summarization.OpenAI')
    def test_summarize_text_api_error(self, mock_openai):
        """Test handling of API errors during summarization"""
        # Mock API error
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client
        
        with patch('app.services.summarization.settings.OPENAI_API_KEY', 'test-key'):
            service = SummarizationService()
        
        test_text = "This is a longer text that needs to be summarized. " * 5
        
        with pytest.raises(Exception, match="Summarization failed: API Error"):
            service.summarize_text(test_text)
    
    @patch('app.services.summarization.OpenAI')
    def test_summarize_text_empty_response(self, mock_openai):
        """Test handling of empty response from API"""
        # Mock empty response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = ""
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch('app.services.summarization.settings.OPENAI_API_KEY', 'test-key'):
            service = SummarizationService()
        
        test_text = "This is a longer text that needs to be summarized. " * 5
        result = service.summarize_text(test_text)
        
        assert result == "Unable to generate summary - no content returned."
    
    def test_create_summarization_prompt(self):
        """Test that summarization prompt is created correctly"""
        test_text = "This is test content for summarization."
        prompt = self.service._create_summarization_prompt(test_text)
        
        assert "Please provide a concise summary" in prompt
        assert test_text in prompt
        assert "Summary:" in prompt
    
    @patch('app.services.summarization.OpenAI')
    def test_validate_api_key_success(self, mock_openai):
        """Test successful API key validation"""
        mock_response = Mock()
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        with patch('app.services.summarization.settings.OPENAI_API_KEY', 'test-key'):
            service = SummarizationService()
        
        assert service.validate_api_key() is True
    
    @patch('app.services.summarization.OpenAI')
    def test_validate_api_key_failure(self, mock_openai):
        """Test API key validation failure"""
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("Invalid API key")
        mock_openai.return_value = mock_client
        
        with patch('app.services.summarization.settings.OPENAI_API_KEY', 'test-key'):
            service = SummarizationService()
        
        assert service.validate_api_key() is False
    
    def test_get_summarization_service_factory(self):
        """Test the factory function"""
        with patch('app.services.summarization.settings.OPENAI_API_KEY', 'test-key'):
            service = get_summarization_service()
            assert isinstance(service, SummarizationService)