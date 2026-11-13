import os
import pandas as pd
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.dataset_loader import DatasetLoader
from app.services.analytics_engine import AnalyticsEngine
from app.services.forecasting_engine import ForecastingEngine
from app.services.ai_service import AIService

analytics_router = APIRouter(prefix="/analytics", tags=["Natural Language Analytics"])
forecasting_router = APIRouter(prefix="/forecasting", tags=["Predictive Forecasting"])

@analytics_router.post("/query/{dataset_id}")
def nl_query(dataset_id: int, query: str, version: str = "latest", db: Session = Depends(get_db)):
    ds, df, file_path = DatasetLoader.load_dataset(db, dataset_id, version=version)
    return AnalyticsEngine.process_nl_query(query, df)

@analytics_router.get("/correlation-matrix/{dataset_id}")
def correlation_matrix(dataset_id: int, version: str = "latest", db: Session = Depends(get_db)):
    ds, df, file_path = DatasetLoader.load_dataset(db, dataset_id, version=version)
    return AnalyticsEngine.get_correlation_matrix(df)

@analytics_router.get("/insights/{dataset_id}")
def executive_insights(dataset_id: int, db: Session = Depends(get_db)):
    return AIService.get_executive_insights(dataset_id, db)

@forecasting_router.get("/{dataset_id}")
def run_forecast(dataset_id: int, target_column: Optional[str] = None, periods: int = 12, version: str = "latest", db: Session = Depends(get_db)):
    ds, df, file_path = DatasetLoader.load_dataset(db, dataset_id, version=version)
    return ForecastingEngine.forecast(df, target_column=target_column or df.columns[-1], periods=periods)
