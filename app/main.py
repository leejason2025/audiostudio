from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from app.database import create_tables, get_db
from app.models import UploadResponse, ErrorResponse, ProcessingResult
from app.crud import JobCRUD
from app.services.file_handler import FileHandler
from app.tasks import process_audio_file
from app.config import settings
import logging

# Get logger (logging is configured in config.py)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Audio Transcription Summarizer",
    description="API for transcribing MP3 files and generating summaries",
    version="1.0.0"
)

# Set up templates and static files
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

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

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Serve the main web interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api")
async def api_root():
    """API endpoint for programmatic access"""
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
    logger.info(f"Upload request received for file: {file.filename}")
    
    try:
        # Validate file format
        FileHandler.validate_mp3_file(file)
        logger.debug(f"File format validation passed for: {file.filename}")
        
        # Validate file size
        FileHandler.validate_file_size(file)
        logger.debug(f"File size validation passed for: {file.filename}")
        
        # Create job record in database
        job = JobCRUD.create_job(db, filename=file.filename or "unknown.mp3")
        logger.info(f"Created job {job.id} for file: {file.filename}")
        
        # Save uploaded file
        file_path = FileHandler.save_uploaded_file(file, job.id)
        logger.info(f"Saved file for job {job.id} at: {file_path}")
        
        # Start asynchronous processing with Celery
        task = process_audio_file.delay(job.id, file_path)
        logger.info(f"Started processing task {task.id} for job {job.id}")
        
        return UploadResponse(
            job_id=job.id,
            status=job.status
        )
        
    except HTTPException as e:
        logger.warning(f"Upload validation failed for {file.filename}: {e.detail}")
        # Re-raise HTTP exceptions (validation errors)
        raise
    except Exception as e:
        logger.error(f"Unexpected error during upload for {file.filename}: {str(e)}")
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process upload: {str(e)}"
        )

@app.get("/status/{job_id}")
async def get_status(job_id: str, db: Session = Depends(get_db)):
    """
    Check the processing status of a job.
    
    Returns the current status of the processing job.
    """
    logger.debug(f"Status request for job: {job_id}")
    
    try:
        # Get job from database
        job = JobCRUD.get_job(db, job_id)
        
        if not job:
            logger.warning(f"Job not found: {job_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Job with ID {job_id} not found"
            )
        
        logger.debug(f"Job {job_id} status: {job.status}")
        
        return {
            "job_id": job.id,
            "status": job.status,
            "filename": job.filename,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "error_message": job.error_message
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting status for job {job_id}: {str(e)}")
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job status: {str(e)}"
        )

@app.get("/result/{job_id}")
async def get_result(job_id: str, db: Session = Depends(get_db)):
    """
    Retrieve the transcription and summary results for a completed job.
    
    Returns the full transcription and summary if processing is complete.
    """
    logger.debug(f"Result request for job: {job_id}")
    
    try:
        # Get job from database
        job = JobCRUD.get_job(db, job_id)
        
        if not job:
            logger.warning(f"Job not found for result request: {job_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Job with ID {job_id} not found"
            )
        
        logger.debug(f"Job {job_id} result status: {job.status}")
        
        result = {
            "job_id": job.id,
            "status": job.status,
            "transcript": job.transcription,  # Frontend expects 'transcript'
            "summary": job.summary,
            "error_message": job.error_message
        }
        
        logger.info(f"Returning result for job {job_id}: transcript length={len(job.transcription or '')}, summary length={len(job.summary or '')}")
        
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting result for job {job_id}: {str(e)}")
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get job result: {str(e)}"
        )