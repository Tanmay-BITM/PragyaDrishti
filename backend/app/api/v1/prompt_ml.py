import os
import json
import joblib
import pandas as pd
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.dataset import Dataset
from app.models.ml_model import MLModel
from app.schemas.dataset import PromptMLRequest, MLModelOut, PredictionRequest
from app.services.dataset_loader import DatasetLoader
from app.services.prompt_engine import PromptEngine
from app.services.automl_engine import AutoMLEngine

router = APIRouter(prefix="/prompt-ml", tags=["Prompt-to-ML Engine"])

@router.post("/train", response_model=MLModelOut)
def train_from_prompt(req: PromptMLRequest, db: Session = Depends(get_db)):
    ds, df, file_path = DatasetLoader.load_dataset(db, req.dataset_id, version=req.version or "latest")

    # 1. Analyze prompt & schema
    analysis = PromptEngine.analyze_prompt_and_dataset(req.prompt, df, target_override=req.target_column)
    
    task_type = analysis["task_type"]
    target_column = analysis["target_column"]
    target_selection_source = analysis["target_selection_source"]
    prompt_features = analysis.get("prompt_features")

    if analysis.get("needs_target_selection") and not target_column:
        raise HTTPException(
            status_code=400,
            detail=f"Target column could not be inferred from prompt '{req.prompt}'. Please explicitly select target column from candidates: {analysis.get('candidate_columns', [])}"
        )
    
    # 2. Run AutoML comparison & fit best model
    try:
        automl_result = AutoMLEngine.train_and_evaluate(
            df=df,
            task_type=task_type,
            target_column=target_column,
            feature_columns=prompt_features,
            target_selection_source=target_selection_source,
            dataset_id=ds.id
        )
    except ValueError as val_err:
        raise HTTPException(status_code=400, detail=str(val_err))
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"AutoML Training Error: {str(err)}")

    # 3. Register model in DB safely
    try:
        explanation_json = json.dumps(automl_result.get("explanation_dict", {}))
        ml_model = MLModel(
            name=f"Model_{automl_result['task_type']}_{ds.name}",
            task_type=automl_result["task_type"],
            target_column=automl_result["target_column"],
            best_algorithm=automl_result["best_algorithm"],
            file_path=automl_result["model_file_path"],
            metrics_json=json.dumps(automl_result["metrics"]),
            feature_importance_json=json.dumps(automl_result["feature_importance"]),
            leaderboard_json=json.dumps(automl_result["leaderboard"]),
            explanation_text=explanation_json,
            endpoint_url=f"/api/v1/prompt-ml/predict",
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
        raise HTTPException(status_code=400, detail=f"Failed to record trained model metadata: {str(db_err)}")

@router.post("/predict/{model_id}")
def predict_model(model_id: int, req: PredictionRequest, db: Session = Depends(get_db)):
    model_record = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not model_record or not os.path.exists(model_record.file_path):
        raise HTTPException(status_code=404, detail=f"Trained model artifact #{model_id} not found on disk.")
        
    try:
        artifact = joblib.load(model_record.file_path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to load model artifact: {str(e)}")

    feature_cols = artifact.get("feature_cols", [])
    pipeline = artifact.get("pipeline")
    label_encoder = artifact.get("label_encoder")

    if not req.features:
        raise HTTPException(status_code=400, detail="Prediction features payload cannot be empty.")

    # Build input DataFrame matching exact feature schema
    input_df = pd.DataFrame([req.features])
    missing_input_cols = [c for c in feature_cols if c not in input_df.columns]
    for col in missing_input_cols:
        input_df[col] = np.nan

    input_df = input_df[feature_cols]

    try:
        if pipeline:
            raw_pred = pipeline.predict(input_df)
            estimator = pipeline.named_steps.get('model')
            prob = pipeline.predict_proba(input_df).tolist() if hasattr(estimator, "predict_proba") else None
        else:
            preprocessor = artifact["preprocessor"]
            model = artifact["model"]
            processed_input = preprocessor.transform(input_df)
            raw_pred = model.predict(processed_input)
            prob = model.predict_proba(processed_input).tolist() if hasattr(model, "predict_proba") else None

        pred_val = raw_pred[0]
        if label_encoder and isinstance(pred_val, (int, np.integer)):
            pred_label = str(label_encoder.inverse_transform([pred_val])[0])
        else:
            pred_label = float(pred_val) if isinstance(pred_val, (float, np.floating)) else str(pred_val)

        return {
            "model_id": model_record.id,
            "algorithm": model_record.best_algorithm,
            "target_column": model_record.target_column,
            "prediction": pred_label,
            "probabilities": prob,
            "status": "SUCCESS"
        }
    except Exception as err:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {str(err)}")

@router.get("/download-model/{model_id}")
def download_model(model_id: int, db: Session = Depends(get_db)):
    model_record = db.query(MLModel).filter(MLModel.id == model_id).first()
    if not model_record or not os.path.exists(model_record.file_path):
        raise HTTPException(status_code=404, detail=f"Model artifact file #{model_id} not found.")
    return FileResponse(path=model_record.file_path, filename=os.path.basename(model_record.file_path), media_type="application/octet-stream")

@router.get("/models/{dataset_id}", response_model=list[MLModelOut])
def get_dataset_models(dataset_id: int, db: Session = Depends(get_db)):
    models = db.query(MLModel).filter(MLModel.dataset_id == dataset_id).order_by(MLModel.created_at.desc()).all()
    result = []
    for m in models:
        feat_cols = []
        if m.explanation_text:
            try:
                exp = json.loads(m.explanation_text)
                feat_cols = exp.get("used_features", [])
            except Exception:
                pass

        if not feat_cols and os.path.exists(m.file_path):
            try:
                artifact = joblib.load(m.file_path)
                feat_cols = artifact.get("feature_cols", [])
            except Exception:
                pass

        if not feat_cols and m.feature_importance_json:
            try:
                fi = json.loads(m.feature_importance_json)
                feat_cols = list(fi.keys())
            except Exception:
                pass

        m_dict = {
            "id": m.id,
            "name": m.name,
            "task_type": m.task_type,
            "target_column": m.target_column,
            "best_algorithm": m.best_algorithm,
            "metrics_json": m.metrics_json,
            "feature_importance_json": m.feature_importance_json,
            "leaderboard_json": m.leaderboard_json,
            "explanation_text": m.explanation_text,
            "feature_columns": feat_cols,
            "endpoint_url": m.endpoint_url,
            "status": m.status,
            "created_at": m.created_at
        }
        result.append(m_dict)
    return result

