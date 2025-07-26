from sqlalchemy.orm import Session
from app.models import ProcessingJob
import uuid

class JobCRUD:
    """CRUD operations for ProcessingJob"""
    
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
    def get_job(db: Session, job_id: str) -> ProcessingJob:
        """Get a job by ID"""
        return db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
    
    @staticmethod
    def update_job_status(db: Session, job_id: str, status: str, error_message: str = None) -> ProcessingJob:
        """Update job status"""
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.status = status
            if error_message:
                job.error_message = error_message
            db.commit()
            db.refresh(job)
        return job
    
    @staticmethod
    def update_job_transcription(db: Session, job_id: str, transcription: str) -> ProcessingJob:
        """Update job with transcription result"""
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.transcription = transcription
            job.status = "transcribed"
            db.commit()
            db.refresh(job)
        return job
    
    @staticmethod
    def update_job_summary(db: Session, job_id: str, summary: str) -> ProcessingJob:
        """Update job with summary result"""
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        if job:
            job.summary = summary
            job.status = "completed"
            db.commit()
            db.refresh(job)
        return job