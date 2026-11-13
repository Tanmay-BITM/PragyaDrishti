from pydantic import BaseModel
from typing import Optional, List, Any, Dict
import datetime

class DatasetOut(BaseModel):
    id: int
    name: str
    filename: str
    row_count: int
    col_count: int
    file_size_bytes: int
    quality_score: float
    summary_json: Optional[str] = None
    columns_json: Optional[str] = None
    version: int
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class CleaningRequest(BaseModel):
    fill_missing: bool = True
    remove_duplicates: bool = True
    handle_outliers: bool = True
    fix_types: bool = True
    normalize: bool = False

class MLModelOut(BaseModel):
    id: int
    name: str
    task_type: str
    target_column: Optional[str] = None
    best_algorithm: str
    metrics_json: Optional[str] = None
    feature_importance_json: Optional[str] = None
    leaderboard_json: Optional[str] = None
    explanation_text: Optional[str] = None
    feature_columns: Optional[List[str]] = None
    endpoint_url: Optional[str] = None
    status: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class PromptMLRequest(BaseModel):
    prompt: str
    dataset_id: int
    target_column: Optional[str] = None
    version: Optional[str] = "latest"

class AutoMLTrainRequest(BaseModel):
    dataset_id: int
    target_column: Optional[str] = None
    feature_columns: Optional[List[str]] = None
    task_type: Optional[str] = "auto"
    version: Optional[str] = "latest"

class PredictionRequest(BaseModel):
    features: Dict[str, Any]
