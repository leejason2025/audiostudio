#!/usr/bin/env python3
"""
Simple test script to verify the upload endpoint functionality
"""
import requests
import io
import os

def test_upload_endpoint():
    """Test the upload endpoint with a mock MP3 file"""
    
    # Create a mock MP3 file content (just for testing the endpoint)
    mock_mp3_content = b"ID3\x03\x00\x00\x00" + b"fake mp3 content for testing" * 100
    
    # Create file-like object
    files = {
        'file': ('test.mp3', io.BytesIO(mock_mp3_content), 'audio/mpeg')
    }
    
    try:
        # Test the upload endpoint
        response = requests.post('http://localhost:8000/upload', files=files)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"Job ID: {result['job_id']}")
            print(f"Status: {result['status']}")
            return result['job_id']
        else:
            print(f"❌ Upload failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Make sure it's running on localhost:8000")
        return None

def test_invalid_file():
    """Test upload with invalid file format"""
    
    # Create a text file instead of MP3
    files = {
        'file': ('test.txt', io.BytesIO(b"This is not an MP3 file"), 'text/plain')
    }
    
    try:
        response = requests.post('http://localhost:8000/upload', files=files)
        
        if response.status_code == 400:
            print("✅ Invalid file correctly rejected")
            print(f"Error: {response.json()['detail']}")
        else:
            print(f"❌ Expected 400 error, got {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server")

if __name__ == "__main__":
    print("Testing upload endpoint...")
    print("\n1. Testing valid MP3 upload:")
    job_id = test_upload_endpoint()
    
    print("\n2. Testing invalid file format:")
    test_invalid_file()
    
    if job_id:
        print(f"\n3. Checking if file was saved in uploads directory:")
        upload_files = os.listdir("uploads") if os.path.exists("uploads") else []
        if any(job_id in f for f in upload_files):
            print("✅ File was saved successfully")
        else:
            print("❌ File was not found in uploads directory")
            print(f"Files in uploads: {upload_files}")