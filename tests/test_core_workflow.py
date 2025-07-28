"""
Test core workflow functionality without API endpoints
"""
import pytest
import os
import tempfile
import uuid
from unittest.mock import patch, Mock, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import get_db
from app.models import Base, ProcessingJob
from app.services.file_handler import FileHandler
from app.tasks import process_audio_file, update_job_status
from app.services.transcription import TranscriptionService
from app.services.summarization import SummarizationService

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_core_workflow.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


class TestCoreWorkflow:
    """Test cases for core workflow functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        # Create mock MP3 content
        self.mock_mp3_content = b"ID3\x03\x00\x00\x00" + b"fake mp3 content for testing" * 50
        
        # Create test uploads directory
        self.test_uploads_dir = "test_uploads"
        os.makedirs(self.test_uploads_dir, exist_ok=True)
    
    def teardown_method(self):
        """Clean up after tests"""
        # Clean up test uploads directory
        if os.path.exists(self.test_uploads_dir):
            for file in os.listdir(self.test_uploads_dir):
                try:
                    os.remove(os.path.join(self.test_uploads_dir, file))
                except:
                    pass
            try:
                os.rmdir(self.test_uploads_dir)
            except:
                pass
    
    def test_file_handler_validation(self):
        """Test FileHandler validation methods"""
        # Test valid MP3 file
        valid_file = Mock()
        valid_file.filename = "test.mp3"
        valid_file.content_type = "audio/mpeg"
        valid_file.size = 1024 * 1024  # 1MB
        
        # Should not raise exception
        try:
            FileHandler.validate_mp3_file(valid_file)
            FileHandler.validate_file_size(valid_file)
            assert True  # Validation passed
        except Exception:
            assert False, "Valid file should pass validation"
        
        # Test invalid file format
        invalid_file = Mock()
        invalid_file.filename = "test.txt"
        invalid_file.content_type = "text/plain"
        
        with pytest.raises(Exception):
            FileHandler.validate_mp3_file(invalid_file)
        
        # Test oversized file
        large_file = Mock()
        large_file.filename = "large.mp3"
        large_file.content_type = "audio/mpeg"
        large_file.size = 30 * 1024 * 1024  # 30MB
        
        with pytest.raises(Exception):
            FileHandler.validate_file_size(large_file)
    
    def test_job_status_update(self):
        """Test job status update functionality"""
        # Create a test job in database
        db = TestingSessionLocal()
        job_id = str(uuid.uuid4())
        job = ProcessingJob(
            id=job_id,
            filename="test.mp3",
            status="pending"
        )
        db.add(job)
        db.commit()
        db.close()
        
        # Test updating job status
        update_job_status(job_id, "processing")
        
        # Verify job was updated
        db = TestingSessionLocal()
        updated_job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        assert updated_job.status == "processing"
        db.close()
        
        # Test updating with additional fields
        update_job_status(job_id, "completed", transcription="Test transcription", summary="Test summary")
        
        # Verify additional fields were updated
        db = TestingSessionLocal()
        final_job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        assert final_job.status == "completed"
        assert final_job.transcription == "Test transcription"
        assert final_job.summary == "Test summary"
        db.close()
    
    @patch('app.services.transcription.get_transcription_service')
    @patch('app.services.summarization.get_summarization_service')
    def test_successful_processing_workflow(self, mock_summarization_service, mock_transcription_service):
        """Test successful end-to-end processing workflow"""
        # Create a test job in database
        db = TestingSessionLocal()
        job_id = str(uuid.uuid4())
        job = ProcessingJob(
            id=job_id,
            filename="test.mp3",
            status="pending"
        )
        db.add(job)
        db.commit()
        db.close()
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(self.mock_mp3_content)
            temp_file_path = temp_file.name
        
        try:
            # Mock services
            mock_transcription = Mock()
            mock_transcription.transcribe_audio.return_value = "This is a test transcription from the audio file."
            mock_transcription_service.return_value = mock_transcription
            
            mock_summarization = Mock()
            mock_summarization.summarize_text.return_value = "This is a test summary of the transcription."
            mock_summarization_service.return_value = mock_summarization
            
            # Execute the processing task
            result = process_audio_file(job_id, temp_file_path)
            
            # Verify result
            assert result["status"] == "completed"
            assert result["transcription"] == "This is a test transcription from the audio file."
            assert result["summary"] == "This is a test summary of the transcription."
            
            # Verify job was updated in database
            db = TestingSessionLocal()
            updated_job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            assert updated_job.status == "completed"
            assert updated_job.transcription == "This is a test transcription from the audio file."
            assert updated_job.summary == "This is a test summary of the transcription."
            db.close()
            
            # Verify services were called correctly
            mock_transcription.transcribe_audio.assert_called_once_with(temp_file_path)
            mock_summarization.summarize_text.assert_called_once_with("This is a test transcription from the audio file.")
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    @patch('app.services.transcription.get_transcription_service')
    def test_transcription_failure_workflow(self, mock_transcription_service):
        """Test workflow when transcription fails"""
        # Create a test job in database
        db = TestingSessionLocal()
        job_id = str(uuid.uuid4())
        job = ProcessingJob(
            id=job_id,
            filename="test.mp3",
            status="pending"
        )
        db.add(job)
        db.commit()
        db.close()
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(self.mock_mp3_content)
            temp_file_path = temp_file.name
        
        try:
            # Mock transcription service to fail
            mock_transcription = Mock()
            mock_transcription.transcribe_audio.side_effect = Exception("Transcription API failed")
            mock_transcription_service.return_value = mock_transcription
            
            # Execute the task - should raise exception
            with pytest.raises(Exception, match="Transcription API failed"):
                process_audio_file(job_id, temp_file_path)
            
            # Verify job was marked as failed
            db = TestingSessionLocal()
            failed_job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            assert failed_job.status == "failed"
            assert "Transcription API failed" in failed_job.error_message
            db.close()
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    @patch('app.services.transcription.get_transcription_service')
    @patch('app.services.summarization.get_summarization_service')
    def test_summarization_failure_workflow(self, mock_summarization_service, mock_transcription_service):
        """Test workflow when summarization fails but transcription succeeds"""
        # Create a test job in database
        db = TestingSessionLocal()
        job_id = str(uuid.uuid4())
        job = ProcessingJob(
            id=job_id,
            filename="test.mp3",
            status="pending"
        )
        db.add(job)
        db.commit()
        db.close()
        
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_file.write(self.mock_mp3_content)
            temp_file_path = temp_file.name
        
        try:
            # Mock transcription to succeed
            mock_transcription = Mock()
            mock_transcription.transcribe_audio.return_value = "This is a successful transcription."
            mock_transcription_service.return_value = mock_transcription
            
            # Mock summarization to fail
            mock_summarization = Mock()
            mock_summarization.summarize_text.side_effect = Exception("Summarization API failed")
            mock_summarization_service.return_value = mock_summarization
            
            # Execute the task - should complete with transcription only
            result = process_audio_file(job_id, temp_file_path)
            
            # Verify result - should be completed with transcription but failed summary
            assert result["status"] == "completed"
            assert result["transcription"] == "This is a successful transcription."
            assert "Summarization API failed" in result["summary"]
            
            # Verify job was updated in database
            db = TestingSessionLocal()
            updated_job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            assert updated_job.status == "completed"
            assert updated_job.transcription == "This is a successful transcription."
            assert "Summarization API failed" in updated_job.summary
            db.close()
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def test_service_integration(self):
        """Test that services can be instantiated and have expected methods"""
        # Test transcription service
        with patch('app.services.transcription.settings.OPENAI_API_KEY', 'test-key'):
            transcription_service = TranscriptionService()
            assert hasattr(transcription_service, 'transcribe_audio')
            assert hasattr(transcription_service, 'validate_api_key')
        
        # Test summarization service
        with patch('app.services.summarization.settings.OPENAI_API_KEY', 'test-key'):
            summarization_service = SummarizationService()
            assert hasattr(summarization_service, 'summarize_text')
            assert hasattr(summarization_service, 'validate_api_key')
    
    def test_file_cleanup_functionality(self):
        """Test file cleanup functionality"""
        from app.tasks import cleanup_file_safe
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test content")
            temp_file_path = temp_file.name
        
        # Verify file exists
        assert os.path.exists(temp_file_path)
        
        # Test cleanup
        result = cleanup_file_safe(temp_file_path, "test-job-id")
        assert result is True
        assert not os.path.exists(temp_file_path)
        
        # Test cleanup of non-existent file
        result = cleanup_file_safe("/nonexistent/file.mp3", "test-job-id")
        assert result is False


if __name__ == "__main__":
    # Clean up test database if it exists
    if os.path.exists("test_core_workflow.db"):
        os.remove("test_core_workflow.db")
    
    print("🧪 Running Core Workflow Tests")
    
    test_instance = TestCoreWorkflow()
    
    tests = [
        ("File handler validation", test_instance.test_file_handler_validation),
        ("Job status update", test_instance.test_job_status_update),
        ("Successful processing workflow", test_instance.test_successful_processing_workflow),
        ("Transcription failure workflow", test_instance.test_transcription_failure_workflow),
        ("Summarization failure workflow", test_instance.test_summarization_failure_workflow),
        ("Service integration", test_instance.test_service_integration),
        ("File cleanup functionality", test_instance.test_file_cleanup_functionality),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_instance.setup_method()
            test_func()
            test_instance.teardown_method()
            print(f"✅ {test_name} - PASSED")
            passed += 1
        except Exception as e:
            test_instance.teardown_method()
            print(f"❌ {test_name} - FAILED: {e}")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    # Clean up
    if os.path.exists("test_core_workflow.db"):
        os.remove("test_core_workflow.db")