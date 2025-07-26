#!/usr/bin/env python3
"""
Manual test script for the summarization service.
Run this to test the summarization functionality with sample text.
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.summarization import get_summarization_service

def test_summarization():
    """Test the summarization service with sample text"""
    
    # Sample text for testing (a longer piece of text that can be summarized)
    sample_text = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of "intelligent agents": any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term "artificial intelligence" is often used to describe machines that mimic "cognitive" functions that humans associate with the human mind, such as "learning" and "problem solving".
    
    The scope of AI is disputed: as machines become increasingly capable, tasks considered to require "intelligence" are often removed from the definition of AI, a phenomenon known as the AI effect. A quip in Tesler's Theorem says "AI is whatever hasn't been done yet." For instance, optical character recognition is frequently excluded from things considered to be AI, having become a routine technology. Modern machine capabilities generally classified as AI include successfully understanding human speech, competing at the highest level in strategic game systems, autonomously operating cars, intelligent routing in content delivery networks, and military simulations.
    
    Artificial intelligence was founded as an academic discipline in 1956, and in the years since has experienced several waves of optimism, followed by disappointment and the loss of funding (known as an "AI winter"), followed by new approaches, success and renewed funding. AI research has tried many different approaches, but no single approach has been entirely successful. Some researchers have suggested that the field needs to return to its roots in cognitive science and neuroscience.
    
    The various sub-fields of AI research are centered around particular goals and the use of particular tools. The traditional goals of AI research include reasoning, knowledge representation, planning, learning, natural language processing, perception, and the ability to move and manipulate objects. General intelligence is among the field's long-term goals. Approaches include statistical methods, computational intelligence, and traditional symbolic AI. Many tools are used in AI, including versions of search and mathematical optimization, artificial neural networks, and methods based on statistics, probability and economics.
    """
    
    try:
        print("🤖 Testing Summarization Service")
        print("=" * 50)
        
        # Initialize the service
        print("Initializing summarization service...")
        service = get_summarization_service()
        
        # Validate API key first
        print("Validating OpenAI API key...")
        if not service.validate_api_key():
            print("❌ API key validation failed. Please check your OPENAI_API_KEY in .env file.")
            return
        
        print("✅ API key is valid!")
        
        # Test summarization
        print(f"\nOriginal text length: {len(sample_text)} characters")
        print("\nGenerating summary...")
        
        summary = service.summarize_text(sample_text)
        
        print("\n" + "=" * 50)
        print("📝 ORIGINAL TEXT:")
        print("=" * 50)
        print(sample_text.strip())
        
        print("\n" + "=" * 50)
        print("📋 GENERATED SUMMARY:")
        print("=" * 50)
        print(summary)
        
        print(f"\nSummary length: {len(summary)} characters")
        print(f"Compression ratio: {len(summary)/len(sample_text):.2%}")
        
        print("\n✅ Summarization test completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during summarization test: {str(e)}")
        return False
    
    return True

def test_edge_cases():
    """Test edge cases for the summarization service"""
    
    print("\n🧪 Testing Edge Cases")
    print("=" * 50)
    
    try:
        service = get_summarization_service()
        
        # Test 1: Empty text
        print("Test 1: Empty text")
        try:
            service.summarize_text("")
            print("❌ Should have failed for empty text")
        except ValueError as e:
            print(f"✅ Correctly handled empty text: {e}")
        
        # Test 2: Text too short
        print("\nTest 2: Text too short")
        try:
            service.summarize_text("Short")
            print("❌ Should have failed for short text")
        except ValueError as e:
            print(f"✅ Correctly handled short text: {e}")
        
        # Test 3: Valid short text (just above minimum)
        print("\nTest 3: Valid short text")
        short_valid_text = "This is a slightly longer text that should be valid for summarization because it meets the minimum character requirement."
        try:
            summary = service.summarize_text(short_valid_text)
            print(f"✅ Successfully summarized short valid text: {summary[:100]}...")
        except Exception as e:
            print(f"❌ Failed to summarize valid short text: {e}")
        
        print("\n✅ Edge case testing completed!")
        
    except Exception as e:
        print(f"❌ Error during edge case testing: {str(e)}")

if __name__ == "__main__":
    print("🚀 Manual Summarization Service Test")
    print("This script will test the summarization service with sample text.")
    print("Make sure you have a valid OPENAI_API_KEY in your .env file.\n")
    
    # Run the main test
    success = test_summarization()
    
    if success:
        # Run edge case tests
        test_edge_cases()
    
    print("\n🏁 Test completed!")