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

## Project Structure

```
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI application entry point
│   └── config.py        # Configuration settings
├── tests/
│   └── __init__.py
├── uploads/             # Temporary file storage
├── venv/               # Virtual environment
├── .env.example        # Environment variables template
└── requirements.txt    # Python dependencies
```

## Getting Started

### Prerequisites
- Python 3.9+
- OpenAI API key

### Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

## Specification

This project includes a complete specification in `.kiro/specs/audio-transcription-summarizer/` with:
- Requirements document
- System design
- Implementation tasks

