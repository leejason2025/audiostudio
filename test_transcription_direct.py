#!/usr/bin/env python3
"""
Direct test of the transcription service with an MP3 file
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add app to path
sys.path.insert(0, 'app')

def test_transcription_with_file(mp3_file_path):
    """Test transcription service with an actual MP3 file"""
    
    if not os.path.exists(mp3_file_path):
        print(f"❌ File not found: {mp3_file_path}")
        return False
    
    try:
        from services.transcription import get_transcription_service
        
        print(f"🎵 Testing transcription with: {mp3_file_path}")
        print("-" * 50)
        
        # Create transcription service
        service = get_transcription_service()
        
        # Transcribe the audio file
        print("🔄 Starting transcription...")
        transcription = service.transcribe_audio(mp3_file_path)
        
        print("✅ Transcription completed!")
        print("\n📝 Transcription Result:")
        print("-" * 30)
        print(transcription)
        print("-" * 30)
        
        return True
        
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return False

if __name__ == "__main__":
    # Check if MP3 file path is provided
    if len(sys.argv) > 1:
        mp3_path = sys.argv[1]
    else:
        # Look for any MP3 files in current directory
        mp3_files = [f for f in os.listdir('.') if f.endswith('.mp3')]
        if mp3_files:
            mp3_path = mp3_files[0]
            print(f"📁 Found MP3 file: {mp3_path}")
        else:
            print("❌ No MP3 file provided or found.")
            print("Usage: python test_transcription_direct.py <path_to_mp3_file>")
            sys.exit(1)
    
    success = test_transcription_with_file(mp3_path)
    sys.exit(0 if success else 1)