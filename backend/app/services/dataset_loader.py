import os
import pandas as pd
import numpy as np
from typing import Tuple
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models.dataset import Dataset

class DatasetLoader:
    @staticmethod
    def read_dataset_file(file_path: str) -> pd.DataFrame:
        """Centralized, robust dataset reader supporting CSV, XLSX, and XLS formats with explicit engines and fallback detection."""
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Dataset file could not be found.")

        ext = os.path.splitext(file_path)[1].lower()
        df = None
        last_error = None

        if ext == ".csv":
            try:
                df = pd.read_csv(file_path, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file_path, encoding='latin-1')
                except Exception as e:
                    last_error = e
            except Exception as e:
                last_error = e

            # Fallback if csv read failed (e.g. real excel file named .csv)
            if df is None:
                try:
                    df = pd.read_excel(file_path, engine="openpyxl")
                except Exception:
                    pass

        elif ext == ".xlsx":
            try:
                df = pd.read_excel(file_path, engine="openpyxl")
            except Exception as openpyxl_err:
                last_error = openpyxl_err
                # Fallback: Check if file is actually CSV content saved with .xlsx extension
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except Exception:
                    try:
                        df = pd.read_csv(file_path, encoding='latin-1')
                    except Exception:
                        pass

        elif ext == ".xls":
            try:
                df = pd.read_excel(file_path, engine="xlrd")
            except Exception:
                try:
                    df = pd.read_excel(file_path, engine="openpyxl")
                except Exception as e:
                    last_error = e
                    # Fallback: Check if CSV content
                    try:
                        df = pd.read_csv(file_path, encoding='utf-8')
                    except Exception:
                        pass
        else:
            # Fallback for unknown/missing extension: try openpyxl then csv
            try:
                df = pd.read_excel(file_path, engine="openpyxl")
            except Exception:
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except Exception as e:
                    last_error = e

        if df is None:
            err_msg = str(last_error) if last_error else "Unsupported file format or unreadable file content."
            raise HTTPException(
                status_code=400,
                detail=f"Failed to read dataset file '{os.path.basename(file_path)}': {err_msg}"
            )

        if df.empty:
            raise HTTPException(status_code=400, detail="The uploaded dataset is empty.")

        # Replace infinite values with NaN for safe processing
        df = df.replace([np.inf, -np.inf], np.nan)

        # Logging / Debug output as required in Section 5
        print(f"[DATASET] Loading File: {file_path}")
        print(f"[DATASET] Format: {ext}")
        print(f"[DATASET] Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"[DATASET] Columns: {list(df.columns)}")

        return df

    @staticmethod
    def load_dataset(db: Session, dataset_id: int, version: str = "latest") -> Tuple[Dataset, pd.DataFrame, str]:
        """Centralized dataset loading service used by all modules.
        
        Retrieves the actual uploaded file by dataset_id, reads CSV/XLSX into Pandas,
        validates the DataFrame, and returns (dataset_record, dataframe, file_path).
        """
        ds = db.query(Dataset).filter(Dataset.id == dataset_id).first()
        if not ds:
            raise HTTPException(status_code=404, detail="Dataset not found. Please upload or select a valid dataset.")

        # Determine file version path
        if version == "cleaned" or (version == "latest" and ds.cleaned_file_path and os.path.exists(ds.cleaned_file_path)):
            file_path = ds.cleaned_file_path
        else:
            file_path = ds.file_path

        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Dataset file could not be found.")

        print(f"[DATASET] Loading ID: {dataset_id}")
        df = DatasetLoader.read_dataset_file(file_path)

        return ds, df, file_path
