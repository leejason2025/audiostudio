from fastapi import FastAPI
from app.database import create_tables

app = FastAPI(
    title="Audio Transcription Summarizer",
    description="API for transcribing MP3 files and generating summaries",
    version="1.0.0"
)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    create_tables()

@app.get("/")
async def root():
    return {"message": "Audio Transcription Summarizer API"}