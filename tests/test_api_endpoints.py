"""
Comprehensive API endpoint tests for the audio transcription summarizer
"""
import pytest
import io
import os
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models import Base, ProcessingJob
import uuid

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_api_endpoints.db"
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


def test_root_endpoint():
    """Test the root endpoint"""
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "Audio Transcription Summarizer API" in response.json()["message"]


def test_health_endpoint():
    """Test the health check endpoint"""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "openai_api_key_configured" in data
    assert "openai_api_key_valid" in data


@patch('app.tasks.process_audio_file.delay')
@patch('app.services.file_handler.FileHandler.save_uploaded_file')
def test_upload_valid_mp3_file(mock_save_file, mock_task):
    """Test uploading a valid MP3 file"""
    # Mock the file save and task
    mock_save_file.return_value = "/fake/path/test.mp3"
    mock_task.return_value = Mock(id="task-123")
    
    # Create mock MP3 file content
    mp3_content = b"ID3\x03\x00\x00\x00" + b"fake mp3 content" * 100
    
    files = {
        'file': ('test.mp3', io.BytesIO(mp3_content), 'audio/mpeg')
    }
    
    client = TestClient(app)
    response = client.post("/upload", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "status" in data
    assert data["status"] == "pending"
    
    # Verify task was called
    mock_task.assert_called_once()
    mock_save_file.assert_called_once()


def test_upload_invalid_file_format():
    """Test uploading an invalid file format"""
    # Create a text file instead of MP3
    files = {
        'file': ('test.txt', io.BytesIO(b"This is not an MP3 file"), 'text/plain')
    }
    
    client = TestClient(app)
    response = client.post("/upload", files=files)
    
    assert response.status_code == 400
    assert "detail" in response.json()
    detail = response.json()["detail"].lower()
    assert "mp3" in detail or "audio" in detail or "format" in detail


def test_upload_oversized_file():
    """Test uploading a file that's too large"""
    # Create a large fake MP3 file (over 25MB)
    large_content = b"ID3\x03\x00\x00\x00" + b"x" * (26 * 1024 * 1024)
    
    files = {
        'file': ('large.mp3', io.BytesIO(large_content), 'audio/mpeg')
    }
    
    client = TestClient(app)
    response = client.post("/upload", files=files)
    
    assert response.status_code == 400
    assert "detail" in response.json()
    assert "size" in response.json()["detail"].lower()


def test_status_endpoint_valid_job():
    """Test status endpoint with valid job ID"""
    # Create a test job directly in database
    db = TestingSessionLocal()
    job_id = str(uuid.uuid4())
    job = ProcessingJob(
        id=job_id,
        filename="test.mp3",
        status="processing"
    )
    db.add(job)
    db.commit()
    db.close()
    
    # Test the endpoint
    client = TestClient(app)
    response = client.get(f"/status/{job_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "processing"
    assert data["filename"] == "test.mp3"
    assert "created_at" in data


def test_status_endpoint_invalid_job():
    """Test status endpoint with invalid job ID"""
    fake_job_id = str(uuid.uuid4())
    client = TestClient(app)
    response = client.get(f"/status/{fake_job_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_result_endpoint_completed_job():
    """Test result endpoint with completed job"""
    # Create a test job with results
    db = TestingSessionLocal()
    job_id = str(uuid.uuid4())
    job = ProcessingJob(
        id=job_id,
        filename="test.mp3",
        status="completed",
        transcription="This is a test transcription",
        summary="This is a test summary"
    )
    db.add(job)
    db.commit()
    db.close()
    
    # Test the endpoint
    client = TestClient(app)
    response = client.get(f"/result/{job_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "completed"
    assert data["transcription"] == "This is a test transcription"
    assert data["summary"] == "This is a test summary"
    assert data["error_message"] is None


def test_result_endpoint_failed_job():
    """Test result endpoint with failed job"""
    # Create a test job with error
    db = TestingSessionLocal()
    job_id = str(uuid.uuid4())
    job = ProcessingJob(
        id=job_id,
        filename="test.mp3",
        status="failed",
        error_message="Processing failed"
    )
    db.add(job)
    db.commit()
    db.close()
    
    # Test the endpoint
    client = TestClient(app)
    response = client.get(f"/result/{job_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "failed"
    assert data["transcription"] is None
    assert data["summary"] is None
    assert data["error_message"] == "Processing failed"


def test_result_endpoint_invalid_job():
    """Test result endpoint with invalid job ID"""
    fake_job_id = str(uuid.uuid4())
    client = TestClient(app)
    response = client.get(f"/result/{fake_job_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_upload_no_file():
    """Test upload endpoint without providing a file"""
    client = TestClient(app)
    response = client.post("/upload")
    assert response.status_code == 422  # Unprocessable Entity


def test_upload_empty_file():
    """Test upload endpoint with empty file"""
    files = {
        'file': ('empty.mp3', io.BytesIO(b""), 'audio/mpeg')
    }
    
    client = TestClient(app)
    response = client.post("/upload", files=files)
    assert response.status_code == 400
    assert "detail" in response.json()


if __name__ == "__main__":
    # Clean up test database if it exists
    if os.path.exists("test_api_endpoints.db"):
        os.remove("test_api_endpoints.db")
    
    print("🧪 Running API Endpoint Tests")
    
    tests = [
        ("Root endpoint", test_root_endpoint),
        ("Health endpoint", test_health_endpoint),
        ("Upload valid MP3", test_upload_valid_mp3_file),
        ("Upload invalid format", test_upload_invalid_file_format),
        ("Upload oversized file", test_upload_oversized_file),
        ("Status valid job", test_status_endpoint_valid_job),
        ("Status invalid job", test_status_endpoint_invalid_job),
        ("Result completed job", test_result_endpoint_completed_job),
        ("Result failed job", test_result_endpoint_failed_job),
        ("Result invalid job", test_result_endpoint_invalid_job),
        ("Upload no file", test_upload_no_file),
        ("Upload empty file", test_upload_empty_file),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            print(f"✅ {test_name} - PASSED")
            passed += 1
        except Exception as e:
            print(f"❌ {test_name} - FAILED: {e}")
            failed += 1
    
    print(f"\n📊 Results: {passed} passed, {failed} failed")
    
    # Clean up
    if os.path.exists("test_api_endpoints.db"):
        os.remove("test_api_endpoints.db")