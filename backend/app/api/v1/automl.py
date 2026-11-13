import os
import json
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.dataset import Dataset
from app.models.ml_model import MLModel
from app.schemas.dataset import AutoMLTrainRequest, MLModelOut
from app.services.dataset_loader import DatasetLoader
from app.services.automl_engine import AutoMLEngine

router = APIRouter(prefix="/automl", tags=["AutoML Benchmark Engine"])

@router.post("/train", response_model=MLModelOut)
def run_automl(req: AutoMLTrainRequest, db: Session = Depends(get_db)):
    ds, df, file_path = DatasetLoader.load_dataset(db, req.dataset_id, version=req.version or "latest")

    try:
        result = AutoMLEngine.train_and_evaluate(
            df=df,
            target_column=req.target_column,
            feature_columns=req.feature_columns,
            task_type=req.task_type,
            dataset_id=ds.id
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"AutoML Training Error: {str(err)}")

    # Register model in database safely
    try:
        ml_model = MLModel(
            name=f"AutoML_{result['task_type']}_{ds.name}",
            task_type=result["task_type"],
            target_column=result["target_column"],
            best_algorithm=result["best_algorithm"],
            file_path=result["model_file_path"],
            metrics_json=json.dumps(result["metrics"]),
            feature_importance_json=json.dumps(result["feature_importance"]),
            leaderboard_json=json.dumps(result["leaderboard"]),
            explanation_text=result["explanation"],
            endpoint_url="/api/v1/prompt-ml/predict",
            status="ACTIVE",
            owner_id=None,
            dataset_id=ds.id
        )
        db.add(ml_model)
        db.commit()
        db.refresh(ml_model)
        return ml_model
    except Exception as db_err:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to record AutoML model metadata: {str(db_err)}")

@router.get("/models/{dataset_id}", response_model=list[MLModelOut])
def list_dataset_models(dataset_id: int, db: Session = Depends(get_db)):
    return db.query(MLModel).filter(MLModel.dataset_id == dataset_id).order_by(MLModel.created_at.desc()).all()
