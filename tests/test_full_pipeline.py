#!/usr/bin/env python3
"""
Full pipeline test: Transcribe audio file then summarize the transcription.
This tests both the transcription and summarization services working together.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.transcription import get_transcription_service
from app.services.summarization import get_summarization_service

def test_full_pipeline():
    """Test the complete pipeline: audio -> transcription -> summary"""
    
    audio_file = "test.mp3"
    
    if not os.path.exists(audio_file):
        print(f"❌ Audio file '{audio_file}' not found!")
        print("Please make sure test.mp3 exists in the current directory.")
        return False
    
    try:
        print("🎵 Full Pipeline Test: Audio → Transcription → Summary")
        print("=" * 60)
        
        # Step 1: Initialize services
        print("Initializing services...")
        transcription_service = get_transcription_service()
        summarization_service = get_summarization_service()
        
        # Step 2: Validate API keys
        print("Validating API keys...")
        if not transcription_service.validate_api_key():
            print("❌ Transcription API key validation failed.")
            return False
        
        if not summarization_service.validate_api_key():
            print("❌ Summarization API key validation failed.")
            return False
        
        print("✅ Both API keys are valid!")
        
        # Step 3: Transcribe audio
        print(f"\n🎤 Step 1: Transcribing audio file '{audio_file}'...")
        transcription = transcription_service.transcribe_audio(audio_file)
        
        print("\n" + "=" * 60)
        print("📝 TRANSCRIPTION RESULT:")
        print("=" * 60)
        print(transcription)
        print(f"\nTranscription length: {len(transcription)} characters")
        
        # Step 4: Check if transcription is long enough for summarization
        if len(transcription) < 50:
            print(f"\n⚠️  Transcription is too short ({len(transcription)} chars) for summarization (minimum 50 chars).")
            print("This is expected for very short audio files.")
            return True
        
        # Step 5: Summarize transcription
        print(f"\n🤖 Step 2: Generating summary from transcription...")
        summary = summarization_service.summarize_text(transcription)
        
        print("\n" + "=" * 60)
        print("📋 GENERATED SUMMARY:")
        print("=" * 60)
        print(summary)
        print(f"\nSummary length: {len(summary)} characters")
        
        # Step 6: Show compression ratio
        compression_ratio = len(summary) / len(transcription)
        print(f"Compression ratio: {compression_ratio:.2%}")
        
        print("\n✅ Full pipeline test completed successfully!")
        print("\n📊 PIPELINE SUMMARY:")
        print(f"   Audio file: {audio_file}")
        print(f"   Transcription: {len(transcription)} characters")
        print(f"   Summary: {len(summary)} characters")
        print(f"   Compression: {compression_ratio:.2%}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during pipeline test: {str(e)}")
        return False

def test_summarization_with_sample_transcription():
    """Test summarization with a realistic sample transcription"""
    
    print("\n🧪 Testing Summarization with Sample Transcription")
    print("=" * 60)
    
    # Sample transcription text (realistic length and content)
    sample_transcription = """
    Hello everyone, welcome to today's meeting. I wanted to discuss our quarterly results and the upcoming product launch. 
    First, let me go over the sales numbers from last quarter. We exceeded our targets by fifteen percent, which is fantastic news. 
    The marketing team did an excellent job with the campaign, and customer feedback has been overwhelmingly positive. 
    Now, regarding the new product launch scheduled for next month, we need to finalize the pricing strategy and ensure 
    our supply chain is ready to handle the expected demand. The engineering team has completed all the testing phases, 
    and we're confident in the product quality. I'd like to schedule follow-up meetings with each department head to 
    coordinate the launch activities. Are there any questions or concerns about these topics?
    """
    
    try:
        print("Initializing summarization service...")
        service = get_summarization_service()
        
        print(f"Sample transcription length: {len(sample_transcription)} characters")
        print("\nGenerating summary...")
        
        summary = service.summarize_text(sample_transcription)
        
        print("\n" + "=" * 60)
        print("📝 SAMPLE TRANSCRIPTION:")
        print("=" * 60)
        print(sample_transcription.strip())
        
        print("\n" + "=" * 60)
        print("📋 GENERATED SUMMARY:")
        print("=" * 60)
        print(summary)
        
        print(f"\nOriginal: {len(sample_transcription)} characters")
        print(f"Summary: {len(summary)} characters")
        print(f"Compression: {len(summary)/len(sample_transcription):.2%}")
        
        print("\n✅ Sample transcription summarization test completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error during sample test: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Full Pipeline Test: Transcription + Summarization")
    print("This script will transcribe test.mp3 and then summarize the result.")
    print("Make sure you have a valid OPENAI_API_KEY in your .env file.\n")
    
    # Test 1: Full pipeline with actual audio file
    success1 = test_full_pipeline()
    
    # Test 2: Summarization with sample transcription (as backup)
    success2 = test_summarization_with_sample_transcription()
    
    if success1 or success2:
        print("\n🏁 At least one test completed successfully!")
    else:
        print("\n❌ All tests failed. Please check your configuration.")