#!/usr/bin/env python3
"""
Test script to verify Celery task processing works correctly.
This tests the process_audio_file task without requiring Redis to be running.
"""

import sys
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.tasks import process_audio_file, update_job_status
from app.database import SessionLocal
from app.models import ProcessingJob

def test_update_job_status():
    """Test the update_job_status function"""
    print("🧪 Testing update_job_status function...")
    
    # Create a test job in the database
    db = SessionLocal()
    try:
        # Create a test job
        test_job = ProcessingJob(
            id="test-job-123",
            filename="test.mp3",
            status="pending"
        )
        db.add(test_job)
        db.commit()
        
        # Test updating status
        update_job_status("test-job-123", "processing")
        
        # Verify the update
        updated_job = db.query(ProcessingJob).filter(ProcessingJob.id == "test-job-123").first()
        if updated_job and updated_job.status == "processing":
            print("✅ update_job_status works correctly")
            
            # Test updating with additional fields
            update_job_status("test-job-123", "completed", transcription="Test transcription", summary="Test summary")
            
            # Refresh the database session to get updated data
            db.refresh(updated_job)
            final_job = db.query(ProcessingJob).filter(ProcessingJob.id == "test-job-123").first()
            if (final_job and final_job.status == "completed" and 
                final_job.transcription == "Test transcription" and 
                final_job.summary == "Test summary"):
                print("✅ update_job_status with additional fields works correctly")
                return True
            else:
                print(f"❌ update_job_status with additional fields failed")
                print(f"   Status: {final_job.status if final_job else 'None'}")
                print(f"   Transcription: {final_job.transcription if final_job else 'None'}")
                print(f"   Summary: {final_job.summary if final_job else 'None'}")
                return False
        else:
            print("❌ update_job_status failed")
            return False
            
    except Exception as e:
        print(f"❌ Error testing update_job_status: {e}")
        return False
    finally:
        # Clean up test data
        try:
            db.query(ProcessingJob).filter(ProcessingJob.id == "test-job-123").delete()
            db.commit()
        except:
            pass
        db.close()

def test_task_processing_logic():
    """Test the task processing logic with mocked services"""
    print("\n🧪 Testing task processing logic with mocked services...")
    
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
        temp_file.write(b"fake mp3 content")
        temp_file_path = temp_file.name
    
    try:
        # Create a test job in the database
        db = SessionLocal()
        test_job = ProcessingJob(
            id="test-task-456",
            filename="test.mp3",
            status="pending"
        )
        db.add(test_job)
        db.commit()
        db.close()
        
        # Mock the transcription and summarization services
        with patch('app.tasks.get_transcription_service') as mock_transcription_service, \
             patch('app.tasks.get_summarization_service') as mock_summarization_service:
            
            # Set up mocks
            mock_transcription_instance = MagicMock()
            mock_transcription_instance.transcribe_audio.return_value = "This is a test transcription of the audio file."
            mock_transcription_service.return_value = mock_transcription_instance
            
            mock_summarization_instance = MagicMock()
            mock_summarization_instance.summarize_text.return_value = "Test summary: Audio file transcription."
            mock_summarization_service.return_value = mock_summarization_instance
            
            # Create a mock task instance
            mock_task = MagicMock()
            
            # Execute the task function directly (not as a Celery task)
            with patch('app.tasks.current_task', mock_task):
                result = process_audio_file.run("test-task-456", temp_file_path)
            
            # Verify the result
            if (result and result.get("status") == "completed" and 
                result.get("transcription") == "This is a test transcription of the audio file." and
                result.get("summary") == "Test summary: Audio file transcription."):
                
                print("✅ Task processing logic works correctly")
                
                # Verify database was updated
                db = SessionLocal()
                final_job = db.query(ProcessingJob).filter(ProcessingJob.id == "test-task-456").first()
                db.close()
                
                if (final_job and final_job.status == "completed" and 
                    final_job.transcription and final_job.summary):
                    print("✅ Database was updated correctly")
                    return True
                else:
                    print("❌ Database was not updated correctly")
                    return False
            else:
                print(f"❌ Task processing failed. Result: {result}")
                return False
                
    except Exception as e:
        print(f"❌ Error testing task processing: {e}")
        return False
    finally:
        # Clean up
        try:
            os.unlink(temp_file_path)
        except:
            pass
        try:
            db = SessionLocal()
            db.query(ProcessingJob).filter(ProcessingJob.id == "test-task-456").delete()
            db.commit()
            db.close()
        except:
            pass

def test_task_error_handling():
    """Test task error handling"""
    print("\n🧪 Testing task error handling...")
    
    # Create a test job in the database
    db = SessionLocal()
    test_job = ProcessingJob(
        id="test-error-789",
        filename="test.mp3",
        status="pending"
    )
    db.add(test_job)
    db.commit()
    db.close()
    
    try:
        # Mock the transcription service to raise an exception
        with patch('app.tasks.get_transcription_service') as mock_transcription_service:
            mock_transcription_instance = MagicMock()
            mock_transcription_instance.transcribe_audio.side_effect = Exception("Transcription failed")
            mock_transcription_service.return_value = mock_transcription_instance
            
            # Create a mock task instance
            mock_task = MagicMock()
            
            # Execute the task function and expect it to raise an exception
            try:
                with patch('app.tasks.current_task', mock_task):
                    process_audio_file.run("test-error-789", "nonexistent_file.mp3")
                print("❌ Task should have raised an exception")
                return False
            except Exception as e:
                if "Audio processing failed" in str(e):
                    print("✅ Task error handling works correctly")
                    
                    # Verify database was updated with error status
                    db = SessionLocal()
                    error_job = db.query(ProcessingJob).filter(ProcessingJob.id == "test-error-789").first()
                    db.close()
                    
                    if error_job and error_job.status == "failed" and error_job.error_message:
                        print("✅ Database was updated with error status")
                        return True
                    else:
                        print("❌ Database was not updated with error status")
                        return False
                else:
                    print(f"❌ Unexpected error: {e}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error testing error handling: {e}")
        return False
    finally:
        # Clean up
        try:
            db = SessionLocal()
            db.query(ProcessingJob).filter(ProcessingJob.id == "test-error-789").delete()
            db.commit()
            db.close()
        except:
            pass

if __name__ == "__main__":
    print("🚀 Celery Task Testing")
    print("This script tests the Celery task processing logic without requiring Redis.")
    print("=" * 70)
    
    # Initialize database
    from app.database import create_tables
    create_tables()
    
    # Run tests
    test1_success = test_update_job_status()
    test2_success = test_task_processing_logic()
    test3_success = test_task_error_handling()
    
    print("\n" + "=" * 70)
    print("📊 TEST RESULTS:")
    print(f"   update_job_status: {'✅ PASS' if test1_success else '❌ FAIL'}")
    print(f"   Task processing:   {'✅ PASS' if test2_success else '❌ FAIL'}")
    print(f"   Error handling:    {'✅ PASS' if test3_success else '❌ FAIL'}")
    
    if all([test1_success, test2_success, test3_success]):
        print("\n🏁 All Celery task tests passed!")
        print("\nNext steps:")
        print("1. Start Redis server: redis-server")
        print("2. Start Celery worker: python start_worker.py")
        print("3. Start FastAPI server: uvicorn app.main:app --reload")
        print("4. Test the full pipeline by uploading an MP3 file")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")