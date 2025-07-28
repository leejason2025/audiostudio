"""
Test the status and result endpoints
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db
from app.models import Base, ProcessingJob
import uuid

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_endpoints.db"
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

app.dependency_overrides[get_db] = override_get_db

def test_status_endpoint_valid_job():
    """Test status endpoint with valid job ID"""
    client = TestClient(app)
    
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
    response = client.get(f"/status/{job_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "processing"
    assert data["filename"] == "test.mp3"
    assert "created_at" in data

def test_status_endpoint_invalid_job():
    """Test status endpoint with invalid job ID"""
    client = TestClient(app)
    fake_job_id = str(uuid.uuid4())
    response = client.get(f"/status/{fake_job_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_result_endpoint_valid_job():
    """Test result endpoint with valid job ID"""
    client = TestClient(app)
    
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
    response = client.get(f"/result/{job_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "completed"
    assert data["transcription"] == "This is a test transcription"
    assert data["summary"] == "This is a test summary"
    assert data["error_message"] is None

def test_result_endpoint_invalid_job():
    """Test result endpoint with invalid job ID"""
    client = TestClient(app)
    fake_job_id = str(uuid.uuid4())
    response = client.get(f"/result/{fake_job_id}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]

def test_result_endpoint_failed_job():
    """Test result endpoint with failed job"""
    client = TestClient(app)
    
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
    response = client.get(f"/result/{job_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "failed"
    assert data["transcription"] is None
    assert data["summary"] is None
    assert data["error_message"] == "Processing failed"

if __name__ == "__main__":
    print("🧪 Testing Status and Result Endpoints")
    
    try:
        test_status_endpoint_valid_job()
        print("✅ Status endpoint with valid job - PASSED")
    except Exception as e:
        print(f"❌ Status endpoint with valid job - FAILED: {e}")
    
    try:
        test_status_endpoint_invalid_job()
        print("✅ Status endpoint with invalid job - PASSED")
    except Exception as e:
        print(f"❌ Status endpoint with invalid job - FAILED: {e}")
    
    try:
        test_result_endpoint_valid_job()
        print("✅ Result endpoint with valid job - PASSED")
    except Exception as e:
        print(f"❌ Result endpoint with valid job - FAILED: {e}")
    
    try:
        test_result_endpoint_invalid_job()
        print("✅ Result endpoint with invalid job - PASSED")
    except Exception as e:
        print(f"❌ Result endpoint with invalid job - FAILED: {e}")
    
    try:
        test_result_endpoint_failed_job()
        print("✅ Result endpoint with failed job - PASSED")
    except Exception as e:
        print(f"❌ Result endpoint with failed job - FAILED: {e}")
    
    print("\n🎉 All endpoint tests completed!")