from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import create_tables, get_db
from app.models import UploadResponse, ErrorResponse
from app.crud import JobCRUD
from app.services.file_handler import FileHandler
from app.tasks import process_audio_file
from app.config import settings
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audio Transcription Summarizer",
    description="API for transcribing MP3 files and generating summaries",
    version="1.0.0"
)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()
    
    # Validate OpenAI API key is configured
    if not settings.OPENAI_API_KEY:
        logger.error("OPENAI_API_KEY environment variable is not set!")
        logger.error("Please set your OpenAI API key in the .env file or environment variables.")
        logger.error("Get your API key from: https://platform.openai.com/api-keys")
        raise ValueError("OPENAI_API_KEY is required for the application to function")
    
    logger.info("✓ OpenAI API key is configured")
    
    # Test the API key validity
    try:
        from app.services.transcription import get_transcription_service
        service = get_transcription_service()
        if service.validate_api_key():
            logger.info("✓ OpenAI API key is valid")
        else:
            logger.warning("⚠ OpenAI API key validation failed - please check your key")
    except Exception as e:
        logger.warning(f"⚠ Could not validate OpenAI API key: {e}")

@app.get("/")
async def root():
    return {"message": "Audio Transcription Summarizer API"}

@app.get("/health")
async def health_check():
    """Health check endpoint that includes API key validation status"""
    health_status = {
        "status": "healthy",
        "openai_api_key_configured": bool(settings.OPENAI_API_KEY),
        "openai_api_key_valid": False
    }
    
    if settings.OPENAI_API_KEY:
        try:
            from app.services.transcription import get_transcription_service
            service = get_transcription_service()
            health_status["openai_api_key_valid"] = service.validate_api_key()
        except Exception as e:
            health_status["openai_api_key_error"] = str(e)
    
    return health_status

@app.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an MP3 file for transcription and summarization.
    
    Returns a job ID that can be used to track processing status and retrieve results.
    """
    try:
        # Validate file format
        FileHandler.validate_mp3_file(file)
        
        # Validate file size
        FileHandler.validate_file_size(file)
        
        # Create job record in database
        job = JobCRUD.create_job(db, filename=file.filename or "unknown.mp3")
        
        # Save uploaded file
        file_path = FileHandler.save_uploaded_file(file, job.id)
        
        # Start asynchronous processing with Celery
        process_audio_file.delay(job.id, file_path)
        
        return UploadResponse(
            job_id=job.id,
            status=job.status
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process upload: {str(e)}"
        )