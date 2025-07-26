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
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── models.py            # Database models and Pydantic schemas
│   ├── database.py          # Database connection and setup
│   ├── crud.py              # Database operations
│   ├── celery_app.py        # Celery configuration
│   ├── tasks.py             # Celery background tasks
│   └── services/
│       ├── __init__.py
│       ├── transcription.py # OpenAI Whisper integration
│       ├── summarization.py # OpenAI GPT integration
│       └── file_handler.py  # File upload and validation
├── tests/
│   ├── __init__.py
│   ├── test_api_key.py          # API key validation tests
│   ├── test_transcription.py    # Transcription service unit tests
│   ├── test_summarization.py    # Summarization service unit tests
│   ├── test_upload.py           # Upload endpoint tests
│   ├── test_celery_tasks.py     # Celery task processing tests
│   ├── test_full_pipeline.py    # End-to-end pipeline tests
│   ├── test_transcription_direct.py  # Direct transcription testing
│   └── test_summarization_manual.py  # Manual summarization testing
├── uploads/             # Temporary file storage
├── .kiro/specs/         # Project specification documents
├── start_worker.py      # Celery worker startup script
├── .env.example         # Environment variables template
└── requirements.txt     # Python dependencies
```

## Getting Started

### Prerequisites
- Python 3.9+
- **OpenAI API key** (required for transcription functionality)
  - Sign up at https://platform.openai.com/
  - Generate an API key at https://platform.openai.com/api-keys
  - Note: This service requires OpenAI credits/billing to be set up

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
   ```
   
   Edit the `.env` file and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-openai-api-key-here
   ```
   
   **Important**: You need to obtain an OpenAI API key from https://platform.openai.com/api-keys

4. Test your API key configuration:
   ```bash
   python test_api_key.py
   ```

5. Start Redis server (required for task processing):
   ```bash
   redis-server
   ```

6. Start the Celery worker (in a separate terminal):
   ```bash
   python start_worker.py
   ```

7. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

The application will be available at http://localhost:8000

### API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check including API key validation status
- `POST /upload` - Upload MP3 file for processing (returns job ID)
- `GET /status/{job_id}` - Check processing status (pending/processing/completed/failed)
- `GET /result/{job_id}` - Retrieve transcription and summary results
- `GET /docs` - Interactive API documentation (Swagger UI)

### Asynchronous Processing

The application uses Celery with Redis for background processing:

1. **Upload**: Client uploads MP3 file, receives job ID immediately
2. **Processing**: Celery worker processes the file in background:
   - Transcribes audio using OpenAI Whisper API
   - Generates summary using OpenAI GPT API
   - Updates job status in database
3. **Retrieval**: Client polls status endpoint and retrieves results when complete

**Processing Pipeline:**
```
MP3 Upload → Job Created → Celery Task → Whisper API → GPT API → Results Stored
```

### Testing

The project includes comprehensive tests organized in the `tests/` directory:

**Quick Setup Validation:**
```bash
# Test API key configuration
python tests/test_api_key.py

# Test transcription with audio file
python tests/test_transcription_direct.py test.mp3

# Test upload endpoint
python tests/test_upload.py
```

**Service Testing:**
```bash
# Test individual services
python -m pytest tests/test_transcription.py -v
python -m pytest tests/test_summarization.py -v

# Manual service testing with sample data
python tests/test_summarization_manual.py
```

**Pipeline Testing:**
```bash
# Test complete transcription → summarization pipeline
python tests/test_full_pipeline.py

# Test Celery task processing (without Redis)
python tests/test_celery_tasks.py
```

**Run All Unit Tests:**
```bash
python -m pytest tests/ -v
```

## Development Workflow

### Testing Organization
All tests are organized in the `tests/` directory for better maintainability:
- **Unit tests**: Individual service testing with pytest
- **Integration tests**: Full pipeline and API endpoint testing  
- **Manual tests**: Interactive testing scripts for development
- **Task tests**: Celery background processing validation

### Workspace Structure
The project follows a clean separation of concerns:
- `app/`: Core application code with services and models
- `tests/`: Comprehensive test suite
- `.kiro/specs/`: Project specification and requirements
- `start_worker.py`: Celery worker management script

## Specification

This project includes a complete specification in `.kiro/specs/audio-transcription-summarizer/` with:
- Requirements document
- System design  
- Implementation tasks

