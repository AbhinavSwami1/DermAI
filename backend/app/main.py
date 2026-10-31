from fastapi import FastAPI

from app.api.upload import router as upload_router
from app.api.users import router as users_router
from app.api.cases import router as cases_router
from app.api.auth import router as auth_router
from app.api.roles import router as roles_router
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.rate_limit import limiter
from app.api.predictions import router as predictions_router

app = FastAPI(
    title="DermAI API",
    description="Backend API for the DermAI skin lesion analysis system.",
    version="1.0.0",
)
app.state.limiter = limiter
app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
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
app.include_router(users_router)
app.include_router(cases_router)
app.include_router(auth_router)
app.include_router(roles_router)
app.include_router(predictions_router)
