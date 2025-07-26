from sqlalchemy.orm import Session
from app.models import ProcessingJob
from typing import Optional
import uuid

class JobCRUD:
    """Basic CRUD operations for ProcessingJob"""
    
    @staticmethod
    def create_job(db: Session, filename: str) -> ProcessingJob:
        """Create a new processing job"""
        job = ProcessingJob(
            id=str(uuid.uuid4()),
            filename=filename,
            status="pending"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        return job
    
    @staticmethod
    def get_job(db: Session, job_id: str) -> Optional[ProcessingJob]:
        """Get a job by ID"""
        return db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    
    @staticmethod
    def update_job_status(db: Session, job_id: str, status: str) -> Optional[ProcessingJob]:
        """Update job status"""
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.status = status
            db.commit()
            db.refresh(job)
        return job
    
    @staticmethod
    def update_job_results(
        db: Session, 
        job_id: str, 
        transcription: Optional[str] = None,
        summary: Optional[str] = None,
        error_message: Optional[str] = None,
        status: str = "completed"
    ) -> Optional[ProcessingJob]:
        """Update job with processing results"""
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            if transcription is not None:
                job.transcription = transcription
            if summary is not None:
                job.summary = summary
            if error_message is not None:
                job.error_message = error_message
            job.status = status
            db.commit()
            db.refresh(job)
        return job
    
    @staticmethod
    def delete_job(db: Session, job_id: str) -> bool:
        """Delete a job"""
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            db.delete(job)
            db.commit()
            return True
        return False