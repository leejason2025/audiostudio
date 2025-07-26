from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import create_tables, get_db
from app.models import UploadResponse, ErrorResponse
from app.crud import JobCRUD
from app.services.file_handler import FileHandler

app = FastAPI(
    title="Audio Transcription Summarizer",
    description="API for transcribing MP3 files and generating summaries",
    version="1.0.0"
)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/")
async def root():
    return {"message": "Audio Transcription Summarizer API"}

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