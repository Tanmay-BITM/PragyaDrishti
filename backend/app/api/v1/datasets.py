import os
import json
import pandas as pd
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.models.dataset import Dataset
from app.schemas.dataset import DatasetOut, CleaningRequest
from app.services.data_cleaner import DataCleaner
from app.services.dataset_loader import DatasetLoader

router = APIRouter(prefix="/datasets", tags=["Datasets"])

@router.post("/upload", response_model=DatasetOut)
async def upload_dataset(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if not file.filename or not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only CSV and Excel files (.csv, .xlsx, .xls) are supported.")
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_location = os.path.join(settings.UPLOAD_DIR, file.filename)
    
    try:
        contents = await file.read()
        with open(file_location, "wb") as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to save file on server: {str(e)}")
        
    try:
        df = DatasetLoader.read_dataset_file(file_location)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse uploaded dataset '{file.filename}': {str(e)}")

    if df.empty:
        raise HTTPException(status_code=400, detail=f"Uploaded dataset '{file.filename}' is empty (0 rows).")

    try:
        inspection = DataCleaner.inspect_dataset(df)
        
        # Check if dataset with the same filename already exists
        existing = db.query(Dataset).filter(Dataset.filename == file.filename).first()
        if existing:
            existing.name = file.filename.split(".")[0]
            existing.file_path = file_location
            existing.row_count = inspection["row_count"]
            existing.col_count = inspection["col_count"]
            existing.file_size_bytes = len(contents)
            existing.quality_score = inspection["quality_score"]
            existing.summary_json = json.dumps(inspection)
            existing.columns_json = json.dumps(inspection["columns"])
            existing.cleaned_file_path = None
            existing.version = 1
            db.commit()
            db.refresh(existing)
            return existing

        dataset = Dataset(
            name=file.filename.split(".")[0],
            filename=file.filename,
            file_path=file_location,
            row_count=inspection["row_count"],
            col_count=inspection["col_count"],
            file_size_bytes=len(contents),
            quality_score=inspection["quality_score"],
            summary_json=json.dumps(inspection),
            columns_json=json.dumps(inspection["columns"]),
            owner_id=None
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        return dataset
    except Exception as err:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Failed to store dataset metadata: {str(err)}")

def deduplicate_dataset_records(db: Session):
    """Ensure each unique filename has only one dataset record, re-pointing any ML models."""
    from app.models.ml_model import MLModel
    all_ds = db.query(Dataset).order_by(Dataset.id.asc()).all()
    seen = {}
    changed = False
    for ds in all_ds:
        if ds.filename not in seen:
            seen[ds.filename] = ds.id
        else:
            canonical_id = seen[ds.filename]
            db.query(MLModel).filter(MLModel.dataset_id == ds.id).update({"dataset_id": canonical_id})
            db.delete(ds)
            changed = True
    if changed:
        db.commit()

@router.get("/list", response_model=list[DatasetOut])
def list_datasets(db: Session = Depends(get_db)):
    deduplicate_dataset_records(db)
    return db.query(Dataset).order_by(Dataset.created_at.desc()).all()

@router.get("/{dataset_id}", response_model=DatasetOut)
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail=f"Dataset #{dataset_id} not found.")
    return ds

@router.get("/{dataset_id}/preview")
def preview_dataset(dataset_id: int, limit: int = 50, version: str = "latest", db: Session = Depends(get_db)):
    ds, df, file_path = DatasetLoader.load_dataset(db, dataset_id, version=version)
    inspection = DataCleaner.inspect_dataset(df)
    
    return {
        "dataset_id": ds.id,
        "name": ds.name,
        "filename": ds.filename,
        "version": version,
        "quality_score": inspection["quality_score"],
        "rows": df.head(limit).fillna("").to_dict(orient="records"),
        "columns": list(df.columns),
        "columns_info": inspection["columns"],
        "missing_per_column": inspection["missing_per_column"],
        "total_rows": len(df),
        "total_cols": len(df.columns)
    }

@router.post("/{dataset_id}/auto-clean")
def auto_clean_dataset(dataset_id: int, req: CleaningRequest, db: Session = Depends(get_db)):
    ds, original_df, original_path = DatasetLoader.load_dataset(db, dataset_id, version="original")
    
    cleaned_df, report = DataCleaner.auto_clean(
        df=original_df,
        fill_missing=req.fill_missing,
        remove_duplicates=req.remove_duplicates,
        handle_outliers=req.handle_outliers
    )
    
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    cleaned_path = os.path.join(settings.UPLOAD_DIR, f"cleaned_v{ds.version + 1}_{ds.filename}")
    if ds.filename.lower().endswith(('.xlsx', '.xls')):
        try:
            cleaned_df.to_excel(cleaned_path, engine='openpyxl', index=False)
        except Exception:
            cleaned_df.to_csv(cleaned_path, index=False)
    else:
        cleaned_df.to_csv(cleaned_path, index=False)
    
    ds.cleaned_file_path = cleaned_path
    ds.quality_score = report["new_quality_score"]
    ds.version += 1
    ds.summary_json = json.dumps(DataCleaner.inspect_dataset(cleaned_df))
    db.commit()
    
    return {
        "message": "Dataset auto-cleaned successfully.",
        "dataset_id": ds.id,
        "version": ds.version,
        "report": report
    }
