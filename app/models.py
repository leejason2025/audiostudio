from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from sqlalchemy import Column, String, Text, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import uuid

# Pydantic models for API requests and responses
class UploadResponse(BaseModel):
    job_id: str
    status: str

class ProcessingResult(BaseModel):
    job_id: str
    status: str
    transcription: Optional[str] = None
    summary: Optional[str] = None
    error_message: Optional[str] = None

class ErrorResponse(BaseModel):
    error_message: str
    job_id: Optional[str] = None

# SQLAlchemy setup
Base = declarative_base()

class ProcessingJob(Base):
    __tablename__ = "processing_jobs"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")  # pending, processing, completed, failed
    transcription = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)