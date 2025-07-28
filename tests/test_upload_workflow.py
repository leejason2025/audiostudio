"""
Test file upload and processing workflow
"""
import pytest
import io
import os
import tempfile
import time
from unittest.mock import patch, Mock, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models import Base, ProcessingJob
from app.services.file_handler import FileHandler
from app.tasks import process_audio_file
import uuid

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_upload_workflow.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# Override the database dependency
app.dependency_overrides[get_db] = override_get_db

# Test client will be created in each test method


class TestUploadWorkflow:
    """Test cases for file upload and processing workflow"""
    
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
        FileHandler.validate_mp3_file(valid_file)
        FileHandler.validate_file_size(valid_file)
        
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
    
    @patch('app.services.file_handler.FileHandler.save_uploaded_file')
    @patch('app.tasks.process_audio_file.delay')
    def test_complete_upload_workflow(self, mock_task, mock_save_file):
        """Test complete upload workflow from file upload to job creation"""
        # Mock file save
        test_file_path = f"{self.test_uploads_dir}/test-file.mp3"
        mock_save_file.return_value = test_file_path
        
        # Mock Celery task
        mock_task_result = Mock()
        mock_task_result.id = "task-123"
        mock_task.return_value = mock_task_result
        
        # Upload file
        files = {
            'file': ('test.mp3', io.BytesIO(self.mock_mp3_content), 'audio/mpeg')
        }
        
        with TestClient(app) as client:
            response = client.post("/upload", files=files)
        
        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        
        job_id = data["job_id"]
        
        # Verify job was created in database
        db = TestingSessionLocal()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        assert job is not None
        assert job.filename == "test.mp3"
        assert job.status == "pending"
        db.close()
        
        # Verify file save was called
        mock_save_file.assert_called_once()
        
        # Verify task was started
        mock_task.assert_called_once_with(job_id, test_file_path)
        
        # Test status endpoint
        with TestClient(app) as client:
            status_response = client.get(f"/status/{job_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["job_id"] == job_id
            assert status_data["status"] == "pending"
    
    @patch('app.services.transcription.get_transcription_service')
    @patch('app.services.summarization.get_summarization_service')
    def test_processing_task_success(self, mock_summarization_service, mock_transcription_service):
        """Test successful processing task execution"""
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
            mock_transcription.transcribe_audio.return_value = "This is a test transcription"
            mock_transcription_service.return_value = mock_transcription
            
            mock_summarization = Mock()
            mock_summarization.summarize_text.return_value = "This is a test summary"
            mock_summarization_service.return_value = mock_summarization
            
            # Execute the task
            result = process_audio_file(job_id, temp_file_path)
            
            # Verify result
            assert result["status"] == "completed"
            assert result["transcription"] == "This is a test transcription"
            assert result["summary"] == "This is a test summary"
            
            # Verify job was updated in database
            db = TestingSessionLocal()
            updated_job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            assert updated_job.status == "completed"
            assert updated_job.transcription == "This is a test transcription"
            assert updated_job.summary == "This is a test summary"
            db.close()
            
            # Verify services were called
            mock_transcription.transcribe_audio.assert_called_once_with(temp_file_path)
            mock_summarization.summarize_text.assert_called_once_with("This is a test transcription")
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    @patch('app.services.transcription.get_transcription_service')
    def test_processing_task_transcription_failure(self, mock_transcription_service):
        """Test processing task when transcription fails"""
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
            mock_transcription.transcribe_audio.side_effect = Exception("Transcription failed")
            mock_transcription_service.return_value = mock_transcription
            
            # Execute the task - should raise exception
            with pytest.raises(Exception, match="Transcription failed"):
                process_audio_file(job_id, temp_file_path)
            
            # Verify job was marked as failed
            db = TestingSessionLocal()
            failed_job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            assert failed_job.status == "failed"
            assert "Transcription failed" in failed_job.error_message
            db.close()
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    @patch('app.services.transcription.get_transcription_service')
    @patch('app.services.summarization.get_summarization_service')
    def test_processing_task_summarization_failure(self, mock_summarization_service, mock_transcription_service):
        """Test processing task when summarization fails but transcription succeeds"""
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
            mock_transcription.transcribe_audio.return_value = "This is a test transcription"
            mock_transcription_service.return_value = mock_transcription
            
            # Mock summarization to fail
            mock_summarization = Mock()
            mock_summarization.summarize_text.side_effect = Exception("Summarization failed")
            mock_summarization_service.return_value = mock_summarization
            
            # Execute the task - should complete with transcription only
            result = process_audio_file(job_id, temp_file_path)
            
            # Verify result - should be completed with transcription but failed summary
            assert result["status"] == "completed"
            assert result["transcription"] == "This is a test transcription"
            assert "Summarization failed" in result["summary"]
            
            # Verify job was updated in database
            db = TestingSessionLocal()
            updated_job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
            assert updated_job.status == "completed"
            assert updated_job.transcription == "This is a test transcription"
            assert "Summarization failed" in updated_job.summary
            db.close()
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
    
    def test_end_to_end_workflow_simulation(self):
        """Test end-to-end workflow simulation without actual API calls"""
        # This test simulates the complete workflow without making real API calls
        
        # Step 1: Upload file
        with patch('app.services.file_handler.FileHandler.save_uploaded_file') as mock_save, \
             patch('app.tasks.process_audio_file.delay') as mock_task:
            
            mock_save.return_value = "/fake/path/test.mp3"
            mock_task.return_value = Mock(id="task-123")
            
            files = {
                'file': ('test.mp3', io.BytesIO(self.mock_mp3_content), 'audio/mpeg')
            }
            
            with TestClient(app) as client:
                upload_response = client.post("/upload", files=files)
                assert upload_response.status_code == 200
                
                job_id = upload_response.json()["job_id"]
        
        # Step 2: Check initial status
        with TestClient(app) as client:
            status_response = client.get(f"/status/{job_id}")
            assert status_response.status_code == 200
            assert status_response.json()["status"] == "pending"
        
        # Step 3: Simulate processing completion by updating database directly
        db = TestingSessionLocal()
        job = db.query(ProcessingJob).filter(ProcessingJob.id == job_id).first()
        job.status = "completed"
        job.transcription = "This is the transcribed text from the audio file."
        job.summary = "This is a summary of the transcription."
        db.commit()
        db.close()
        
        # Step 4: Check final status
        with TestClient(app) as client:
            final_status_response = client.get(f"/status/{job_id}")
            assert final_status_response.status_code == 200
            assert final_status_response.json()["status"] == "completed"
        
        # Step 5: Get results
        with TestClient(app) as client:
            result_response = client.get(f"/result/{job_id}")
            assert result_response.status_code == 200
        
        result_data = result_response.json()
        assert result_data["status"] == "completed"
        assert result_data["transcription"] == "This is the transcribed text from the audio file."
        assert result_data["summary"] == "This is a summary of the transcription."
        assert result_data["error_message"] is None


if __name__ == "__main__":
    # Clean up test database if it exists
    if os.path.exists("test_upload_workflow.db"):
        os.remove("test_upload_workflow.db")
    
    print("🧪 Running Upload Workflow Tests")
    
    test_instance = TestUploadWorkflow()
    
    tests = [
        ("File handler validation", test_instance.test_file_handler_validation),
        ("Complete upload workflow", test_instance.test_complete_upload_workflow),
        ("Processing task success", test_instance.test_processing_task_success),
        ("Processing transcription failure", test_instance.test_processing_task_transcription_failure),
        ("Processing summarization failure", test_instance.test_processing_task_summarization_failure),
        ("End-to-end workflow simulation", test_instance.test_end_to_end_workflow_simulation),
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
    if os.path.exists("test_upload_workflow.db"):
        os.remove("test_upload_workflow.db")