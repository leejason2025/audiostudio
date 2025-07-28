# 🎵 Audio Transcription Summarizer (Talkyy)

A modern, AI-powered web application that converts MP3 audio files into text transcriptions and generates concise summaries using OpenAI's Whisper and GPT models.

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
│   ├── templates/
│   │   └── index.html       # Web interface template
│   ├── static/
│   │   └── talkyy.png       # Application logo
│   └── services/
│       ├── __init__.py
│       ├── transcription.py # OpenAI Whisper integration
│       ├── summarization.py # OpenAI GPT integration
│       └── file_handler.py  # File upload and validation
├── tests/
│   ├── __init__.py
│   ├── test_api_endpoints.py    # API endpoint tests
│   ├── test_transcription.py    # Transcription service unit tests
│   ├── test_summarization.py    # Summarization service unit tests
│   ├── test_celery_tasks.py     # Celery task processing tests
│   ├── test_full_pipeline.py    # End-to-end pipeline tests
│   ├── test_core_workflow.py    # Core workflow tests
│   ├── test_upload_workflow.py  # Upload workflow tests
│   └── test_status_result_endpoints.py  # Status and result endpoint tests
├── uploads/             # Temporary file storage (gitignored)
├── .kiro/specs/         # Project specification documents
├── run_app.py           # Simple app launcher script
├── start_worker.py      # Celery worker startup script
├── Dockerfile           # Docker container configuration
├── docker-compose.yml   # Docker Compose setup
├── .env.example         # Environment variables template
└── requirements.txt     # Python dependencies
```

## 🚀 Quick Start

The fastest way to get started:

```bash
# 1. Clone and setup
git clone <your-repo-url>
cd audiostudio

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# 4. Start Redis (macOS)
brew install redis
brew services start redis

# 5. Run the application
python run_app.py
```

Then open http://localhost:8000 in your browser and start uploading MP3 files!

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

## Docker Deployment

### Quick Start with Docker Compose

1. Clone the repository and navigate to the project directory

2. Copy the environment file:
   ```bash
   cp .env.example .env
   ```

3. Edit `.env` and add your OpenAI API key:
   ```
   OPENAI_API_KEY=sk-your-actual-openai-api-key-here
   ```

4. Build and start all services:
   ```bash
   docker-compose up --build
   ```

This will start:
- Redis server for task queue
- FastAPI application on port 8000
- Celery worker for background processing

The application will be available at http://localhost:8000

### Manual Docker Build

If you prefer to build and run containers manually:

1. Build the Docker image:
   ```bash
   docker build -t audio-transcription-summarizer .
   ```

2. Start Redis:
   ```bash
   docker run -d --name redis -p 6379:6379 redis:7-alpine
   ```

3. Run the application:
   ```bash
   docker run -d --name app -p 8000:8000 --env-file .env \
     --link redis:redis \
     -e REDIS_URL=redis://redis:6379 \
     audio-transcription-summarizer
   ```

4. Start the worker:
   ```bash
   docker run -d --name worker --env-file .env \
     --link redis:redis \
     -e REDIS_URL=redis://redis:6379 \
     audio-transcription-summarizer python start_worker.py
   ```

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

## Deployment

### Production Considerations

For production deployment, consider:

1. **Environment Variables**: Ensure all required environment variables are properly set
2. **Database**: Consider using PostgreSQL instead of SQLite for production
3. **Redis**: Use a managed Redis service or configure Redis persistence
4. **File Storage**: Consider using cloud storage (AWS S3, etc.) instead of local filesystem
5. **Monitoring**: Add application monitoring and logging
6. **Security**: Implement proper authentication and rate limiting

### Environment Variables Reference

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for Whisper and GPT | - | Yes |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` | Yes |
| `DATABASE_URL` | Database connection URL | `sqlite:///./app.db` | No |
| `UPLOAD_DIR` | Directory for temporary file storage | `./uploads` | No |
| `MAX_FILE_SIZE_MB` | Maximum upload file size in MB | `50` | No |
| `LOG_LEVEL` | Application logging level | `INFO` | No |

### Health Check

The application provides a health check endpoint at `/health` that verifies:
- Application status
- OpenAI API key configuration
- Database connectivity

Use this endpoint for container health checks and monitoring.

