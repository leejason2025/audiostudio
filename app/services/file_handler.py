import os
import shutil
from typing import Tuple
from fastapi import UploadFile, HTTPException
from app.config import settings


class FileHandler:
    """Handles file upload validation and storage"""
    
    @staticmethod
    def validate_mp3_file(file: UploadFile) -> None:
        """Validate that the uploaded file is a valid MP3 file"""
        # Check file extension
        if not file.filename or not file.filename.lower().endswith('.mp3'):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Only MP3 files are allowed."
            )
        
        # Check content type (allow if not specified or if it's audio)
        # Some browsers/clients might not send correct MIME type
        if file.content_type and file.content_type not in ['application/octet-stream', 'audio/mpeg', 'audio/mp3']:
            # Only reject if it's clearly not an audio file
            if not file.content_type.startswith('audio/') and file.content_type != 'application/octet-stream':
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only audio files are allowed."
                )
    
    @staticmethod
    def validate_file_size(file: UploadFile) -> None:
        """Validate file size against configured limits"""
        if file.size and file.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds limit of {settings.MAX_FILE_SIZE_MB}MB"
            )
    
    @staticmethod
    def ensure_upload_directory() -> None:
        """Ensure the upload directory exists"""
        os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    @staticmethod
    def save_uploaded_file(file: UploadFile, job_id: str) -> str:
        """Save uploaded file to temporary directory and return file path"""
        FileHandler.ensure_upload_directory()
        
        # Create unique filename using job_id
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.mp3'
        filename = f"{job_id}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        
        return file_path
    
    @staticmethod
    def cleanup_file(file_path: str) -> None:
        """Remove file from temporary storage"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            # Log error but don't raise - cleanup failures shouldn't break the flow
            pass