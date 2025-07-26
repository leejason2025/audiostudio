# Audio Transcription Summarizer

A FastAPI-based web application that converts MP3 audio files into text transcriptions and generates concise summaries using AI.

## Features

- **MP3 File Upload**: Simple file upload interface for MP3 audio files
- **Speech-to-Text**: Converts audio to text using OpenAI's Whisper API
- **Text Summarization**: Generates concise summaries using OpenAI's GPT models
- **Asynchronous Processing**: Background processing with job status tracking
- **RESTful API**: Clean API endpoints for upload, status checking, and result retrieval

## Technology Stack

- **Backend**: FastAPI with Python 3.9+
- **AI Services**: OpenAI Whisper API (transcription) + OpenAI GPT API (summarization)
- **Task Queue**: Celery with Redis for asynchronous processing
- **Database**: SQLite for job tracking and results storage
- **Deployment**: Docker containerization support

## Getting Started

This project includes a complete specification in `.kiro/specs/audio-transcription-summarizer/` with:
- Requirements document
- System design
- Implementation tasks

To begin development, follow the tasks outlined in the spec or start with task 1: setting up the project structure and dependencies.
