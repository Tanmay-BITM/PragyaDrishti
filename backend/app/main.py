from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base

# Import all models to ensure creation
from app.models.user import User
from app.models.dataset import Dataset
from app.models.ml_model import MLModel
from app.models.report import Report

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Powered Data Visualization & Prompt-to-ML Assistant SaaS API"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from app.api.v1.auth import router as auth_router
from app.api.v1.datasets import router as datasets_router
from app.api.v1.prompt_ml import router as prompt_ml_router
from app.api.v1.automl import router as automl_router
from app.api.v1.analytics import analytics_router, forecasting_router
from app.api.v1.reports import reports_router
from app.api.v1.admin import admin_router
from app.api.v1.chatbot import chatbot_router

app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(datasets_router, prefix=settings.API_V1_STR)
app.include_router(prompt_ml_router, prefix=settings.API_V1_STR)
app.include_router(automl_router, prefix=settings.API_V1_STR)
app.include_router(analytics_router, prefix=settings.API_V1_STR)
app.include_router(forecasting_router, prefix=settings.API_V1_STR)
app.include_router(reports_router, prefix=settings.API_V1_STR)
app.include_router(admin_router, prefix=settings.API_V1_STR)
app.include_router(chatbot_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "message": "Welcome to PragyaDrishti AI Data Platform API",
        "docs": "/docs",
        "version": settings.VERSION
    }
