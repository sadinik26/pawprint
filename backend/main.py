
from fastapi import FastAPI

app = FastAPI(
    title="Pawprint API",
    description="Lost Dog Matcher using Computer Vision and Image Similarity",
    version="1.0.0"
)


@app.get("/")
async def home():
    return {
        "message": "Welcome to Pawprint!",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "application": "Pawprint"
    }
