import os
import logging
from typing import Dict, Any
from celery import current_task
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.celery_app import celery_app
from app.database import SessionLocal
from app.models import ProcessingJob
from app.services.transcription import get_transcription_service
from app.services.summarization import get_summarization_service
from app.services.file_handler import FileHandler

# Set up logging
logger = logging.getLogger(__name__)


def update_job_status(job_id: str, status: str, **kwargs):
    """Update job status in database with enhanced error handling"""
    db: Session = SessionLocal()
    try:
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            logger.info(f"Updating job {job_id} status to: {status}")
            job.status = status
            for key, value in kwargs.items():
                if hasattr(job, key):
                    setattr(job, key, value)
                    logger.debug(f"Updated job {job_id} field {key}")
            db.commit()
            db.refresh(job)  # Refresh to get updated values
            logger.info(f"Successfully updated job {job_id} status")
        else:
            logger.error(f"Job {job_id} not found in database")
            raise ValueError(f"Job {job_id} not found")
    except SQLAlchemyError as e:
        logger.error(f"Database error updating job {job_id}: {str(e)}")
        db.rollback()
        raise Exception(f"Database error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error updating job {job_id}: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def cleanup_file_safe(file_path: str, job_id: str) -> bool:
    """
    Safely clean up uploaded file with comprehensive error handling
    
    Args:
        file_path: Path to the file to clean up
        job_id: Job ID for logging context
        
    Returns:
        bool: True if cleanup was successful, False otherwise
    """
    try:
        if not file_path:
            logger.warning(f"Job {job_id}: No file path provided for cleanup")
            return False
            
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Job {job_id}: Successfully cleaned up file: {file_path}")
            return True
        else:
            logger.warning(f"Job {job_id}: File not found for cleanup: {file_path}")
            return False
            
    except PermissionError as e:
        logger.error(f"Job {job_id}: Permission denied cleaning up file {file_path}: {str(e)}")
        return False
    except OSError as e:
        logger.error(f"Job {job_id}: OS error cleaning up file {file_path}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Job {job_id}: Unexpected error cleaning up file {file_path}: {str(e)}")
        return False


@celery_app.task(bind=True)
def process_audio_file(self, job_id: str, file_path: str) -> Dict[str, Any]:
    """
    Process audio file: transcription → summarization with comprehensive error handling
    
    Args:
        job_id: Unique identifier for the processing job
        file_path: Path to the uploaded MP3 file
        
    Returns:
        Dict containing processing results
        
    Raises:
        Exception: For any processing failures
    """
    logger.info(f"Starting audio processing for job {job_id}, file: {file_path}")
    
    transcription = None
    summary = None
    
    try:
        # Validate file exists before processing
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Audio file not found: {file_path}")
        
        # Update status to processing
        update_job_status(job_id, "processing")
        logger.info(f"Job {job_id}: Status updated to processing")
        
        # Step 1: Transcribe audio
        logger.info(f"Job {job_id}: Starting transcription")
        current_task.update_state(
            state="PROGRESS",
            meta={"current": 1, "total": 2, "status": "Transcribing audio..."}
        )
        
        try:
            transcription_service = get_transcription_service()
            transcription = transcription_service.transcribe_audio(file_path)
            
            if not transcription or not transcription.strip():
                raise Exception("Transcription failed - no text returned")
            
            logger.info(f"Job {job_id}: Transcription completed successfully ({len(transcription)} characters)")
            
            # Update job with transcription
            update_job_status(job_id, "processing", transcription=transcription)
            
        except Exception as e:
            logger.error(f"Job {job_id}: Transcription failed: {str(e)}")
            raise Exception(f"Transcription failed: {str(e)}")
        
        # Step 2: Generate summary
        logger.info(f"Job {job_id}: Starting summarization")
        current_task.update_state(
            state="PROGRESS", 
            meta={"current": 2, "total": 2, "status": "Generating summary..."}
        )
        
        try:
            summarization_service = get_summarization_service()
            summary = summarization_service.summarize_text(transcription)
            
            if not summary or not summary.strip():
                logger.warning(f"Job {job_id}: Summarization returned empty result, using fallback")
                summary = "Summary could not be generated, but transcription is available."
            
            logger.info(f"Job {job_id}: Summarization completed successfully ({len(summary)} characters)")
            
        except Exception as e:
            logger.error(f"Job {job_id}: Summarization failed: {str(e)}")
            # Don't fail the entire job if only summarization fails
            summary = f"Summary generation failed: {str(e)}"
            logger.info(f"Job {job_id}: Continuing with transcription only")
        
        # Update job as completed
        update_job_status(
            job_id, 
            "completed", 
            transcription=transcription,
            summary=summary
        )
        
        logger.info(f"Job {job_id}: Processing completed successfully")
        
        # Clean up uploaded file
        cleanup_success = cleanup_file_safe(file_path, job_id)
        if not cleanup_success:
            logger.warning(f"Job {job_id}: File cleanup failed, but processing was successful")
        
        return {
            "job_id": job_id,
            "status": "completed",
            "transcription": transcription,
            "summary": summary
        }
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"Job {job_id}: Processing failed with error: {error_message}")
        
        try:
            # Update job as failed
            update_job_status(job_id, "failed", error_message=error_message)
            logger.info(f"Job {job_id}: Status updated to failed")
        except Exception as db_error:
            logger.error(f"Job {job_id}: Failed to update job status to failed: {str(db_error)}")
        
        # Clean up uploaded file even on failure
        cleanup_success = cleanup_file_safe(file_path, job_id)
        if cleanup_success:
            logger.info(f"Job {job_id}: File cleanup completed after failure")
        else:
            logger.error(f"Job {job_id}: File cleanup failed after processing failure")
        
        # Re-raise the exception so Celery marks the task as failed
        raise Exception(f"Audio processing failed for job {job_id}: {error_message}")