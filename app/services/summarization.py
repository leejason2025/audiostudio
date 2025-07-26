import logging
from typing import Optional
from openai import OpenAI
from app.config import settings

# Set up logging
logger = logging.getLogger(__name__)

class SummarizationService:
    """Service for summarizing text using OpenAI GPT API"""
    
    def __init__(self):
        """Initialize the summarization service with OpenAI client"""
        if not settings.OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Configuration for summarization
        self.min_text_length = 50  # Minimum characters for summarization
        self.max_text_length = 100000  # Maximum characters to avoid token limits
        self.model = "gpt-3.5-turbo"  # Default model for summarization
    
    def summarize_text(self, text: str) -> str:
        """
        Generate a summary of the provided text using OpenAI GPT API.
        
        Args:
            text: The text to summarize
            
        Returns:
            str: The generated summary
            
        Raises:
            ValueError: If the text is too short or too long for summarization
            Exception: For API failures or other summarization errors
        """
        # Basic text length validation
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        text = text.strip()
        
        if len(text) < self.min_text_length:
            raise ValueError(f"Text is too short for summarization (minimum {self.min_text_length} characters)")
        
        if len(text) > self.max_text_length:
            raise ValueError(f"Text is too long for summarization (maximum {self.max_text_length} characters)")
        
        try:
            logger.info(f"Starting summarization for text of length: {len(text)}")
            
            # Create a simple but effective prompt for summarization
            prompt = self._create_summarization_prompt(text)
            
            # Generate summary using OpenAI GPT API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant that creates concise, accurate summaries of text content."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=500,  # Limit summary length
                temperature=0.3  # Lower temperature for more focused summaries
            )
            
            summary = response.choices[0].message.content.strip()
            
            if not summary:
                logger.warning("Empty summary generated")
                return "Unable to generate summary - no content returned."
            
            logger.info("Summarization completed successfully")
            return summary
            
        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            
            # Handle specific OpenAI API errors
            if hasattr(e, 'response') and hasattr(e.response, 'status_code'):
                status_code = e.response.status_code
                if status_code == 401:
                    raise Exception("Invalid OpenAI API key")
                elif status_code == 429:
                    raise Exception("OpenAI API rate limit exceeded. Please try again later.")
                elif status_code == 413:
                    raise Exception("Text is too large for processing")
                elif status_code >= 500:
                    raise Exception("OpenAI API service is temporarily unavailable")
            
            # Re-raise the original exception if it's not an API error
            raise Exception(f"Summarization failed: {str(e)}")
    
    def _create_summarization_prompt(self, text: str) -> str:
        """
        Create a prompt for text summarization that captures main points.
        
        Args:
            text: The text to be summarized
            
        Returns:
            str: The formatted prompt for summarization
        """
        return f"""Please provide a concise summary of the following text. Focus on capturing the main points, key ideas, and important details. The summary should be clear, well-organized, and significantly shorter than the original text while preserving the essential information.

Text to summarize:
{text}

Summary:"""
    
    def validate_api_key(self) -> bool:
        """
        Validate that the OpenAI API key is working for chat completions.
        
        Returns:
            bool: True if API key is valid, False otherwise
        """
        try:
            # Make a simple API call to test the key
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False


# Factory function to create summarization service instance
def get_summarization_service() -> SummarizationService:
    """Get a summarization service instance"""
    return SummarizationService()