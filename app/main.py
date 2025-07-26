from fastapi import FastAPI

app = FastAPI(
    title="Audio Transcription Summarizer",
    description="API for transcribing MP3 files and generating summaries",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "Audio Transcription Summarizer API"}