#!/usr/bin/env python3
"""
Simple script to run the audio transcription app locally.
This will start both the Celery worker and FastAPI server.
"""

import subprocess
import sys
import time
import signal
import os

def signal_handler(sig, frame):
    print('\n🛑 Shutting down...')
    sys.exit(0)

def main():
    print("🚀 Starting Audio Transcription Summarizer...")
    print("📋 This will start:")
    print("   - Celery worker for background processing")
    print("   - FastAPI server on http://localhost:8000")
    print("\n⚠️  Make sure Redis is running: brew services start redis")
    print("🔑 Make sure your .env file has a valid OPENAI_API_KEY")
    print("\n" + "="*50)
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Start Celery worker in background
        print("🔄 Starting Celery worker...")
        worker_process = subprocess.Popen([
            "celery", "-A", "app.celery_app", "worker", 
            "--loglevel=info", "--concurrency=1"
        ])
        
        # Give worker time to start
        time.sleep(3)
        
        # Start FastAPI server
        print("🌐 Starting FastAPI server on http://localhost:8000...")
        print("📖 API docs available at: http://localhost:8000/docs")
        print("🏥 Health check at: http://localhost:8000/health")
        print("\n💡 Press Ctrl+C to stop both services")
        print("="*50 + "\n")
        
        server_process = subprocess.Popen([
            "uvicorn", "app.main:app", "--reload", 
            "--host", "0.0.0.0", "--port", "8000"
        ])
        
        # Wait for server process
        server_process.wait()
        
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal...")
    finally:
        # Clean up processes
        try:
            worker_process.terminate()
            server_process.terminate()
            print("✅ Services stopped")
        except:
            pass

if __name__ == "__main__":
    main()