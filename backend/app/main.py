from fastapi import FastAPI

from app.api.upload import router as upload_router

app = FastAPI(
    title="DermAI API",
    description="Backend API for the DermAI skin lesion analysis system.",
    version="1.0.0",
)


@app.get("/")
def root():
    return {
        "message": "Welcome to DermAI API",
        "status": "running",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "DermAI API",
    }


app.include_router(upload_router)
