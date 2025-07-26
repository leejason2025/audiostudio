#!/usr/bin/env python3
"""
Script to start the Celery worker for processing audio files.
Run this in a separate terminal while the FastAPI server is running.
"""

import os
import sys

# Add the current directory to Python path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.celery_app import celery_app

if __name__ == "__main__":
    # Start the Celery worker
    celery_app.start([
        "worker",
        "--loglevel=info",
        "--concurrency=1",  # Process one task at a time for simplicity
    ])