import os
import shutil
import logging
from typing import Tuple
from fastapi import UploadFile, HTTPException
from app.config import settings

# Set up logging
logger = logging.getLogger(__name__)


class FileHandler:
    """Handles file upload validation and storage"""
    
    @staticmethod
    def validate_mp3_file(file: UploadFile) -> None:
        """Validate that the uploaded file is a valid MP3 file"""
        logger.debug(f"Validating MP3 file: {file.filename}, content_type: {file.content_type}")
        
        # Check file extension
        if not file.filename or not file.filename.lower().endswith('.mp3'):
            logger.warning(f"Invalid file extension for file: {file.filename}")
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Only MP3 files are allowed."
            )
        
        # Check content type (allow if not specified or if it's audio)
        # Some browsers/clients might not send correct MIME type
        if file.content_type and file.content_type not in ['application/octet-stream', 'audio/mpeg', 'audio/mp3']:
            # Only reject if it's clearly not an audio file
            if not file.content_type.startswith('audio/') and file.content_type != 'application/octet-stream':
                logger.warning(f"Invalid content type for file {file.filename}: {file.content_type}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid file type. Only audio files are allowed."
                )
        
        logger.debug(f"MP3 file validation passed for: {file.filename}")
    
    @staticmethod
    def validate_file_size(file: UploadFile) -> None:
        """Validate file size against configured limits"""
        if file.size:
            size_mb = file.size / (1024 * 1024)
            logger.debug(f"File {file.filename} size: {size_mb:.2f}MB")
            
            if file.size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
                logger.warning(f"File {file.filename} exceeds size limit: {size_mb:.2f}MB > {settings.MAX_FILE_SIZE_MB}MB")
                raise HTTPException(
                    status_code=413,
                    detail=f"File size exceeds limit of {settings.MAX_FILE_SIZE_MB}MB"
                )
        else:
            logger.debug(f"File {file.filename} size not provided by client")
    
    @staticmethod
    def ensure_upload_directory() -> None:
        """Ensure the upload directory exists"""
        try:
            os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
            logger.debug(f"Upload directory ensured: {settings.UPLOAD_DIR}")
        except Exception as e:
            logger.error(f"Failed to create upload directory {settings.UPLOAD_DIR}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create upload directory: {str(e)}"
            )
    
    @staticmethod
    def save_uploaded_file(file: UploadFile, job_id: str) -> str:
        """Save uploaded file to temporary directory and return file path"""
        FileHandler.ensure_upload_directory()
        
        # Create unique filename using job_id
        file_extension = os.path.splitext(file.filename)[1] if file.filename else '.mp3'
        filename = f"{job_id}{file_extension}"
        file_path = os.path.join(settings.UPLOAD_DIR, filename)
        
        logger.info(f"Saving uploaded file for job {job_id} to: {file_path}")
        
        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Verify file was saved successfully
            if not os.path.exists(file_path):
                raise Exception("File was not saved successfully")
            
            file_size = os.path.getsize(file_path)
            logger.info(f"Successfully saved file for job {job_id}: {file_path} ({file_size} bytes)")
            
        except PermissionError as e:
            logger.error(f"Permission denied saving file for job {job_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Permission denied saving file: {str(e)}"
            )
        except OSError as e:
            logger.error(f"OS error saving file for job {job_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"System error saving file: {str(e)}"
            )
        except Exception as e:
            logger.error(f"Unexpected error saving file for job {job_id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save file: {str(e)}"
            )
        
        return file_path
    
    @staticmethod
    def cleanup_file(file_path: str) -> bool:
        """
        Remove file from temporary storage with enhanced error handling
        
        Args:
            file_path: Path to the file to remove
            
        Returns:
            bool: True if cleanup was successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Successfully cleaned up file: {file_path}")
                return True
            else:
                logger.warning(f"File not found for cleanup: {file_path}")
                return False
        except PermissionError as e:
            logger.error(f"Permission denied cleaning up file {file_path}: {str(e)}")
            return False
        except OSError as e:
            logger.error(f"OS error cleaning up file {file_path}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error cleaning up file {file_path}: {str(e)}")
            return False