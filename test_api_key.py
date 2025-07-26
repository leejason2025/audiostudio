#!/usr/bin/env python3
"""
Test script to validate OpenAI API key configuration.
Run this script to check if your API key is properly configured.
"""

import os
import sys
from dotenv import load_dotenv

def test_api_key():
    """Test the OpenAI API key configuration"""
    
    # Load environment variables from .env file
    load_dotenv()
    
    print("🔍 Testing OpenAI API Key Configuration...")
    print("-" * 50)
    
    # Check if API key is set
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY is not set!")
        print("\n📝 To fix this:")
        print("1. Copy .env.example to .env: cp .env.example .env")
        print("2. Edit .env and add your OpenAI API key")
        print("3. Get your API key from: https://platform.openai.com/api-keys")
        return False
    
    print(f"✅ OPENAI_API_KEY is set (length: {len(api_key)} characters)")
    
    # Test the API key by creating a transcription service
    try:
        sys.path.insert(0, 'app')
        from services.transcription import get_transcription_service
        
        print("🔧 Creating transcription service...")
        service = get_transcription_service()
        
        print("🌐 Validating API key with OpenAI...")
        if service.validate_api_key():
            print("✅ API key is valid and working!")
            return True
        else:
            print("❌ API key validation failed!")
            print("\n📝 Possible issues:")
            print("- API key is invalid or expired")
            print("- No internet connection")
            print("- OpenAI API is temporarily unavailable")
            return False
            
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        return False

if __name__ == "__main__":
    success = test_api_key()
    
    if success:
        print("\n🎉 Your OpenAI API key is properly configured!")
        print("You can now run the application with: uvicorn app.main:app --reload")
    else:
        print("\n💡 Please fix the API key configuration and try again.")
    
    sys.exit(0 if success else 1)