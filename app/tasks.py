import os
from typing import Dict, Any
from celery import current_task
from sqlalchemy.orm import Session

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import ProcessingJob
from app.services.transcription import get_transcription_service
from app.services.summarization import get_summarization_service


def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status in database"""
    db: Session = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.status = status
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
            db.commit()
            db.refresh(job)  # Refresh to get updated values
    finally:
        db.close()


@celery_app.task(bind=True)
def process_audio_file(self, job_id: str, file_path: str) -> Dict[str, Any]:
    """
    Process audio file: transcription → summarization
    
    Args:
        job_id: Unique identifier for the processing job
        file_path: Path to the uploaded MP3 file
        
    Returns:
        Dict containing processing results
    """
    try:
        # Update status to processing
        update_job_status(job_id, "processing")
        
        # Step 1: Transcribe audio
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 1, "total": 2, "status": "Transcribing audio..."}
        )
        
        transcription_service = get_transcription_service()
        transcription = transcription_service.transcribe_audio(file_path)
        
        if not transcription:
            raise Exception("Transcription failed - no text returned")
        
        # Update job with transcription
        update_job_status(job_id, "processing", transcription=transcription)
        
        # Step 2: Generate summary
        current_task.update_state(
            state="PROGRESS", 
            meta={"current": 2, "total": 2, "status": "Generating summary..."}
        )
        
        summarization_service = get_summarization_service()
        summary = summarization_service.summarize_text(transcription)
        
        if not summary:
            raise Exception("Summarization failed - no summary returned")
        
        # Update job as completed
        update_job_status(
            job_id, 
            "completed", 
            transcription=transcription,
            summary=summary
        )
        
        # Clean up uploaded file
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as cleanup_error:
            print(f"Warning: Failed to clean up file {file_path}: {cleanup_error}")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "transcription": transcription,
            "summary": summary
        }
        
    except Exception as e:
        error_message = str(e)
        
        # Update job as failed
        update_job_status(job_id, "failed", error_message=error_message)
        
        # Clean up uploaded file even on failure
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as cleanup_error:
            print(f"Warning: Failed to clean up file {file_path}: {cleanup_error}")
        
        # Re-raise the exception so Celery marks the task as failed
        raise Exception(f"Audio processing failed: {error_message}")